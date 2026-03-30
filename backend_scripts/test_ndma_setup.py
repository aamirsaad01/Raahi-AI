"""
Quick test script to check NDMA setup
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

def check_table_exists():
    """Check if ndma_alerts table exists"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'ndma_alerts'
            );
        """)
        exists = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return exists
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Checking NDMA Setup")
    print("=" * 60)
    
    exists = check_table_exists()
    
    if exists:
        print("✅ ndma_alerts table exists!")
        print("\nYou can now run the poller:")
        print("  python backend_scripts/ndma_poller.py --once")
    else:
        print("❌ ndma_alerts table does NOT exist!")
        print("\nPlease create it first:")
        print("  psql -U postgres -d raahi_ai -f database/postgresql/add_ndma_alerts_table.sql")
        print("\nOr in pgAdmin:")
        print("  1. Open Query Tool")
        print("  2. Execute: database/postgresql/add_ndma_alerts_table.sql")



