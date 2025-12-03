#!/bin/bash

# Database Backup Script for Dashboard
# Purpose: Create timestamped backup of validations database

set -e  # Exit on any error

DB_PATH="/opt/citations/dashboard/data/validations.db"
BACKUP_DIR="/opt/citations/dashboard/data/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/validations.db.backup-$TIMESTAMP"

echo "🗄️  Database Backup Script"
echo "=========================="

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found: $DB_PATH"
    echo "   Is the dashboard deployed?"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Get original database size
DB_SIZE=$(ls -lh "$DB_PATH" | awk '{print $5}')
echo "📂 Source database: $DB_PATH ($DB_SIZE)"

# Create backup
echo "📦 Creating backup: $BACKUP_FILE"
cp "$DB_PATH" "$BACKUP_FILE"

# Verify backup created and has reasonable size
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup failed: File not created"
    exit 1
fi

BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
echo "✅ Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)"

# Show recent backups (last 5)
echo ""
echo "📋 Recent backups:"
ls -lh "$BACKUP_DIR"/*.backup-* 2>/dev/null | tail -5 || echo "   No previous backups found"

# Verify backup integrity (quick SQLite check)
echo ""
echo "🔍 Verifying backup integrity..."
if sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM validations;" >/dev/null 2>&1; then
    RECORD_COUNT=$(sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM validations;")
    echo "✅ Backup verified: $RECORD_COUNT validation records"
else
    echo "⚠️  Warning: Could not verify backup integrity"
fi

echo ""
echo "🎉 Backup completed successfully!"
echo "   File: $BACKUP_FILE"
echo "   Size: $BACKUP_SIZE"
echo "   Records: $RECORD_COUNT"