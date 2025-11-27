# Dashboard Systemd Service Setup

## Files Created

1. **Service Configuration**: `citations-dashboard.service`
2. **API Application**: `dashboard/api.py`
3. **Web Interface**: `dashboard/static/index.html`

## Service Configuration Verification

The systemd service `citations-dashboard.service` is configured with:

### ✅ Auto-Restart Functionality
- `Restart=always` - Automatically restarts the service if it fails
- `RestartSec=10` - Waits 10 seconds before restarting

### ✅ Boot Startup Functionality
- `[Install]` section with `WantedBy=multi-user.target` - Service starts on system boot
- `After=network.target` - Ensures network is available before starting

### ✅ Service Configuration
- **Type**: `simple` - Standard service type for FastAPI/uvicorn
- **User**: `deploy` - Runs as deploy user (matches existing backend service)
- **WorkingDirectory**: `/opt/citations/dashboard` - Correct working directory
- **Environment**: `PATH=/opt/citations/venv/bin` - Uses virtual environment
- **ExecStart**: Uses uvicorn to run the dashboard API on port 4646
- **Host binding**: `0.0.0.0` - Accessible from all interfaces (for VPN access)

## API Features Implemented

- ✅ Health check endpoint: `/api/health`
- ✅ Validations endpoint: `/api/validations` with filtering and pagination
- ✅ Statistics endpoint: `/api/stats`
- ✅ Single validation details: `/api/validations/{job_id}`
- ✅ Parser errors: `/api/parser-errors`
- ✅ Static file serving for web interface
- ✅ Database integration with SQLite

## Web Interface Features

- ✅ Real-time validation monitoring
- ✅ Filtering by date range, status, user type
- ✅ Search by job ID
- ✅ Sortable columns
- ✅ Pagination (50/100/200 per page)
- ✅ Expandable job details
- ✅ Statistics summary
- ✅ Manual refresh
- ✅ Color-coded status indicators
- ✅ Responsive design with brand colors

## Deployment Commands

```bash
# Enable service to start on boot
sudo systemctl enable citations-dashboard

# Start the service
sudo systemctl start citations-dashboard

# Check service status
sudo systemctl status citations-dashboard

# View service logs
sudo journalctl -u citations-dashboard -f

# Test API endpoints
curl http://localhost:4646/api/health
curl http://localhost:4646/api/stats
```

## Access Methods

1. **SSH Tunnel** (recommended for local development):
   ```bash
   ssh -L 4646:localhost:4646 deploy@178.156.161.140
   # Then browse to http://localhost:4646
   ```

2. **VPN Direct Access**:
   ```
   http://178.156.161.140:4646
   ```

## Cron Job Setup

The cron job for parsing logs should be configured separately:
```bash
# File: /etc/cron.d/citations-dashboard
*/5 * * * * deploy /opt/citations/venv/bin/python3 /opt/citations/dashboard/parse_logs_cron.py >> /opt/citations/logs/dashboard-cron.log 2>&1
```

## Service Dependencies

- **Network**: Requires network to be up (`After=network.target`)
- **Virtual Environment**: Requires `/opt/citations/venv` to exist
- **Dashboard Directory**: Requires `/opt/citations/dashboard` to exist
- **Database**: SQLite database will be created automatically

## Troubleshooting

### Service Won't Start
1. Check if virtual environment exists: `ls -la /opt/citations/venv/`
2. Check if dashboard directory exists: `ls -la /opt/citations/dashboard/`
3. Check if port 4646 is available: `netstat -tlnp | grep 4646`
4. Check service logs: `sudo journalctl -u citations-dashboard -n 50`

### API Errors
1. Check database permissions: `ls -la /opt/citations/dashboard/data/`
2. Test database connection manually:
   ```bash
   cd /opt/citations/dashboard
   /opt/citations/venv/bin/python3 -c "from database import get_database; print('DB OK')"
   ```

### Web Interface Issues
1. Check if static files exist: `ls -la /opt/citations/dashboard/static/`
2. Test API endpoints directly: `curl http://localhost:4646/api/health`

## Security Considerations

- **No Authentication**: Accessible to anyone who can reach port 4646
- **Network Access**: Protected by VPN/SSH tunnel requirements
- **User Permissions**: Runs as non-privileged `deploy` user
- **File Permissions**: Standard file permissions on dashboard files

## Performance Considerations

- **Database**: SQLite with indexes on frequently queried columns
- **Pagination**: Limits result sets to prevent memory issues
- **Static Files**: Served efficiently by FastAPI
- **Auto-restart**: Prevents extended downtime due to crashes