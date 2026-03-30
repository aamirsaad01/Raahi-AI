"""
Quick script to view alerts from ndma_alerts_ai table
"""
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "raahi_ai"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
    )
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all alerts
    cursor.execute("SELECT * FROM ndma_alerts_ai ORDER BY scraped_at DESC")
    alerts = cursor.fetchall()
    
    print(f"\n📊 Total alerts in database: {len(alerts)}\n")
    print("=" * 100)
    
    for i, alert in enumerate(alerts, 1):
        print(f"\nAlert {i}:")
        print(f"  ID: {alert.get('alert_id')}")
        print(f"  Heading: {alert.get('heading')}")
        print(f"  Location: {alert.get('location_name')}")
        print(f"  Severity: {alert.get('severity')}")
        print(f"  Type: {alert.get('icon_type')}")
        print(f"  Description: {alert.get('description', '')[:100]}...")
        print(f"  Published: {alert.get('published_date')}")
        print(f"  Scraped: {alert.get('scraped_at')}")
        print(f"  Active: {alert.get('is_active')}")
        print(f"  Lat/Lon: {alert.get('latitude')}, {alert.get('longitude')}")
        print("-" * 100)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")

