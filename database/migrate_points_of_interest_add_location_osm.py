#!/usr/bin/env python3
"""
Migrate points_of_interest to include POI/location/OSM fields.

Requested changes:
1) Rename `id` -> `poi_id`
2) Add `location_id` (INT), populated by matching points_of_interest.city
   against location_mapping.city
3) Add `osm_id` (VARCHAR(100)) + `osm_type` (VARCHAR(100))
   - osm_type forced to "node"
   - osm_id forced to NULL for every POI row

Also supports physical column re-ordering so the first columns are:
    poi_id, location_id, osm_id, osm_type, ...

Usage:
    python database/migrate_points_of_interest_add_location_osm.py --dry-run
    python database/migrate_points_of_interest_add_location_osm.py --apply
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


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


def ensure_columns(cur) -> None:
    # 1) rename id -> poi_id (if needed)
    cur.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='public' AND table_name='points_of_interest'
                  AND column_name='id'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='public' AND table_name='points_of_interest'
                  AND column_name='poi_id'
            ) THEN
                ALTER TABLE points_of_interest RENAME COLUMN id TO poi_id;
            END IF;
        END$$;
        """
    )

    # 2) add new columns
    cur.execute("ALTER TABLE points_of_interest ADD COLUMN IF NOT EXISTS location_id INT")
    cur.execute("ALTER TABLE points_of_interest ADD COLUMN IF NOT EXISTS osm_id VARCHAR(100)")
    cur.execute("ALTER TABLE points_of_interest ADD COLUMN IF NOT EXISTS osm_type VARCHAR(100)")

    # keep PK on poi_id
    cur.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conrelid='points_of_interest'::regclass
                  AND contype='p'
                  AND pg_get_constraintdef(oid) LIKE '%(poi_id)%'
            ) THEN
                IF EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conrelid='points_of_interest'::regclass
                      AND contype='p'
                ) THEN
                    ALTER TABLE points_of_interest DROP CONSTRAINT points_of_interest_pkey;
                END IF;
                ALTER TABLE points_of_interest ADD CONSTRAINT points_of_interest_pkey PRIMARY KEY (poi_id);
            END IF;
        END$$;
        """
    )


def populate_location_id(cur) -> int:
    cur.execute(
        """
        UPDATE points_of_interest p
        SET location_id = lm.location_id
        FROM location_mapping lm
        WHERE LOWER(TRIM(p.city)) = LOWER(TRIM(lm.city))
          AND p.location_id IS DISTINCT FROM lm.location_id
        """
    )
    return cur.rowcount


def load_pois_missing_osm(cur, start_poi_id: Optional[int] = None) -> List[Dict]:
    where = "WHERE osm_id IS NULL OR TRIM(osm_id) = ''"
    params: List = []
    if start_poi_id is not None:
        where += " AND poi_id >= %s"
        params.append(start_poi_id)
    cur.execute(
        f"""
        SELECT poi_id, name, city, latitude, longitude
        FROM points_of_interest
        {where}
        ORDER BY poi_id
        """,
        params,
    )
    return [dict(r) for r in cur.fetchall()]


def backfill_osm_ids(
    cur,
    pause_ms: int = 200,
    limit: Optional[int] = None,
    start_poi_id: Optional[int] = None,
    log_every: int = 25,
) -> Tuple[int, int]:
    rows = load_pois_missing_osm(cur, start_poi_id=start_poi_id)
    if limit is not None:
        rows = rows[:limit]
    updated = 0
    failed = 0
    total = len(rows)
    if total == 0:
        return 0, 0
    print(f"Setting osm_id=NULL, osm_type='node' for {total} POIs...")

    for i, r in enumerate(rows, start=1):
        poi_id = r["poi_id"]
        cur.execute(
            """
            UPDATE points_of_interest
            SET osm_id = NULL,
                osm_type = 'node'
            WHERE poi_id = %s
            """,
            (poi_id,),
        )
        updated += 1

        if pause_ms > 0:
            time.sleep(pause_ms / 1000.0)
        if log_every > 0 and (i % log_every == 0 or i == total):
            print(f"  progress: {i}/{total} | updated={updated}")

    # ensure all rows have osm_type node
    cur.execute(
        """
        UPDATE points_of_interest
        SET osm_type = 'node'
        WHERE osm_type IS NULL OR TRIM(osm_type) = ''
        """
    )

    return updated, failed


def reorder_columns(cur) -> None:
    """
    PostgreSQL cannot insert columns at positions directly.
    Rebuild table so first columns are:
      poi_id, location_id, osm_id, osm_type, ...
    """
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public'
          AND table_name='points_of_interest'
        ORDER BY ordinal_position
        """
    )
    cols = [r["column_name"] for r in cur.fetchall()]
    desired_front = ["poi_id", "location_id", "osm_id", "osm_type"]
    remaining = [c for c in cols if c not in desired_front]
    ordered = desired_front + remaining

    # Build "CREATE TABLE ... AS SELECT ..." with desired order
    select_cols = ", ".join(ordered)
    cur.execute(f"CREATE TABLE points_of_interest_new AS SELECT {select_cols} FROM points_of_interest")

    # Re-apply primary key and useful indexes that existed in this project
    cur.execute("ALTER TABLE points_of_interest_new ALTER COLUMN poi_id SET NOT NULL")
    cur.execute("ALTER TABLE points_of_interest_new ADD CONSTRAINT points_of_interest_new_pkey PRIMARY KEY (poi_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_poi_city ON points_of_interest_new(city)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_poi_region ON points_of_interest_new(region)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_poi_category ON points_of_interest_new(category)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_poi_rating ON points_of_interest_new(rating)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_poi_location_id ON points_of_interest_new(location_id)")

    # Atomic swap
    cur.execute("DROP TABLE points_of_interest")
    cur.execute("ALTER TABLE points_of_interest_new RENAME TO points_of_interest")
    cur.execute("ALTER INDEX points_of_interest_new_pkey RENAME TO points_of_interest_pkey")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate points_of_interest to add poi_id/location_id/osm fields."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview actions; rollback transaction.")
    parser.add_argument("--apply", action="store_true", help="Apply changes and commit.")
    parser.add_argument("--limit", type=int, default=None, help="Limit POI rows for testing.")
    parser.add_argument("--pause-ms", type=int, default=0, help="Delay between row updates in milliseconds.")
    parser.add_argument("--start-poi-id", type=int, default=None, help="Resume from this poi_id onward.")
    parser.add_argument("--log-every", type=int, default=25, help="Print progress every N rows.")
    parser.add_argument(
        "--skip-reorder",
        action="store_true",
        help="Do not physically reorder columns; only rename/add/populate.",
    )
    args = parser.parse_args()

    if args.dry_run == args.apply:
        print("Choose exactly one of --dry-run or --apply", file=sys.stderr)
        return 2

    conn = db_connect()
    try:
        conn.autocommit = False
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            ensure_columns(cur)
            mapped = populate_location_id(cur)
            updated, failed = backfill_osm_ids(
                cur,
                pause_ms=args.pause_ms,
                limit=args.limit,
                start_poi_id=args.start_poi_id,
                log_every=args.log_every,
            )
            if not args.skip_reorder:
                reorder_columns(cur)

            # preview stats
            cur.execute("SELECT COUNT(*) AS c FROM points_of_interest")
            total = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM points_of_interest WHERE location_id IS NULL")
            no_loc = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM points_of_interest WHERE osm_id IS NULL OR TRIM(osm_id) = ''")
            no_osm = cur.fetchone()["c"]
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name='points_of_interest'
                ORDER BY ordinal_position
                """
            )
            col_order = [r["column_name"] for r in cur.fetchall()]

        print(f"Total POIs: {total}")
        print(f"location_id mapped/updated: {mapped}")
        print(f"osm_id resolved this run: {updated}")
        print(f"osm_id unresolved this run: {failed}")
        print(f"rows still missing location_id: {no_loc}")
        print(f"rows still missing osm_id: {no_osm}")
        print("Current column order:")
        print("  " + " | ".join(col_order))

        if args.apply:
            conn.commit()
            print("\nApplied successfully.")
        else:
            conn.rollback()
            print("\nDry run complete. No changes committed.")
        return 0
    except KeyboardInterrupt:
        conn.rollback()
        print("Interrupted by user. Rolled back transaction.", file=sys.stderr)
        return 130
    except Exception as exc:
        conn.rollback()
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

