-- Allow multiple itineraries per user with the same title (each row keeps its own itinerary_id).
-- Replaces unique index ux_itineraries_user_title with a non-unique index for lookups.

DROP INDEX IF EXISTS ux_itineraries_user_title;

CREATE INDEX IF NOT EXISTS idx_itineraries_user_title ON itineraries(user_id, title);

SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'itineraries' AND indexname LIKE '%user%title%';