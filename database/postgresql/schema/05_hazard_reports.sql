-- ---------------------------------------------------------------------------
-- hazard_reports — user-submitted hazards
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hazard_reports (
    hazard_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    itinerary_id INT REFERENCES itineraries(itinerary_id) ON DELETE SET NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low','medium','high','critical')),
    location VARCHAR(150),
    latitude NUMERIC(10,8),
    longitude NUMERIC(11,8),
    hazard_type VARCHAR(50) DEFAULT 'roadblock',
    reported_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE hazard_reports ADD COLUMN IF NOT EXISTS latitude NUMERIC(10,8);
ALTER TABLE hazard_reports ADD COLUMN IF NOT EXISTS longitude NUMERIC(11,8);
ALTER TABLE hazard_reports ADD COLUMN IF NOT EXISTS hazard_type VARCHAR(50) DEFAULT 'roadblock';

CREATE INDEX IF NOT EXISTS idx_hazard_reports_user_id ON hazard_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_hazard_reports_itinerary_id ON hazard_reports(itinerary_id);
CREATE INDEX IF NOT EXISTS idx_hazard_reports_coords ON hazard_reports(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_hazard_reports_type ON hazard_reports(hazard_type);
