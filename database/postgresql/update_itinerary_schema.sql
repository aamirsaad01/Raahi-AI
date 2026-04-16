

-- ===============================================
-- Update Itineraries Table for Full Itinerary Support
-- Run this script to add new columns for itinerary generation
-- ===============================================

-- Add new columns to itineraries table
ALTER TABLE itineraries 
ADD COLUMN IF NOT EXISTS daily_plan JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS total_cost NUMERIC(12,2),
ADD COLUMN IF NOT EXISTS mood_tags JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS activities JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS travel_month SMALLINT;

-- Add comments
COMMENT ON COLUMN itineraries.daily_plan IS 'Day-by-day itinerary schedule with POIs';
COMMENT ON COLUMN itineraries.total_cost IS 'Estimated total cost including attractions, food, hotels, transport';
COMMENT ON COLUMN itineraries.mood_tags IS 'User mood preferences used for generation';
COMMENT ON COLUMN itineraries.activities IS 'User activity preferences used for generation';
COMMENT ON COLUMN itineraries.travel_month IS 'Month of travel (1-12)';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_itineraries_mood_tags ON itineraries USING gin(mood_tags);
CREATE INDEX IF NOT EXISTS idx_itineraries_activities ON itineraries USING gin(activities);
CREATE INDEX IF NOT EXISTS idx_itineraries_travel_month ON itineraries(travel_month);
CREATE INDEX IF NOT EXISTS idx_itineraries_destination ON itineraries(destination);

-- Display success message
DO $$ 
BEGIN
    RAISE NOTICE '✅ Itinerary table updated successfully!';
    RAISE NOTICE '📊 New columns added: daily_plan, total_cost, mood_tags, activities, travel_month';
END $$;

SELECT * FROM points_of_interest
SELECT * FROM points_of_interest WHERE name = 'Altit Fort'

SELECT *
FROM points_of_interest
WHERE name IN (
    SELECT name
    FROM points_of_interest
    GROUP BY name
    HAVING COUNT(*) > 1
);

WITH DuplicateCTE AS (
    SELECT 
        *, 
        COUNT(*) OVER(PARTITION BY name) as duplicate_count
    FROM points_of_interest
)
SELECT *
FROM DuplicateCTE
WHERE duplicate_count > 1
ORDER BY name;

SELECT DISTINCT location_id
FROM points_of_interest;

SELECT * FROM travel_corridors

