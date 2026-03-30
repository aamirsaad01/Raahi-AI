"""
Script to create ndma_alerts table programmatically
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

def create_table():
    """Create ndma_alerts table"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        cursor = conn.cursor()
        
        # Read SQL file
        sql_file = os.path.join(repo_root, 'database', 'postgresql', 'add_ndma_alerts_table.sql')
        
        if not os.path.exists(sql_file):
            print(f"❌ SQL file not found: {sql_file}")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Execute SQL
        cursor.execute(sql)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Creating ndma_alerts table")
    print("=" * 60)
    
    success = create_table()
    
    if success:
        print("✅ Table created successfully!")
        print("\nYou can now run the poller:")
        print("  python backend_scripts/ndma_poller.py --once")
    else:
        print("\n❌ Failed to create table.")
        print("Please check the error above or create it manually using pgAdmin.")



