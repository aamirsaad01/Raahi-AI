"""
Script to count how many destinations have POIs in the database
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "raahi_ai"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
    )

def count_destinations_with_pois():
    """Count how many destinations have POIs"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Query 1: Count distinct locations with POIs
    cursor.execute("""
        SELECT COUNT(DISTINCT location_id) as destination_count
        FROM points_of_interest
        WHERE location_id IS NOT NULL
    """)
    result = cursor.fetchone()
    total_destinations = result['destination_count'] if result else 0
    
    # Query 2: Get list of destinations with POI counts
    cursor.execute("""
        SELECT 
            lm.location_id,
            lm.city as destination,
            lm.parent_region as region,
            COUNT(poi.poi_id) as poi_count
        FROM location_mapping lm
        INNER JOIN points_of_interest poi ON lm.location_id = poi.location_id
        GROUP BY lm.location_id, lm.city, lm.parent_region
        ORDER BY poi_count DESC, lm.city
    """)
    
    destinations = cursor.fetchall()
    
    print("\n" + "=" * 80)
    print("📊 DESTINATIONS WITH POIs - SUMMARY")
    print("=" * 80)
    print(f"\n✅ Total destinations with POIs: {total_destinations}\n")
    
    if destinations:
        print("📋 Detailed List:")
        print("-" * 80)
        print(f"{'Destination':<25} {'Region':<20} {'POI Count':<12} {'Location ID':<12}")
        print("-" * 80)
        
        total_pois = 0
        for dest in destinations:
            destination = dest['destination'] or 'N/A'
            region = dest['region'] or 'N/A'
            poi_count = dest['poi_count']
            location_id = dest['location_id']
            total_pois += poi_count
            print(f"{destination:<25} {region:<20} {poi_count:<12} {location_id:<12}")
        
        print("-" * 80)
        print(f"\n📈 Total POIs across all destinations: {total_pois}")
        print(f"📊 Average POIs per destination: {total_pois / len(destinations):.1f}")
        
        # Query 3: Get all POIs for each destination
        print("\n" + "=" * 80)
        print("📋 ALL POIs BY DESTINATION")
        print("=" * 80)
        
        for dest in destinations:
            location_id = dest['location_id']
            destination = dest['destination'] or 'N/A'
            region = dest['region'] or 'N/A'
            poi_count = dest['poi_count']
            
            cursor.execute("""
                SELECT 
                    poi_id,
                    name,
                    category,
                    rating,
                    estimated_cost_pkr_max
                FROM points_of_interest
                WHERE location_id = %s
                ORDER BY name
            """, (location_id,))
            
            pois = cursor.fetchall()
            
            print(f"\n📍 {destination} ({region}) - {poi_count} POI(s)")
            print("-" * 80)
            if pois:
                print(f"{'POI Name':<40} {'Category':<20} {'Rating':<10} {'Cost (PKR)':<12}")
                print("-" * 80)
                for poi in pois:
                    poi_name = poi['name'] or 'N/A'
                    category = poi['category'] or 'N/A'
                    rating = f"{poi['rating']:.1f}" if poi['rating'] else 'N/A'
                    cost = poi['estimated_cost_pkr_max'] if poi['estimated_cost_pkr_max'] else 'N/A'
                    print(f"{poi_name:<40} {category:<20} {rating:<10} {cost:<12}")
            else:
                print("  (No POIs found)")
            print("-" * 80)
    else:
        print("⚠️  No destinations with POIs found in the database.")
    
    # Query 3: Count total locations in location_mapping (for comparison)
    cursor.execute("SELECT COUNT(*) as total FROM location_mapping")
    total_locations = cursor.fetchone()['total']
    
    print(f"\n📌 Total locations in location_mapping table: {total_locations}")
    print(f"📌 Locations without POIs: {total_locations - total_destinations}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    try:
        count_destinations_with_pois()
    except psycopg2.OperationalError as e:
        print(f"\n❌ Database connection error: {e}")
        print("\n💡 Make sure:")
        print("   1. PostgreSQL is running")
        print("   2. Database credentials in .env file are correct")
        print("   3. Database 'raahi_ai' exists")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

