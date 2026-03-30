"""
Create ndma_alerts_ai table in database
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

def create_table():
    """Create the ndma_alerts_ai table"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
        cursor = conn.cursor()
        
        # SQL to create the ndma_alerts_ai table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ndma_alerts_ai (
            alert_id SERIAL PRIMARY KEY,
            
            -- Basic Info
            heading VARCHAR(255) NOT NULL,
            source VARCHAR(50) DEFAULT 'NDMA',
            
            -- Location
            location_name VARCHAR(255) NOT NULL,
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            affected_regions TEXT[],
            
            -- Alert Details
            severity VARCHAR(20) NOT NULL CHECK (severity IN ('low','medium','high','critical')),
            icon_type VARCHAR(50),
            color_code VARCHAR(20),
            description TEXT,
            
            -- Metadata
            advisory_url TEXT,
            published_date DATE,
            scraped_at TIMESTAMPTZ DEFAULT NOW(),
            is_active BOOLEAN DEFAULT TRUE,
            
            -- AI Processing Info
            ai_extracted BOOLEAN DEFAULT TRUE,
            original_pdf_content TEXT,
            extraction_confidence DECIMAL(3, 2),
            
            -- Duplicate Detection
            content_hash VARCHAR(64) UNIQUE NOT NULL,
            
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_location ON ndma_alerts_ai(location_name);
        CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_severity ON ndma_alerts_ai(severity);
        CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_is_active ON ndma_alerts_ai(is_active);
        CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_published_date ON ndma_alerts_ai(published_date DESC);
        CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_scraped_at ON ndma_alerts_ai(scraped_at DESC);
        CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_hash ON ndma_alerts_ai(content_hash);
        CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_coords ON ndma_alerts_ai(latitude, longitude);
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        print("✅ Table 'ndma_alerts_ai' created successfully!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.errors.DuplicateTable:
        print("ℹ️  Table 'ndma_alerts_ai' already exists!")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Creating ndma_alerts_ai table")
    print("=" * 60)
    create_table()
    print("=" * 60)
    print("✅ Done!")
    print("=" * 60)

