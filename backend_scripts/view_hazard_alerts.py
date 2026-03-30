"""
View all hazard alerts from database (NDMA alerts + User reports)
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

def view_all_hazards():
    """View all hazards from database"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=" * 100)
        print("🚨 HAZARD ALERTS DATABASE VIEWER")
        print("=" * 100)
        
        # Get NDMA alerts count
        cursor.execute("SELECT COUNT(*) as count FROM ndma_alerts WHERE is_active = TRUE")
        ndma_count = cursor.fetchone()['count']
        
        # Get user reports count
        cursor.execute("SELECT COUNT(*) as count FROM hazard_reports")
        user_count = cursor.fetchone()['count']
        
        print(f"\n📊 Database Summary:")
        print(f"   NDMA Alerts (Active): {ndma_count}")
        print(f"   User Reports: {user_count}")
        print(f"   Total Hazards: {ndma_count + user_count}")
        
        # View NDMA Alerts
        print("\n" + "=" * 100)
        print("📡 NDMA ALERTS")
        print("=" * 100)
        
        cursor.execute("""
            SELECT 
                alert_id,
                title,
                published_date,
                advisory_type,
                severity,
                affected_regions,
                scraped_at,
                is_active,
                advisory_url
            FROM ndma_alerts
            WHERE is_active = TRUE
            ORDER BY scraped_at DESC
            LIMIT 50
        """)
        
        ndma_alerts = cursor.fetchall()
        
        if not ndma_alerts:
            print("\n   No NDMA alerts found.")
        else:
            for i, alert in enumerate(ndma_alerts, 1):
                print(f"\n{i}. {alert['title']}")
                print(f"   ID: {alert['alert_id']}")
                print(f"   Type: {alert['advisory_type'] or 'N/A'}")
                print(f"   Severity: {alert['severity'].upper()}")
                print(f"   Date: {alert['published_date'] or 'N/A'}")
                print(f"   Regions: {', '.join(alert['affected_regions']) if alert['affected_regions'] else 'General'}")
                print(f"   Scraped: {alert['scraped_at']}")
                print(f"   URL: {alert['advisory_url'][:80]}..." if len(alert['advisory_url'] or '') > 80 else f"   URL: {alert['advisory_url']}")
        
        # View User Reports
        print("\n" + "=" * 100)
        print("👤 USER-REPORTED HAZARDS")
        print("=" * 100)
        
        cursor.execute("""
            SELECT 
                hazard_id,
                title,
                description,
                severity,
                location,
                reported_at,
                user_id
            FROM hazard_reports
            ORDER BY reported_at DESC
            LIMIT 50
        """)
        
        user_reports = cursor.fetchall()
        
        if not user_reports:
            print("\n   No user reports found.")
        else:
            for i, report in enumerate(user_reports, 1):
                print(f"\n{i}. {report['title']}")
                print(f"   ID: {report['hazard_id']}")
                print(f"   Severity: {report['severity'].upper()}")
                print(f"   Location: {report['location'] or 'N/A'}")
                print(f"   Reported: {report['reported_at']}")
                if report['description']:
                    desc = report['description'][:100] + "..." if len(report['description']) > 100 else report['description']
                    print(f"   Description: {desc}")
        
        # Statistics
        print("\n" + "=" * 100)
        print("📈 STATISTICS")
        print("=" * 100)
        
        # NDMA by severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM ndma_alerts
            WHERE is_active = TRUE
            GROUP BY severity
            ORDER BY 
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
        """)
        
        print("\nNDMA Alerts by Severity:")
        for stat in cursor.fetchall():
            print(f"   {stat['severity'].upper()}: {stat['count']}")
        
        # User reports by severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM hazard_reports
            GROUP BY severity
            ORDER BY 
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
        """)
        
        print("\nUser Reports by Severity:")
        for stat in cursor.fetchall():
            print(f"   {stat['severity'].upper()}: {stat['count']}")
        
        # Recent activity
        print("\n" + "=" * 100)
        print("🕐 RECENT ACTIVITY (Last 24 hours)")
        print("=" * 100)
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM ndma_alerts
            WHERE scraped_at >= NOW() - INTERVAL '24 hours'
        """)
        recent_ndma = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM hazard_reports
            WHERE reported_at >= NOW() - INTERVAL '24 hours'
        """)
        recent_user = cursor.fetchone()['count']
        
        print(f"   New NDMA alerts: {recent_ndma}")
        print(f"   New user reports: {recent_user}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 100)
        print("✅ Done!")
        print("=" * 100)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    view_all_hazards()


