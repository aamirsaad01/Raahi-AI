"""
AI-powered alert extractor for NDMA PDF advisories
Uses Groq (Llama 3) to extract structured hazard alerts from PDF content
"""
import os
import json
import logging
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ groq package not installed. Install with: pip install groq")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)


class AIAlertExtractor:
    """Extract structured alerts from PDF content using Groq (Llama 3)"""
    
    def __init__(self):
        if not GROQ_AVAILABLE:
            logger.error("❌ groq package not available")
            self.client = None
            return
        
        # Groq configuration
        api_key = os.getenv('GROQ_API_KEY')
        model_name = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
        
        if not api_key:
            logger.warning("⚠️ GROQ_API_KEY not found in environment variables")
            self.client = None
            return
        
        try:
            self.client = Groq(api_key=api_key)
            self.model = model_name
            logger.info(f"✅ Groq initialized successfully with model: {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq: {e}")
            self.client = None
        
        # Icon mapping for hazard types
        self.icon_mapping = {
            'snowfall': 'snowfall',
            'snow': 'snowfall',
            'avalanche': 'snowfall',
            'flood': 'flood',
            'flooding': 'flood',
            'rain': 'flood',
            'monsoon': 'flood',
            'landslide': 'landslide',
            'land slide': 'landslide',
            'mudslide': 'landslide',
            'rockfall': 'landslide',
            'roadblock': 'roadblock',
            'road block': 'roadblock',
            'road closure': 'roadblock',
            'blocked': 'roadblock',
            'protest': 'protest',
            'strike': 'protest',
            'demonstration': 'protest',
            'accident': 'accident',
            'crash': 'accident',
            'drought': 'drought',
            'heatwave': 'heatwave',
            'heat wave': 'heatwave',
            'glof': 'glof',
            'glacial lake': 'glof',
        }
    
    def extract_alerts_from_pdf(self, pdf_content: str, advisory_url: str = None) -> List[Dict]:
        """
        Extract structured alerts from PDF content using AI
        
        Args:
            pdf_content: Text content extracted from PDF
            advisory_url: Original advisory URL (optional)
            
        Returns:
            List of structured alert dictionaries
        """
        if not pdf_content or len(pdf_content.strip()) < 100:
            logger.warning("PDF content too short or empty")
            return []
        
        try:
            # Clean PDF content - remove excessive whitespace but keep structure
            pdf_content_clean = ' '.join(pdf_content.split())  # Normalize whitespace
            pdf_content_clean = pdf_content_clean.strip()
            
            if len(pdf_content_clean) < 100:
                logger.warning("PDF content too short after cleaning")
                return []
            
            if not self.client:
                logger.warning("⚠️ Groq client not available, cannot extract alerts")
                return []
            
            # Create prompt for AI
            prompt = self._create_extraction_prompt(pdf_content_clean)
            
            logger.info(f"🤖 Sending {len(pdf_content_clean)} characters of PDF text to Groq ({self.model})...")
            
            # Call Groq API
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert at extracting hazard alerts from NDMA advisory PDFs. Always respond with valid JSON array only, no markdown formatting, no code blocks."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,  # Low temperature for consistent JSON
                    max_tokens=8192
                )
                
                ai_text = response.choices[0].message.content
                
                if not ai_text:
                    logger.error("❌ Empty response from Groq")
                    return []
                
                # Log raw response for debugging
                logger.debug(f"Raw Groq response (first 1000 chars):\n{ai_text[:1000]}")
                
                # Parse AI response
                alerts = self._parse_ai_response(ai_text)
                
            except Exception as e:
                logger.error(f"❌ Error calling Groq API: {e}")
                return []
            
            logger.info(f"✅ AI extracted {len(alerts)} alert(s) from PDF")
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error extracting alerts with AI: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            return []
    
    def _create_extraction_prompt(self, pdf_content: str) -> str:
        """Create prompt for AI extraction - receives summarized PDF text"""
        # Clean and normalize the PDF content
        pdf_text = pdf_content.strip()
        logger.info(f"📄 Sending {len(pdf_text)} characters of summarized PDF text to Groq")
        
        return f"""You are an expert at extracting hazard alerts from NDMA (National Disaster Management Authority) advisory PDFs.

Extract ALL hazard alerts from the following PDF content. Read the ENTIRE PDF carefully.

For EACH alert found, return a JSON object with these EXACT fields:
- **heading**: Alert type - MUST be one of: "Snowfall", "Flood", "Landslide", "Roadblock", "Avalanche", "Drought", "Heatwave", "Thunderstorm", "Smog", "Fog", "Protest", "Accident"
- **location_name**: Specific location (e.g., "Gilgit", "Naran", "Murree", "Skardu", "Kaghan", "Hunza", "Swat", "Chitral")
- **latitude**: Decimal latitude (e.g., 35.9208) - use known coordinates for Pakistani locations
- **longitude**: Decimal longitude (e.g., 74.3083) - use known coordinates for Pakistani locations
- **severity**: MUST be one of: "low", "medium", "high", "critical"
- **description**: 2-3 sentence summary of the alert from the PDF
- **affected_regions**: Array of regions (e.g., ["Gilgit-Baltistan"], ["KPK"], ["Punjab"])
- **icon_type**: MUST match heading and be one of: "snowfall", "flood", "landslide", "roadblock", "protest", "accident" (map others to closest match)
- **color_code**: "red" for critical/high, "yellow" for medium, "green" for low

CRITICAL RULES:
1. If multiple locations are mentioned, create SEPARATE alerts for EACH location
2. Icon type must be one of: snowfall, flood, landslide, roadblock, protest, accident (map others appropriately)
3. Severity: "critical"/"high" = severe, "medium" = moderate, "low" = mild
4. Read the ENTIRE PDF - don't miss any locations or hazards
5. Return ONLY valid JSON array - no markdown, no code blocks, no extra text

EXAMPLE FORMAT (return as JSON array):
[
  {{
    "heading": "Snowfall",
    "location_name": "Naran",
    "latitude": 34.9208,
    "longitude": 73.3083,
    "severity": "high",
    "description": "Heavy snowfall expected in Naran valley. Roads may be blocked. Travelers advised to avoid the area.",
    "affected_regions": ["KPK"],
    "icon_type": "snowfall",
    "color_code": "red"
  }},
  {{
    "heading": "Roadblock",
    "location_name": "Babusar Pass",
    "latitude": 35.1234,
    "longitude": 74.5678,
    "severity": "medium",
    "description": "Road blocked due to snowfall. Alternative route available.",
    "affected_regions": ["Gilgit-Baltistan"],
    "icon_type": "roadblock",
    "color_code": "yellow"
  }}
]

PDF CONTENT:
{pdf_text}

Extract all alerts and return as JSON array (no markdown, no code blocks):"""

    def _parse_ai_response(self, ai_text: str) -> List[Dict]:
        """Parse AI response and extract JSON with robust error handling"""
        try:
            # Clean the response text
            cleaned_text = ai_text.strip()
            
            # Groq may return JSON with extra text - extract just the JSON array
            # Find the first [ and matching ] (handling nested structures)
            json_str = self._extract_json_from_text(cleaned_text)
            
            if not json_str:
                # Fallback: Try to extract JSON from response
                # AI might wrap JSON in markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', cleaned_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Try to find JSON array directly (more flexible)
                    json_match = re.search(r'(\[[\s\S]*\])', cleaned_text)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        # Try to parse entire response as JSON
                        json_str = cleaned_text
            
            # Clean JSON string - fix common issues
            json_str = self._clean_json_string(json_str)
            
            # Try to parse complete JSON first
            try:
                alerts = json.loads(json_str)
            except json.JSONDecodeError as e:
                # JSON is truncated - try to extract complete objects
                logger.warning(f"JSON appears truncated, attempting to extract complete objects...")
                alerts = self._extract_complete_objects(json_str)
            
            # Validate and normalize alerts
            normalized_alerts = []
            for alert in alerts:
                normalized = self._normalize_alert(alert)
                if normalized:
                    normalized_alerts.append(normalized)
            
            return normalized_alerts
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"JSON Error at position {e.pos}: {e.msg}")
            # Try to extract complete objects from truncated JSON
            logger.info("Attempting to extract complete objects from truncated JSON...")
            try:
                alerts = self._extract_complete_objects(ai_text)
                if alerts:
                    logger.info(f"Successfully extracted {len(alerts)} complete alert(s) from truncated JSON")
                    normalized_alerts = []
                    for alert in alerts:
                        normalized = self._normalize_alert(alert)
                        if normalized:
                            normalized_alerts.append(normalized)
                    return normalized_alerts
            except:
                pass
            # Log the problematic section
            if hasattr(e, 'pos') and e.pos:
                start = max(0, e.pos - 100)
                end = min(len(ai_text), e.pos + 100)
                logger.error(f"Problematic section: ...{ai_text[start:end]}...")
            # Log full response for debugging (first 2000 chars)
            logger.error(f"Full AI Response (first 2000 chars):\n{ai_text[:2000]}")
            return []
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            logger.debug(f"AI Response: {ai_text[:500]}")
            return []
    
    def _extract_complete_objects(self, json_str: str) -> List[Dict]:
        """Extract complete JSON objects from potentially truncated JSON"""
        alerts = []
        try:
            # Clean the string
            json_str = json_str.strip()
            
            # Remove markdown code blocks if present
            json_str = re.sub(r'^```(?:json)?\s*', '', json_str)
            json_str = re.sub(r'\s*```$', '', json_str)
            
            # Find the start of the array
            start_idx = json_str.find('[')
            if start_idx == -1:
                return alerts
            json_str = json_str[start_idx + 1:]
            
            # Extract complete objects using regex (more reliable)
            # Pattern: { ... } where braces are balanced
            pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.finditer(pattern, json_str)
            
            for match in matches:
                obj_str = match.group(0)
                try:
                    # Clean up the object string
                    obj_str = obj_str.strip().rstrip(',')
                    obj = json.loads(obj_str)
                    # Validate it has required fields
                    if isinstance(obj, dict) and 'heading' in obj and 'location_name' in obj:
                        alerts.append(obj)
                except json.JSONDecodeError:
                    # Try to fix common issues
                    try:
                        # Fix trailing commas
                        obj_str = re.sub(r',\s*}', '}', obj_str)
                        obj_str = re.sub(r',\s*]', ']', obj_str)
                        obj = json.loads(obj_str)
                        if isinstance(obj, dict) and 'heading' in obj and 'location_name' in obj:
                            alerts.append(obj)
                    except:
                        continue
                except:
                    continue
            
            # If regex didn't work, try manual parsing
            if not alerts:
                alerts = self._manual_extract_objects(json_str)
            
        except Exception as e:
            logger.error(f"Error extracting complete objects: {e}")
        
        return alerts
    
    def _manual_extract_objects(self, json_str: str) -> List[Dict]:
        """Manually extract complete JSON objects by tracking braces"""
        alerts = []
        try:
            depth = 0
            current_obj = ""
            in_string = False
            escape_next = False
            
            for i, char in enumerate(json_str):
                if escape_next:
                    current_obj += char
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    current_obj += char
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    current_obj += char
                    continue
                
                if not in_string:
                    if char == '{':
                        if depth == 0:
                            current_obj = char
                        else:
                            current_obj += char
                        depth += 1
                    elif char == '}':
                        current_obj += char
                        depth -= 1
                        if depth == 0:
                            # Complete object found
                            try:
                                obj_str = current_obj.strip().rstrip(',')
                                obj = json.loads(obj_str)
                                if isinstance(obj, dict) and 'heading' in obj and 'location_name' in obj:
                                    alerts.append(obj)
                            except:
                                pass
                            current_obj = ""
                    else:
                        if depth > 0:
                            current_obj += char
                else:
                    if depth > 0:
                        current_obj += char
        except Exception as e:
            logger.error(f"Error in manual extraction: {e}")
        
        return alerts
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean and fix common JSON syntax errors"""
        # Remove leading/trailing whitespace
        json_str = json_str.strip()
        
        # Remove markdown code block markers if still present
        json_str = re.sub(r'^```(?:json)?\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)
        
        # Fix common issues:
        # 1. Missing commas between objects
        json_str = re.sub(r'\}\s*\{', '},{', json_str)
        
        # 2. Trailing commas before closing brackets
        json_str = re.sub(r',\s*\]', ']', json_str)
        json_str = re.sub(r',\s*\}', '}', json_str)
        
        # 3. Unescaped quotes in strings (basic fix)
        # This is tricky, so we'll be conservative
        
        # 4. Ensure it starts with [ and ends with ]
        if not json_str.startswith('['):
            # Try to find the first [
            first_bracket = json_str.find('[')
            if first_bracket != -1:
                json_str = json_str[first_bracket:]
        
        if not json_str.endswith(']'):
            # Try to find the last ]
            last_bracket = json_str.rfind(']')
            if last_bracket != -1:
                json_str = json_str[:last_bracket + 1]
        
        return json_str
    
    def _normalize_alert(self, alert: Dict) -> Optional[Dict]:
        """Normalize and validate alert data"""
        try:
            # Required fields
            heading = alert.get('heading', '').strip()
            location_name = alert.get('location_name', '').strip()
            severity = alert.get('severity', 'medium').lower()
            
            if not heading or not location_name:
                logger.warning(f"Skipping alert with missing required fields: {alert}")
                return None
            
            # Normalize severity
            if severity not in ['low', 'medium', 'high', 'critical']:
                severity = 'medium'
            
            # Determine icon type from heading
            icon_type = self._determine_icon_type(heading)
            
            # Determine color from severity
            color_code = self._determine_color(severity)
            
            # Normalize coordinates
            latitude = float(alert.get('latitude', 0.0))
            longitude = float(alert.get('longitude', 0.0))
            
            # If coordinates are 0, try to get from location name
            if latitude == 0.0 or longitude == 0.0:
                lat, lon = self._get_coordinates_for_location(location_name)
                latitude = lat
                longitude = lon
            
            # Normalize affected regions
            affected_regions = alert.get('affected_regions', [])
            if isinstance(affected_regions, str):
                affected_regions = [affected_regions]
            if not affected_regions:
                # Try to infer from location
                affected_regions = self._infer_region_from_location(location_name)
            
            return {
                'heading': heading,
                'location_name': location_name,
                'latitude': latitude,
                'longitude': longitude,
                'severity': severity,
                'description': alert.get('description', '').strip(),
                'affected_regions': affected_regions,
                'icon_type': icon_type,
                'color_code': color_code,
                'source': 'NDMA',
            }
            
        except Exception as e:
            logger.error(f"Error normalizing alert: {e}")
            return None
    
    def _determine_icon_type(self, heading: str) -> str:
        """
        Determine icon type from heading
        Must return one of: snowfall, flood, landslide, roadblock, protest, accident
        (matching frontend HazardType enum)
        """
        heading_lower = heading.lower()
        
        # Map to frontend HazardType enum values
        if any(word in heading_lower for word in ['snow', 'snowfall', 'avalanche']):
            return 'snowfall'
        elif any(word in heading_lower for word in ['flood', 'flooding', 'rain', 'monsoon']):
            return 'flood'
        elif any(word in heading_lower for word in ['landslide', 'land slide', 'mudslide', 'rockfall']):
            return 'landslide'
        elif any(word in heading_lower for word in ['protest', 'strike', 'demonstration', 'rally']):
            return 'protest'
        elif any(word in heading_lower for word in ['accident', 'crash', 'collision']):
            return 'accident'
        elif any(word in heading_lower for word in ['road', 'block', 'closure', 'closed', 'blocked']):
            return 'roadblock'
        else:
            # Default to roadblock for unknown types
            return 'roadblock'
    
    def _determine_color(self, severity: str) -> str:
        """Determine color code from severity"""
        severity_lower = severity.lower()
        if severity_lower in ['critical', 'high']:
            return 'red'
        elif severity_lower == 'medium':
            return 'yellow'
        else:
            return 'green'
    
    def _get_coordinates_for_location(self, location_name: str) -> tuple:
        """Get approximate coordinates for a location"""
        # Common Pakistani tourist locations with coordinates
        location_coords = {
            'gilgit': (35.9208, 74.3083),
            'skardu': (35.2971, 75.6333),
            'hunza': (36.3167, 74.6500),
            'naran': (34.9208, 73.3083),
            'kaghan': (34.7833, 73.5167),
            'murree': (33.9072, 73.3903),
            'swat': (35.2208, 72.4250),
            'kalam': (35.4833, 72.5833),
            'chitral': (35.8514, 71.7869),
            'abbottabad': (34.1467, 73.2117),
            'mansehra': (34.3333, 73.2000),
            'balakot': (34.5500, 73.3500),
            'nathia gali': (34.0500, 73.3833),
            'shogran': (34.6333, 73.4833),
            'babusar': (35.1234, 74.5678),
            'lulusar': (35.0833, 73.9167),
            'saiful muluk': (34.8833, 73.6833),
            'fairy meadows': (35.4167, 74.5833),
            'attabad': (36.3167, 74.8333),
        }
        
        location_lower = location_name.lower()
        for loc, coords in location_coords.items():
            if loc in location_lower:
                return coords
        
        # Default to Islamabad if not found
        return (33.6844, 73.0479)
    
    def _infer_region_from_location(self, location_name: str) -> List[str]:
        """Infer region from location name"""
        location_lower = location_name.lower()
        
        if any(loc in location_lower for loc in ['gilgit', 'skardu', 'hunza', 'fairy meadows', 'attabad']):
            return ['Gilgit-Baltistan']
        elif any(loc in location_lower for loc in ['naran', 'kaghan', 'shogran', 'babusar', 'lulusar', 'saiful muluk', 'mansehra', 'balakot']):
            return ['Hazara Division']
        elif any(loc in location_lower for loc in ['murree', 'nathia gali', 'ayubia', 'dunga gali']):
            return ['Murree & Galyat']
        elif any(loc in location_lower for loc in ['swat', 'kalam', 'chitral']):
            return ['KPK Highlands']
        else:
            return ['General']
    
    def _extract_json_from_text(self, text: str) -> str:
        """
        Extract JSON array from text, handling extra text before/after
        Similar to LLM enricher's robust JSON extraction
        """
        text = text.strip()
        
        # Find the first [ and its matching ]
        start_idx = text.find('[')
        if start_idx == -1:
            return ''
        
        # Find matching closing bracket
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start_idx, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '[':
                    depth += 1
                elif char == ']':
                    depth -= 1
                    if depth == 0:
                        # Found matching bracket
                        return text[start_idx:i+1]
        
        # If we get here, bracket wasn't closed - return what we have
        return text[start_idx:]

