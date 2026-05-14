-- ---------------------------------------------------------------------------
-- users — authentication & profile
-- (Includes set_updated_at so this file can be applied alone via run_user_setup.)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $func$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$func$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contact_number VARCHAR(20),
    dob DATE,
    cnic VARCHAR(20),
    medical_conditions TEXT,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_number VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS dob DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS cnic VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS medical_conditions TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

UPDATE users SET contact_number = COALESCE(NULLIF(contact_number, ''), '00000000000')
WHERE contact_number IS NULL OR contact_number = '';
UPDATE users SET dob = COALESCE(dob, DATE '1970-01-01') WHERE dob IS NULL;
UPDATE users SET cnic = COALESCE(NULLIF(cnic, ''), CONCAT('00000-000000', user_id::text, '-0'))
WHERE cnic IS NULL OR cnic = '';

ALTER TABLE users ALTER COLUMN contact_number SET NOT NULL;
ALTER TABLE users ALTER COLUMN dob SET NOT NULL;
ALTER TABLE users ALTER COLUMN cnic SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'users_cnic_key') THEN
        ALTER TABLE users ADD CONSTRAINT users_cnic_key UNIQUE (cnic);
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'users_set_updated_at') THEN
        CREATE TRIGGER users_set_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    END IF;
END$$;
