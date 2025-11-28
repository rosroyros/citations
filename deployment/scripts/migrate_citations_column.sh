#!/bin/bash
set -e  # Exit on any error

# Production Database Migration Script for citations_text column
# This script safely adds the citations_text column to the validations table
# Usage: ./migrate_citations_column.sh [--dry-run]

DB_PATH="/opt/citations/dashboard/data/validations.db"
DRY_RUN=${1:-"false"}

echo "🗄️  Starting citations_text column migration..."

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found at: $DB_PATH"
    echo "⚠️  This is normal for new deployments - database will be created with citations_text column"
    exit 0
fi

echo "📊 Database found: $DB_PATH"

# Check if citations_text column already exists
echo "🔍 Checking current schema..."
CITATIONS_EXISTS=$(sqlite3 "$DB_PATH" "PRAGMA table_info(validations);" | grep citations_text | wc -l)

if [ "$CITATIONS_EXISTS" -gt 0 ]; then
    echo "✅ citations_text column already exists"

    # Verify column type
    COLUMN_TYPE=$(sqlite3 "$DB_PATH" "PRAGMA table_info(validations);" | grep citations_text | awk '{print $3}')
    echo "📝 Column type: $COLUMN_TYPE"

    if [ "$COLUMN_TYPE" = "TEXT" ]; then
        echo "✅ citations_text column has correct type"
    else
        echo "⚠️  citations_text column has unexpected type: $COLUMN_TYPE"
    fi

    # Check if index exists
    INDEX_EXISTS=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_citations_text';" | wc -l)
    if [ "$INDEX_EXISTS" -gt 0 ]; then
        echo "✅ citations_text index exists"
    else
        echo "⚠️  citations_text index missing - will be created"
        if [ "$DRY_RUN" != "true" ]; then
            echo "🔄 Creating citations_text index..."
            sqlite3 "$DB_PATH" "CREATE INDEX IF NOT EXISTS idx_citations_text ON validations(citations_text) WHERE citations_text IS NOT NULL AND length(citations_text) > 0;"
            echo "✅ citations_text index created"
        fi
    fi

    echo "✅ Migration already completed"
    exit 0
fi

echo "⚠️  citations_text column missing - migration needed"

if [ "$DRY_RUN" = "true" ]; then
    echo "🔍 DRY RUN: Would add citations_text column"
    echo "🔍 DRY RUN: Would create citations_text index"
    echo "🔍 DRY RUN: Migration completed successfully"
    exit 0
fi

# Create backup before migration
echo "📦 Creating pre-migration backup..."
BACKUP_FILE="${DB_PATH}.pre_citations_migration_$(date +%Y%m%d_%H%M%S)"
cp "$DB_PATH" "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# Get current database stats
echo "📊 Current database stats:"
RECORD_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM validations;")
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo "   Records: $RECORD_COUNT"
echo "   Size: $DB_SIZE"

# Perform migration
echo "🔄 Adding citations_text column to validations table..."
sqlite3 "$DB_PATH" "ALTER TABLE validations ADD COLUMN citations_text TEXT;"

if [ $? -ne 0 ]; then
    echo "❌ Migration failed - restoring backup"
    mv "$BACKUP_FILE" "$DB_PATH"
    exit 1
fi

echo "✅ citations_text column added"

# Create index for performance
echo "🔄 Creating citations_text index..."
sqlite3 "$DB_PATH" "CREATE INDEX IF NOT EXISTS idx_citations_text ON validations(citations_text) WHERE citations_text IS NOT NULL AND length(citations_text) > 0;"

if [ $? -ne 0 ]; then
    echo "⚠️  Index creation failed, but column migration succeeded"
else
    echo "✅ citations_text index created"
fi

# Verify migration
echo "🔍 Verifying migration..."
sqlite3 "$DB_PATH" "PRAGMA table_info(validations);" | grep citations_text > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ citations_text column exists"
else
    echo "❌ citations_text column missing after migration"
    mv "$BACKUP_FILE" "$DB_PATH"
    exit 1
fi

# Test insertion with new column
echo "🧪 Testing citations_text insertion..."
TEST_JOB_ID="migration_test_$(date +%s)"
sqlite3 "$DB_PATH" "INSERT INTO validations (job_id, created_at, user_type, status, citations_text) VALUES ('$TEST_JOB_ID', '2025-11-28T10:00:00Z', 'test', 'completed', 'Test citation for migration verification');" > /dev/null

CITATION_TEXT=$(sqlite3 "$DB_PATH" "SELECT citations_text FROM validations WHERE job_id = '$TEST_JOB_ID';")
if [ "$CITATION_TEXT" = "Test citation for migration verification" ]; then
    echo "✅ citations_text insertion test passed"
    # Clean up test record
    sqlite3 "$DB_PATH" "DELETE FROM validations WHERE job_id = '$TEST_JOB_ID';"
else
    echo "❌ citations_text insertion test failed"
    mv "$BACKUP_FILE" "$DB_PATH"
    exit 1
fi

# Post-migration stats
echo "📊 Post-migration database stats:"
POST_RECORD_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM validations;")
POST_DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo "   Records: $POST_RECORD_COUNT"
echo "   Size: $POST_DB_SIZE"
echo "   Size increase: $(expr $(du -k "$DB_PATH" | cut -f1) - $(du -k "$BACKUP_FILE" | cut -f1)) KB"

# Get new schema
echo "📋 Updated schema:"
sqlite3 "$DB_PATH" "PRAGMA table_info(validations);"

# Get indexes
echo "📋 Indexes:"
sqlite3 "$DB_PATH" "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='validations';"

echo "✅ Migration completed successfully!"
echo "📦 Backup file: $BACKUP_FILE"
echo ""
echo "🧹 Cleanup: Remove backup file after confirming deployment success:"
echo "   rm $BACKUP_FILE"