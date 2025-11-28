#!/bin/bash
set -e  # Exit on any error

# Production Database Backup Script
# For citations dashboard deployment
# Usage: ./backup_database.sh [backup_type]

BACKUP_DIR="/opt/citations/backups"
DB_PATH="/opt/citations/dashboard/data/validations.db"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_TYPE=${1:-"daily"}  # daily, weekly, pre-deployment

echo "🗄️  Starting database backup..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/daily"
mkdir -p "$BACKUP_DIR/weekly"
mkdir -p "$BACKUP_DIR/pre-deployment"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found at: $DB_PATH"
    exit 1
fi

# Create backup based on type
case "$BACKUP_TYPE" in
    "daily")
        BACKUP_FILE="$BACKUP_DIR/daily/validations_$DATE.db"
        RETENTION_DAYS=7
        ;;
    "weekly")
        BACKUP_FILE="$BACKUP_DIR/weekly/validations_weekly_$DATE.db"
        RETENTION_DAYS=30
        ;;
    "pre-deployment")
        BACKUP_FILE="$BACKUP_DIR/pre-deployment/validations_pre_deploy_$DATE.db"
        RETENTION_DAYS=90
        ;;
    *)
        echo "❌ Invalid backup type: $BACKUP_TYPE"
        echo "Usage: $0 [daily|weekly|pre-deployment]"
        exit 1
        ;;
esac

echo "📦 Creating $BACKUP_TYPE backup: $BACKUP_FILE"

# Use sqlite backup command for consistency
sqlite3 "$DB_PATH" ".backup $BACKUP_FILE"

# Verify backup was created
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup failed to create"
    exit 1
fi

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup created successfully ($BACKUP_SIZE)"

# Verify backup integrity
sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Backup integrity check failed"
    rm "$BACKUP_FILE"
    exit 1
fi
echo "✅ Backup integrity verified"

# Get database stats
RECORD_COUNT=$(sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM validations;")
DB_SIZE=$(sqlite3 "$BACKUP_FILE" "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();")
DB_SIZE_MB=$((DB_SIZE / 1024 / 1024))
echo "📊 Backup contains $RECORD_COUNT validation records ($DB_SIZE_MB MB)"

# Clean up old backups based on retention policy
case "$BACKUP_TYPE" in
    "daily")
        find "$BACKUP_DIR/daily" -name "validations_*.db" -mtime +$RETENTION_DAYS -delete
        echo "🧹 Cleaned up daily backups older than $RETENTION_DAYS days"
        ;;
    "weekly")
        find "$BACKUP_DIR/weekly" -name "validations_weekly_*.db" -mtime +$RETENTION_DAYS -delete
        echo "🧹 Cleaned up weekly backups older than $RETENTION_DAYS days"
        ;;
    "pre-deployment")
        find "$BACKUP_DIR/pre-deployment" -name "validations_pre_deploy_*.db" -mtime +$RETENTION_DAYS -delete
        echo "🧹 Cleaned up pre-deployment backups older than $RETENTION_DAYS days"
        ;;
esac

echo "📋 Backup summary:"
echo "   Type: $BACKUP_TYPE"
echo "   File: $BACKUP_FILE"
echo "   Size: $BACKUP_SIZE"
echo "   Records: $RECORD_COUNT"
echo "   Retention: $RETENTION_DAYS days"

echo "✅ Database backup completed successfully"