-- ===============================================
-- Raahi AI - NDMA Alerts Table
-- Adds table for storing scraped NDMA advisories
-- ===============================================

-- NDMA ALERTS TABLE
CREATE TABLE IF NOT EXISTS ndma_alerts (
    alert_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    advisory_url TEXT NOT NULL,
    published_date DATE,
    advisory_type VARCHAR(100), -- e.g., "Heatwave Advisory", "GLOF Alert", "Monsoon Alert"
    content TEXT, -- Full content/description of the advisory
    severity VARCHAR(20) CHECK (severity IN ('low','medium','high','critical')),
    affected_regions TEXT[], -- Array of affected regions (e.g., {'Gilgit-Baltistan', 'KPK Highlands'})
    alert_hash VARCHAR(64) UNIQUE NOT NULL, -- MD5/SHA256 hash of (title + published_date) for duplicate detection
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE, -- Mark as inactive if advisory is outdated
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_published_date ON ndma_alerts(published_date DESC);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_is_active ON ndma_alerts(is_active);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_severity ON ndma_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_scraped_at ON ndma_alerts(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_ndma_alerts_hash ON ndma_alerts(alert_hash);

-- Auto-update updated_at on update
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'ndma_alerts_set_updated_at'
    ) THEN
        CREATE TRIGGER ndma_alerts_set_updated_at
        BEFORE UPDATE ON ndma_alerts
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

-- Comments for documentation
COMMENT ON TABLE ndma_alerts IS 'Stores NDMA (National Disaster Management Authority) advisories scraped from their website';
COMMENT ON COLUMN ndma_alerts.alert_hash IS 'Unique hash to prevent duplicate entries (hash of title + published_date)';
COMMENT ON COLUMN ndma_alerts.affected_regions IS 'Array of regions affected by this alert (e.g., Gilgit-Baltistan, KPK Highlands)';
COMMENT ON COLUMN ndma_alerts.is_active IS 'Set to FALSE when advisory is outdated or superseded';



