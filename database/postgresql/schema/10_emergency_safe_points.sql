-- ---------------------------------------------------------------------------
-- itinerary_emergency_contacts — ICE contacts per saved itinerary
-- safe_points — hospitals / police / fuel for Emergency Mode
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS itinerary_emergency_contacts (
    contact_id SERIAL PRIMARY KEY,
    itinerary_id INT NOT NULL REFERENCES itineraries(itinerary_id) ON DELETE CASCADE,
    contact_name VARCHAR(120) NOT NULL,
    relationship VARCHAR(80) NOT NULL,
    phone_number VARCHAR(25) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'itinerary_emergency_contacts_set_updated_at') THEN
        CREATE TRIGGER itinerary_emergency_contacts_set_updated_at
        BEFORE UPDATE ON itinerary_emergency_contacts
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_itinerary_emergency_contacts_itinerary
    ON itinerary_emergency_contacts(itinerary_id, created_at DESC);

CREATE TABLE IF NOT EXISTS safe_points (
    safe_point_id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    name VARCHAR(180) NOT NULL,
    category VARCHAR(40) NOT NULL,
    location VARCHAR(220),
    latitude NUMERIC(10,8) NOT NULL,
    longitude NUMERIC(11,8) NOT NULL,
    osm_type VARCHAR(20),
    osm_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_safe_points_city_osm UNIQUE (city, category, osm_type, osm_id)
);

CREATE INDEX IF NOT EXISTS idx_safe_points_city ON safe_points(city);
CREATE INDEX IF NOT EXISTS idx_safe_points_lat_lon ON safe_points(latitude, longitude);
