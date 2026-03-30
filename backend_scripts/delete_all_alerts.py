"""
Delete all records from ndma_alerts_ai table
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

def delete_all_alerts():
    """Delete all alerts from database"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM ndma_alerts_ai")
        count_before = cursor.fetchone()[0]
        
        # Delete all records
        cursor.execute("DELETE FROM ndma_alerts_ai")
        deleted_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Deleted {deleted_count} alert(s) from ndma_alerts_ai table")
        print(f"   (Found {count_before} record(s) before deletion)")
        
    except Exception as e:
        print(f"❌ Error deleting alerts: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🗑️  Deleting all alerts from ndma_alerts_ai table")
    print("=" * 60)
    delete_all_alerts()
    print("=" * 60)

