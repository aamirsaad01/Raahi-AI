-- ---------------------------------------------------------------------------
-- itineraries — stored trips (supports anonymous: user_id NULL)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS itineraries (
    itinerary_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    title VARCHAR(150) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    days SMALLINT CHECK (days >= 0) NOT NULL,
    budget NUMERIC(12,2) CHECK (budget >= 0) NOT NULL,
    season VARCHAR(50),
    daily_plan JSONB DEFAULT '[]'::jsonb,
    total_cost NUMERIC(12,2),
    mood_tags JSONB DEFAULT '[]'::jsonb,
    activities JSONB DEFAULT '[]'::jsonb,
    travel_month SMALLINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT season_valid CHECK (
        season IS NULL OR season IN ('Spring','Summer','Autumn','Winter','Monsoon')
    )
);

ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS daily_plan JSONB DEFAULT '[]'::jsonb;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS total_cost NUMERIC(12,2);
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS mood_tags JSONB DEFAULT '[]'::jsonb;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS activities JSONB DEFAULT '[]'::jsonb;
ALTER TABLE itineraries ADD COLUMN IF NOT EXISTS travel_month SMALLINT;

ALTER TABLE itineraries ALTER COLUMN user_id DROP NOT NULL;

DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT c.conname AS conname
        FROM pg_constraint c
        JOIN pg_class rel ON rel.oid = c.conrelid
        JOIN pg_class ref ON ref.oid = c.confrelid
        WHERE rel.relname = 'itineraries'
          AND ref.relname = 'users'
          AND c.contype = 'f'
    LOOP
        EXECUTE format('ALTER TABLE itineraries DROP CONSTRAINT IF EXISTS %I', r.conname);
    END LOOP;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'itineraries_user_id_fkey') THEN
        ALTER TABLE itineraries
            ADD CONSTRAINT itineraries_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL;
    END IF;
END$$;

COMMENT ON COLUMN itineraries.user_id IS 'User ID (NULL for anonymous itineraries)';

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'itineraries_set_updated_at') THEN
        CREATE TRIGGER itineraries_set_updated_at
        BEFORE UPDATE ON itineraries
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_itineraries_user_id ON itineraries(user_id);
CREATE INDEX IF NOT EXISTS idx_itineraries_mood_tags ON itineraries USING gin(mood_tags);
CREATE INDEX IF NOT EXISTS idx_itineraries_activities ON itineraries USING gin(activities);
CREATE INDEX IF NOT EXISTS idx_itineraries_travel_month ON itineraries(travel_month);
CREATE INDEX IF NOT EXISTS idx_itineraries_destination ON itineraries(destination);

DROP INDEX IF EXISTS ux_itineraries_user_title;
CREATE INDEX IF NOT EXISTS idx_itineraries_user_title ON itineraries(user_id, title);
