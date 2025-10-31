# database/postgresql/connection.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Optional dotenv support for local development
try:
    from dotenv import load_dotenv  # type: ignore
    # Load from repo root (go up 2 directories from this file)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))
    env_path = os.path.join(repo_root, '.env')
    load_dotenv(dotenv_path=env_path)
except Exception as e:
    pass

def connect():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        print("✅ Connected to PostgreSQL successfully!")

        # Create a cursor to test a query
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT NOW() AS server_time;")
        result = cur.fetchone()
        print("📅 Server Time:", result["server_time"])

        cur.close()
        conn.close()

    except Exception as e:
        print("❌ Connection failed:", str(e))

if __name__ == "__main__":
    connect()
