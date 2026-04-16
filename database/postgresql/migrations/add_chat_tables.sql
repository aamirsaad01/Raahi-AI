-- =========================================================
-- Migration: chat sessions and messages
-- =========================================================

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

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    token_count INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_last_message
    ON chat_sessions(user_id, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created
    ON chat_messages(session_id, created_at ASC);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'set_updated_at'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'chat_sessions_set_updated_at'
    ) THEN
        CREATE TRIGGER chat_sessions_set_updated_at
        BEFORE UPDATE ON chat_sessions
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;

