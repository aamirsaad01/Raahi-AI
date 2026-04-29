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
    contact_number VARCHAR(20) NOT NULL,
    dob DATE NOT NULL,
    cnic VARCHAR(20) UNIQUE NOT NULL,
    medical_conditions TEXT,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
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

-- LOCATION MAPPING TABLE
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
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'location_mapping_set_updated_at'
    ) THEN
        CREATE TRIGGER location_mapping_set_updated_at
        BEFORE UPDATE ON location_mapping
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_itineraries_user_id ON itineraries(user_id);
CREATE INDEX IF NOT EXISTS idx_checklist_itinerary_id ON checklist(itinerary_id);
CREATE INDEX IF NOT EXISTS idx_hazard_reports_user_id ON hazard_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_hazard_reports_itinerary_id ON hazard_reports(itinerary_id);
CREATE INDEX IF NOT EXISTS idx_location_mapping_parent_region ON location_mapping(parent_region);
CREATE INDEX IF NOT EXISTS idx_location_mapping_verified ON location_mapping(verified);
CREATE INDEX IF NOT EXISTS idx_location_mapping_climate_zone ON location_mapping(climate_zone);

-- Avoid duplicate itinerary titles per user (optional but helpful)
CREATE UNIQUE INDEX IF NOT EXISTS ux_itineraries_user_title ON itineraries(user_id, title);

-- ===============================================
-- POINTS OF INTEREST TABLE (Phase 2: Itinerary Generation)
-- ===============================================
CREATE TABLE IF NOT EXISTS points_of_interest (
    poi_id SERIAL PRIMARY KEY,
    location_id INT REFERENCES location_mapping(location_id) ON DELETE CASCADE,
    
    -- OSM Data
    osm_id VARCHAR(100) UNIQUE NOT NULL,
    osm_type VARCHAR(20), -- node, way, relation
    name VARCHAR(150) NOT NULL,
    latitude NUMERIC(10,8) NOT NULL,
    longitude NUMERIC(11,8) NOT NULL,
    
    -- LLM Generated Content
    description TEXT,
    rating NUMERIC(3,2) CHECK (rating >= 0 AND rating <= 5), -- Estimated rating 0-5
    category VARCHAR(50), -- nature, cultural, adventure, religious, historical
    difficulty VARCHAR(20), -- easy, moderate, hard, extreme
    
    -- Activities & Mood Matching (JSONB arrays)
    activities JSONB DEFAULT '[]'::jsonb, -- ["hiking", "photography", "camping"]
    mood_tags JSONB DEFAULT '[]'::jsonb, -- ["adventurous", "romantic", "family"]
    highlights JSONB DEFAULT '[]'::jsonb, -- ["key feature 1", "key feature 2"]
    
    -- Cost Information
    estimated_cost VARCHAR(20), -- "Low", "Medium", "High"
    estimated_cost_pkr_min INT,
    estimated_cost_pkr_max INT,
    
    -- Timing & Logistics
    best_months VARCHAR(100), -- "March-October" or specific months
    avg_duration_hours NUMERIC(5,2), -- How long to spend
    accessibility TEXT, -- Road conditions, vehicle requirements
    permits_required BOOLEAN DEFAULT FALSE,
    nearby_facilities TEXT, -- Hotels, restaurants, fuel stations
    
    -- Photos (from Unsplash or other sources)
    photos JSONB DEFAULT '[]'::jsonb, -- Array of photo objects with URLs
    
    -- Metadata
    verified BOOLEAN DEFAULT FALSE,
    last_api_fetch TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- POI Triggers
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'poi_set_updated_at'
    ) THEN
        CREATE TRIGGER poi_set_updated_at
        BEFORE UPDATE ON points_of_interest
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

-- POI Indexes for Fast Queries
CREATE INDEX IF NOT EXISTS idx_poi_location_id ON points_of_interest(location_id);
CREATE INDEX IF NOT EXISTS idx_poi_category ON points_of_interest(category);
CREATE INDEX IF NOT EXISTS idx_poi_rating ON points_of_interest(rating);
CREATE INDEX IF NOT EXISTS idx_poi_difficulty ON points_of_interest(difficulty);
CREATE INDEX IF NOT EXISTS idx_poi_estimated_cost ON points_of_interest(estimated_cost);
CREATE INDEX IF NOT EXISTS idx_poi_activities ON points_of_interest USING gin(activities);
CREATE INDEX IF NOT EXISTS idx_poi_mood_tags ON points_of_interest USING gin(mood_tags);

-- CHAT SESSIONS TABLE
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    linked_itinerary_id INT REFERENCES itineraries(itinerary_id) ON DELETE SET NULL,
    title VARCHAR(180),
    context_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    snapshot_refreshed_at TIMESTAMPTZ,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'chat_sessions_set_updated_at'
    ) THEN
        CREATE TRIGGER chat_sessions_set_updated_at
        BEFORE UPDATE ON chat_sessions
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

-- CHAT MESSAGES TABLE
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    token_count INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_last_message ON chat_sessions(user_id, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created ON chat_messages(session_id, created_at ASC);

-- ITINERARY EMERGENCY CONTACTS TABLE
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
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'itinerary_emergency_contacts_set_updated_at'
    ) THEN
        CREATE TRIGGER itinerary_emergency_contacts_set_updated_at
        BEFORE UPDATE ON itinerary_emergency_contacts
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_itinerary_emergency_contacts_itinerary ON itinerary_emergency_contacts(itinerary_id, created_at DESC);