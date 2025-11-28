#!/bin/bash
set -e  # Exit on any error

# Production Database Restore Script
# For citations dashboard deployment
# Usage: ./restore_database.sh <backup_file>

DB_PATH="/opt/citations/dashboard/data/validations.db"
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ No backup file specified"
    echo "Usage: $0 <backup_file_path>"
    echo ""
    echo "Available backups:"
    if [ -d "/opt/citations/backups" ]; then
        find /opt/citations/backups -name "validations_*.db" -type f -exec ls -lh {} \;
    fi
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Starting database restore from: $BACKUP_FILE"

# Stop dashboard service during restore
echo "⏸️  Stopping dashboard service..."
sudo systemctl stop citations-dashboard || echo "Service already stopped"

# Stop backend service if it might be accessing the database
echo "⏸️  Stopping backend service..."
sudo systemctl stop citations-backend || echo "Service already stopped"

# Create backup of current database before restore
if [ -f "$DB_PATH" ]; then
    EMERGENCY_BACKUP="${DB_PATH}.emergency_backup_$(date +%Y%m%d_%H%M%S)"
    echo "🚨 Creating emergency backup: $EMERGENCY_BACKUP"
    cp "$DB_PATH" "$EMERGENCY_BACKUP"
fi

# Verify backup integrity
echo "🔍 Verifying backup integrity..."
sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Backup file integrity check failed"
    echo "❌ Restore aborted"
    exit 1
fi

# Get backup stats
RECORD_COUNT=$(sqlite3 "$BACKUP_FILE" "SELECT COUNT(*) FROM validations;")
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "📊 Backup contains $RECORD_COUNT validation records ($BACKUP_SIZE)"

# Confirm restore
read -p "⚠️  This will replace the current database. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled by user"
    # Start services again
    sudo systemctl start citations-backend
    sudo systemctl start citations-dashboard
    exit 1
fi

# Perform restore
echo "📦 Restoring database..."
cp "$BACKUP_FILE" "$DB_PATH"

# Set proper permissions
sudo chown deploy:deploy "$DB_PATH"
sudo chmod 644 "$DB_PATH"

# Verify restored database
echo "🔍 Verifying restored database..."
sqlite3 "$DB_PATH" "PRAGMA integrity_check;" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Restored database integrity check failed"
    if [ -f "$EMERGENCY_BACKUP" ]; then
        echo "🔄 Restoring from emergency backup..."
        cp "$EMERGENCY_BACKUP" "$DB_PATH"
        sudo chown deploy:deploy "$DB_PATH"
        sudo chmod 644 "$DB_PATH"
    fi
    echo "❌ Restore failed - database reverted"
    exit 1
fi

# Get restored database stats
RESTORED_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM validations;")
echo "✅ Database restored successfully"
echo "📊 Restored database contains $RESTORED_COUNT validation records"

# Start services
echo "▶️  Starting backend service..."
sudo systemctl start citations-backend
echo "▶️  Starting dashboard service..."
sudo systemctl start citations-dashboard

# Wait a moment and check service status
sleep 2
BACKEND_STATUS=$(sudo systemctl is-active citations-backend)
DASHBOARD_STATUS=$(sudo systemctl is-active citations-dashboard)

echo "📊 Service Status:"
echo "   Backend: $BACKEND_STATUS"
echo "   Dashboard: $DASHBOARD_STATUS"

if [ "$BACKEND_STATUS" = "active" ] && [ "$DASHBOARD_STATUS" = "active" ]; then
    echo "✅ All services started successfully"
else
    echo "⚠️  Some services may need manual attention"
fi

echo "📋 Restore summary:"
echo "   Source: $BACKUP_FILE"
echo "   Destination: $DB_PATH"
echo "   Records restored: $RESTORED_COUNT"
echo "   Emergency backup: $EMERGENCY_BACKUP"

echo "✅ Database restore completed successfully"