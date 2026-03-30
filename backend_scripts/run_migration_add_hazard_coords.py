"""
Migration script to add latitude, longitude, and hazard_type columns to hazard_reports table
Run this once to update the database schema
"""

import sys
import os
import psycopg2
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(repo_root, '.env')

# Try loading from expected location first, then fallback to default search
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    # Try loading from current directory or parent directories
    load_dotenv()  # This will look for .env in current and parent directories

def get_db_connection():
    """Get database connection"""
    db_password = os.getenv('DB_PASSWORD', '')
    if not db_password:
        raise ValueError("DB_PASSWORD not found in environment variables. Please check your .env file.")
    
    return psycopg2.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'raahi_ai'),
        user=os.getenv('DB_USER', 'postgres'),
        password=db_password
    )

def run_migration():
    """Run the migration"""
    migration_sql = """
    -- Add latitude column if it doesn't exist
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='hazard_reports' AND column_name='latitude'
        ) THEN
            ALTER TABLE hazard_reports ADD COLUMN latitude NUMERIC(10,8);
        END IF;
    END$$;

    -- Add longitude column if it doesn't exist
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='hazard_reports' AND column_name='longitude'
        ) THEN
            ALTER TABLE hazard_reports ADD COLUMN longitude NUMERIC(11,8);
        END IF;
    END$$;

    -- Add hazard_type column if it doesn't exist
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='hazard_reports' AND column_name='hazard_type'
        ) THEN
            ALTER TABLE hazard_reports ADD COLUMN hazard_type VARCHAR(50) DEFAULT 'roadblock';
        END IF;
    END$$;

    -- Create index on coordinates for faster spatial queries
    CREATE INDEX IF NOT EXISTS idx_hazard_reports_coords ON hazard_reports(latitude, longitude);

    -- Create index on hazard_type for filtering
    CREATE INDEX IF NOT EXISTS idx_hazard_reports_type ON hazard_reports(hazard_type);
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🔄 Running migration: Adding latitude, longitude, and hazard_type columns to hazard_reports...")
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Migration completed successfully!")
        
        # Verify columns were added
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='hazard_reports' 
            AND column_name IN ('latitude', 'longitude', 'hazard_type')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        if columns:
            print("\n📋 Added columns:")
            for col_name, col_type in columns:
                print(f"   - {col_name}: {col_type}")
        else:
            print("\n⚠️  Warning: Could not verify columns were added")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        sys.exit(1)

if __name__ == '__main__':
    run_migration()

