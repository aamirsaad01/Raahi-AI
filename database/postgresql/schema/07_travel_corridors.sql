-- ---------------------------------------------------------------------------
-- travel_corridors — multi-stop road-trip templates
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS travel_corridors (
    corridor_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    min_days SMALLINT NOT NULL CHECK (min_days >= 1),
    base_transport_cost_pkr INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'travel_corridors_set_updated_at') THEN
        CREATE TRIGGER travel_corridors_set_updated_at
        BEFORE UPDATE ON travel_corridors
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS corridor_locations (
    corridor_id INT NOT NULL REFERENCES travel_corridors(corridor_id) ON DELETE CASCADE,
    location_id INT NOT NULL REFERENCES location_mapping(location_id) ON DELETE CASCADE,
    route_order SMALLINT NOT NULL CHECK (route_order >= 1),
    PRIMARY KEY (corridor_id, location_id),
    UNIQUE (corridor_id, route_order)
);

CREATE INDEX IF NOT EXISTS idx_corridor_locations_corridor ON corridor_locations(corridor_id);
CREATE INDEX IF NOT EXISTS idx_corridor_locations_location ON corridor_locations(location_id);
