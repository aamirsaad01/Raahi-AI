#!/usr/bin/env python3
"""
Wipe all rows from points_of_interest, then re-collect POIs from OSM for every
verified location and enrich with OpenAI (when OPENAI_API_KEY is set).

Usage (from repo root):
  python backend_scripts/api_collectors/repopulate_pois.py --yes

Or from backend_scripts:
  python -m api_collectors.repopulate_pois --yes

Requires .env at repo root with DB_* and OPENAI_API_KEY (recommended).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

import psycopg2
from dotenv import load_dotenv

_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_BACKEND_ROOT = os.path.join(_REPO_ROOT, "backend_scripts")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

load_dotenv(os.path.join(_REPO_ROOT, ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _connect():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "raahi_ai"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
    )


def wipe_all_pois(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM points_of_interest")
        (before,) = cur.fetchone()
        cur.execute("DELETE FROM points_of_interest")
        deleted = cur.rowcount
    conn.commit()
    return before, deleted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete all POIs and re-run OSM + LLM pipeline for all locations."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm destructive delete (required unless --skip-wipe).",
    )
    parser.add_argument(
        "--skip-wipe",
        action="store_true",
        help="Do not delete; only run pipeline with --force semantics.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: limit number of locations (for testing).",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Optional: skip first N locations.",
    )
    args = parser.parse_args()

    if not args.skip_wipe and not args.yes:
        parser.error("Refusing to delete without --yes (or use --skip-wipe).")

    if not args.skip_wipe:
        conn = _connect()
        try:
            before, deleted = wipe_all_pois(conn)
            logger.info("Removed %s POI row(s) (count before: %s).", deleted, before)
        finally:
            conn.close()

    # Import after path/env so pipeline picks up OPENAI_API_KEY
    from api_collectors.poi_pipeline import POIPipeline

    pipeline = POIPipeline()
    try:
        pipeline.process_all_locations(
            limit=args.limit,
            skip=args.skip,
            force_repopulate=True,
        )
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
