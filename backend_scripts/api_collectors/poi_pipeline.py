"""
POI Data Collection Pipeline
Orchestrates the complete data collection process:
1. Fetch locations from database
2. Get POIs from OpenStreetMap
3. Enrich with LLM (OpenAI by default if OPENAI_API_KEY is set; else Ollama)
4. Fetch photos (Unsplash)
5. Save to database
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import time
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_collectors.geoapify_collector import GeoapifyCollector
from api_collectors.llm_enricher import POIEnricher
from api_collectors.openai_enricher import OpenAIPOIEnricher
from api_collectors.photo_fetcher import PhotoFetcher

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class POIPipeline:
    """
    Complete POI data collection and enrichment pipeline
    """
    
    def __init__(self):
        """Initialize pipeline with database connection and API clients"""
        self.conn = self._connect_to_db()
        self.osm_collector = GeoapifyCollector()

        self.enricher, self._enricher_backend = self._create_enricher()
        self.enricher_available = True
        
        # Initialize photo fetcher (optional)
        self.photo_fetcher = PhotoFetcher()
        
        logger.info("✅ POI Pipeline initialized (enricher=%s)", self._enricher_backend)

    def _create_enricher(self):
        """
        OPENAI_API_KEY set → OpenAI (paid). Else Ollama (local).
        Override with POI_ENRICHER=openai | ollama (openai still requires the key).
        """
        mode = (os.getenv("POI_ENRICHER") or "").strip().lower()
        has_openai_key = bool((os.getenv("OPENAI_API_KEY") or "").strip())

        if mode == "ollama":
            return POIEnricher(), "ollama"

        if mode == "openai":
            return OpenAIPOIEnricher(), "openai"

        # auto
        if has_openai_key:
            try:
                return OpenAIPOIEnricher(), "openai"
            except Exception as e:
                logger.warning(
                    "OpenAI enricher failed (%s); falling back to Ollama.", e
                )
                return POIEnricher(), "ollama"

        logger.info("OPENAI_API_KEY not set; using Ollama for POI enrichment.")
        return POIEnricher(), "ollama"

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
            logger.info("✅ Connected to database")
            return conn
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def process_all_locations(
        self,
        limit: Optional[int] = None,
        skip: int = 0,
        force_repopulate: bool = False,
    ):
        """
        Process all locations in database
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query
        query = """
            SELECT location_id, city, latitude, longitude, parent_region 
            FROM location_mapping 
            WHERE verified = TRUE
            ORDER BY location_id
        """
        
        if skip > 0:
            query += f" OFFSET {skip}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        locations = cursor.fetchall()
        cursor.close()
        
        total_locations = len(locations)
        total_pois = 0
        successful_pois = 0
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 STARTING PIPELINE: Processing {total_locations} locations")
        logger.info(f"{'='*70}\n")
        
        for idx, location in enumerate(locations, 1):
            loc_id = location['location_id']
            city = location['city']
            lat = location['latitude']
            lng = location['longitude']
            region = location['parent_region']
            
            logger.info(f"\n{'='*70}")
            logger.info(f"📍 [{idx}/{total_locations}] Processing: {city}, {region}")
            logger.info(f"{'='*70}")
            
            existing_count = self._count_existing_pois(loc_id)
            if existing_count > 0 and not force_repopulate:
                logger.info(
                    f"ℹ️  Already have {existing_count} POIs for {city}, skipping..."
                )
                continue
            if existing_count > 0 and force_repopulate:
                logger.info(
                    f"🔄 Force repopulate: re-processing {city} ({existing_count} existing rows will be upserted)"
                )
            
            # Step 1: Fetch POIs from OSM
            logger.info(f"\n1️⃣  Fetching POIs from OpenStreetMap...")
            osm_pois = self.osm_collector.fetch_pois_for_location(city, lat, lng)
            
            if not osm_pois:
                logger.warning(f"⚠️  No POIs found in OSM for {city}")
                continue
            
            logger.info(f"✅ Ready to process {len(osm_pois)} deduplicated POIs")
            
            # Step 2: Enrich and save each POI
            logger.info(f"\n2️⃣  Enriching POIs with LLM and photos...")
            
            for poi_idx, poi in enumerate(osm_pois, 1):
                try:
                    logger.info(f"\n   [{poi_idx}/{len(osm_pois)}] Processing: {poi['name']}")
                    
                    # Macro-Level Deduplication Check
                    existing_poi_anywhere = (
                        None
                        if force_repopulate
                        else self._get_existing_poi_anywhere(poi["osm_id"])
                    )

                    if existing_poi_anywhere:
                        # Prevent duplicate insertions globally if search radii overlap
                        logger.info(f"   ℹ️  POI already mapped to Location ID {existing_poi_anywhere['location_id']}. Skipping to prevent global duplicates.")
                        total_pois += 1
                        continue

                    # New POI - enrich with LLM
                    enriched = self.enricher.enrich_poi(poi)
                    
                    # Fetch photos (if available)
                    photos = []
                    if self.photo_fetcher.access_key:
                        photos = self.photo_fetcher.fetch_photos(poi['name'], city, max_photos=3)
                        if not photos:
                            # Try fallback generic photos
                            photos = self.photo_fetcher.fetch_fallback_photos(
                                enriched.get('category', 'nature'),
                                region
                            )
                    
                    # Merge all data
                    full_poi = {
                        **poi,
                        **enriched,
                        'photos': photos,
                        'location_id': loc_id
                    }
                    
                    # Save to database
                    self._save_poi(full_poi)
                    successful_pois += 1
                    total_pois += 1
                    
                    logger.info(f"   ✅ Saved new POI: {poi['name']}")
                    
                    # Prevent rate limits
                    time.sleep(0.35 if self._enricher_backend == "openai" else 1)
                    
                except Exception as e:
                    logger.error(f"   ❌ Error processing {poi.get('name', 'Unknown')}: {e}")
                    # Rollback the failed transaction so the next INSERT can proceed
                    try:
                        self.conn.rollback()
                    except Exception:
                        pass
                    total_pois += 1
                    continue
            
            logger.info(f"\n✅ Completed {city}: {successful_pois} new POIs saved")
            
            # Longer delay between locations
            time.sleep(2)
        
        # Final summary
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 PIPELINE COMPLETE!")
        logger.info(f"{'='*70}")
        logger.info(f"Locations processed: {total_locations}")
        logger.info(f"Total POIs Evaluated: {total_pois}")
        logger.info(f"Successfully saved: {successful_pois}")
        logger.info(f"Success rate: {(successful_pois/total_pois*100) if total_pois > 0 else 0:.1f}%")
        logger.info(f"{'='*70}\n")
    
    def _count_existing_pois(self, location_id: int) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM points_of_interest WHERE location_id = %s",
            (location_id,)
        )
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    
    def _check_poi_exists_for_location(self, osm_id: str, location_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM points_of_interest WHERE osm_id = %s AND location_id = %s",
            (osm_id, location_id)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            poi_data = dict(result)
            for field in ['activities', 'mood_tags', 'highlights', 'photos']:
                if field in poi_data and isinstance(poi_data[field], str):
                    try:
                        poi_data[field] = json.loads(poi_data[field])
                    except:
                        poi_data[field] = []
            return poi_data
        return None
    
    def _get_existing_poi_anywhere(self, osm_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM points_of_interest WHERE osm_id = %s LIMIT 1",
            (osm_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            poi_data = dict(result)
            for field in ['activities', 'mood_tags', 'highlights', 'photos']:
                if field in poi_data and isinstance(poi_data[field], str):
                    try:
                        poi_data[field] = json.loads(poi_data[field])
                    except:
                        poi_data[field] = []
            return poi_data
        return None
    
    def _save_poi(self, poi_data: Dict):
        cursor = self.conn.cursor()
        
        query = """
        INSERT INTO points_of_interest 
        (location_id, osm_id, osm_type, name, latitude, longitude, 
         description, rating, category, difficulty, activities, mood_tags, 
         highlights, estimated_cost, estimated_cost_pkr_min, estimated_cost_pkr_max,
         best_months, avg_duration_hours, accessibility, permits_required, 
         nearby_facilities, photos, verified, last_api_fetch)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (osm_id, location_id) DO UPDATE SET
            osm_type = EXCLUDED.osm_type,
            name = EXCLUDED.name,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            description = EXCLUDED.description,
            rating = EXCLUDED.rating,
            category = EXCLUDED.category,
            difficulty = EXCLUDED.difficulty,
            activities = EXCLUDED.activities,
            mood_tags = EXCLUDED.mood_tags,
            highlights = EXCLUDED.highlights,
            estimated_cost = EXCLUDED.estimated_cost,
            estimated_cost_pkr_min = EXCLUDED.estimated_cost_pkr_min,
            estimated_cost_pkr_max = EXCLUDED.estimated_cost_pkr_max,
            best_months = EXCLUDED.best_months,
            avg_duration_hours = EXCLUDED.avg_duration_hours,
            accessibility = EXCLUDED.accessibility,
            permits_required = EXCLUDED.permits_required,
            nearby_facilities = EXCLUDED.nearby_facilities,
            photos = EXCLUDED.photos,
            last_api_fetch = NOW(),
            updated_at = NOW()
        """
        
        cursor.execute(query, (
            poi_data['location_id'],
            poi_data['osm_id'],
            poi_data['osm_type'],
            poi_data['name'],
            poi_data['latitude'],
            poi_data['longitude'],
            poi_data.get('description', ''),
            poi_data.get('estimated_rating', 4.0),
            poi_data['category'],
            poi_data['difficulty'],
            json.dumps(poi_data['activities']),
            json.dumps(poi_data['mood_tags']),
            json.dumps(poi_data.get('highlights', [])),
            poi_data['estimated_cost'],
            poi_data['cost_range_pkr']['min'],
            poi_data['cost_range_pkr']['max'],
            poi_data['best_months'],
            poi_data['avg_duration_hours'],
            poi_data['accessibility'],
            poi_data['permits_required'],
            poi_data.get('nearby_facilities', ''),
            json.dumps(poi_data.get('photos', [])),
            False  # verified = False
        ))
        
        self.conn.commit()
        cursor.close()
    
    def get_stats(self):
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT COUNT(*) as total FROM points_of_interest")
        total = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM points_of_interest 
            GROUP BY category 
            ORDER BY count DESC
        """)
        by_category = cursor.fetchall()
        
        cursor.execute("""
            SELECT lm.parent_region, COUNT(*) as count
            FROM points_of_interest poi
            JOIN location_mapping lm ON poi.location_id = lm.location_id
            GROUP BY lm.parent_region
            ORDER BY count DESC
        """)
        by_region = cursor.fetchall()
        
        cursor.execute("SELECT AVG(rating) as avg_rating FROM points_of_interest")
        avg_rating = cursor.fetchone()['avg_rating']
        
        cursor.close()
        
        return {
            'total': total,
            'by_category': by_category,
            'by_region': by_region,
            'avg_rating': float(avg_rating) if avg_rating else 0
        }
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='POI Data Collection Pipeline')
    parser.add_argument('--limit', type=int, help='Limit number of locations to process')
    parser.add_argument('--skip', type=int, default=0, help='Skip first N locations')
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-fetch OSM and re-enrich for every location (use after wiping POIs or to refresh)',
    )
    parser.add_argument('--stats', action='store_true', help='Show current statistics')
    
    args = parser.parse_args()
    pipeline = None
    
    try:
        pipeline = POIPipeline()
        
        if args.stats:
            stats = pipeline.get_stats()
            print(f"\n{'='*60}")
            print("📊 POI DATABASE STATISTICS")
            print(f"{'='*60}")
            print(f"\nTotal POIs: {stats['total']}")
            print(f"Average Rating: {stats['avg_rating']:.2f}/5.0")
            print(f"\nPOIs by Category:")
            for item in stats['by_category']:
                print(f"  {item['category']:15s}: {item['count']:4d}")
            print(f"\nPOIs by Region:")
            for item in stats['by_region']:
                print(f"  {item['parent_region']:20s}: {item['count']:4d}")
            print(f"\n{'='*60}\n")
        else:
            pipeline.process_all_locations(
                limit=args.limit,
                skip=args.skip,
                force_repopulate=args.force,
            )
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Pipeline error: {e}")
        raise
    finally:
        if pipeline:
            pipeline.close()

if __name__ == "__main__":
    main()