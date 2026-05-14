-- ---------------------------------------------------------------------------
-- location_mapping — cities / regions for packing & itinerary routing
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS location_mapping (
    location_id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL UNIQUE,
    parent_region VARCHAR(100) NOT NULL,
    elevation NUMERIC(10,2),
    climate_zone VARCHAR(50),
    tourist_season VARCHAR(50),
    latitude NUMERIC(10,8) NOT NULL,
    longitude NUMERIC(11,8) NOT NULL,
    verified BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'location_mapping_set_updated_at') THEN
        CREATE TRIGGER location_mapping_set_updated_at
        BEFORE UPDATE ON location_mapping
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_location_mapping_parent_region ON location_mapping(parent_region);
CREATE INDEX IF NOT EXISTS idx_location_mapping_verified ON location_mapping(verified);
CREATE INDEX IF NOT EXISTS idx_location_mapping_climate_zone ON location_mapping(climate_zone);
