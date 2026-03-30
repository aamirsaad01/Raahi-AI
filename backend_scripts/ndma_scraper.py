"""
NDMA Scraper
Scrapes advisories from NDMA Pakistan website and extracts hazard alerts using AI
"""
import os
import re
import requests
import hashlib
import logging
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pdfplumber
import PyPDF2
from io import BytesIO

from ai_alert_extractor import AIAlertExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)


class NDMAScraper:
    """Scraper for NDMA advisories"""
    
    def __init__(self):
        self.base_url = "http://www.ndma.gov.pk"
        self.advisories_url = f"{self.base_url}/advisories"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Initialize AI extractor (optional - will fallback if not available)
        self.ai_extractor = None
        try:
            self.ai_extractor = AIAlertExtractor()
            logger.info("✅ AI extractor initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize AI extractor: {e}")
            logger.warning("⚠️ Will use fallback extraction method")
    
    def scrape_advisories(self) -> List[Dict]:
        """
        Scrape all advisories from NDMA website
        Each advisory has a "View" button that links to a PDF
        
        Returns:
            List of advisory dictionaries with title, url, date, etc.
        """
        try:
            logger.info(f"📡 Fetching advisories from {self.advisories_url}")
            response = self.session.get(self.advisories_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            advisories = []
            
            # Step 1: Find all advisory cards
            advisory_cards = soup.find_all('div', class_=lambda x: x and 'advisory' in str(x).lower() and 'card' in str(x).lower())
            logger.info(f"📋 Found {len(advisory_cards)} advisory cards")
            
            if not advisory_cards:
                logger.warning("No advisory cards found. Website structure may have changed.")
                return []
            
            # Step 2: Find ALL "View" links on the page (they should match the cards)
            all_view_links = soup.find_all('a', href=True, string=re.compile(r'view', re.I))
            # Also find links with empty text that might be View buttons
            all_links = soup.find_all('a', href=True)
            view_links_by_position = []
            
            for link in all_links:
                link_text = link.get_text(strip=True).lower()
                if link_text == 'view' or (link_text == '' and 'view' in str(link.get('class', [])).lower()):
                    view_links_by_position.append(link)
            
            logger.info(f"📋 Found {len(view_links_by_position)} 'View' links on page")
            
            # Step 3: Extract advisories - match cards with their View links
            for idx, card in enumerate(advisory_cards, 1):
                try:
                    # Extract title
                    title = None
                    title_elem = card.find(['h4', 'h3', 'h2', 'h1'], class_=lambda x: x and 'title' in str(x).lower())
                    if not title_elem:
                        title_elem = card.find(['h4', 'h3', 'h2', 'h1'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    
                    if not title:
                        all_text = card.get_text(separator='\n', strip=True)
                        lines = [line.strip() for line in all_text.split('\n') if line.strip() and len(line.strip()) > 5]
                        for line in lines:
                            if not re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line) and 'view' not in line.lower():
                                title = line
                                break
                    
                    if not title or len(title) < 3:
                        continue
                    
                    title = ' '.join(title.split()).strip()
                    logger.info(f"📋 Advisory {idx}: {title[:60]}")
                    
                    # Find the "View" link for this advisory
                    # The parent of advisory-card is often the <a> tag with the PDF URL
                    href = None
                    
                    # Method 1: Check if parent is a link (most common case for NDMA)
                    parent = card.parent
                    if parent and parent.name == 'a':
                        href = parent.get('href', '')
                        if href:
                            logger.info(f"   ✅ Found link in parent: {href}")
                    
                    # Method 2: Look inside the card for "View" link
                    if not href:
                        card_links = card.find_all('a', href=True)
                        for link in card_links:
                            if link.get_text(strip=True).lower() == 'view':
                                href = link.get('href', '')
                                if href:
                                    logger.info(f"   ✅ Found 'View' link in card: {href}")
                                break
                    
                    # Method 3: Match by position (View links should be in same order as cards)
                    if not href and idx <= len(view_links_by_position):
                        href = view_links_by_position[idx - 1].get('href', '')
                        if href:
                            logger.info(f"   ✅ Found 'View' link by position: {href}")
                    
                    # Method 4: Look in parent for any link
                    if not href and parent:
                        parent_view = parent.find('a', href=True, string=re.compile(r'view', re.I))
                        if parent_view:
                            href = parent_view.get('href', '')
                            if href:
                                logger.info(f"   ✅ Found link in parent element: {href}")
                    
                    # Method 5: Find any link in card
                    if not href:
                        card_links = card.find_all('a', href=True)
                        for link in card_links:
                            potential_href = link.get('href', '').strip()
                            if potential_href and not potential_href.startswith('#'):
                                href = potential_href
                                logger.info(f"   ✅ Found link (fallback): {href}")
                                break
                    
                    if not href:
                        logger.warning(f"   ❌ No View link found for: {title[:50]}")
                        continue
                    
                    # Make absolute URL
                    if href.startswith('http'):
                        advisory_url = href
                    elif href.startswith('/'):
                        advisory_url = f"{self.base_url}{href}"
                    else:
                        advisory_url = urljoin(self.advisories_url, href)
                    
                    logger.info(f"   ✅ View URL: {advisory_url}")
                    
                    # Extract date
                    date_str = ''
                    date_elem = card.find(['p', 'span', 'div'], class_=lambda x: x and 'date' in str(x).lower())
                    if date_elem:
                        date_str = date_elem.get_text(strip=True)
                    if not date_str:
                        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', card.get_text())
                        if date_match:
                            date_str = date_match.group(1)
                    
                    published_date = self._parse_date(date_str)
                    
                    advisories.append({
                        'title': title,
                        'advisory_url': advisory_url,  # This URL will be used to fetch PDF
                        'published_date': published_date,
                        'affected_regions': self._extract_regions_from_title(title),
                        'severity': self._determine_severity(title),
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing card {idx}: {e}", exc_info=True)
                    continue
            
            logger.info(f"✅ Scraped {len(advisories)} advisories")
            return advisories
            
        except Exception as e:
            logger.error(f"❌ Error scraping advisories: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def fetch_advisory_content(self, advisory_url: str) -> Optional[str]:
        """
        Fetch PDF content from advisory URL
        Handles both direct PDF links and secure-viewer pages
        
        Args:
            advisory_url: URL to the advisory (may be PDF or viewer page)
            
        Returns:
            PDF text content or None if failed
        """
        try:
            logger.info(f"📥 Fetching content from: {advisory_url}")
            
            # Handle secure-viewer URLs - extract PDF path from query parameter
            if 'secure-viewer' in advisory_url.lower():
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(advisory_url)
                params = urlparse.parse_qs(parsed.query)
                if 'file' in params:
                    pdf_path = urlparse.unquote(params['file'][0])
                    # Make absolute URL
                    if pdf_path.startswith('/'):
                        pdf_url = f"{self.base_url}{pdf_path}"
                    else:
                        pdf_url = pdf_path
                    logger.info(f"📄 Extracted PDF URL from secure-viewer: {pdf_url}")
                    # Download the actual PDF
                    pdf_response = self.session.get(pdf_url, timeout=60, stream=True)
                    pdf_response.raise_for_status()
                    return self._extract_pdf_text(BytesIO(pdf_response.content))
            
            # Handle secure-viewer URLs first - extract PDF path directly from URL parameter
            if 'secure-viewer' in advisory_url.lower():
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(advisory_url)
                params = urlparse.parse_qs(parsed.query)
                if 'file' in params:
                    pdf_path = urlparse.unquote(params['file'][0])
                    # Make absolute URL
                    if pdf_path.startswith('/'):
                        pdf_url = f"{self.base_url}{pdf_path}"
                    else:
                        pdf_url = pdf_path
                    logger.info(f"📄 Extracted PDF URL from secure-viewer: {pdf_url}")
                    # Download the actual PDF directly
                    pdf_response = self.session.get(pdf_url, timeout=60, stream=True)
                    pdf_response.raise_for_status()
                    # Verify it's actually a PDF
                    content_type = pdf_response.headers.get('Content-Type', '').lower()
                    if 'pdf' in content_type:
                        logger.info("✅ Confirmed PDF content type, extracting text...")
                        return self._extract_pdf_text(BytesIO(pdf_response.content))
                    else:
                        logger.warning(f"⚠️ Expected PDF but got content-type: {content_type}")
                        # Try extracting anyway
                        return self._extract_pdf_text(BytesIO(pdf_response.content))
            
            # For direct PDF URLs or other URLs, fetch and check
            response = self.session.get(advisory_url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # Check if response is already a PDF
            content_type = response.headers.get('Content-Type', '').lower()
            if 'pdf' in content_type or advisory_url.lower().endswith('.pdf'):
                # Direct PDF - extract text
                logger.info("📄 Direct PDF detected, extracting text...")
                return self._extract_pdf_text(BytesIO(response.content))
            
            # Not a direct PDF - try to find PDF link in HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            pdf_url = None
            
            # Method 1: Look for PDF iframe
            pdf_iframe = soup.find('iframe', src=re.compile(r'\.pdf|pdf|viewer', re.I))
            if pdf_iframe:
                pdf_url = pdf_iframe.get('src')
                logger.debug(f"Found PDF in iframe: {pdf_url}")
            
            # Method 2: Look for PDF link
            if not pdf_url:
                pdf_link = soup.find('a', href=re.compile(r'\.pdf|pdf', re.I))
                if pdf_link:
                    pdf_url = pdf_link.get('href')
                    logger.debug(f"Found PDF link: {pdf_url}")
            
            # Method 3: Look for embed/object with PDF
            if not pdf_url:
                pdf_embed = soup.find(['embed', 'object'], src=re.compile(r'\.pdf|pdf', re.I))
                if pdf_embed:
                    pdf_url = pdf_embed.get('src') or pdf_embed.get('data')
                    logger.debug(f"Found PDF in embed/object: {pdf_url}")
            
            # If we found a PDF URL, make it absolute and download
            if pdf_url:
                if not pdf_url.startswith('http'):
                    pdf_url = urljoin(advisory_url, pdf_url)
                logger.info(f"📥 Downloading PDF from extracted URL: {pdf_url}")
                pdf_response = self.session.get(pdf_url, timeout=60, stream=True)
                pdf_response.raise_for_status()
                return self._extract_pdf_text(BytesIO(pdf_response.content))
            
            # If no PDF found, log warning
            logger.warning(f"⚠️ Could not find PDF in advisory page: {advisory_url}")
            logger.debug(f"Page content type: {content_type}")
            logger.debug(f"Page title: {soup.title.string if soup.title else 'No title'}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error fetching PDF content from {advisory_url}: {e}")
            return None
    
    def _extract_pdf_text(self, pdf_bytes: BytesIO) -> Optional[str]:
        """
        Extract text from PDF bytes
        
        Args:
            pdf_bytes: BytesIO object containing PDF data
            
        Returns:
            Extracted text or None if failed
        """
        # Try pdfplumber first (better text extraction)
        try:
            pdf_bytes.seek(0)
            with pdfplumber.open(pdf_bytes) as pdf:
                text_parts = []
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                        logger.debug(f"Extracted {len(page_text)} chars from page {page_num}")
                if text_parts:
                    full_text = '\n\n'.join(text_parts)
                    logger.info(f"✅ Extracted {len(full_text)} characters from PDF using pdfplumber")
                    return full_text
        except Exception as e:
            logger.debug(f"pdfplumber failed, trying PyPDF2: {e}")
        
        # Fallback to PyPDF2
        try:
            pdf_bytes.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_bytes)
            text_parts = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                    logger.debug(f"Extracted {len(page_text)} chars from page {page_num}")
            if text_parts:
                full_text = '\n\n'.join(text_parts)
                logger.info(f"✅ Extracted {len(full_text)} characters from PDF using PyPDF2")
                return full_text
        except Exception as e:
            logger.error(f"❌ Failed to extract text from PDF: {e}")
            return None
        
        logger.warning("⚠️ No text could be extracted from PDF")
        return None
    
    def _summarize_pdf_text(self, pdf_content: str, max_words: int = 400) -> str:
        """
        Create a brief summary of PDF text using extractive summarization
        Focuses on sentences containing alert-relevant keywords
        
        Args:
            pdf_content: Full PDF text content
            max_words: Maximum words in summary
            
        Returns:
            Summarized text
        """
        if not pdf_content or len(pdf_content.strip()) < 100:
            return pdf_content
        
        # Split into sentences
        sentences = re.split(r'[.!?]\s+', pdf_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return pdf_content[:max_words * 6]  # Rough word limit
        
        # Keywords that indicate important alert information
        alert_keywords = [
            'alert', 'advisory', 'warning', 'hazard', 'risk', 'danger',
            'flood', 'snowfall', 'landslide', 'drought', 'heatwave', 'earthquake',
            'severe', 'severe', 'critical', 'high', 'medium', 'low',
            'expected', 'likely', 'forecast', 'predicted', 'issued',
            'karachi', 'lahore', 'islamabad', 'peshawar', 'quetta', 'gilgit',
            'balochistan', 'punjab', 'sindh', 'kpk', 'gilgit-baltistan',
            'northern', 'southern', 'eastern', 'western', 'upper', 'lower',
            'mm', 'inches', 'temperature', 'rainfall', 'wind', 'storm'
        ]
        
        # Score sentences based on keyword presence and position
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_lower = sentence.lower()
            
            # Higher score for keywords
            for keyword in alert_keywords:
                if keyword in sentence_lower:
                    score += 2
            
            # Higher score for sentences with dates
            if re.search(r'\d{1,2}[\s/-]\w+[\s/-]\d{2,4}', sentence):
                score += 3
            
            # Higher score for location names (capitalized words)
            location_words = re.findall(r'\b[A-Z][a-z]+\b', sentence)
            if len(location_words) > 2:
                score += 2
            
            # Slight preference for earlier sentences (usually contain main info)
            if i < len(sentences) * 0.3:  # First 30% of sentences
                score += 1
            
            scored_sentences.append((score, sentence))
        
        # Sort by score (highest first)
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # Build summary from top sentences
        summary_sentences = []
        word_count = 0
        
        for score, sentence in scored_sentences:
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= max_words:
                summary_sentences.append(sentence)
                word_count += sentence_words
            else:
                # Add partial sentence if we have room
                remaining_words = max_words - word_count
                if remaining_words > 10:  # Only if meaningful
                    words = sentence.split()[:remaining_words]
                    summary_sentences.append(' '.join(words))
                break
        
        # If summary is too short, add more sentences
        if word_count < max_words * 0.5 and len(summary_sentences) < len(sentences):
            for score, sentence in scored_sentences[len(summary_sentences):]:
                sentence_words = len(sentence.split())
                if word_count + sentence_words <= max_words:
                    summary_sentences.append(sentence)
                    word_count += sentence_words
                else:
                    break
        
        summary = '. '.join(summary_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'
        
        logger.info(f"📝 Summarized PDF: {len(pdf_content)} chars → {len(summary)} chars ({word_count} words)")
        return summary
    
    def extract_alerts_from_pdf_ai(self, pdf_content: str, advisory_url: str, advisory: Dict) -> List[Dict]:
        """
        Extract structured alerts from PDF content using AI
        Uses summarization first to reduce input size and prevent timeouts
        
        Args:
            pdf_content: Text content extracted from PDF
            advisory_url: URL of the advisory
            advisory: Original advisory dict with title, date, etc.
            
        Returns:
            List of structured alert dictionaries
        """
        if not self.ai_extractor:
            logger.warning("⚠️ AI extractor not available, using fallback extraction")
            return self._create_fallback_alert(pdf_content, advisory_url, advisory)
        
        try:
            # Step 1: Summarize PDF text to reduce size and prevent timeouts
            logger.info("📝 Summarizing PDF content before AI extraction...")
            summarized_text = self._summarize_pdf_text(pdf_content, max_words=400)
            
            if not summarized_text or len(summarized_text.strip()) < 50:
                logger.warning("⚠️ Summary too short, using full text")
                summarized_text = pdf_content[:2000]  # Fallback to first 2000 chars
            
            # Step 2: Use AI to extract alerts from summarized text
            logger.info(f"🤖 Sending summarized text ({len(summarized_text)} chars) to Ollama...")
            alerts = self.ai_extractor.extract_alerts_from_pdf(summarized_text, advisory_url)
            
            if alerts:
                logger.info(f"✅ AI extracted {len(alerts)} alert(s) from PDF summary")
                return alerts
            else:
                logger.warning("⚠️ AI extraction returned no alerts, using fallback")
                return self._create_fallback_alert(pdf_content, advisory_url, advisory)
                
        except Exception as e:
            logger.error(f"❌ Error in AI extraction: {e}")
            logger.warning("⚠️ Falling back to manual extraction")
            return self._create_fallback_alert(pdf_content, advisory_url, advisory)
    
    def _create_fallback_alert(self, pdf_content: str, advisory_url: str, advisory: Dict) -> List[Dict]:
        """
        Create a basic alert structure from PDF content when AI is unavailable
        
        Args:
            pdf_content: Text content from PDF
            advisory_url: URL of the advisory
            advisory: Original advisory dict
            
        Returns:
            List with one basic alert dict
        """
        # Extract heading from title
        heading = self._extract_heading_from_title(advisory['title'])
        
        # Try to extract location from content or title
        location_name = self._extract_location_from_content(pdf_content[:1000] + ' ' + advisory['title'])
        
        # Get coordinates for location (simplified - would need location mapping)
        lat, lon = self._get_coordinates_for_location(location_name)
        
        # Determine severity
        severity = advisory.get('severity', 'medium')
        
        # Create description from PDF content
        description = pdf_content[:500] if pdf_content else advisory['title']
        
        # Generate hash
        content_hash = self.generate_alert_hash(
            title=advisory.get('title', heading),
            published_date=advisory.get('published_date')
        )
        
        return [{
            'heading': heading,
            'location_name': location_name,
            'latitude': lat,
            'longitude': lon,
            'severity': severity,
            'description': description,
            'affected_regions': advisory.get('affected_regions', []),
            'icon_type': heading.lower().replace(' ', '_'),
            'color_code': 'red' if severity in ['high', 'critical'] else 'yellow' if severity == 'medium' else 'green',
            'advisory_url': advisory_url,
            'published_date': advisory.get('published_date'),
            'content_hash': content_hash,
            'original_pdf_content': pdf_content[:5000],  # Store first 5000 chars
            'ai_extracted': False,
            'extraction_confidence': 0.5,
        }]
    
    def generate_alert_hash(self, title: str = None, published_date: str = None, alert: Dict = None) -> str:
        """
        Generate hash for duplicate detection
        
        Args:
            title: Advisory title (if alert dict not provided)
            published_date: Published date (if alert dict not provided)
            alert: Alert dictionary (alternative to title/date)
            
        Returns:
            SHA256 hash string
        """
        # Support both calling styles
        if alert:
            hash_string = f"{alert.get('heading', '')}_{alert.get('location_name', '')}_{alert.get('advisory_url', '')}_{alert.get('published_date', '')}"
        else:
            hash_string = f"{title}_{published_date}"
        
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        if not date_str:
            return None
        
        # Try common date formats
        date_formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%d %B %Y',
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        # Try to extract date from string
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
        if date_match:
            day, month, year = date_match.groups()
            if len(year) == 2:
                year = '20' + year
            try:
                dt = datetime(int(year), int(month), int(day))
                return dt.strftime('%Y-%m-%d')
            except:
                pass
        
        return None
    
    def _extract_regions_from_title(self, title: str) -> List[str]:
        """Extract affected regions from advisory title"""
        title_lower = title.lower()
        regions = []
        
        # Map common region names
        region_map = {
            'gilgit': 'Gilgit-Baltistan',
            'baltistan': 'Gilgit-Baltistan',
            'hunza': 'Gilgit-Baltistan',
            'skardu': 'Gilgit-Baltistan',
            'naran': 'KPK',
            'kaghan': 'KPK',
            'swat': 'KPK',
            'chitral': 'KPK',
            'murree': 'Punjab',
            'neelum': 'Azad Kashmir',
            'balochistan': 'Balochistan',
            'sindh': 'Sindh',
            'punjab': 'Punjab',
            'kpk': 'KPK',
            'khyber': 'KPK',
        }
        
        for keyword, region in region_map.items():
            if keyword in title_lower:
                if region not in regions:
                    regions.append(region)
        
        if not regions:
            regions = ['General']
        
        return regions
    
    def _determine_severity(self, title: str) -> str:
        """Determine severity from title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['critical', 'emergency', 'urgent', 'severe', 'extreme']):
            return 'critical'
        elif any(word in title_lower for word in ['high', 'warning', 'alert']):
            return 'high'
        elif any(word in title_lower for word in ['moderate', 'medium']):
            return 'medium'
        else:
            return 'low'
    
    def _extract_heading_from_title(self, title: str) -> str:
        """Extract alert heading from title"""
        title_lower = title.lower()
        
        if 'snow' in title_lower or 'snowfall' in title_lower:
            return 'Snowfall'
        elif 'flood' in title_lower or 'rain' in title_lower:
            return 'Flood'
        elif 'landslide' in title_lower or 'land slide' in title_lower:
            return 'Landslide'
        elif 'road block' in title_lower or 'road closure' in title_lower or 'road closed' in title_lower:
            return 'Roadblock'
        elif 'drought' in title_lower:
            return 'Drought'
        elif 'smog' in title_lower or 'fog' in title_lower:
            return 'Smog/Fog'
        elif 'thunderstorm' in title_lower or 'storm' in title_lower:
            return 'Thunderstorm'
        elif 'heatwave' in title_lower or 'heat wave' in title_lower:
            return 'Heatwave'
        elif 'earthquake' in title_lower:
            return 'Earthquake'
        else:
            return 'Weather Alert'
    
    def _extract_location_from_content(self, content: str) -> str:
        """Extract location name from content"""
        # Common location names in Pakistan
        locations = [
            'Hunza', 'Skardu', 'Gilgit', 'Naran', 'Kaghan', 'Swat', 'Chitral',
            'Murree', 'Neelum', 'Shogran', 'Fairy Meadows', 'Kalash',
            'Islamabad', 'Karachi', 'Lahore', 'Peshawar', 'Quetta',
            'Balochistan', 'Sindh', 'Punjab', 'KPK', 'Gilgit-Baltistan',
        ]
        
        content_lower = content.lower()
        for loc in locations:
            if loc.lower() in content_lower:
                return loc
        
        return 'Unknown'
    
    def _get_coordinates_for_location(self, location_name: str) -> tuple:
        """Get approximate coordinates for location"""
        # Simplified coordinate mapping
        coord_map = {
            'Hunza': (36.3167, 74.6500),
            'Skardu': (35.2971, 75.6333),
            'Gilgit': (35.9208, 74.3083),
            'Naran': (34.9078, 73.6486),
            'Kaghan': (34.7833, 73.5167),
            'Swat': (35.2208, 72.4250),
            'Chitral': (35.8514, 71.7869),
            'Murree': (33.9072, 73.3903),
            'Neelum': (34.5833, 73.9167),
            'Islamabad': (33.6844, 73.0479),
            'Karachi': (24.8607, 67.0011),
            'Lahore': (31.5497, 74.3436),
            'Peshawar': (34.0151, 71.5249),
            'Quetta': (30.1798, 66.9750),
        }
        
        return coord_map.get(location_name, (0.0, 0.0))


if __name__ == '__main__':
    # Test scraper
    scraper = NDMAScraper()
    advisories = scraper.scrape_advisories()
    print(f"\n✅ Found {len(advisories)} advisories\n")
    for i, adv in enumerate(advisories[:5], 1):
        print(f"{i}. {adv['title'][:60]}")
        print(f"   URL: {adv['advisory_url']}")
        print(f"   Date: {adv['published_date']}")
        print(f"   Regions: {adv['affected_regions']}")
        print()

