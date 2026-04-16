#!/usr/bin/env python3
"""
Recreate `corridor_locations` with `location_id` as the second column.

Target structure:
  1) corridor_id  INT   (FK -> travel_corridors.corridor_id)
  2) location_id  INT   (FK -> location_mapping.location_id)
  3) route_order  SMALLINT (>=1)

This script:
- Backs up existing rows (if table exists)
- Drops `corridor_locations`
- Recreates it with the new schema
- Re-inserts data from backup:
  - If old table had `location_id`, uses it directly
  - If old table had `city`, maps city -> location_mapping.location_id

Usage:
  python database/recreate_corridor_locations_with_location_id.py --dry-run
  python database/recreate_corridor_locations_with_location_id.py --apply
"""

from __future__ import annotations

import argparse
import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, ".env"))


def db_connect():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "raahi_ai"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
    )


def _table_exists(cur, table_name: str) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        )
        """,
        (table_name,),
    )
    return bool(cur.fetchone()["exists"])


def _column_exists(cur, table_name: str, column_name: str) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name = %s
              AND column_name = %s
        )
        """,
        (table_name, column_name),
    )
    return bool(cur.fetchone()["exists"])


def _create_new_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE corridor_locations (
            corridor_id INT NOT NULL REFERENCES travel_corridors(corridor_id) ON DELETE CASCADE,
            location_id INT NOT NULL REFERENCES location_mapping(location_id) ON DELETE CASCADE,
            route_order SMALLINT NOT NULL CHECK (route_order >= 1),
            PRIMARY KEY (corridor_id, location_id),
            UNIQUE (corridor_id, route_order)
        )
        """
    )
    cur.execute(
        "CREATE INDEX idx_corridor_locations_corridor ON corridor_locations(corridor_id)"
    )
    cur.execute(
        "CREATE INDEX idx_corridor_locations_location ON corridor_locations(location_id)"
    )


def _migrate_from_backup(cur, has_old_location_id: bool, has_old_city: bool) -> tuple[int, int]:
    """
    Returns:
      (inserted_rows, unmapped_rows)
    """
    inserted = 0
    unmapped = 0

    if has_old_location_id:
        cur.execute(
            """
            INSERT INTO corridor_locations (corridor_id, location_id, route_order)
            SELECT corridor_id, location_id, route_order
            FROM corridor_locations_backup
            WHERE location_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """
        )
        inserted = cur.rowcount
        return inserted, 0

    if has_old_city:
        # Count unmapped rows first
        cur.execute(
            """
            SELECT COUNT(*) AS c
            FROM corridor_locations_backup b
            LEFT JOIN location_mapping lm
              ON LOWER(TRIM(b.city)) = LOWER(TRIM(lm.city))
            WHERE lm.location_id IS NULL
            """
        )
        unmapped = int(cur.fetchone()["c"])

        cur.execute(
            """
            INSERT INTO corridor_locations (corridor_id, location_id, route_order)
            SELECT b.corridor_id, lm.location_id, b.route_order
            FROM corridor_locations_backup b
            JOIN location_mapping lm
              ON LOWER(TRIM(b.city)) = LOWER(TRIM(lm.city))
            ON CONFLICT DO NOTHING
            """
        )
        inserted = cur.rowcount
        return inserted, unmapped

    return 0, 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Drop/recreate corridor_locations with location_id as FK."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview and rollback.")
    parser.add_argument("--apply", action="store_true", help="Commit changes.")
    args = parser.parse_args()

    if args.dry_run == args.apply:
        print("Choose exactly one of --dry-run or --apply", file=sys.stderr)
        return 2

    conn = db_connect()
    try:
        conn.autocommit = False
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            table_exists = _table_exists(cur, "corridor_locations")
            has_old_location_id = False
            has_old_city = False
            backup_rows = 0

            if table_exists:
                has_old_location_id = _column_exists(cur, "corridor_locations", "location_id")
                has_old_city = _column_exists(cur, "corridor_locations", "city")

                cur.execute(
                    "CREATE TEMP TABLE corridor_locations_backup AS SELECT * FROM corridor_locations"
                )
                cur.execute("SELECT COUNT(*) AS c FROM corridor_locations_backup")
                backup_rows = int(cur.fetchone()["c"])

                cur.execute("DROP TABLE corridor_locations")

            _create_new_table(cur)
            inserted, unmapped = _migrate_from_backup(cur, has_old_location_id, has_old_city)

            cur.execute("SELECT COUNT(*) AS c FROM corridor_locations")
            final_rows = int(cur.fetchone()["c"])

        print("Recreated corridor_locations successfully.")
        print(f"Backup rows from old table: {backup_rows}")
        print(f"Rows inserted into new table: {inserted}")
        print(f"Rows currently in new table: {final_rows}")
        if has_old_city:
            print(f"Unmapped old city rows (not inserted): {unmapped}")

        if args.apply:
            conn.commit()
            print("Applied successfully.")
        else:
            conn.rollback()
            print("Dry run complete. No changes committed.")
        return 0
    except Exception as exc:
        conn.rollback()
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

