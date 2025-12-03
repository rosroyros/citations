# Database Migration Procedures

This directory contains scripts and documentation for safely managing database migrations for the citations dashboard.

## Overview

The dashboard uses SQLite database located at `/opt/citations/dashboard/data/validations.db`. Since SQLite doesn't support `DROP COLUMN`, migrations require careful backup planning.

## Files

- `backup.sh` - Create timestamped database backups
- `rollback.sh` - Restore database from backup
- `add_user_id_columns.py` - Migration script for adding user ID columns

## Backup Procedures

### When to Run Backup

**ALWAYS run backup before any migration:**
- Before running migration scripts
- Before major database schema changes
- Before any risky database operations
- Before upgrading dashboard code that might affect database

### Creating a Backup

```bash
cd /opt/citations/dashboard/migrations
./backup.sh
```

**Example output:**
```
🗄️  Database Backup Script
==========================
📂 Source database: /opt/citations/dashboard/data/validations.db (340K)
📦 Creating backup: /opt/citations/dashboard/data/backups/validations.db.backup-20251203-1648
✅ Backup created successfully: validations.db.backup-20251203-1648 (340K)

📋 Recent backups:
-rw-r--r-- 1 deploy deploy 340K Dec  3 16:48 validations.db.backup-20251203-1648
-rw-r--r-- 1 deploy deploy 264K Dec  2 07:30 validations.db.backup_1764660655

🔍 Verifying backup integrity...
✅ Backup verified: 474 validation records

🎉 Backup completed successfully!
   File: /opt/citations/dashboard/data/backups/validations.db.backup-20251203-1648
   Size: 340K
   Records: 474
```

### Verifying Backup Success

**Check these indicators:**
1. ✅ "Backup created successfully" message
2. ✅ File exists in backups directory
3. ✅ File size is reasonable (similar to original)
4. ✅ Backup verification shows record count
5. ✅ No error messages displayed

**Manual verification:**
```bash
# List backups
ls -lh /opt/citations/dashboard/data/backups/

# Check specific backup size
ls -lh /opt/citations/dashboard/data/backups/validations.db.backup-20251203-1648

# Verify backup integrity
sqlite3 /opt/citations/dashboard/data/backups/validations.db.backup-20251203-1648 "SELECT COUNT(*) FROM validations;"
```

## Rollback Procedures

### When Rollback is Needed

**Rollback if migration fails or causes issues:**
- Migration script reports errors
- Dashboard becomes inaccessible after migration
- Database integrity check fails
- Unexpected data loss or corruption
- User reports dashboard problems after deployment

### Performing Rollback

```bash
cd /opt/citations/dashboard/migrations
./rollback.sh
```

**Rollback process:**
1. Lists available backups with numbers
2. User selects backup to restore
3. Shows current vs backup database stats
4. Requires 'YES' confirmation for safety
5. Creates emergency backup of current database
6. Restores selected backup
7. Verifies restoration success

**Example rollback:**
```
🔄 Database Rollback Script
===========================
📋 Available backups:
     1	/opt/citations/dashboard/data/backups/validations.db.backup-20251203-1648
     2	/opt/citations/dashboard/data/backups/validations.db.backup_1764660655

Enter backup number to restore (or 'q' to quit): 1

⚠️  WARNING: This will replace the current database!
   Current database: /opt/citations/dashboard/data/validations.db
   Restore from: /opt/citations/dashboard/data/backups/validations.db.backup-20251203-1648
   Current size: 340K
   Current records: 474
   Backup size: 340K
   Backup records: 474

Are you sure you want to continue? (type 'YES' to confirm): YES

📦 Creating emergency backup: /opt/citations/dashboard/data/validations.db.emergency_backup_20251203_1650
✅ Emergency backup created

🔄 Restoring database...
🔍 Verifying restoration...
✅ Database restored successfully!
   New size: 340K
   New records: 474
✅ Database integrity check passed

🎉 Rollback completed successfully!
   Database restored from: /opt/citations/dashboard/data/backups/validations.db.backup-20251203-1648
   Emergency backup saved: /opt/citations/dashboard/data/validations.db.emergency_backup_20251203_1650
```

### Testing After Rollback

**Verify rollback success:**
```bash
# Check dashboard accessible
curl -I http://localhost:4646

# Check database contents
sqlite3 /opt/citations/dashboard/data/validations.db "SELECT COUNT(*) FROM validations;"

# Check dashboard functionality
# (Visit dashboard URL in browser)
```

## Migration Procedures

### Running Migration Scripts

**General migration process:**
1. Create backup: `./backup.sh`
2. Verify backup success
3. Run migration: `python3 migration_script.py`
4. Verify migration results
5. Test dashboard functionality

**Migration script safety features:**
- Idempotent: Safe to run multiple times
- Non-destructive: Only adds columns/data
- Verification: Checks success/failure
- Clear messages: Reports each step

### Example: User ID Columns Migration

```bash
# Step 1: Create backup
./backup.sh

# Step 2: Run migration
python3 add_user_id_columns.py

# Step 3: Verify migration
sqlite3 /opt/citations/dashboard/data/validations.db ".schema validations"

# Step 4: Test dashboard
curl -I http://localhost:4646
```

## Testing Procedures Safely

### Using Test Database Copy

**Create test database:**
```bash
# Copy production database to test location
cp /opt/citations/dashboard/data/validations.db /opt/citations/dashboard/data/validations.test.db

# Test migration on copy
DB_PATH=/opt/citations/dashboard/data/validations.test.db python3 add_user_id_columns.py

# Clean up test database when done
rm /opt/citations/dashboard/data/validations.test.db
```

### Staging Environment

If available, test procedures in staging environment first before production.

## Troubleshooting

### Common Issues

**Backup fails:**
- Check disk space: `df -h`
- Check permissions: `ls -la /opt/citations/dashboard/data/`
- Check database exists: `ls -la /opt/citations/dashboard/data/validations.db`

**Rollback fails:**
- Check backup file exists and is readable
- Check write permissions on database directory
- Verify database not locked by dashboard service

**Migration fails:**
- Check Python version: `python3 --version`
- Check sqlite3 module: `python3 -c "import sqlite3"`
- Check database permissions: `ls -la /opt/citations/dashboard/data/validations.db`

### Getting Help

**Check logs:**
```bash
# Dashboard service logs
systemctl status citations-backend

# Application logs
tail -f /opt/citations/backend/logs/app.log
```

**Database diagnostics:**
```bash
# Check database integrity
sqlite3 /opt/citations/dashboard/data/validations.db "PRAGMA integrity_check;"

# Check database schema
sqlite3 /opt/citations/dashboard/data/validations.db ".schema"

# Check database size
ls -lh /opt/citations/dashboard/data/validations.db
```

## Safety Checklist

### Before Migration
- [ ] Created recent backup
- [ ] Verified backup integrity
- [ ] Checked available disk space
- [ ] Reviewed migration script
- [ ] Notified users of planned maintenance

### After Migration
- [ ] Migration completed without errors
- [ ] Dashboard accessible (HTTP 200)
- [ ] Database integrity check passed
- [ ] Expected columns/indexes created
- [ ] No errors in application logs
- [ ] Basic functionality tested

### After Rollback
- [ ] Rollback completed without errors
- [ ] Dashboard accessible (HTTP 200)
- [ ] Database integrity check passed
- [ ] Emergency backup created
- [ ] Original functionality restored
- [ ] No errors in application logs