-- Migration: Add latitude, longitude, and hazard_type columns to hazard_reports table
-- This allows storing coordinates directly instead of parsing from location string

-- Add latitude column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='hazard_reports' AND column_name='latitude'
    ) THEN
        ALTER TABLE hazard_reports ADD COLUMN latitude NUMERIC(10,8);
    END IF;
END$$;

-- Add longitude column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='hazard_reports' AND column_name='longitude'
    ) THEN
        ALTER TABLE hazard_reports ADD COLUMN longitude NUMERIC(11,8);
    END IF;
END$$;

-- Add hazard_type column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='hazard_reports' AND column_name='hazard_type'
    ) THEN
        ALTER TABLE hazard_reports ADD COLUMN hazard_type VARCHAR(50) DEFAULT 'roadblock';
    END IF;
END$$;

-- Create index on coordinates for faster spatial queries
CREATE INDEX IF NOT EXISTS idx_hazard_reports_coords ON hazard_reports(latitude, longitude);

-- Create index on hazard_type for filtering
CREATE INDEX IF NOT EXISTS idx_hazard_reports_type ON hazard_reports(hazard_type);

