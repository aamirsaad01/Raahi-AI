"""
Empty the points_of_interest table.
For wipe + full re-ingest, prefer: repopulate_pois.py --yes
"""

import argparse
import logging
import os

import psycopg2
from dotenv import load_dotenv

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_REPO_ROOT, ".env"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def connect_to_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        logger.info("Connected to database")
        return conn
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        raise


def get_poi_count(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM points_of_interest")
    count = cursor.fetchone()[0]
    cursor.close()
    return count


def empty_pois_table(conn):
    cursor = conn.cursor()
    count_before = get_poi_count(conn)
    cursor.execute("DELETE FROM points_of_interest")
    conn.commit()
    deleted_count = cursor.rowcount
    cursor.close()
    return count_before, deleted_count


def main():
    parser = argparse.ArgumentParser(description="Delete all rows from points_of_interest.")
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip interactive confirmation.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Empty POIs table")
    print("=" * 60)
    print()

    conn = connect_to_db()
    count_before = get_poi_count(conn)
    print(f"Current POI count: {count_before}")

    if count_before == 0:
        print("Table is already empty.")
        conn.close()
        return

    print("\nWARNING: This deletes ALL POIs.")
    print("After deletion, run e.g.:")
    print("  python backend_scripts/api_collectors/repopulate_pois.py --yes")

    if not args.yes:
        response = input("\nDelete all POIs? (yes/no): ").strip().lower()
        if response not in ("yes", "y"):
            print("Cancelled.")
            conn.close()
            return

    print("\nDeleting...")
    try:
        count_before, deleted_count = empty_pois_table(conn)
        print(f"Deleted {deleted_count} row(s) (had {count_before} before).")
        count_after = get_poi_count(conn)
        if count_after == 0:
            print("Table is now empty.")
        else:
            print(f"Warning: {count_after} row(s) still remain")
    except Exception as e:
        logger.error("Error deleting POIs: %s", e)
        conn.rollback()
    finally:
        conn.close()

    print("\n" + "=" * 60)
    print("Next: set OPENAI_API_KEY in .env, then:")
    print("  python backend_scripts/api_collectors/repopulate_pois.py --yes")
    print("=" * 60)


if __name__ == "__main__":
    main()
