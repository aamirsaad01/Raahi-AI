-- ===============================================
-- Raahi AI - Database Initialization Script
-- Database: raahi_ai
-- Author: Muhammad Taha
-- Created: Iteration 1
-- ===============================================

-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-update updated_at on update
DO $$
BEGIN
    -- Ensure the function exists (use different dollar-quoting to avoid nesting issues)
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'set_updated_at'
    ) THEN
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $func$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $func$ LANGUAGE plpgsql;
    END IF;

    -- Create the trigger only if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'users_set_updated_at'
    ) THEN
        CREATE TRIGGER users_set_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

-- ITINERARIES TABLE
CREATE TABLE IF NOT EXISTS itineraries (
    itinerary_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    days SMALLINT CHECK (days >= 0) NOT NULL,
    budget NUMERIC(12,2) CHECK (budget >= 0) NOT NULL,
    season VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT season_valid CHECK (
        season IS NULL OR season IN ('Spring','Summer','Autumn','Winter','Monsoon')
    )
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'itineraries_set_updated_at'
    ) THEN
        CREATE TRIGGER itineraries_set_updated_at
        BEFORE UPDATE ON itineraries
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

-- CHECKLIST TABLE
CREATE TABLE IF NOT EXISTS checklist (
    checklist_id SERIAL PRIMARY KEY,
    itinerary_id INT NOT NULL REFERENCES itineraries(itinerary_id) ON DELETE CASCADE,
    location VARCHAR(100) NOT NULL,
    month VARCHAR(50),
    items JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- HAZARD REPORTS TABLE
CREATE TABLE IF NOT EXISTS hazard_reports (
    hazard_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    itinerary_id INT REFERENCES itineraries(itinerary_id) ON DELETE SET NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low','medium','high','critical')),
    location VARCHAR(150),
    reported_at TIMESTAMPTZ DEFAULT NOW()
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_itineraries_user_id ON itineraries(user_id);
CREATE INDEX IF NOT EXISTS idx_checklist_itinerary_id ON checklist(itinerary_id);
CREATE INDEX IF NOT EXISTS idx_hazard_reports_user_id ON hazard_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_hazard_reports_itinerary_id ON hazard_reports(itinerary_id);

-- Avoid duplicate itinerary titles per user (optional but helpful)
CREATE UNIQUE INDEX IF NOT EXISTS ux_itineraries_user_title ON itineraries(user_id, title);
