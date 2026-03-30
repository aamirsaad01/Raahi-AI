"""
Script to delete POIs for destinations starting from Karimabad (position 8 and below)
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

def delete_pois_from_destinations():
    """Delete POIs for destinations starting from Karimabad (position 8+)"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Destinations to delete (starting from Karimabad, position 8+)
    # Based on the previous count output:
    # 8. Karimabad - Location ID: 8
    # 9. Nagar - Location ID: 12
    # 10. Ghizer - Location ID: 5
    # 11. Hussaini - Location ID: 13
    # 12. Passu - Location ID: 10
    
    location_ids_to_delete = [8, 10]
    
    # First, get the destination names and POI counts for confirmation
    print("\n" + "=" * 80)
    print("🗑️  POI DELETION - PREVIEW")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            lm.location_id,
            lm.city as destination,
            lm.parent_region as region,
            COUNT(poi.poi_id) as poi_count
        FROM location_mapping lm
        INNER JOIN points_of_interest poi ON lm.location_id = poi.location_id
        WHERE lm.location_id = ANY(%s)
        GROUP BY lm.location_id, lm.city, lm.parent_region
        ORDER BY poi_count DESC
    """, (location_ids_to_delete,))
    
    destinations_to_delete = cursor.fetchall()
    
    if not destinations_to_delete:
        print("\n⚠️  No POIs found for the specified destinations.")
        cursor.close()
        conn.close()
        return
    
    print("\n📋 Destinations that will have their POIs deleted:")
    print("-" * 80)
    print(f"{'Destination':<25} {'Region':<20} {'POI Count':<12} {'Location ID':<12}")
    print("-" * 80)
    
    total_pois_to_delete = 0
    for dest in destinations_to_delete:
        destination = dest['destination'] or 'N/A'
        region = dest['region'] or 'N/A'
        poi_count = dest['poi_count']
        location_id = dest['location_id']
        total_pois_to_delete += poi_count
        print(f"{destination:<25} {region:<20} {poi_count:<12} {location_id:<12}")
    
    print("-" * 80)
    print(f"\n⚠️  Total POIs to be deleted: {total_pois_to_delete}")
    print(f"⚠️  Number of destinations affected: {len(destinations_to_delete)}")
    
    # Ask for confirmation
    print("\n" + "=" * 80)
    response = input("\n❓ Are you sure you want to delete these POIs? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n❌ Deletion cancelled.")
        cursor.close()
        conn.close()
        return
    
    # Delete POIs
    print("\n🗑️  Deleting POIs...")
    
    cursor.execute("""
        DELETE FROM points_of_interest
        WHERE location_id = ANY(%s)
    """, (location_ids_to_delete,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    
    print(f"\n✅ Successfully deleted {deleted_count} POIs from {len(destinations_to_delete)} destinations.")
    
    # Verify deletion
    cursor.execute("""
        SELECT 
            lm.location_id,
            lm.city as destination,
            COUNT(poi.poi_id) as poi_count
        FROM location_mapping lm
        LEFT JOIN points_of_interest poi ON lm.location_id = poi.location_id
        WHERE lm.location_id = ANY(%s)
        GROUP BY lm.location_id, lm.city
        ORDER BY lm.city
    """, (location_ids_to_delete,))
    
    remaining = cursor.fetchall()
    
    print("\n📊 Verification - Remaining POIs for these destinations:")
    print("-" * 80)
    for dest in remaining:
        destination = dest['destination'] or 'N/A'
        poi_count = dest['poi_count'] or 0
        if poi_count == 0:
            print(f"✅ {destination}: 0 POIs (all deleted)")
        else:
            print(f"⚠️  {destination}: {poi_count} POIs remaining")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    try:
        delete_pois_from_destinations()
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

