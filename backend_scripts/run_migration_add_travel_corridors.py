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
    # ==========================================
    # --- 1. THE KKH & HUNZA NETWORK ---
    # ==========================================
    {
        "name": "The Kaghan-Naran Gateway (Segment)",
        "description": (
            "A beautiful and accessible shorter road trip from the capital. Follow the Kunhar River "
            "from Abbottabad up to the alpine lakes of Naran without committing to "
            "the deep north."
        ),
        "min_days": 3,
        "base_transport_cost_pkr": 15000, # ~600km round trip from ISB
        "cities": [
            "Abbottabad",
            "Mansehra",
            "Balakot",
            "Kaghan",
            "Naran",
        ],
    },
    {
        "name": "The Babusar-Gilgit Approach (Segment)",
        "description": (
            "Push further north over the scenic Babusar Pass. This route introduces "
            "you to the rugged Karakoram Highway and the historic hub of Gilgit."
        ),
        "min_days": 4,
        "base_transport_cost_pkr": 25000, # ~1000km round trip from ISB
        "cities": [
            "Abbottabad",
            "Mansehra",
            "Balakot",
            "Naran",
            "Chilas",
            "Diamer",
            "Gilgit",
        ],
    },
    {
        "name": "The Classic KKH Route (Branch)",
        "description": (
            "The standard Northern Pakistan holiday. Travel from Islamabad through the lush Kaghan Valley "
            "up to the historic forts, majestic peaks, and vibrant culture of Central Hunza."
        ),
        "min_days": 6,
        "base_transport_cost_pkr": 30000, # ~1200km round trip from ISB
        "cities": [
            "Abbottabad",
            "Balakot",
            "Naran",
            "Chilas",
            "Gilgit",
            "Nagar",
            "Aliabad",
            "Karimabad",
            "Hunza",
        ],
    },
    {
        "name": "The Ultimate KKH & Khunjerab Run (Mega Trip)",
        "description": (
            "The quintessential road trip. Winds through the majestic Hunza Valley, "
            "past the towering Passu Cones, and goes all the way up to the China border."
        ),
        "min_days": 8,
        "base_transport_cost_pkr": 35000, # ~1400km round trip from ISB
        "cities": [
            "Abbottabad",
            "Balakot",
            "Naran",
            "Chilas",
            "Gilgit",
            "Hunza",
            "Gulmit",
            "Passu",
            "Sost",
        ],
    },
    {
        "name": "The Gojal & Shimshal Expedition (Specialized Mega)",
        "description": (
            "For true adventurers. Bypass the standard tourist spots and venture deep "
            "into Upper Hunza, traversing the terrifying and thrilling jeep track "
            "to the remote Shimshal Valley."
        ),
        "min_days": 8,
        "base_transport_cost_pkr": 42000, # Includes extra for specialized jeep hire from Passu
        "cities": [
            "Abbottabad",
            "Naran",
            "Gilgit",
            "Hunza",
            "Gulmit",
            "Gulkin",
            "Passu",
            "Shimshal",
        ],
    },

    # ==========================================
    # --- 2. THE BALTISTAN NETWORK ---
    # ==========================================
    {
        "name": "The Skardu Valley Intro (Segment)",
        "description": (
            "Drive up the KKH and take the Jaglot-Skardu turnoff. "
            "Visit the high-altitude cold deserts, and relax by the stunning Kachura Lakes."
        ),
        "min_days": 5,
        "base_transport_cost_pkr": 32000, # ~1280km round trip from ISB
        "cities": [
            "Abbottabad",
            "Naran",
            "Chilas",
            "Skardu",
        ],
    },
    {
        "name": "The Deep Baltistan Expedition (Mega Trip)",
        "description": (
            "A journey into the rugged heart of Baltistan. Explore the cold deserts, "
            "navigate the Indus river, and visit the ancient stone forts of "
            "Shigar and Khaplu deep in the Karakoram range."
        ),
        "min_days": 7,
        "base_transport_cost_pkr": 38000, # ~1500km round trip from ISB
        "cities": [
            "Abbottabad",
            "Naran",
            "Chilas",
            "Skardu",
            "Shigar",
            "Khaplu",
        ],
    },

    # ==========================================
    # --- 3. THE SWAT VALLEY NETWORK ---
    # ==========================================
    {
        "name": "The Lower Swat Escape (Segment)",
        "description": (
            "Take the Swat Motorway from Islamabad for a quick weekend getaway to the "
            "vibrant bazaars of Mingora and the riverside towns of Madyan and Bahrain."
        ),
        "min_days": 3,
        "base_transport_cost_pkr": 12500, # ~500km round trip via Motorway
        "cities": [
            "Swat",
            "Mingora",
            "Madyan",
            "Bahrain",
        ],
    },
    {
        "name": "The Complete Swat Explorer (Mega Trip)",
        "description": (
            "Often called the Switzerland of the East. Travel up the valley from Mingora "
            "to the alpine lakes and dense, untouched pine forests of Kalam."
        ),
        "min_days": 5,
        "base_transport_cost_pkr": 18000, # ~700km round trip from ISB
        "cities": [
            "Swat",
            "Mingora",
            "Madyan",
            "Bahrain",
            "Kalam",
        ],
    },

    # ==========================================
    # --- 4. THE CHITRAL & DIR NETWORK ---
    # ==========================================
    {
        "name": "The Dir & Chitral Gateway",
        "description": (
            "A culturally rich journey passing through the lush Dir valley and "
            "crossing the Lowari Tunnel into the isolated, majestic valleys of Chitral."
        ),
        "min_days": 5,
        "base_transport_cost_pkr": 20000, # ~800km round trip from ISB
        "cities": [
            "Dir",
            "Chitral",
        ],
    },

    # ==========================================
    # --- 5. OFFBEAT GB (GHIZER & ASTORE) ---
    # ==========================================
    {
        "name": "The Ghizer Blossom Trail",
        "description": (
            "Drive all the way to Gilgit, then head west into the 'Land of Lakes'. "
            "Famous for its crystal clear blue waters, trout fishing, and vibrant foliage."
        ),
        "min_days": 6,
        "base_transport_cost_pkr": 34000, # ~1350km round trip from ISB
        "cities": [
            "Abbottabad",
            "Naran",
            "Gilgit",
            "Gahkuch",
            "Ghizer",
            "Phander",
        ],
    },
    {
        "name": "The Astore Valley Adventure",
        "description": (
            "Venture off the KKH just after Chilas into the dramatic Astore Valley. A rugged, raw "
            "experience offering stunning views of the Nanga Parbat massif."
        ),
        "min_days": 5,
        "base_transport_cost_pkr": 25000, # ~1000km round trip from ISB
        "cities": [
            "Abbottabad",
            "Naran",
            "Chilas",
            "Astore",
        ],
    },

    # ==========================================
    # --- 6. AZAD KASHMIR NETWORK ---
    # ==========================================
    {
        "name": "The Kashmir Gateway (Segment)",
        "description": (
            "A short, refreshing trip bridging the colonial-era Galyat region "
            "with the bustling capital of Azad Kashmir, Muzaffarabad."
        ),
        "min_days": 2,
        "base_transport_cost_pkr": 6500, # ~250km round trip from ISB
        "cities": [
            "Murree",
            "Muzaffarabad",
        ],
    },
    {
        "name": "The Neelum Valley Run (Mega Trip)",
        "description": (
            "A long, winding drive alongside the LOC. Features dense forests, "
            "waterfalls, and deeply cultural wooden architecture stretching all "
            "the way up the Neelum Valley."
        ),
        "min_days": 5,
        "base_transport_cost_pkr": 15000, # ~600km round trip from ISB
        "cities": [
            "Murree",
            "Muzaffarabad",
            "Neelum Valley",
        ],
    },
    {
        "name": "The Leepa Valley Expedition",
        "description": (
            "An off-the-beaten-path journey into one of Kashmir's most beautiful "
            "and secluded valleys. Expect tough roads and unparalleled natural beauty."
        ),
        "min_days": 4,
        "base_transport_cost_pkr": 12000, # ~480km round trip from ISB
        "cities": [
            "Murree",
            "Muzaffarabad",
            "Hattian Bala",
            "Leepa Valley",
        ],
    },
    {
        "name": "The Pearl Valley Circuit",
        "description": (
            "A serene exploration of the Poonch district in Azad Kashmir, "
            "covering the lush meadows of Rawalakot and the scenic views of Bagh."
        ),
        "min_days": 3,
        "base_transport_cost_pkr": 7500, # ~300km round trip from ISB via Kahuta/Azad Pattan
        "cities": [
            "Rawalakot",
            "Bagh",
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
