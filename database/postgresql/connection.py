# database/postgresql/connection.py
import psycopg2
from psycopg2.extras import RealDictCursor

def connect():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname="raahi_ai",         # database name you created
            user="postgres",           # default postgres user
            password="m201418.",  # <-- replace this with your actual password
            host="localhost",
            port="5432"
        )
        print("✅ Connected to PostgreSQL successfully!")

        # Create a cursor to test a query
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT NOW() AS server_time;")
        result = cur.fetchone()
        print("📅 Server Time:", result["server_time"])

        # Always close connections
        cur.close()
        conn.close()

    except Exception as e:
        print("❌ Connection failed:", str(e))

if __name__ == "__main__":
    connect()
