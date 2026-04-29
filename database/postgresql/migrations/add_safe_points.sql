-- Safe points for Emergency Mode (city browse + nearby lookup)
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
