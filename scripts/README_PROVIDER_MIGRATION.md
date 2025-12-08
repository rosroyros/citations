# Provider Column Migration

## Overview
This migration adds a `provider` column to the `validations` table to track which AI provider (OpenAI, Gemini, etc.) was used for each validation job.

## Migration Script
- **File**: `scripts/migrate_provider_column.py`
- **Purpose**: Adds `provider` TEXT column to validations table
- **Creates**: Index on provider column for dashboard query performance

## Prerequisites
- Database must exist at `dashboard/data/validations.db`
- Python 3.6+

## Execution Instructions

### Production Database
```bash
# From project root
python3 scripts/migrate_provider_column.py
```

The script will:
1. Ask for confirmation before modifying production database
2. Check if provider column already exists (idempotent)
3. Add column and index if not present

### Test Database
```bash
export TEST_VALIDATIONS_DB_PATH="/path/to/test.db"
python3 scripts/migrate_provider_column.py
```

## Schema Changes

### Before
```sql
CREATE TABLE validations (
    job_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    duration_seconds REAL,
    citation_count INTEGER,
    token_usage_prompt INTEGER,
    token_usage_completion INTEGER,
    token_usage_total INTEGER,
    user_type TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    results_gated BOOLEAN,
    results_revealed_at TEXT,
    gated_outcome TEXT,
    paid_user_id TEXT,
    free_user_id TEXT,
    upgrade_state TEXT
);
```

### After
```sql
CREATE TABLE validations (
    job_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    duration_seconds REAL,
    citation_count INTEGER,
    token_usage_prompt INTEGER,
    token_usage_completion INTEGER,
    token_usage_total INTEGER,
    user_type TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    results_gated BOOLEAN,
    results_revealed_at TEXT,
    gated_outcome TEXT,
    paid_user_id TEXT,
    free_user_id TEXT,
    upgrade_state TEXT,
    provider TEXT
);

-- Index created for dashboard performance
CREATE INDEX idx_provider ON validations(provider);
```

## Code Updates

The following files were updated to handle the new provider column:

1. **dashboard/database.py**:
   - Added `provider` column to table schema
   - Added provider to index creation
   - Updated `insert_validation()` method to handle provider field

2. **backend/database.py**:
   - No changes needed (uses different database for credits)

## Verification

After migration, verify with:
```sql
-- Check column exists
PRAGMA table_info(validations);

-- Check index exists
.schema validations

-- Verify on sample data
SELECT job_id, provider FROM validations LIMIT 5;
```

## Rollback
If needed, rollback by removing the column:
```sql
-- SQLite doesn't support DROP COLUMN directly on older versions
-- Create new table without provider and copy data
CREATE TABLE validations_backup AS SELECT * FROM validations;
DROP TABLE validations;
CREATE TABLE validations (/* original schema */);
INSERT INTO validations SELECT * FROM validations_backup;
DROP TABLE validations_backup;
```

## Dependencies
- This migration must be completed **before** deploying CitationLogParser changes
- Required for Dashboard UI updates to display provider information