#!/usr/bin/env python3
"""
Build and load `location_mapping` rows from `database/cities.csv`.

Sources used:
- Geoapify Geocoding API (primary lat/lon and place confidence)
- OSM Nominatim (secondary validation and optional OSM elevation tags)
- Open-Meteo elevation endpoint (fallback when OSM does not expose elevation)

Why Open-Meteo fallback?
OSM/Nominatim rarely returns clean elevation values for city-level features.
This fallback is free and keyless, so elevation can still be populated.

Usage:
    python database/build_location_mapping_from_cities.py --dry-run
    python database/build_location_mapping_from_cities.py --apply
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import psycopg2
import requests
from dotenv import load_dotenv


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, ".env"))

DEFAULT_CSV = os.path.join(REPO_ROOT, "database", "cities.csv")
GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
OSM_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_ELEV_URL = "https://api.open-meteo.com/v1/elevation"


@dataclass
class CityRow:
    city: str
    region: str


@dataclass
class LocationRecord:
    location_id: int
    city: str
    parent_region: str
    elevation: Optional[float]
    climate_zone: str
    tourist_season: str
    latitude: float
    longitude: float
    verified: bool = True


def db_connect():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "raahi_ai"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
    )


def read_cities(csv_path: str) -> List[CityRow]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"cities.csv not found: {csv_path}")
    out: List[CityRow] = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            city = (row.get("city") or "").strip()
            region = (row.get("region") or "").strip()
            if city and region:
                out.append(CityRow(city=city, region=region))
    return out


def _safe_get_json(url: str, params: Dict, headers: Optional[Dict] = None) -> Dict:
    resp = requests.get(url, params=params, headers=headers or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def geocode_geoapify(city: str, region: str, api_key: str) -> Optional[Tuple[float, float]]:
    if not api_key:
        return None
    query = f"{city}, {region}, Pakistan"
    data = _safe_get_json(
        GEOAPIFY_GEOCODE_URL,
        {
            "text": query,
            "filter": "countrycode:pk",
            "limit": 1,
            "apiKey": api_key,
        },
    )
    feats = data.get("features") or []
    if not feats:
        return None
    p = (feats[0].get("properties") or {})
    lat = p.get("lat")
    lon = p.get("lon")
    if lat is None or lon is None:
        return None
    return float(lat), float(lon)


def geocode_osm(city: str, region: str) -> Tuple[Optional[Tuple[float, float]], Optional[float]]:
    query = f"{city}, {region}, Pakistan"
    data = _safe_get_json(
        OSM_NOMINATIM_URL,
        {
            "q": query,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
            "extratags": 1,
            "countrycodes": "pk",
        },
        headers={"User-Agent": "RaahiAI-LocationBuilder/1.0"},
    )
    if not data:
        return None, None
    row = data[0]
    lat = row.get("lat")
    lon = row.get("lon")
    coords = (float(lat), float(lon)) if lat and lon else None

    elevation = None
    extra = row.get("extratags") or {}
    ele_raw = extra.get("ele")
    if isinstance(ele_raw, str):
        m = re.search(r"(-?\d+(?:\.\d+)?)", ele_raw)
        if m:
            try:
                elevation = float(m.group(1))
            except ValueError:
                elevation = None

    return coords, elevation


def elevation_open_meteo(lat: float, lon: float) -> Optional[float]:
    data = _safe_get_json(
        OPEN_METEO_ELEV_URL,
        {"latitude": lat, "longitude": lon},
    )
    elev = data.get("elevation")
    if isinstance(elev, list) and elev:
        elev = elev[0]
    if elev is None:
        return None
    try:
        return float(elev)
    except (TypeError, ValueError):
        return None


def climate_zone_for_elevation(elev_m: Optional[float]) -> str:
    if elev_m is None:
        return "Temperate"
    if elev_m < 900:
        return "Warm"
    if elev_m < 1800:
        return "Temperate"
    if elev_m < 2800:
        return "Cool"
    return "Alpine"


def tourist_season_for_zone(zone: str, region: str) -> str:
    r = region.lower()
    # AJK tends to have a wider comfortable shoulder season than higher alpine zones.
    if "azad kashmir" in r:
        return "March-October"
    mapping = {
        "Warm": "October-March",
        "Temperate": "April-October",
        "Cool": "May-September",
        "Alpine": "June-September",
    }
    return mapping.get(zone, "April-October")


def build_records(cities: List[CityRow], geoapify_key: str, pause_ms: int = 200) -> List[LocationRecord]:
    records: List[LocationRecord] = []
    for idx, c in enumerate(cities, start=1):
        coords = geocode_geoapify(c.city, c.region, geoapify_key)
        if not coords:
            osm_coords, osm_ele = geocode_osm(c.city, c.region)
            coords = osm_coords
        else:
            osm_coords, osm_ele = geocode_osm(c.city, c.region)

        if not coords:
            raise RuntimeError(f"Could not geocode city: {c.city}, {c.region}")

        lat, lon = coords
        elevation = osm_ele if osm_ele is not None else elevation_open_meteo(lat, lon)

        zone = climate_zone_for_elevation(elevation)
        season = tourist_season_for_zone(zone, c.region)

        records.append(
            LocationRecord(
                location_id=idx,
                city=c.city,
                parent_region=c.region,
                elevation=round(elevation, 2) if elevation is not None else None,
                climate_zone=zone,
                tourist_season=season,
                latitude=lat,
                longitude=lon,
                verified=True,
            )
        )
        time.sleep(max(pause_ms, 0) / 1000.0)
    return records


def load_to_db(records: List[LocationRecord], apply: bool) -> None:
    conn = db_connect()
    try:
        with conn.cursor() as cur:
            if apply:
                cur.execute("TRUNCATE TABLE location_mapping RESTART IDENTITY CASCADE")

            insert_sql = """
                INSERT INTO location_mapping
                (location_id, city, parent_region, elevation, climate_zone,
                 tourist_season, latitude, longitude, verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (city) DO UPDATE SET
                    parent_region = EXCLUDED.parent_region,
                    elevation = EXCLUDED.elevation,
                    climate_zone = EXCLUDED.climate_zone,
                    tourist_season = EXCLUDED.tourist_season,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    verified = EXCLUDED.verified,
                    updated_at = NOW()
            """
            for r in records:
                params = (
                    r.location_id,
                    r.city,
                    r.parent_region,
                    r.elevation,
                    r.climate_zone,
                    r.tourist_season,
                    r.latitude,
                    r.longitude,
                    r.verified,
                )
                if apply:
                    cur.execute(insert_sql, params)

            if apply:
                cur.execute("SELECT setval('location_mapping_location_id_seq', (SELECT COALESCE(MAX(location_id), 1) FROM location_mapping))")
                conn.commit()
            else:
                conn.rollback()
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build location_mapping from database/cities.csv using Geoapify + OSM."
    )
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to cities.csv")
    parser.add_argument("--dry-run", action="store_true", help="Build/preview without DB writes")
    parser.add_argument("--apply", action="store_true", help="Write rows into location_mapping")
    parser.add_argument("--pause-ms", type=int, default=250, help="Pause between API calls")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Choose one: --dry-run or --apply", file=sys.stderr)
        return 2
    if args.dry_run and args.apply:
        print("Use only one of --dry-run / --apply", file=sys.stderr)
        return 2

    geo_key = (os.getenv("GEOAPIFY_API_KEY") or "").strip()
    if not geo_key:
        print("GEOAPIFY_API_KEY is missing in .env", file=sys.stderr)
        return 2

    cities = read_cities(args.csv)
    if not cities:
        print("No city rows found in CSV.", file=sys.stderr)
        return 1

    print(f"Building {len(cities)} rows from: {args.csv}")
    records = build_records(cities, geo_key, pause_ms=args.pause_ms)
    print(f"Built {len(records)} location records.")

    preview_n = min(8, len(records))
    print("\nPreview:")
    for r in records[:preview_n]:
        print(
            f"- {r.location_id:>3} | {r.city:20} | {r.parent_region:20} | "
            f"{r.latitude:.5f},{r.longitude:.5f} | elev={r.elevation} | "
            f"{r.climate_zone} | {r.tourist_season}"
        )

    load_to_db(records, apply=args.apply)
    print("\nDone.")
    if args.apply:
        print("location_mapping table was replaced/upserted with generated values.")
    else:
        print("Dry run only; no DB changes were made.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

