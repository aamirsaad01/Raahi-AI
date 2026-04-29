-- =========================================================
-- Migration: emergency contacts linked with itineraries
-- =========================================================

CREATE TABLE IF NOT EXISTS itinerary_emergency_contacts (
    contact_id SERIAL PRIMARY KEY,
    itinerary_id INT NOT NULL REFERENCES itineraries(itinerary_id) ON DELETE CASCADE,
    contact_name VARCHAR(120) NOT NULL,
    relationship VARCHAR(80) NOT NULL,
    phone_number VARCHAR(25) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_itinerary_emergency_contacts_itinerary
    ON itinerary_emergency_contacts(itinerary_id, created_at DESC);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'set_updated_at')
       AND NOT EXISTS (
           SELECT 1 FROM pg_trigger
           WHERE tgname = 'itinerary_emergency_contacts_set_updated_at'
       ) THEN
        CREATE TRIGGER itinerary_emergency_contacts_set_updated_at
        BEFORE UPDATE ON itinerary_emergency_contacts
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

