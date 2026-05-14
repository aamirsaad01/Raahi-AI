-- ---------------------------------------------------------------------------
-- checklist — packing lists linked to an itinerary
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS checklist (
    checklist_id SERIAL PRIMARY KEY,
    itinerary_id INT NOT NULL REFERENCES itineraries(itinerary_id) ON DELETE CASCADE,
    location VARCHAR(100) NOT NULL,
    month VARCHAR(50),
    items JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_checklist_itinerary_id ON checklist(itinerary_id);
