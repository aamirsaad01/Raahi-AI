"""
Migration: Add travel_corridors + corridor_locations tables and seed
three legendary Pakistani road-trip corridors.

Usage (from repo root):
    python backend_scripts/run_migration_add_travel_corridors.py
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(repo_root, ".env"))

# ── Seed data ────────────────────────────────────────────────────────────
# Each corridor maps an ordered list of city names (must exist in
# location_mapping) to route_order positions.
CORRIDORS = [
    # --- THE KKH & HUNZA NETWORK ---
    {
        "name": "The Kaghan-Gilgit Gateway (Segment)",
        "description": (
            "A perfect shorter road trip. Cross the scenic Babusar Pass "
            "into Gilgit-Baltistan without committing to the deep north. "
            "Ideal for a quick mountainous escape."
        ),
        "min_days": 3,
        "base_transport_cost_pkr": 18000,
        "cities": [
            "Balakot",
            "Naran",
            "Gilgit",
        ],
    },
    {
        "name": "The Classic KKH Route",
        "description": (
            "The standard Northern Pakistan holiday. Travel from the lush "
            "Kaghan Valley up to the historic forts, majestic peaks, and "
            "vibrant culture of Central Hunza."
        ),
        "min_days": 5,
        "base_transport_cost_pkr": 25000,
        "cities": [
            "Balakot",
            "Naran",
            "Gilgit",
            "Aliabad",
            "Karimabad",
        ],
    },
    {
        "name": "The Ultimate KKH & Khunjerab Run (Mega Trip)",
        "description": (
            "The quintessential road trip. Winds through the majestic Hunza Valley, "
            "past the towering Passu Cones, and goes all the way up to the "
            "China border at Khunjerab Pass."
        ),
        "min_days": 7,
        "base_transport_cost_pkr": 35000,
        "cities": [
            "Balakot",
            "Naran",
            "Gilgit",
            "Aliabad",
            "Karimabad",
            "Attabad Lake",
            "Gulmit",
            "Passu",
            "Sost",
        ],
    },

    # --- THE BALTISTAN NETWORK ---
    {
        "name": "The Skardu Valley Intro (Segment)",
        "description": (
            "An introduction to Baltistan. Drive the rugged Skardu road, "
            "visit the high-altitude cold deserts, and relax by the stunning "
            "blue waters of the Kachura Lakes."
        ),
        "min_days": 4,
        "base_transport_cost_pkr": 28000,
        "cities": [
            "Naran",
            "Skardu",
            "Kachura Lake",
            "Satpara Lake",
        ],
    },
    {
        "name": "The Deep Baltistan Expedition (Mega Trip)",
        "description": (
            "A journey into the rugged heart of Baltistan. Explore the cold deserts, "
            "navigate the Indus river, and visit the ancient stone forts of "
            "Shigar and Khaplu deep in the Karakoram range."
        ),
        "min_days": 6,
        "base_transport_cost_pkr": 38000,
        "cities": [
            "Naran",
            "Skardu",
            "Kachura Lake",
            "Satpara Lake",
            "Shigar Valley",
            "Shigar",
            "Khaplu Valley",
            "Khaplu",
        ],
    },

    # --- THE SWAT VALLEY NETWORK ---
    {
        "name": "The Lower Swat Escape (Segment)",
        "description": (
            "A quick weekend getaway to the historical and vibrant bazaars "
            "of Mingora, concluding in the riverside towns of Madyan and Bahrain."
        ),
        "min_days": 2,
        "base_transport_cost_pkr": 10000,
        "cities": [
            "Mingora",
            "Madyan",
            "Bahrain",
        ],
    },
    {
        "name": "The Complete Swat Explorer (Mega Trip)",
        "description": (
            "Often called the Switzerland of the East. Travel from Mingora up "
            "to the alpine lakes of Kalam and the dense, untouched pine "
            "forests of Utror and Mahodand."
        ),
        "min_days": 4,
        "base_transport_cost_pkr": 18000,
        "cities": [
            "Mingora",
            "Madyan",
            "Bahrain",
            "Kalam",
            "Utror",
            "Mahodand Lake",
        ],
    },

    # --- THE KAGHAN VALLEY NETWORK ---
    {
        "name": "The Shogran & Kaghan Intro (Segment)",
        "description": (
            "A short, beautiful escape taking you off the main road up to the "
            "lush Siri Paye meadows, and relaxing by the calming Kunhar River."
        ),
        "min_days": 2,
        "base_transport_cost_pkr": 9000,
        "cities": [
            "Balakot",
            "Kawai",
            "Shogran",
            "Kaghan",
        ],
    },
    {
        "name": "The Ultimate Kaghan Escape (Mega Trip)",
        "description": (
            "A classic nature retreat following the Kunhar River. Crosses through "
            "Naran, stops at beautiful waterfalls, and reaches the stunning "
            "high-altitude Lulusar Lake."
        ),
        "min_days": 4,
        "base_transport_cost_pkr": 14000,
        "cities": [
            "Balakot",
            "Kawai",
            "Shogran",
            "Kaghan",
            "Naran",
            "Batakundi",
            "Lulusar Lake",
        ],
    },

    # --- INDEPENDENT UNIQUE CORRIDORS ---
    {
        "name": "The Chitral & Kalash Cultural Immersive",
        "description": (
            "A culturally rich journey over the Lowari Pass into the isolated "
            "valleys of Chitral. Home to the unique Kalash people and stunning "
            "views of the Hindu Kush."
        ),
        "min_days": 5,
        "base_transport_cost_pkr": 22000,
        "cities": [
            "Upper Dir",
            "Drosh",
            "Chitral",
            "Ayun",
            "Bumburet",
        ],
    },
    {
        "name": "The Dir & Kumrat Forest Expedition",
        "description": (
            "Venture off the beaten path into the dense, towering deodar forests "
            "of Kumrat Valley. Features river crossings and ends at pristine alpine lakes."
        ),
        "min_days": 4,
        "base_transport_cost_pkr": 20000,
        "cities": [
            "Lower Dir",
            "Upper Dir",
            "Kumrat",
            "Kumrat Valley",
            "Jahaz Banda",
        ],
    },
    {
        "name": "The Ghizer Blossom Trail",
        "description": (
            "A mesmerizing drive through the 'Land of Lakes' in Gilgit-Baltistan, "
            "famous for its crystal clear blue waters, trout fishing, and vibrant foliage."
        ),
        "min_days": 5,
        "base_transport_cost_pkr": 30000,
        "cities": [
            "Gilgit",
            "Gupis",
            "Ghizer",
            "Phandar Lake",
        ],
    },
    {
        "name": "The Galyat Weekend Getaway",
        "description": (
            "A quick, refreshing escape from the capital through the colonial-era "
            "hill stations, offering easy pipeline hikes and cool mountain air."
        ),
        "min_days": 2,
        "base_transport_cost_pkr": 5000,
        "cities": [
            "Murree",
            "Bhurban",
            "Ayubia",
            "Nathiagali",
        ],
    },
]

def _connect():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "raahi_ai"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
    )


def run_migration(conn):
    migration_path = os.path.join(
        repo_root,
        "database",
        "postgresql",
        "migrations",
        "add_travel_corridors.sql",
    )
    with open(migration_path, "r") as f:
        sql = f.read()

    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("✅ Tables travel_corridors + corridor_locations created (or already exist).")


def _resolve_city(conn, city_name: str) -> int | None:
    """Look up location_id by city name (case-insensitive)."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT location_id FROM location_mapping WHERE LOWER(city) = LOWER(%s)",
            (city_name,),
        )
        row = cur.fetchone()
    return row["location_id"] if row else None


def seed_corridors(conn):
    seeded = 0
    skipped_corridors = 0

    for corridor in CORRIDORS:
        # Check if corridor already exists
        with conn.cursor() as cur:
            cur.execute(
                "SELECT corridor_id FROM travel_corridors WHERE name = %s",
                (corridor["name"],),
            )
            if cur.fetchone():
                print(f"   ⏭️  Corridor '{corridor['name']}' already exists — skipping")
                skipped_corridors += 1
                continue

        # Resolve every city → location_id
        location_ids: list[tuple[int, int]] = []
        missing: list[str] = []
        for order, city in enumerate(corridor["cities"], start=1):
            loc_id = _resolve_city(conn, city)
            if loc_id is None:
                missing.append(city)
            else:
                location_ids.append((loc_id, order))

        if missing:
            print(
                f"   ⚠️  Corridor '{corridor['name']}': "
                f"cities not found in location_mapping: {missing} — "
                f"seeding with {len(location_ids)} of {len(corridor['cities'])} cities"
            )

        if not location_ids:
            print(f"   ❌ Corridor '{corridor['name']}': no cities matched — skipping entirely")
            continue

        # Insert corridor
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO travel_corridors (name, description, min_days, base_transport_cost_pkr)
                VALUES (%s, %s, %s, %s)
                RETURNING corridor_id
                """,
                (
                    corridor["name"],
                    corridor["description"],
                    corridor["min_days"],
                    corridor["base_transport_cost_pkr"],
                ),
            )
            corridor_id = cur.fetchone()[0]

            for loc_id, order in location_ids:
                cur.execute(
                    """
                    INSERT INTO corridor_locations (corridor_id, location_id, route_order)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (corridor_id, loc_id, order),
                )

        conn.commit()
        seeded += 1
        cities_str = " → ".join(corridor["cities"])
        print(f"   ✅ Seeded: {corridor['name']}  ({cities_str})")

    print(f"\n📊 Summary: {seeded} corridors seeded, {skipped_corridors} already existed.")


def main():
    conn = _connect()
    try:
        print("🔄 Running migration: Add Travel Corridors")
        print("=" * 60)
        run_migration(conn)

        print("\n🌍 Seeding corridors …")
        seed_corridors(conn)

        print("\n✅ Migration complete!")
    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
