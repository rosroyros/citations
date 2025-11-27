# Cron Job Setup for Incremental Log Parsing

## Overview

The citation validator uses a cron job to run incremental log parsing every 5 minutes. This ensures the dashboard database stays up-to-date with the latest validation events.

## Cron Configuration

### Add to System Cron (Recommended)

Edit the system crontab:
```bash
sudo crontab -e
```

Add the following line:
```bash
# Incremental log parsing every 5 minutes
*/5 * * * * /opt/citations/venv/bin/python3 /opt/citations/dashboard/parse_logs_cron.py >> /opt/citations/logs/cron.log 2>&1
```

### Or Add to User Cron

Edit the deploy user's crontab:
```bash
crontab -e
```

Add the same line as above (without sudo).

### Cron Entry Breakdown

```
*/5 * * * *                    # Schedule: every 5 minutes
/opt/citations/venv/bin/python3   # Python interpreter
/opt/citations/dashboard/parse_logs_cron.py  # Script to run
>> /opt/citations/logs/cron.log   # Log output to file
2>&1                               # Redirect stderr to stdout
```

## File Paths Used

- **Log File**: `/opt/citations/logs/app.log` - Main application log
- **Database**: `/opt/citations/dashboard/data/validations.db` - SQLite database
- **Cron Log**: `/opt/citations/logs/cron.log` - Cron job execution log
- **Script**: `/opt/citations/dashboard/parse_logs_cron.py` - Executable cron script

## Requirements

1. **Python Virtual Environment**: `/opt/citations/venv/bin/python3`
2. **Permissions**: Script must be executable (`chmod +x`)
3. **Log Directory**: `/opt/citations/logs/` must exist and be writable
4. **Database Directory**: `/opt/citations/dashboard/data/` must exist

## Verification

### Test Manual Execution

```bash
# Test the script manually
/opt/citations/venv/bin/python3 /opt/citations/dashboard/parse_logs_cron.py

# Check if it completed successfully
echo $?
# Should return 0 for success
```

### Check Cron Logs

```bash
# View recent cron execution logs
tail -f /opt/citations/logs/cron.log

# Check system cron logs (if available)
sudo tail -f /var/log/cron
```

### Verify Database Updates

```bash
# Connect to database and check recent entries
sqlite3 /opt/citations/dashboard/data/validations.db
SELECT * FROM validations ORDER BY created_at DESC LIMIT 10;
.quit
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure script is executable and paths exist
2. **Python Path**: Use full path to python in virtual environment
3. **Log Permissions**: Ensure `/opt/citations/logs/` is writable by deploy user
4. **Database Lock**: Avoid overlapping cron runs (5-minute间隔 prevents this)

### Debug Mode

For debugging, add verbose output:
```bash
*/5 * * * * /opt/citations/venv/bin/python3 -v /opt/citations/dashboard/parse_logs_cron.py >> /opt/citations/logs/cron.log 2>&1
```

## Monitoring

### Log Monitoring

Monitor `/opt/citations/logs/cron.log` for:
- Parse duration warnings
- Error messages
- Number of jobs processed per run

### Database Monitoring

Monitor `validations.db` for:
- New records appearing every 5 minutes
- No duplicate job IDs
- Recent timestamps in `last_parsed_timestamp` metadata

## Alternative: Using Cron.d Directory

For better organization, create `/etc/cron.d/citations-parser`:
```bash
# /etc/cron.d/citations-parser
# Incremental log parsing every 5 minutes
*/5 * * * * deploy /opt/citations/venv/bin/python3 /opt/citations/dashboard/parse_logs_cron.py >> /opt/citations/logs/cron.log 2>&1
```

Then reload cron:
```bash
sudo systemctl reload cron
```

## Security Considerations

1. **File Permissions**: Ensure only `deploy` user can write to log files
2. **Database Access**: Script runs as `deploy` user with database ownership
3. **Log Rotation**: Consider logrotate for `/opt/citations/logs/cron.log`
4. **Resource Limits**: Monitor CPU/memory usage during log parsing

## Performance

- **Expected Duration**: < 5 seconds for incremental parsing
- **Initial Load**: < 30 seconds for first run (last 3 days)
- **Database Size**: Approximately 1MB per 1000 validation records
- **Log Processing**: Designed for logs up to 30MB without performance issues