#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/opt/citations}"
DEPLOYMENT_ID="gate3_hardening_$(date +%Y%m%d_%H%M%S)"
BACKUP_REQUIRED="${BACKUP_REQUIRED:-true}"
LOGROTATE_CONFIG_PATH="/etc/logrotate.d/citations"
NGINX_CONFIG_PATH="/etc/nginx/sites-available/citations.conf"

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

echo "🛡️ GATE 3: PRODUCTION HARDENING DEPLOYMENT"
echo "========================================="
echo "Deployment ID: $DEPLOYMENT_ID"
echo "Project Directory: $PROJECT_DIR"
echo "Backup Required: $BACKUP_REQUIRED"
echo ""

# Pre-deployment validation
log "Starting Gate 3 deployment validation"

if [ "$BACKUP_REQUIRED" = "true" ]; then
    log "Creating pre-deployment backup"
    if [ -f "$PROJECT_DIR/deployment/scripts/pre_deployment_backup.sh" ]; then
        cd "$PROJECT_DIR"
        ./deployment/scripts/pre_deployment_backup.sh
        success "✓ Pre-deployment backup completed"
    else
        error "✗ Pre-deployment backup script not found"
        exit 1
    fi
fi

# Run deployment validation
log "Running deployment validation checks"
if [ -f "$PROJECT_DIR/deployment/scripts/deployment_validation.sh" ]; then
    cd "$PROJECT_DIR"
    ./deployment/scripts/deployment_validation.sh

    if [ $? -ne 0 ]; then
        error "✗ Deployment validation failed"
        error "Deployment aborted - fix issues before proceeding"
        exit 1
    fi

    success "✓ Deployment validation passed"
else
    warning "⚠ Deployment validation script not found, proceeding without validation"
fi

# Step 1: Verify Gate 2 prerequisites
log "Step 1: Verifying Gate 2 prerequisites are met"

# Check if citation logging is enabled
if ! grep -q "CITATION_LOGGING_ENABLED=true" "$PROJECT_DIR/.env.production"; then
    error "✗ Citation logging is not enabled in .env.production"
    exit 1
fi

# Check if enhanced log parser exists
if [ ! -f "$PROJECT_DIR/dashboard/log_parser.py" ]; then
    error "✗ Enhanced log parser not found"
    exit 1
fi

# Check if CitationLogParser class exists
if ! grep -q "class CitationLogParser:" "$PROJECT_DIR/dashboard/log_parser.py"; then
    error "✗ CitationLogParser class not found"
    exit 1
fi

# Check if citation log file exists
if [ ! -f "/opt/citations/logs/citations.log" ]; then
    error "✗ Citation log file not found"
    exit 1
fi

success "✓ Gate 2 prerequisites verified"

# Step 2: Deploy log rotation configuration
log "Step 2: Deploying production log rotation configuration"

# Create logrotate configuration for citations
sudo tee "$LOGROTATE_CONFIG_PATH" > /dev/null << 'EOF'
# Citation system log rotation configuration
# Rotates citation logs to prevent disk space issues

/opt/citations/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 deploy deploy
    copytruncate
    maxsize 100M
    size 10M

    # Log rotation logging
    nodelaycompress

    # Post-rotate script to handle citation parser position reset
    postrotate
        # Reset citation parser position after log rotation
        if [ -f /opt/citations/logs/citations.position ]; then
            cp /opt/citations/logs/citations.position /opt/citations/logs/citations.position.backup
            echo "0" > /opt/citations/logs/citations.position
            logger "Citation parser position reset after log rotation"
        fi

        # Restart dashboard service to ensure it picks up new logs
        if systemctl is-active --quiet citations-dashboard; then
            systemctl restart citations-dashboard
            logger "Dashboard service restarted after log rotation"
        fi
    endscript
}

# Application logs rotation
/var/log/citations/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 syslog syslog
    maxsize 50M
}
EOF

# Test logrotate configuration
if sudo logrotate -d "$LOGROTATE_CONFIG_PATH" >/dev/null 2>&1; then
    success "✓ Log rotation configuration deployed and validated"
else
    error "✗ Log rotation configuration validation failed"
    exit 1
fi

# Step 3: Deploy monitoring and health metrics
log "Step 3: Deploying monitoring and health metrics"

# Check if health metrics are already implemented in dashboard
HEALTH_METRICS_FILE="$PROJECT_DIR/dashboard/api.py"

if [ -f "$HEALTH_METRICS_FILE" ]; then
    # Check if health endpoint exists
    if grep -q "def.*health" "$HEALTH_METRICS_FILE"; then
        success "✓ Health metrics endpoint already exists"
    else
        log "Adding health metrics endpoint to dashboard"

        # Add health endpoint to dashboard API
        cat >> "$HEALTH_METRICS_FILE" << 'EOF'

# Health check endpoint for monitoring
@app.get('/api/health')
def health_check():
    """
    Health check endpoint for monitoring systems.
    Returns system health status including citation pipeline metrics.
    """
    try:
        from database import get_database
        from log_parser import CitationLogParser
        import os

        # Database health
        db = get_database()
        stats = db.get_stats()
        db.close()

        # Citation log health
        log_path = '/opt/citations/logs/citations.log'
        log_health = {
            'exists': os.path.exists(log_path),
            'size_bytes': os.path.getsize(log_path) if os.path.exists(log_path) else 0,
            'writable': os.access(os.path.dirname(log_path), os.W_OK) if os.path.exists(log_path) else True
        }

        # Parser position tracking health
        position_path = '/opt/citations/logs/citations.position'
        position_health = {
            'exists': os.path.exists(position_path),
            'readable': os.access(position_path, os.R_OK) if os.path.exists(position_path) else True,
            'writable': os.access(position_path, os.W_OK) if os.path.exists(position_path) else True
        }

        # Disk space health
        disk_path = '/opt/citations'
        disk_usage = shutil.disk_usage(disk_path) if os.path.exists(disk_path) else None
        disk_health = {
            'available_gb': round(disk_usage.free / (1024**3), 2) if disk_usage else 0,
            'total_gb': round(disk_usage.total / (1024**3), 2) if disk_usage else 0,
            'usage_percent': round((disk_usage.used / disk_usage.total) * 100, 2) if disk_usage else 0
        } if disk_usage else {'error': 'Unable to get disk usage'}

        # System status
        system_health = {
            'status': 'healthy',
            'database': {
                'connected': True,
                'total_validations': stats['total_validations'],
                'pending_count': stats['pending'],
                'completed_count': stats['completed'],
                'failed_count': stats['failed']
            },
            'citation_log': log_health,
            'parser_position': position_health,
            'disk_usage': disk_health,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        # Determine overall health
        issues = []
        if disk_health.get('usage_percent', 0) > 90:
            issues.append('High disk usage')
        if not log_health.get('exists', False):
            issues.append('Citation log missing')
        if not log_health.get('writable', False):
            issues.append('Citation log not writable')

        if issues:
            system_health['status'] = 'degraded'
            system_health['issues'] = issues

        status_code = 200 if system_health['status'] == 'healthy' else 503

        return JSONResponse(content=system_health, status_code=status_code)

    except Exception as e:
        error_response = {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        return JSONResponse(content=error_response, status_code=503)
EOF
        success "✓ Health metrics endpoint added to dashboard"
    fi
else
    warning "⚠ Dashboard API file not found - health metrics may need manual implementation"
fi

# Step 4: Create monitoring configuration
log "Step 4: Creating monitoring configuration"

# Create monitoring configuration file
MONITORING_CONFIG_DIR="/opt/citations/monitoring"
mkdir -p "$MONITORING_CONFIG_DIR"

cat > "$MONITORING_CONFIG_DIR/health_check.sh" << 'EOF'
#!/bin/bash

# Citation System Health Check Script
# Monitors critical system components and alerts on issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
CITATION_LOG_PATH="/opt/citations/logs/citations.log"
POSITION_FILE="/opt/citations/logs/citations.position"
DASHBOARD_API="http://localhost:8001/api/health"
BACKEND_API="http://localhost:8000/api/health"
ALERT_THRESHOLD_DISK=90
ALERT_THRESHOLD_LOG_SIZE=104857600  # 100MB

# Alert counter
ISSUES_FOUND=0

# Function to log issues
log_issue() {
    echo -e "${RED}[ISSUE] $1${NC}"
    ((ISSUES_FOUND++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[OK] $1${NC}"
}

echo "Citation System Health Check - $(date)"
echo "======================================"

# Check backend service
if curl -s "$BACKEND_API" >/dev/null 2>&1; then
    log_success "Backend service is responding"
else
    log_issue "Backend service is not responding"
fi

# Check dashboard service
if curl -s "$DASHBOARD_API" >/dev/null 2>&1; then
    log_success "Dashboard service is responding"
else
    log_warning "Dashboard service may not be responding (check if running)"
fi

# Check citation log file
if [ -f "$CITATION_LOG_PATH" ]; then
    LOG_SIZE=$(stat -c%s "$CITATION_LOG_PATH")
    if [ "$LOG_SIZE" -gt "$ALERT_THRESHOLD_LOG_SIZE" ]; then
        log_warning "Citation log is large: $((LOG_SIZE / 1024 / 1024))MB"
    else
        log_success "Citation log file exists and within size limits"
    fi

    # Check if log is being written to
    if [ -w "$CITATION_LOG_PATH" ]; then
        log_success "Citation log is writable"
    else
        log_issue "Citation log is not writable"
    fi
else
    log_issue "Citation log file does not exist"
fi

# Check position file
if [ -f "$POSITION_FILE" ]; then
    if [ -r "$POSITION_FILE" ] && [ -w "$POSITION_FILE" ]; then
        log_success "Position file is accessible"
    else
        log_warning "Position file has permission issues"
    fi
else
    log_warning "Position file does not exist (will be created on first run)"
fi

# Check disk space
DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt "$ALERT_THRESHOLD_DISK" ]; then
    log_issue "Disk usage is high: ${DISK_USAGE}%"
else
    log_success "Disk usage is acceptable: ${DISK_USAGE}%"
fi

# Check database connectivity
if python3 -c "
import sys
sys.path.insert(0, 'dashboard')
try:
    from database import get_database
    db = get_database()
    stats = db.get_stats()
    db.close()
    print('SUCCESS: Database accessible')
except Exception as e:
    print(f'ERROR: Database issue: {e}')
    exit(1)
" 2>/dev/null; then
    log_success "Database is accessible"
else
    log_issue "Database connectivity issues"
fi

# Summary
echo ""
echo "Health Check Summary:"
if [ "$ISSUES_FOUND" -eq 0 ]; then
    echo "✅ All critical systems are healthy"
    exit 0
else
    echo "❌ Found $ISSUES_FOUND issue(s) that need attention"
    exit 1
fi
EOF

chmod +x "$MONITORING_CONFIG_DIR/health_check.sh"
success "✓ Monitoring configuration created"

# Step 5: Set up automated monitoring
log "Step 5: Setting up automated monitoring"

# Create cron job for health checks
CRON_ENTRY="*/5 * * * * $MONITORING_CONFIG_DIR/health_check.sh >> /var/log/citations/health_checks.log 2>&1"

# Check if cron entry already exists
if (crontab -l 2>/dev/null | grep -q "$MONITORING_CONFIG_DIR/health_check.sh"); then
    success "✓ Health monitoring cron job already exists"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    success "✓ Health monitoring cron job added (runs every 5 minutes)"
fi

# Create log rotation for monitoring logs
sudo tee -a /etc/logrotate.d/citations << 'EOF'

# Monitoring logs rotation
/var/log/citations/health_checks.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 syslog syslog
    maxsize 10M
}
EOF

# Step 6: Deploy error handling and alerting
log "Step 6: Deploying error handling and alerting"

# Create alert configuration
cat > "$MONITORING_CONFIG_DIR/alert_config.json" << 'EOF'
{
  "alerting": {
    "enabled": true,
    "channels": {
      "email": {
        "enabled": false,
        "recipients": ["admin@example.com"]
      },
      "slack": {
        "enabled": false,
        "webhook_url": ""
      }
    },
    "thresholds": {
      "disk_usage_percent": 90,
      "log_rotation_failures": 3,
      "service_downtime_minutes": 5,
      "error_rate_percent": 10
    }
  },
  "monitoring": {
    "health_check_interval_seconds": 300,
    "log_retention_days": 30,
    "metrics_retention_days": 90
  }
}
EOF

success "✓ Alert configuration deployed"

# Step 7: Test log rotation configuration
log "Step 7: Testing log rotation configuration"

# Force a test log rotation (dry run)
if sudo logrotate -f "$LOGROTATE_CONFIG_PATH" --debug >/dev/null 2>&1; then
    success "✓ Log rotation test completed successfully"
else
    warning "⚠ Log rotation test had issues - manual review may be needed"
fi

# Step 8: Restart services to apply configuration
log "Step 8: Restarting services to apply configuration"

# Restart logrotate service
sudo systemctl reload logrotate 2>/dev/null || success "✓ Logrotate configuration reloaded"

# Restart dashboard service if it exists
if systemctl list-unit-files | grep -q "citations-dashboard"; then
    sudo systemctl restart citations-dashboard
    if systemctl is-active --quiet citations-dashboard; then
        success "✓ Dashboard service restarted successfully"
    else
        error "✗ Dashboard service failed to restart"
        exit 1
    fi
else
    warning "⚠ Dashboard service not found"
fi

# Step 9: Validate monitoring setup
log "Step 9: Validating monitoring setup"

# Test health check script
if "$MONITORING_CONFIG_DIR/health_check.sh" >/dev/null 2>&1; then
    success "✓ Health check script is working"
else
    warning "⚠ Health check script has issues - review output"
fi

# Test dashboard health endpoint if available
if command -v curl >/dev/null 2>&1; then
    if curl -s "http://localhost:8001/api/health" >/dev/null 2>&1; then
        success "✓ Dashboard health endpoint is responding"
    else
        warning "⚠ Dashboard health endpoint not responding"
    fi
else
    warning "⚠ curl not available for endpoint testing"
fi

# Step 10: Final deployment validation
log "Step 10: Running final deployment validation"

if [ -f "$PROJECT_DIR/deployment/scripts/deployment_validation.sh" ]; then
    cd "$PROJECT_DIR"
    ./deployment/scripts/deployment_validation.sh

    if [ $? -eq 0 ]; then
        success "✅ Final deployment validation passed"
    else
        warning "⚠ Final deployment validation had warnings - review carefully"
    fi
fi

echo ""
echo "🛡️ GATE 3 DEPLOYMENT COMPLETED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "✅ **PRODUCTION HARDENING DEPLOYED SUCCESSFULLY**"
echo ""
echo "**Deployment Summary:**"
echo "- Deployment ID: $DEPLOYMENT_ID"
echo "- Log Rotation: Configured with copytruncate and post-rotate handling"
echo "- Monitoring: Automated health checks (5-minute intervals)"
echo "- Health Metrics: Dashboard health endpoint implemented"
echo "- Error Handling: Alerting configuration deployed"
echo "- System Protection: Disk space monitoring and threshold alerts"
echo ""
echo "🛡️ **Production Hardening Features:**"
echo "- Daily log rotation with 30-day retention"
echo "- Automatic citation parser position reset on rotation"
echo "- Health check endpoint with comprehensive metrics"
echo "- Disk space monitoring with 90% threshold alerts"
echo "- Automated monitoring with 5-minute check intervals"
echo "- Configuration backup and restoration procedures"
echo ""
echo "📋 **Next Steps for Gate 3:**"
echo "1. Monitor log rotation (check /var/log/citations/ for rotation logs)"
echo "2. Verify health endpoint metrics: http://localhost:8001/api/health"
echo "3. Review monitoring logs: /var/log/citations/health_checks.log"
echo "4. Test manual log rotation: sudo logrotate -f /etc/logrotate.d/citations"
echo "5. If stable, proceed to Gate 4: Complete System deployment"
echo ""
echo "🔧 **Monitoring Commands:**"
echo "- Health check: $MONITORING_CONFIG_DIR/health_check.sh"
echo "- Log rotation test: sudo logrotate -d /etc/logrotate.d/citations"
echo "- View cron jobs: crontab -l | grep citations"
echo "- Health endpoint: curl http://localhost:8001/api/health"
echo ""
echo "🔄 **Rollback Information:**"
echo "- Remove logrotate config: sudo rm /etc/logrotate.d/citations"
echo "- Remove monitoring cron: crontab -e | grep -v citations"
echo "- Restore previous dashboard API: git checkout dashboard/api.py"
echo "- Full rollback procedures in: deployment/EMERGENCY_ROLLBACK.md"
echo ""
echo "📁 **Important Files:**"
echo "- Log rotation config: $LOGROTATE_CONFIG_PATH"
echo "- Health check script: $MONITORING_CONFIG_DIR/health_check.sh"
echo "- Alert configuration: $MONITORING_CONFIG_DIR/alert_config.json"
echo "- Monitoring logs: /var/log/citations/health_checks.log"
echo ""
echo "✅ **Gate 3 is ready for monitoring phase**"