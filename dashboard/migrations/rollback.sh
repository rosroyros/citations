#!/bin/bash

# Database Rollback Script for Dashboard
# Purpose: Restore database from selected backup

set -e  # Exit on any error

DB_PATH="/opt/citations/dashboard/data/validations.db"
BACKUP_DIR="/opt/citations/dashboard/data/backups"

echo "🔄 Database Rollback Script"
echo "==========================="

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# List available backups
echo "📋 Available backups:"
ls -1 "$BACKUP_DIR"/validations.db.backup-* 2>/dev/null | sort -r | head -10 | nl -n ln

if [ $(ls "$BACKUP_DIR"/validations.db.backup-* 2>/dev/null | wc -l) -eq 0 ]; then
    echo "❌ No backups found in: $BACKUP_DIR"
    exit 1
fi

# Get user selection
echo ""
read -p "Enter backup number to restore (or 'q' to quit): " SELECTION

if [ "$SELECTION" = "q" ]; then
    echo "🚫 Rollback cancelled"
    exit 0
fi

# Validate selection
if ! [[ "$SELECTION" =~ ^[0-9]+$ ]]; then
    echo "❌ Invalid selection: $SELECTION"
    exit 1
fi

# Get the backup file path
BACKUP_FILE=$(ls -1 "$BACKUP_DIR"/validations.db.backup-* 2>/dev/null | sort -r | head -10 | sed -n "${SELECTION}p")

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Backup not found for selection: $SELECTION"
    exit 1
fi

# Confirmation
echo ""
echo "⚠️  WARNING: This will replace the current database!"
echo "   Current database: $DB_PATH"
echo "   Restore from: $BACKUP_FILE"
echo ""

# Show current stats
if [ -f "$DB_PATH" ]; then
    CURRENT_SIZE=$(ls -lh "$DB_PATH" | awk '{print $5}')
    CURRENT_RECORDS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM validations;" 2>/dev/null || echo "Unknown")
    echo "   Current size: $CURRENT_SIZE"
    echo "   Current records: $CURRENT_RECORDS"
else
    echo "   Current database: NOT FOUND"
fi

# Show backup stats
BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
BACKUP_RECORDS=$(sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM validations;" 2>/dev/null || echo "Unknown")
echo "   Backup size: $BACKUP_SIZE"
echo "   Backup records: $BACKUP_RECORDS"

echo ""
read -p "Are you sure you want to continue? (type 'YES' to confirm): " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo "🚫 Rollback cancelled - confirmation not received"
    exit 0
fi

# Create emergency backup of current database (if it exists)
if [ -f "$DB_PATH" ]; then
    EMERGENCY_BACKUP="$DB_PATH.emergency_backup_$(date +%Y%m%d_%H%M%S)"
    echo "📦 Creating emergency backup: $EMERGENCY_BACKUP"
    cp "$DB_PATH" "$EMERGENCY_BACKUP"
    echo "✅ Emergency backup created"
fi

# Perform rollback
echo ""
echo "🔄 Restoring database..."
cp "$BACKUP_FILE" "$DB_PATH"

# Verify restoration
echo "🔍 Verifying restoration..."
if [ -f "$DB_PATH" ]; then
    NEW_SIZE=$(ls -lh "$DB_PATH" | awk '{print $5}')
    NEW_RECORDS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM validations;" 2>/dev/null || echo "Unknown")

    echo "✅ Database restored successfully!"
    echo "   New size: $NEW_SIZE"
    echo "   New records: $NEW_RECORDS"

    # Quick database integrity check
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>/dev/null | grep -q "ok"; then
        echo "✅ Database integrity check passed"
    else
        echo "⚠️  Warning: Database integrity check failed"
    fi

else
    echo "❌ Restoration failed: Database file not found after restore"
    exit 1
fi

echo ""
echo "🎉 Rollback completed successfully!"
echo "   Database restored from: $BACKUP_FILE"
echo "   Emergency backup saved: $EMERGENCY_BACKUP"
echo ""
echo "💡 Test the dashboard: curl -I http://localhost:4646"