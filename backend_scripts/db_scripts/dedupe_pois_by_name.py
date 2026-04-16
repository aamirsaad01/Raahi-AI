#!/usr/bin/env python3
"""
Remove duplicate rows in ``points_of_interest`` that share the same name
(case-insensitive, trimmed), keeping a single row per name (lowest ``poi_id``).

**Warning:** This is a global dedupe by name only. If two different real-world
places share an identical name, one will be deleted. Use ``--dry-run`` first.

Itinerary JSON stored in ``itineraries.daily_plan`` may reference ``poi_id``;
after deletion, some references can become stale — re-generate affected
itineraries if needed.

Usage (from repo root):

    python backend_scripts/db_scripts/dedupe_pois_by_name.py --dry-run
    python backend_scripts/db_scripts/dedupe_pois_by_name.py --yes
"""

from __future__ import annotations

import argparse
import os
import sys

import psycopg2
from dotenv import load_dotenv

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(dotenv_path=os.path.join(_REPO_ROOT, ".env"))


def _connect():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "raahi_ai"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
    )


def count_duplicates(cur) -> tuple[int, int]:
    """Return (name_groups_with_2plus_rows, rows_that_would_be_deleted)."""
    cur.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT LOWER(TRIM(name))
            FROM points_of_interest
            GROUP BY LOWER(TRIM(name))
            HAVING COUNT(*) > 1
        ) g
        """
    )
    dup_groups = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT 1 FROM (
                SELECT poi_id,
                       ROW_NUMBER() OVER (
                           PARTITION BY LOWER(TRIM(name))
                           ORDER BY poi_id
                       ) AS rn
                FROM points_of_interest
            ) t
            WHERE rn > 1
        ) x
        """
    )
    to_delete = cur.fetchone()[0]
    return dup_groups, to_delete


def delete_duplicates(cur) -> int:
    """
    Delete all but one row per normalized name (keeps minimum poi_id).
    Returns number of rows deleted.
    """
    cur.execute(
        """
        DELETE FROM points_of_interest
        WHERE poi_id IN (
            SELECT poi_id
            FROM (
                SELECT
                    poi_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY LOWER(TRIM(name))
                        ORDER BY poi_id
                    ) AS rn
                FROM points_of_interest
            ) t
            WHERE rn > 1
        )
        """
    )
    return cur.rowcount


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove duplicate POIs with the same name (keep lowest poi_id)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many rows would be deleted; do not delete.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required to actually perform deletion (unless --dry-run).",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.yes:
        print(
            "Refusing to delete without --yes. Use --dry-run to preview, "
            "or --yes to execute.",
            file=sys.stderr,
        )
        return 2

    conn = _connect()
    try:
        with conn.cursor() as cur:
            dup_groups, to_delete = count_duplicates(cur)

        print(f"Duplicate name groups (2+ rows): {dup_groups}")
        print(f"Rows that would be removed:       {to_delete}")

        if args.dry_run:
            print("\nDry run: no changes made.")
            return 0

        with conn.cursor() as cur:
            deleted = delete_duplicates(cur)
        conn.commit()
        print(f"\nDeleted {deleted} duplicate row(s).")
        return 0
    except Exception as exc:
        conn.rollback()
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
