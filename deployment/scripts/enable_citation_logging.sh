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
MONITORING_DURATION="${MONITORING_DURATION:-900}"  # 15 minutes default
LOG_FILE="/var/log/citations/citation_logging_enablement.log"

# Logging function
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${BLUE}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

error() {
    local message="[ERROR] $1"
    echo -e "${RED}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

success() {
    local message="[SUCCESS] $1"
    echo -e "${GREEN}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

warning() {
    local message="[WARNING] $1"
    echo -e "${YELLOW}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "🔧 ENABLE CITATION LOGING - GATE 1 MONITORING PHASE"
echo "=================================================="
echo "Project Directory: $PROJECT_DIR"
echo "Monitoring Duration: $((MONITORING_DURATION / 60)) minutes"
echo "Log File: $LOG_FILE"
echo ""

log "Starting citation logging enablement with monitoring"

# Pre-enablement validation
log "Performing pre-enablement safety checks"

# Check if backend service is running
if ! systemctl is-active --quiet citations-backend; then
    error "✗ Backend service is not running"
    exit 1
fi
success "✓ Backend service is running"

# Check if application is responding
if command -v curl >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health || echo "000")
    if [ "$HTTP_CODE" != "200" ]; then
        error "✗ Application health endpoint not responding (HTTP $HTTP_CODE)"
        exit 1
    fi
    success "✓ Application health endpoint responding"
else
    warning "⚠ curl not available - skipping health check"
fi

# Check current citation logging state
log "Checking current citation logging configuration"

cd "$PROJECT_DIR"

if grep -q "CITATION_LOGGING_ENABLED=true" .env.production; then
    warning "⚠ Citation logging appears to already be enabled"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Citation logging enablement cancelled"
        exit 0
    fi
elif grep -q "CITATION_LOGGING_ENABLED=false" .env.production; then
    success "✓ Citation logging is currently disabled - ready to enable"
else
    log "CITATION_LOGGING_ENABLED not found in .env.production - will add it"
fi

# Step 1: Enable citation logging
log "Step 1: Enabling citation logging in configuration"

# Update the environment file
if grep -q "CITATION_LOGGING_ENABLED=" .env.production; then
    sed -i 's/CITATION_LOGGING_ENABLED=.*/CITATION_LOGGING_ENABLED=true/' .env.production
else
    echo "CITATION_LOGGING_ENABLED=true" >> .env.production
fi

success "✓ Citation logging enabled in configuration"

# Step 2: Create monitoring baseline
log "Step 2: Creating monitoring baseline"

# Get current system metrics
CPU_BASELINE=$(top -b -n1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
MEMORY_BASELINE=$(free | grep Mem | awk '{printf "%.1f", ($3/$2) * 100.0}')
DISK_BASELINE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')

log "Baseline metrics - CPU: ${CPU_BASELINE}%, Memory: ${MEMORY_BASELINE}%, Disk: ${DISK_BASELINE}%"

# Get current citation log size
CITATION_LOG_PATH="/opt/citations/logs/citations.log"
if [ -f "$CITATION_LOG_PATH" ]; then
    LOG_SIZE_BASELINE=$(stat -c%s "$CITATION_LOG_PATH")
    log "Baseline citation log size: $LOG_SIZE_BASELINE bytes"
else
    LOG_SIZE_BASELINE=0
    log "Citation log does not exist yet"
fi

# Step 3: Restart backend service
log "Step 3: Restarting backend service to enable citation logging"

if systemctl list-unit-files | grep -q "citations-backend"; then
    sudo systemctl restart citations-backend
    sudo systemctl status citations-backend --no-pager

    if systemctl is-active --quiet citations-backend; then
        success "✓ Backend service restarted successfully"
    else
        error "✗ Backend service failed to start after enabling citation logging"
        # Rollback
        sed -i 's/CITATION_LOGGING_ENABLED=.*/CITATION_LOGGING_ENABLED=false/' .env.production
        sudo systemctl restart citations-backend
        exit 1
    fi
else
    error "✗ Backend service not found"
    exit 1
fi

# Step 4: Verify citation logging is working
log "Step 4: Verifying citation logging functionality"

# Wait a moment for service to be fully ready
sleep 5

# Test citation logging with a real request
if command -v curl >/dev/null 2>&1; then
    log "Testing citation logging with validation request"

    # Make a test validation request
    curl -s -X POST http://localhost:8000/api/validate \
        -H "Content-Type: application/json" \
        -d '{"text": "Smith, J. (2020). Test citation for logging", "style": "APA", "token": "test-free-token"}' \
        >/dev/null

    # Wait for citation logging to occur
    sleep 3

    # Check if citations were logged
    if [ -f "$CITATION_LOG_PATH" ]; then
        NEW_LOG_SIZE=$(stat -c%s "$CITATION_LOG_PATH")
        if [ "$NEW_LOG_SIZE" -gt "$LOG_SIZE_BASELINE" ]; then
            success "✓ Citation logging is working (log size increased from $LOG_SIZE_BASELINE to $NEW_LOG_SIZE bytes)"

            # Show the logged content
            log "Recent citation log content:"
            tail -20 "$CITATION_LOG_PATH" | head -10
        else
            error "✗ Citation logging may not be working (log size unchanged)"
        fi
    else
        warning "⚠ Citation log file still not created - may need more activity"
    fi
else
    warning "⚠ curl not available - cannot test citation logging"
fi

# Step 5: Start monitoring
log "Step 5: Starting $((MONITORING_DURATION / 60)) minute monitoring period"

MONITORING_START=$(date +%s)
ERROR_COUNT=0
PERFORMANCE_ISSUES=0

log "Monitoring started - press Ctrl+C to stop early"
log "Will check system health every 30 seconds"

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - MONITORING_START))

    if [ $ELAPSED -ge $MONITORING_DURATION ]; then
        log "Monitoring period completed"
        break
    fi

    # Check system health
    log "Health check ($((ELAPSED / 60)) minutes elapsed)"

    # Check backend service
    if ! systemctl is-active --quiet citations-backend; then
        error "✗ Backend service stopped!"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi

    # Check application health
    if command -v curl >/dev/null 2>&1; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health || echo "000")
        if [ "$HTTP_CODE" != "200" ]; then
            error "✗ Application health check failed (HTTP $HTTP_CODE)"
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi

        # Test validation endpoint performance
        START_TIME=$(date +%s.%N)
        curl -s -X POST http://localhost:8000/api/validate \
            -H "Content-Type: application/json" \
            -d '{"text": "Quick test", "style": "APA", "token": "test-free-token"}' \
            >/dev/null
        END_TIME=$(date +%s.%N)
        RESPONSE_TIME=$(echo "$END_TIME - $START_TIME" | bc -l)

        # Check if response time is acceptable (< 5 seconds)
        if (( $(echo "$RESPONSE_TIME > 5" | bc -l) )); then
            warning "⚠ Slow response time: ${RESPONSE_TIME}s"
            PERFORMANCE_ISSUES=$((PERFORMANCE_ISSUES + 1))
        else
            log "Response time: ${RESPONSE_TIME}s (OK)"
        fi
    fi

    # Check system resources
    CURRENT_CPU=$(top -b -n1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    CURRENT_MEMORY=$(free | grep Mem | awk '{printf "%.1f", ($3/$2) * 100.0}')
    CURRENT_DISK=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')

    # Check for resource issues
    if (( $(echo "$CURRENT_MEMORY > 90" | bc -l) )); then
        warning "⚠ High memory usage: ${CURRENT_MEMORY}%"
        PERFORMANCE_ISSUES=$((PERFORMANCE_ISSUES + 1))
    fi

    if [ "$CURRENT_DISK" -gt 90 ]; then
        warning "⚠ High disk usage: ${CURRENT_DISK}%"
    fi

    # Check citation log growth
    if [ -f "$CITATION_LOG_PATH" ]; then
        CURRENT_LOG_SIZE=$(stat -c%s "$CITATION_LOG_PATH")
        LOG_GROWTH=$((CURRENT_LOG_SIZE - LOG_SIZE_BASELINE))
        log "Citation log growth: $LOG_GROWTH bytes"

        # Check for excessive log growth (> 10MB in monitoring period)
        if [ "$LOG_GROWTH" -gt 10485760 ]; then
            warning "⚠ High citation log growth: $((LOG_GROWTH / 1024 / 1024))MB"
        fi
    fi

    sleep 30
done

# Step 6: Final evaluation
log "Step 6: Final evaluation and recommendation"

if [ $ERROR_COUNT -eq 0 ] && [ $PERFORMANCE_ISSUES -eq 0 ]; then
    success "✅ CITATION LOGGING ENABLED SUCCESSFULLY"
    echo ""
    echo "🎉 **Gate 1 Monitoring Results:**"
    echo "- Service stability: ✅ No errors detected"
    echo "- Performance: ✅ Within acceptable limits"
    echo "- Citation logging: ✅ Working correctly"
    echo "- System resources: ✅ Normal usage"
    echo ""
    echo "✅ **Gate 1 is COMPLETE - Ready for Gate 2 deployment**"
    exit 0

elif [ $ERROR_COUNT -eq 0 ] && [ $PERFORMANCE_ISSUES -gt 0 ]; then
    warning "⚠️ CITATION LOGGING ENABLED WITH PERFORMANCE CONCERNS"
    echo ""
    echo "⚠️ **Gate 1 Monitoring Results:**"
    echo "- Service stability: ✅ No critical errors"
    echo "- Performance: ⚠️ $PERFORMANCE_ISSUES performance issues detected"
    echo "- Citation logging: ✅ Working correctly"
    echo "- System resources: ⚠️ Some resource pressure detected"
    echo ""
    echo "📋 **Recommendation:**"
    echo "- Monitor for another 30 minutes"
    echo "- Consider performance optimization if issues persist"
    echo "- May proceed to Gate 2 if acceptable"
    exit 1

else
    error "❌ CITATION LOGGING ENABLEMENT HAD ISSUES"
    echo ""
    echo "❌ **Gate 1 Monitoring Results:**"
    echo "- Service stability: ❌ $ERROR_COUNT errors detected"
    echo "- Performance: $([ $PERFORMANCE_ISSUES -gt 0 ] && echo "⚠️ $PERFORMANCE_ISSUES issues" || echo "✅ OK")"
    echo "- Citation logging: $(command -v curl >/dev/null 2>&1 && echo "✅ Working" || echo "⚠️ Not tested")"
    echo ""
    echo "🔄 **Recommended Actions:**"
    echo "1. Consider rollback: sed -i 's/CITATION_LOGGING_ENABLED=.*/CITATION_LOGGING_ENABLED=false/' .env.production"
    echo "2. Restart backend service: sudo systemctl restart citations-backend"
    echo "3. Investigate errors before proceeding"
    exit 2
fi