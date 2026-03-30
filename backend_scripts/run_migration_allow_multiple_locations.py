"""
Script to run migration: Allow POIs to exist for multiple destinations
"""

import sys
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

def run_migration():
    """Run the migration to allow POIs in multiple locations"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        
        cursor = conn.cursor()
        
        # Read migration SQL file
        migration_file = os.path.join(
            repo_root, 
            'database', 
            'postgresql', 
            'migrations', 
            'allow_poi_multiple_locations.sql'
        )
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("🔄 Running migration: Allow POIs in multiple destinations")
        print("=" * 70)
        
        # Execute migration
        cursor.execute(migration_sql)
        conn.commit()
        
        print("\n✅ Migration completed successfully!")
        print("\n📋 Changes made:")
        print("   - Removed UNIQUE constraint on osm_id")
        print("   - Added composite UNIQUE constraint on (osm_id, location_id)")
        print("   - Created index for faster lookups")
        print("\n💡 Now the same POI can exist for multiple destinations!")
        
        cursor.close()
        conn.close()
        
    except FileNotFoundError:
        print(f"❌ Migration file not found: {migration_file}")
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection error: {e}")
        print("\n💡 Make sure:")
        print("   1. PostgreSQL is running")
        print("   2. Database credentials in .env file are correct")
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_migration()

