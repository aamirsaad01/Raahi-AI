-- ---------------------------------------------------------------------------
-- ndma_alerts — raw scraped advisories (poller compatibility)
-- ndma_alerts_ai — structured / AI-extracted alerts (API + map)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ndma_alerts (
    alert_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    advisory_url TEXT NOT NULL,
    published_date DATE,
    advisory_type VARCHAR(100),
    content TEXT,
    severity VARCHAR(20) CHECK (severity IN ('low','medium','high','critical')),
    affected_regions TEXT[],
    alert_hash VARCHAR(64) UNIQUE NOT NULL,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ndma_alerts_published_date ON ndma_alerts(published_date DESC);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_is_active ON ndma_alerts(is_active);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_severity ON ndma_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_scraped_at ON ndma_alerts(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_hash ON ndma_alerts(alert_hash);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'ndma_alerts_set_updated_at') THEN
        CREATE TRIGGER ndma_alerts_set_updated_at
        BEFORE UPDATE ON ndma_alerts
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS ndma_alerts_ai (
    alert_id SERIAL PRIMARY KEY,
    heading VARCHAR(255) NOT NULL,
    source VARCHAR(50) DEFAULT 'NDMA',
    location_name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    affected_regions TEXT[],
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low','medium','high','critical')),
    icon_type VARCHAR(50),
    color_code VARCHAR(20),
    description TEXT,
    advisory_url TEXT,
    published_date DATE,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    ai_extracted BOOLEAN DEFAULT TRUE,
    original_pdf_content TEXT,
    extraction_confidence DECIMAL(3, 2),
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_location ON ndma_alerts_ai(location_name);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_severity ON ndma_alerts_ai(severity);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_is_active ON ndma_alerts_ai(is_active);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_published_date ON ndma_alerts_ai(published_date DESC);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_scraped_at ON ndma_alerts_ai(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_hash ON ndma_alerts_ai(content_hash);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_ai_coords ON ndma_alerts_ai(latitude, longitude);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'ndma_alerts_ai_set_updated_at') THEN
        CREATE TRIGGER ndma_alerts_ai_set_updated_at
        BEFORE UPDATE ON ndma_alerts_ai
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

COMMENT ON TABLE ndma_alerts IS 'Raw NDMA advisories scraped from official sources';
COMMENT ON TABLE ndma_alerts_ai IS 'AI-extracted structured hazard alerts derived from NDMA advisories';
