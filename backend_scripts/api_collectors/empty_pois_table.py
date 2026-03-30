"""
Empty the points_of_interest table
Use this before re-running the POI collection pipeline from scratch
"""

import os
import psycopg2
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

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


def get_poi_count(conn):
    """Get current POI count"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM points_of_interest")
    count = cursor.fetchone()[0]
    cursor.close()
    return count


def empty_pois_table(conn):
    """Delete all records from points_of_interest table"""
    cursor = conn.cursor()
    
    # Get count before deletion
    count_before = get_poi_count(conn)
    
    # Delete all records
    cursor.execute("DELETE FROM points_of_interest")
    conn.commit()
    
    deleted_count = cursor.rowcount
    cursor.close()
    
    return count_before, deleted_count


def main():
    """Main function"""
    print("=" * 60)
    print("🗑️  Empty POIs Table")
    print("=" * 60)
    print()
    
    # Connect to database
    conn = connect_to_db()
    
    # Get current count
    count_before = get_poi_count(conn)
    print(f"📊 Current POI count: {count_before}")
    
    if count_before == 0:
        print("✅ Table is already empty. Nothing to delete.")
        conn.close()
        return
    
    # Warning
    print("\n⚠️  WARNING: This will delete ALL POIs from the database!")
    print("   This action cannot be undone.")
    print("\n   After deletion, you can re-run the collection pipeline:")
    print("   cd backend_scripts/api_collectors")
    print("   python poi_pipeline.py")
    
    # Ask for confirmation
    response = input("\nAre you sure you want to delete all POIs? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Cancelled by user")
        conn.close()
        return
    
    # Delete all POIs
    print("\n🗑️  Deleting all POIs...")
    try:
        count_before, deleted_count = empty_pois_table(conn)
        print(f"✅ Successfully deleted {deleted_count} POI(s)")
        print(f"   (Found {count_before} record(s) before deletion)")
        
        # Verify
        count_after = get_poi_count(conn)
        if count_after == 0:
            print("✅ Table is now empty")
        else:
            print(f"⚠️  Warning: {count_after} record(s) still remain")
            
    except Exception as e:
        logger.error(f"❌ Error deleting POIs: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print("\n" + "=" * 60)
    print("📝 Next Steps:")
    print("=" * 60)
    print("1. Make sure GEMINI_API_KEY is set in your .env file")
    print("2. Run the POI collection pipeline:")
    print("   cd backend_scripts/api_collectors")
    print("   python poi_pipeline.py")
    print("=" * 60)


if __name__ == "__main__":
    main()

