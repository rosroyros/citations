# Backfill Test Job Indicator

This document describes how to use the backfill script to update existing validation records with the `is_test_job` flag.

## Overview

The test job indicator feature was implemented to automatically detect and flag test submissions. However, historical data in the database may contain test jobs that were submitted before this feature was implemented.

The `backfill_test_jobs.py` script identifies these historical test jobs and updates them to have `is_test_job = true` in the database.

## When to Run

Run this script once after deploying the test job indicator feature to clean up historical data.

## Usage

### Basic Usage

```bash
# Dry run (recommended first) - see what would be updated
python3 backfill_test_jobs.py --dry-run

# Actual update
python3 backfill_test_jobs.py
```

### With Custom Database Path

```bash
# For production database on server
python3 backfill_test_jobs.py --db-path /opt/citations/dashboard/data/validations.db

# For local development
python3 backfill_test_jobs.py --db-path ./dashboard/data/validations.db
```

### Verbose Output

```bash
python3 backfill_test_jobs.py --verbose
```

## How It Works

1. **Database Schema Check**: Verifies the `validations` table has the required `is_test_job` column
2. **Find Test Jobs**: Searches for records containing 'test' in the `citations` column
3. **Filter False Positives**: Uses heuristics to distinguish real test jobs from legitimate citations
4. **Update Records**: Sets `is_test_job = 1` for identified test jobs

## Detection Logic

The script considers a record a test job if it contains:

**Strong Indicators** (automatically flagged):
- `testtesttest` - New official marker
- `e2e test` - E2E test citations
- `test citation` - Explicit test citations
- `test job` - Test job mentions
- `unittest` - Unit test patterns

**Multiple Occurrences**:
- 'test' appears 2+ times in the citation text

**Suspicious Patterns**:
- Multiple indicators like 'example', 'demo', 'sample'
- Fake data patterns like 'asdf', 'qwerty', 'test123'

## Safety Features

- **Dry Run Mode**: Always run with `--dry-run` first to see what will be changed
- **Conservative Filtering**: Avoids false positives on legitimate academic citations about testing
- **Database Backup**: Always backup your database before running updates

## Production Deployment

1. **SSH to Server**:
   ```bash
   ssh deploy@178.156.161.140
   cd /opt/citations
   ```

2. **Backup Database**:
   ```bash
   cp dashboard/data/validations.db dashboard/data/validations.db.backup.$(date +%Y%m%d)
   ```

3. **Run Dry Run**:
   ```bash
   python3 backfill_test_jobs.py --dry-run --db-path /opt/citations/dashboard/data/validations.db
   ```

4. **Review Results**: Check the output carefully
   - Ensure no legitimate citations are being flagged
   - Verify the count looks reasonable

5. **Run Update**:
   ```bash
   python3 backfill_test_jobs.py --db-path /opt/citations/dashboard/data/validations.db
   ```

6. **Verify Results**:
   ```bash
   # Check dashboard - test jobs should be filtered out
   # Query database directly:
   sqlite3 /opt/citations/dashboard/data/validations.db "SELECT COUNT(*) FROM validations WHERE is_test_job = 1;"
   ```

## Troubleshooting

### Database Not Found
```
Error: Database not found at: dashboard/data/validations.db
```
- Check if the database path is correct
- Verify the database exists on the server

### Schema Issues
```
Database schema missing 'is_test_job' column
```
- Ensure the latest code has been deployed
- The database schema should auto-migrate

### Too Many False Positives
- Review the detection logic in the script
- Add exceptions for specific legitimate citations
- Use `--verbose` to see detailed reasoning

## After Running

Once the backfill is complete:
1. The dashboard should exclude historical test jobs from metrics
2. Only new submissions with `testtesttest` will be flagged automatically
3. No further action is needed for the test job indicator feature

## Related Files

- `backend/app.py` - Test job detection in new submissions
- `dashboard/database.py` - Database query filtering
- `dashboard/static/index.html` - Frontend filtering logic
- `backend/database.py` - `create_validation_record` function