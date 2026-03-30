-- ================================================
-- Migration: Make user_id nullable in itineraries table
-- Allows anonymous users to generate itineraries
-- ================================================

-- Drop the NOT NULL constraint on user_id
ALTER TABLE itineraries 
ALTER COLUMN user_id DROP NOT NULL;

-- Update foreign key to allow NULL (ON DELETE SET NULL instead of CASCADE)
-- First, drop the existing foreign key constraint
DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    -- Find the constraint name
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'itineraries'::regclass
    AND confrelid = 'users'::regclass
    AND contype = 'f';
    
    -- Drop it if it exists
    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE itineraries DROP CONSTRAINT %I', constraint_name);
    END IF;
END$$;

-- Recreate foreign key with SET NULL on delete
ALTER TABLE itineraries
ADD CONSTRAINT itineraries_user_id_fkey
FOREIGN KEY (user_id) 
REFERENCES users(user_id) 
ON DELETE SET NULL;

-- Add comment
COMMENT ON COLUMN itineraries.user_id IS 'User ID (NULL for anonymous users)';

