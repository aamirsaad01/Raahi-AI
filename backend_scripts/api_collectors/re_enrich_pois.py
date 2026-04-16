"""
Re-enrich POIs that have default/fallback values (same enricher selection as poi_pipeline:
OpenAI when OPENAI_API_KEY is set, else Ollama).
"""

import os
import sys
import psycopg2
import json
import time
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_collectors.llm_enricher import POIEnricher
from api_collectors.openai_enricher import OpenAIPOIEnricher

# Load environment variables
load_dotenv()


def _make_enricher():
    mode = (os.getenv("POI_ENRICHER") or "").strip().lower()
    if mode == "ollama":
        return POIEnricher()
    if mode == "openai":
        return OpenAIPOIEnricher()
    if (os.getenv("OPENAI_API_KEY") or "").strip():
        try:
            return OpenAIPOIEnricher()
        except Exception as e:
            logger.warning("OpenAI unavailable (%s); using Ollama.", e)
    return POIEnricher()

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


def connect_to_db():
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


def find_pois_with_default_values(conn):
    """
    Find POIs that likely have default enrichment values
    
    Criteria:
    - Description contains generic template text
    - OR cost_max is exactly 4000 (default)
    - OR duration is exactly 3.0 (default)
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT poi_id, name, location_id, description, 
               estimated_cost_pkr_max, avg_duration_hours, category,
               lm.city, lm.parent_region
        FROM points_of_interest poi
        JOIN location_mapping lm ON poi.location_id = lm.location_id
        WHERE 
            -- Generic description pattern
            description LIKE '%is a tourist attraction in Northern Pakistan known for its natural beauty and cultural significance%'
            OR 
            -- Default cost (exactly 4000)
            (estimated_cost_pkr_max = 4000 AND estimated_cost_pkr_min = 1500)
            OR
            -- Default duration (exactly 3.0)
            avg_duration_hours = 3.0
        ORDER BY poi_id
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    
    return [dict(row) for row in results]


def update_poi(conn, poi_id: int, enriched_data: dict):
    """Update POI with enriched data"""
    cursor = conn.cursor()
    
    query = """
        UPDATE points_of_interest
        SET 
            description = %s,
            rating = %s,
            category = %s,
            difficulty = %s,
            activities = %s::jsonb,
            mood_tags = %s::jsonb,
            highlights = %s::jsonb,
            estimated_cost = %s,
            estimated_cost_pkr_min = %s,
            estimated_cost_pkr_max = %s,
            best_months = %s,
            avg_duration_hours = %s,
            accessibility = %s,
            permits_required = %s,
            nearby_facilities = %s,
            updated_at = NOW()
        WHERE poi_id = %s
    """
    
    cursor.execute(query, (
        enriched_data.get('description', ''),
        enriched_data.get('estimated_rating', 4.0),
        enriched_data.get('category', 'nature'),
        enriched_data.get('difficulty', 'moderate'),
        json.dumps(enriched_data.get('activities', [])),
        json.dumps(enriched_data.get('mood_tags', [])),
        json.dumps(enriched_data.get('highlights', [])),
        enriched_data.get('estimated_cost', 'Medium'),
        enriched_data.get('cost_range_pkr', {}).get('min', 1500),
        enriched_data.get('cost_range_pkr', {}).get('max', 4000),
        enriched_data.get('best_months', 'March-October'),
        enriched_data.get('avg_duration_hours', 3.0),
        enriched_data.get('accessibility', 'accessible by sedan on paved roads'),
        enriched_data.get('permits_required', False),
        enriched_data.get('nearby_facilities', ''),
        poi_id
    ))
    
    conn.commit()
    cursor.close()


def main():
    """Main re-enrichment process"""
    print("=" * 60)
    print("🔄 POI Re-Enrichment Script")
    print("=" * 60)
    print()
    
    # Connect to database
    conn = connect_to_db()
    
    try:
        enricher = _make_enricher()
        logger.info("LLM enricher initialized (%s)", type(enricher).__name__)
    except Exception as e:
        logger.error("Failed to initialize enricher: %s", e)
        logger.error("Set OPENAI_API_KEY or run Ollama (POI_ENRICHER=ollama).")
        return
    
    # Find POIs with default values
    logger.info("🔍 Finding POIs with default enrichment values...")
    pois_to_re_enrich = find_pois_with_default_values(conn)
    
    if not pois_to_re_enrich:
        print("✅ No POIs found with default values. All POIs appear to be properly enriched!")
        return
    
    print(f"\n📊 Found {len(pois_to_re_enrich)} POI(s) with default values")
    print("\nSample POIs to re-enrich:")
    for i, poi in enumerate(pois_to_re_enrich[:5], 1):
        print(f"  {i}. {poi['name']} ({poi['city']}, {poi['parent_region']})")
    if len(pois_to_re_enrich) > 5:
        print(f"  ... and {len(pois_to_re_enrich) - 5} more")
    
    # Ask for confirmation
    print("\n⚠️  This will update POI data using Gemini AI (may take time and use API quota)")
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return
    
    # Re-enrich each POI
    print("\n🚀 Starting re-enrichment...\n")
    successful = 0
    failed = 0
    
    for i, poi in enumerate(pois_to_re_enrich, 1):
        poi_id = poi['poi_id']
        poi_name = poi['name']
        location = poi['city']
        category = poi.get('category', 'nature')
        
        print(f"[{i}/{len(pois_to_re_enrich)}] Processing: {poi_name} ({location})")
        
        try:
            # Prepare POI data for enrichment
            poi_data = {
                'name': poi_name,
                'location_name': location,
                'category': category,
                'activities': [],  # Will be enriched by LLM
                'osm_tags': {}  # Not available, but enricher can work without it
            }
            
            # Enrich with LLM
            enriched_data = enricher.enrich_poi(poi_data)
            
            # Update database
            update_poi(conn, poi_id, enriched_data)
            
            print(f"   ✅ Re-enriched: {poi_name}")
            print(f"      Cost: PKR {enriched_data.get('cost_range_pkr', {}).get('min', 0)}-{enriched_data.get('cost_range_pkr', {}).get('max', 0)}")
            print(f"      Duration: {enriched_data.get('avg_duration_hours', 0)} hours")
            successful += 1
            
            # Rate limiting - wait 1 second between requests
            if i < len(pois_to_re_enrich):
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"   ❌ Failed to re-enrich {poi_name}: {e}")
            failed += 1
            continue
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Re-Enrichment Summary")
    print("=" * 60)
    print(f"✅ Successfully re-enriched: {successful} POI(s)")
    print(f"❌ Failed: {failed} POI(s)")
    print(f"📝 Total processed: {len(pois_to_re_enrich)} POI(s)")
    print("=" * 60)
    
    conn.close()


if __name__ == "__main__":
    main()

