-- Migration: Add upgrade_state column to validations table
-- Purpose: Track upgrade funnel progression (NULL → locked → clicked → modal → success)
-- Created: 2025-12-06 for issue x6ky

-- Add upgrade_state column to track upgrade funnel states
ALTER TABLE validations ADD COLUMN upgrade_state TEXT;

-- Create index for efficient queries on upgrade_state
CREATE INDEX idx_validations_upgrade_state ON validations(upgrade_state);

-- Set default values to NULL for existing records (already NULL by default)
-- No action needed - SQLite defaults new column to NULL for existing rows