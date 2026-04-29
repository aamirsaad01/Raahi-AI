-- Speed up resume: active session per user + itinerary anchor
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_itinerary_active
ON chat_sessions (user_id, linked_itinerary_id)
WHERE is_archived = FALSE;
