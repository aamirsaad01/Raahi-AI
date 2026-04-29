#!/usr/bin/env python3
"""
Fetch and store safe points for all cities in location_mapping using Geoapify Places API.

Categories:
- hospital
- police station
- fuel station
- car workshop

Usage:
    python backend_scripts/db_scripts/fetch_safe_points.py
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(dotenv_path=os.path.join(REPO_ROOT, ".env"))

GEOAPIFY_PLACES_URL = os.getenv("GEOAPIFY_PLACES_URL", "https://api.geoapify.com/v2/places")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "").strip()
REQUEST_TIMEOUT = int(os.getenv("SAFE_POINTS_TIMEOUT_SEC", "40"))
SLEEP_BETWEEN_CALLS_SEC = float(os.getenv("SAFE_POINTS_SLEEP_SEC", "4.0"))
SEARCH_RADIUS_METERS = int(os.getenv("SAFE_POINTS_CITY_RADIUS_M", "10000"))
RESULT_LIMIT = int(os.getenv("SAFE_POINTS_LIMIT", "100"))

CATEGORIES = {
    "hospital": ["healthcare.hospital"],
    "police station": ["service.police"],
    "fuel station": ["service.vehicle.fuel"],
    "car workshop": ["service.vehicle.repair"],
}


def connect_db() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "raahi_ai"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
    )  # type: ignore[return-value]


def ensure_table(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS safe_points (
                safe_point_id SERIAL PRIMARY KEY,
                city VARCHAR(100) NOT NULL,
                name VARCHAR(180) NOT NULL,
                category VARCHAR(40) NOT NULL,
                location VARCHAR(220),
                latitude NUMERIC(10,8) NOT NULL,
                longitude NUMERIC(11,8) NOT NULL,
                osm_type VARCHAR(20),
                osm_id BIGINT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                CONSTRAINT uq_safe_points_city_osm UNIQUE (city, category, osm_type, osm_id)
            );

            CREATE INDEX IF NOT EXISTS idx_safe_points_city ON safe_points(city);
            CREATE INDEX IF NOT EXISTS idx_safe_points_lat_lon ON safe_points(latitude, longitude);
            """
        )
    conn.commit()


def fetch_cities(conn: psycopg2.extensions.connection) -> List[Dict[str, Any]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT city, latitude, longitude
            FROM location_mapping
            WHERE city IS NOT NULL AND latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY city ASC
            """
        )
        return cur.fetchall()


def build_geoapify_url(lat: float, lon: float, category: str) -> str:
    category_filter = ",".join(CATEGORIES[category])
    params = {
        "categories": category_filter,
        "filter": f"circle:{lon},{lat},{SEARCH_RADIUS_METERS}",
        "bias": f"proximity:{lon},{lat}",
        "limit": str(RESULT_LIMIT),
        "apiKey": GEOAPIFY_API_KEY,
    }
    return f"{GEOAPIFY_PLACES_URL}?{urllib.parse.urlencode(params)}"


def run_geoapify(url: str, max_retries: int = 3) -> Dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                payload = resp.read().decode("utf-8")
            return json.loads(payload)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 504) and attempt < max_retries:
                wait_sec = 15 * attempt
                print(
                    f"    ! Geoapify HTTP {exc.code} "
                    f"(attempt {attempt}/{max_retries}), retrying in {wait_sec}s..."
                )
                time.sleep(wait_sec)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            if attempt < max_retries:
                wait_sec = 15 * attempt
                print(
                    f"    ! Geoapify network timeout/error ({exc}) "
                    f"(attempt {attempt}/{max_retries}), retrying in {wait_sec}s..."
                )
                time.sleep(wait_sec)
                continue
            raise
    raise RuntimeError("Geoapify request exhausted retries")


def feature_coords(feature: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    geometry = feature.get("geometry") or {}
    if geometry.get("type") == "Point":
        coords = geometry.get("coordinates") or []
        if len(coords) >= 2:
            return float(coords[1]), float(coords[0])
    properties = feature.get("properties") or {}
    lat = properties.get("lat")
    lon = properties.get("lon")
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    return None, None


def feature_name(feature: Dict[str, Any], category: str) -> str:
    properties = feature.get("properties") or {}
    return (
        properties.get("name")
        or properties.get("address_line1")
        or f"Unnamed {category.title()}"
    ).strip()


def feature_location_text(feature: Dict[str, Any], city: str) -> str:
    properties = feature.get("properties") or {}
    return (
        properties.get("formatted")
        or properties.get("address_line2")
        or properties.get("address_line1")
        or city
    )


def feature_source_id(feature: Dict[str, Any]) -> int:
    properties = feature.get("properties") or {}
    raw_id = (
        properties.get("place_id")
        or properties.get("datasource", {}).get("raw", {}).get("id")
        or properties.get("datasource", {}).get("raw", {}).get("osm_id")
        or json.dumps(feature, sort_keys=True)
    )
    digest = hashlib.sha1(str(raw_id).encode("utf-8")).hexdigest()[:15]
    return int(digest, 16)


def upsert_point(
    conn: psycopg2.extensions.connection,
    city: str,
    category: str,
    feature: Dict[str, Any],
) -> bool:
    lat, lon = feature_coords(feature)
    if lat is None or lon is None:
        return False

    osm_type = "geoapify"
    osm_id = feature_source_id(feature)
    name = feature_name(feature, category)
    location = feature_location_text(feature, city)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO safe_points (
                city, name, category, location, latitude, longitude, osm_type, osm_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (city, category, osm_type, osm_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                location = EXCLUDED.location,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                updated_at = NOW()
            """,
            (city, name, category, location, lat, lon, osm_type, osm_id),
        )
    return True


def main() -> int:
    conn: Optional[psycopg2.extensions.connection] = None
    try:
        if not GEOAPIFY_API_KEY:
            print("Error: GEOAPIFY_API_KEY is not set in environment/.env", file=sys.stderr)
            return 1

        conn = connect_db()
        ensure_table(conn)
        cities = fetch_cities(conn)
        print(f"Cities found: {len(cities)}")
        total_upserts = 0

        for i, city_row in enumerate(cities, start=1):
            city = str(city_row["city"]).strip()
            lat = float(city_row["latitude"])
            lon = float(city_row["longitude"])
            print(f"\n[{i}/{len(cities)}] {city} ({lat:.5f}, {lon:.5f})")

            for category in CATEGORIES:
                url = build_geoapify_url(lat, lon, category)
                try:
                    data = run_geoapify(url)
                except (
                    urllib.error.HTTPError,
                    urllib.error.URLError,
                    TimeoutError,
                    socket.timeout,
                    Exception,
                ) as exc:
                    print(f"  - {category}: request failed: {exc}")
                    continue

                features = data.get("features") or []
                inserted = 0
                for feature in features:
                    try:
                        if upsert_point(conn, city, category, feature):
                            inserted += 1
                    except Exception:
                        continue
                conn.commit()
                total_upserts += inserted
                print(
                    f"  - {category}: processed {len(features)} places, "
                    f"upserted {inserted}"
                )
                time.sleep(SLEEP_BETWEEN_CALLS_SEC)

        print(f"\nDone. Total upserts: {total_upserts}")
        return 0
    except Exception as exc:
        if conn is not None:
            conn.rollback()
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
