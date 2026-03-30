-- Migration: Allow POIs to exist for multiple destinations
-- This removes the UNIQUE constraint on osm_id and adds a composite unique constraint
-- on (osm_id, location_id) so the same POI can belong to multiple locations

-- Step 1: Drop the existing UNIQUE constraint on osm_id
DO $$
BEGIN
    -- Check if the unique constraint exists
    IF EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conname = 'points_of_interest_osm_id_key'
    ) THEN
        ALTER TABLE points_of_interest DROP CONSTRAINT points_of_interest_osm_id_key;
        RAISE NOTICE 'Dropped UNIQUE constraint on osm_id';
    END IF;
END$$;

-- Step 2: Add composite unique constraint on (osm_id, location_id)
-- This allows the same POI (osm_id) to exist for multiple locations,
-- but prevents duplicate entries for the same location
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conname = 'points_of_interest_osm_id_location_id_key'
    ) THEN
        ALTER TABLE points_of_interest 
        ADD CONSTRAINT points_of_interest_osm_id_location_id_key 
        UNIQUE (osm_id, location_id);
        RAISE NOTICE 'Added composite UNIQUE constraint on (osm_id, location_id)';
    END IF;
END$$;

-- Step 3: Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_poi_osm_id_location_id 
ON points_of_interest(osm_id, location_id);

