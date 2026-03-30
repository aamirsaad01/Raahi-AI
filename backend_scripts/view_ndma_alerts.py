"""
View NDMA alerts from database
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

def view_alerts():
    """View all alerts from database"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get count
        cursor.execute("SELECT COUNT(*) as count FROM ndma_alerts")
        count = cursor.fetchone()['count']
        
        print(f"\n📊 Total alerts in database: {count}\n")
        
        if count == 0:
            print("No alerts found.")
            cursor.close()
            conn.close()
            return
        
        # Get all alerts
        cursor.execute("""
            SELECT 
                alert_id,
                title,
                published_date,
                advisory_type,
                severity,
                affected_regions,
                scraped_at,
                is_active
            FROM ndma_alerts
            ORDER BY scraped_at DESC
            LIMIT 10
        """)
        
        alerts = cursor.fetchall()
        
        print("=" * 80)
        print("📋 Recent Alerts")
        print("=" * 80)
        
        for i, alert in enumerate(alerts, 1):
            print(f"\n{i}. {alert['title']}")
            print(f"   Type: {alert['advisory_type']}")
            print(f"   Date: {alert['published_date'] or 'N/A'}")
            print(f"   Severity: {alert['severity'].upper()}")
            print(f"   Regions: {', '.join(alert['affected_regions']) if alert['affected_regions'] else 'General'}")
            print(f"   Scraped: {alert['scraped_at']}")
            print(f"   Active: {'Yes' if alert['is_active'] else 'No'}")
        
        # Get statistics
        cursor.execute("""
            SELECT 
                severity,
                COUNT(*) as count
            FROM ndma_alerts
            GROUP BY severity
            ORDER BY 
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
        """)
        
        stats = cursor.fetchall()
        
        print("\n" + "=" * 80)
        print("📈 Statistics by Severity")
        print("=" * 80)
        for stat in stats:
            print(f"  {stat['severity'].upper()}: {stat['count']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("🔍 Viewing NDMA Alerts")
    print("=" * 80)
    view_alerts()



