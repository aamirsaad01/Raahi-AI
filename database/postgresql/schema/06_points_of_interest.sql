-- ---------------------------------------------------------------------------
-- points_of_interest — POI catalog (same OSM id may appear in multiple cities)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS points_of_interest (
    poi_id SERIAL PRIMARY KEY,
    location_id INT REFERENCES location_mapping(location_id) ON DELETE CASCADE,
    osm_id VARCHAR(100) NOT NULL,
    osm_type VARCHAR(20),
    name VARCHAR(150) NOT NULL,
    latitude NUMERIC(10,8) NOT NULL,
    longitude NUMERIC(11,8) NOT NULL,
    description TEXT,
    rating NUMERIC(3,2) CHECK (rating >= 0 AND rating <= 5),
    category VARCHAR(50),
    difficulty VARCHAR(20),
    activities JSONB DEFAULT '[]'::jsonb,
    mood_tags JSONB DEFAULT '[]'::jsonb,
    highlights JSONB DEFAULT '[]'::jsonb,
    estimated_cost VARCHAR(20),
    estimated_cost_pkr_min INT,
    estimated_cost_pkr_max INT,
    best_months VARCHAR(100),
    avg_duration_hours NUMERIC(5,2),
    accessibility TEXT,
    permits_required BOOLEAN DEFAULT FALSE,
    nearby_facilities TEXT,
    photos JSONB DEFAULT '[]'::jsonb,
    verified BOOLEAN DEFAULT FALSE,
    last_api_fetch TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'points_of_interest_osm_id_key'
    ) THEN
        ALTER TABLE points_of_interest DROP CONSTRAINT points_of_interest_osm_id_key;
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'points_of_interest_osm_id_location_id_key'
    ) THEN
        ALTER TABLE points_of_interest
            ADD CONSTRAINT points_of_interest_osm_id_location_id_key
            UNIQUE (osm_id, location_id);
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'poi_set_updated_at') THEN
        CREATE TRIGGER poi_set_updated_at
        BEFORE UPDATE ON points_of_interest
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_poi_location_id ON points_of_interest(location_id);
CREATE INDEX IF NOT EXISTS idx_poi_osm_id_location_id ON points_of_interest(osm_id, location_id);
CREATE INDEX IF NOT EXISTS idx_poi_category ON points_of_interest(category);
CREATE INDEX IF NOT EXISTS idx_poi_rating ON points_of_interest(rating);
CREATE INDEX IF NOT EXISTS idx_poi_difficulty ON points_of_interest(difficulty);
CREATE INDEX IF NOT EXISTS idx_poi_estimated_cost ON points_of_interest(estimated_cost);
CREATE INDEX IF NOT EXISTS idx_poi_activities ON points_of_interest USING gin(activities);
CREATE INDEX IF NOT EXISTS idx_poi_mood_tags ON points_of_interest USING gin(mood_tags);
