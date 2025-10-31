"""
Script to load location_mapping.csv data into PostgreSQL database
"""
import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables from repo root
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

def get_db_connection():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

def load_csv_to_db(csv_path):
    """Load CSV data into location_mapping table"""
    
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Read CSV file
    print(f"📖 Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"📊 Found {len(df)} rows in CSV")
    
    # Connect to database
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Prepare data for insertion
        # Convert boolean 'verified' column to proper boolean type
        df['verified'] = df['verified'].astype(bool)
        
        # Handle empty elevation values (convert to None/Null)
        df['elevation'] = df['elevation'].replace('', None)
        df['elevation'] = pd.to_numeric(df['elevation'], errors='coerce')
        
        # Prepare rows (excluding any index column if present)
        rows = []
        for _, row in df.iterrows():
            rows.append((
                row['city'],
                row['parent_region'],
                None if pd.isna(row['elevation']) else float(row['elevation']),
                row['climate_zone'] if pd.notna(row['climate_zone']) else None,
                row['tourist_season'] if pd.notna(row['tourist_season']) else None,
                float(row['latitude']),
                float(row['longitude']),
                bool(row['verified'])
            ))
        
        # Insert data using ON CONFLICT DO NOTHING (skip duplicates based on city UNIQUE constraint)
        insert_query = """
            INSERT INTO location_mapping 
            (city, parent_region, elevation, climate_zone, tourist_season, latitude, longitude, verified)
            VALUES %s
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
        
        print("💾 Inserting data into database...")
        execute_values(cur, insert_query, rows, page_size=100)
        
        # Commit changes
        conn.commit()
        
        # Count inserted/updated rows
        cur.execute("SELECT COUNT(*) FROM location_mapping")
        total_count = cur.fetchone()[0]
        
        print(f"✅ Successfully loaded data!")
        print(f"📈 Total locations in database: {total_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting data: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # Path to CSV file (relative to script location)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    csv_path = os.path.join(repo_root, 'backend_scripts', 'data', 'location_mapping.csv')
    
    print("🚀 Starting location data import...")
    print(f"📍 CSV path: {csv_path}")
    print("-" * 50)
    
    load_csv_to_db(csv_path)
    
    print("-" * 50)
    print("✨ Done!")

