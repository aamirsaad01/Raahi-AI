-- ===============================================
-- Raahi AI - NDMA Alerts Table (AI-Enhanced)
-- Updates table to store AI-extracted structured alerts
-- ===============================================

-- Drop old table if exists (backup first!)
-- ALTER TABLE ndma_alerts RENAME TO ndma_alerts_old;

-- Create new table with AI-extracted fields
CREATE TABLE IF NOT EXISTS ndma_alerts_ai (
    alert_id SERIAL PRIMARY KEY,
    
    -- Basic Info
    heading VARCHAR(255) NOT NULL, -- e.g., "Snowfall", "Flood", "Landslide"
    source VARCHAR(50) DEFAULT 'NDMA', -- Source: NDMA, PMD, Crowd-Sourced
    
    -- Location
    location_name VARCHAR(255) NOT NULL, -- e.g., "Gilgit", "Naran", "Murree"
    latitude DECIMAL(10, 8), -- Location coordinates
    longitude DECIMAL(11, 8),
    affected_regions TEXT[], -- Array of affected regions
    
    -- Alert Details
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low','medium','high','critical')),
    icon_type VARCHAR(50), -- e.g., "snowfall", "flood", "landslide", "roadblock"
    color_code VARCHAR(20), -- e.g., "red", "yellow", "green" (for severity)
    description TEXT, -- Brief description for detail sheet
    
    -- Metadata
    advisory_url TEXT, -- Original PDF/advisory URL
    published_date DATE,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- AI Processing Info
    ai_extracted BOOLEAN DEFAULT TRUE, -- Whether extracted by AI
    original_pdf_content TEXT, -- Store original PDF text for reference
    extraction_confidence DECIMAL(3, 2), -- AI confidence score (0.0-1.0)
    
    -- Duplicate Detection
    content_hash VARCHAR(64) UNIQUE NOT NULL, -- Hash for duplicate detection
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_location ON ndma_alerts_ai(location_name);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_severity ON ndma_alerts_ai(severity);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_is_active ON ndma_alerts_ai(is_active);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_published_date ON ndma_alerts_ai(published_date DESC);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_scraped_at ON ndma_alerts_ai(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_hash ON ndma_alerts_ai(content_hash);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_coords ON ndma_alerts_ai(latitude, longitude);

-- Auto-update updated_at on update
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'ndma_alerts_ai_set_updated_at'
    ) THEN
        CREATE TRIGGER ndma_alerts_ai_set_updated_at
        BEFORE UPDATE ON ndma_alerts_ai
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

-- Comments for documentation
COMMENT ON TABLE ndma_alerts_ai IS 'Stores AI-extracted structured hazard alerts from NDMA advisories';
COMMENT ON COLUMN ndma_alerts_ai.heading IS 'Alert type heading (e.g., Snowfall, Flood, Landslide)';
COMMENT ON COLUMN ndma_alerts_ai.icon_type IS 'Icon type for UI display (matches HazardType enum)';
COMMENT ON COLUMN ndma_alerts_ai.color_code IS 'Color code for severity (red=critical/high, yellow=medium, green=low)';
COMMENT ON COLUMN ndma_alerts_ai.ai_extracted IS 'Whether this alert was extracted using AI';
COMMENT ON COLUMN ndma_alerts_ai.extraction_confidence IS 'AI confidence score for the extraction (0.0-1.0)';

