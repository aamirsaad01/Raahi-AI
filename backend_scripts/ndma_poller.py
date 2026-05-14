"""
NDMA Poller Service
Runs periodically to scrape NDMA advisories and save them to database
"""
import os
import sys
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime, timedelta
import logging
import time
import hashlib
from typing import List, Dict
from dotenv import load_dotenv
from ndma_scraper import NDMAScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from repo root
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)


class NDMAPoller:
    """Poller service for NDMA advisories"""
    
    def __init__(self):
        self.scraper = NDMAScraper()
        self.conn = self._connect_to_db()
    
    def _connect_to_db(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME", "raahi_ai"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                host=os.getenv("DB_HOST", "127.0.0.1"),
                port=os.getenv("DB_PORT", "5432"),
            )
            logger.info("✅ Connected to database successfully")
            return conn
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise ConnectionError(f"Could not connect to database: {e}")
    
    def ensure_table_exists(self):
        """Ensure ndma_alerts table exists"""
        try:
            cursor = self.conn.cursor()
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'ndma_alerts'
                );
            """)
            exists = cursor.fetchone()[0]
            
            if not exists:
                logger.warning("⚠️  ndma_alerts table does not exist. Apply database/postgresql/db_init.sql (psql -f).")
                cursor.close()
                return False
            
            cursor.close()
            logger.info("✅ ndma_alerts table exists")
            return True
        except Exception as e:
            logger.error(f"Error checking table: {e}")
            return False
    
    def get_existing_hashes(self) -> set:
        """Get all existing alert hashes from database"""
        try:
            cursor = self.conn.cursor()
            # Check new AI table
            try:
                cursor.execute("SELECT content_hash FROM ndma_alerts_ai")
                hashes = {row[0] for row in cursor.fetchall()}
            except psycopg2.errors.UndefinedTable:
                # New table doesn't exist yet
                hashes = set()
            cursor.close()
            logger.info(f"Found {len(hashes)} existing alerts in database")
            return hashes
        except Exception as e:
            logger.error(f"Error fetching existing hashes: {e}")
            return set()
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            exists = cursor.fetchone()[0]
            cursor.close()
            return exists
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
    
    def _ensure_ai_table_exists(self):
        """Ensure the AI alerts table exists"""
        if not self._table_exists('ndma_alerts_ai'):
            logger.error("❌ ndma_alerts_ai table does NOT exist!")
            logger.error("Please run: database/postgresql/db_init.sql (psql -f)")
            raise Exception("ndma_alerts_ai table not found. Run migration script first.")
        logger.info("✅ ndma_alerts_ai table exists")
    
    def save_advisories(self, advisories: List[Dict]) -> int:
        """
        Save new advisories to database
        
        Args:
            advisories: List of advisory dictionaries
            
        Returns:
            Number of new advisories saved
        """
        if not advisories:
            return 0
        
        existing_hashes = self.get_existing_hashes()
        new_advisories = []
        
        for advisory in advisories:
            # Generate hash for duplicate detection
            alert_hash = self.scraper.generate_alert_hash(
                advisory['title'],
                advisory['published_date']
            )
            
            # Skip if already exists
            if alert_hash in existing_hashes:
                logger.debug(f"Skipping duplicate: {advisory['title']}")
                continue
            
            # Process ALL advisories - each advisory is a PDF that needs to be downloaded and processed
            advisory_url = advisory.get('advisory_url', '')
            
            if not advisory_url:
                logger.warning(f"⚠️ No URL found for advisory: {advisory['title']}")
                continue
            
            logger.info(f"📄 Processing advisory: {advisory['title']}")
            logger.info(f"   URL: {advisory_url}")
            
            # Fetch PDF content (handles both direct PDFs and secure-viewer pages)
            pdf_content = self.scraper.fetch_advisory_content(advisory_url)
            time.sleep(1)  # Be respectful to the server
            
            if not pdf_content or len(pdf_content.strip()) < 100:
                logger.warning(f"⚠️ Could not extract PDF content for: {advisory['title']} (URL: {advisory_url})")
                logger.warning(f"   Content length: {len(pdf_content) if pdf_content else 0} chars")
                continue
            
            logger.info(f"✅ Extracted {len(pdf_content)} characters from PDF")
            
            # Use AI (OpenAI) to extract structured alerts from PDF
            logger.info(f"🤖 Sending PDF text to OpenAI to extract alerts...")
            ai_alerts = self.scraper.extract_alerts_from_pdf_ai(pdf_content, advisory_url, advisory)
            
            if not ai_alerts:
                logger.warning(f"⚠️ AI extraction returned no alerts for: {advisory['title']}")
                logger.warning(f"   This might mean the PDF doesn't contain hazard alerts, or AI extraction failed")
                continue
            
            logger.info(f"✅ AI extracted {len(ai_alerts)} alert(s) from PDF")
            
            # Add each AI-extracted alert
            for ai_alert in ai_alerts:
                # Generate hash for duplicate detection
                hash_string = f"{ai_alert['heading']}_{ai_alert['location_name']}_{advisory.get('published_date')}"
                alert_hash = hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
                
                # Skip if already exists
                if alert_hash in existing_hashes:
                    logger.debug(f"Skipping duplicate alert: {ai_alert['heading']} - {ai_alert['location_name']}")
                    continue
                
                # Ensure icon_type matches frontend HazardType enum
                icon_type = ai_alert.get('icon_type', 'roadblock')
                valid_icon_types = ['snowfall', 'flood', 'landslide', 'roadblock', 'protest', 'accident']
                if icon_type not in valid_icon_types:
                    # Map to closest valid type
                    if 'snow' in icon_type.lower():
                        icon_type = 'snowfall'
                    elif 'flood' in icon_type.lower() or 'rain' in icon_type.lower():
                        icon_type = 'flood'
                    elif 'landslide' in icon_type.lower() or 'slide' in icon_type.lower():
                        icon_type = 'landslide'
                    elif 'protest' in icon_type.lower() or 'strike' in icon_type.lower():
                        icon_type = 'protest'
                    elif 'accident' in icon_type.lower() or 'crash' in icon_type.lower():
                        icon_type = 'accident'
                    else:
                        icon_type = 'roadblock'  # Default
                
                # Ensure severity is valid
                severity = ai_alert.get('severity', 'medium').lower()
                if severity not in ['low', 'medium', 'high', 'critical']:
                    severity = 'medium'
                
                # Prepare alert for database (matching frontend format)
                new_advisories.append({
                    'heading': ai_alert.get('heading', 'Weather Alert'),
                    'location_name': ai_alert.get('location_name', 'Unknown'),
                    'latitude': float(ai_alert.get('latitude', 0.0)),
                    'longitude': float(ai_alert.get('longitude', 0.0)),
                    'severity': severity,
                    'description': ai_alert.get('description', ''),
                    'affected_regions': ai_alert.get('affected_regions', []),
                    'icon_type': icon_type,  # Must match frontend HazardType enum
                    'color_code': ai_alert.get('color_code', 'yellow'),
                    'source': 'NDMA',
                    'advisory_url': advisory_url,
                    'published_date': advisory.get('published_date'),
                    'content_hash': alert_hash,
                    'original_pdf_content': pdf_content[:10000],  # Store first 10k chars
                    'ai_extracted': True,
                    'extraction_confidence': 0.85,  # Default confidence
                })
                existing_hashes.add(alert_hash)
                
                logger.info(f"   ✅ Alert: {ai_alert.get('heading')} - {ai_alert.get('location_name')} ({severity})")
        
        if not new_advisories:
            logger.info("No new advisories to save")
            return 0
        
        # Insert new AI-extracted alerts
        try:
            cursor = self.conn.cursor()
            
            # Check if is_active column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='ndma_alerts_ai' AND column_name='is_active'
            """)
            has_is_active = cursor.fetchone() is not None
            
            if has_is_active:
                insert_query = """
                    INSERT INTO ndma_alerts_ai 
                    (heading, source, location_name, latitude, longitude, affected_regions,
                     severity, icon_type, color_code, description, advisory_url, published_date,
                     content_hash, original_pdf_content, ai_extracted, extraction_confidence, is_active)
                    VALUES %s
                    ON CONFLICT (content_hash) DO NOTHING
                """
            else:
                insert_query = """
                    INSERT INTO ndma_alerts_ai 
                    (heading, source, location_name, latitude, longitude, affected_regions,
                     severity, icon_type, color_code, description, advisory_url, published_date,
                     content_hash, original_pdf_content, ai_extracted, extraction_confidence)
                    VALUES %s
                    ON CONFLICT (content_hash) DO NOTHING
                """
            
            rows = []
            for adv in new_advisories:
                if has_is_active:
                    rows.append((
                        adv['heading'],
                        adv.get('source', 'NDMA'),
                        adv['location_name'],
                        adv['latitude'],
                        adv['longitude'],
                        adv['affected_regions'],
                        adv['severity'],
                        adv.get('icon_type', 'roadblock'),
                        adv.get('color_code', 'yellow'),
                        adv.get('description', ''),
                        adv.get('advisory_url', ''),
                        adv.get('published_date'),
                        adv['content_hash'],
                        adv.get('original_pdf_content', ''),
                        adv.get('ai_extracted', True),
                        adv.get('extraction_confidence', 0.85),
                        True,  # is_active = TRUE
                    ))
                else:
                    rows.append((
                        adv['heading'],
                        adv.get('source', 'NDMA'),
                        adv['location_name'],
                        adv['latitude'],
                        adv['longitude'],
                        adv['affected_regions'],
                        adv['severity'],
                        adv.get('icon_type', 'roadblock'),
                        adv.get('color_code', 'yellow'),
                        adv.get('description', ''),
                        adv.get('advisory_url', ''),
                        adv.get('published_date'),
                        adv['content_hash'],
                        adv.get('original_pdf_content', ''),
                        adv.get('ai_extracted', True),
                        adv.get('extraction_confidence', 0.85),
                    ))
            
            execute_values(cursor, insert_query, rows)
            self.conn.commit()
            cursor.close()
            
            logger.info(f"✅ Saved {len(new_advisories)} new AI-extracted alerts to database")
            return len(new_advisories)
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Error saving advisories: {e}")
            raise
    
    def poll(self) -> Dict:
        """
        Perform one polling cycle
        
        Returns:
            Dictionary with polling results
        """
        logger.info("=" * 60)
        logger.info("🔄 Starting NDMA polling cycle")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Ensure AI table exists
            self._ensure_ai_table_exists()
            
            # Scrape advisories
            logger.info("📡 Scraping NDMA advisories...")
            advisories = self.scraper.scrape_advisories()
            
            if not advisories:
                logger.warning("⚠️  No advisories found")
                return {
                    'success': True,
                    'advisories_found': 0,
                    'new_advisories': 0,
                    'duration_seconds': (datetime.now() - start_time).total_seconds()
                }
            
            logger.info(f"📋 Found {len(advisories)} advisories")
            
            # Save new advisories
            new_count = self.save_advisories(advisories)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                'success': True,
                'advisories_found': len(advisories),
                'new_advisories': new_count,
                'duration_seconds': duration
            }
            
            logger.info("=" * 60)
            logger.info(f"✅ Polling complete: {new_count} new advisories saved")
            logger.info(f"⏱️  Duration: {duration:.2f} seconds")
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error during polling: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }
    
    def run_continuous(self, interval_hours: float = 1.0):
        """
        Run poller continuously with specified interval
        
        Args:
            interval_hours: Hours between polling cycles (default: 1 hour)
        """
        interval_seconds = interval_hours * 3600
        
        logger.info("🚀 Starting NDMA Poller Service")
        logger.info(f"⏰ Polling interval: {interval_hours} hour(s)")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        try:
            while True:
                self.poll()
                
                logger.info(f"💤 Sleeping for {interval_hours} hour(s)...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Poller stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Database connection closed")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NDMA Poller Service')
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (default: run continuously)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='Polling interval in hours (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    poller = NDMAPoller()
    
    try:
        if args.once:
            # Run once
            result = poller.poll()
            if result['success']:
                print(f"\n✅ Success: {result['new_advisories']} new advisories saved")
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        else:
            # Run continuously
            poller.run_continuous(interval_hours=args.interval)
    finally:
        poller.close()


if __name__ == "__main__":
    main()

