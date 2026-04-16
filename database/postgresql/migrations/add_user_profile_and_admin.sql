-- =========================================================
-- Migration: extend users table for auth/profile/admin
-- =========================================================

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS contact_number VARCHAR(20),
    ADD COLUMN IF NOT EXISTS dob DATE,
    ADD COLUMN IF NOT EXISTS cnic VARCHAR(20),
    ADD COLUMN IF NOT EXISTS medical_conditions TEXT,
    ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

-- Keep legacy rows valid
UPDATE users
SET contact_number = COALESCE(NULLIF(contact_number, ''), '00000000000')
WHERE contact_number IS NULL OR contact_number = '';

UPDATE users
SET dob = COALESCE(dob, DATE '1970-01-01')
WHERE dob IS NULL;

UPDATE users
SET cnic = COALESCE(NULLIF(cnic, ''), CONCAT('00000-000000', user_id::text, '-0'))
WHERE cnic IS NULL OR cnic = '';

ALTER TABLE users
    ALTER COLUMN contact_number SET NOT NULL,
    ALTER COLUMN dob SET NOT NULL,
    ALTER COLUMN cnic SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_cnic_key'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_cnic_key UNIQUE (cnic);
    END IF;
END$$;

