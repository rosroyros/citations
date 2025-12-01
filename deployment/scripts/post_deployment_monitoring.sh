#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-https://citationformatchecker.com}"
MONITORING_DURATION="${MONITORING_DURATION:-1800}"  # 30 minutes default
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"  # Check every minute
LOG_FILE="/var/log/citations/post_deployment_monitoring.log"
ALERT_THRESHOLD="${ALERT_THRESHOLD:-3}"  # Alert after 3 consecutive failures

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging functions
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

# Initialize monitoring variables
consecutive_failures=0
total_checks=0
passed_checks=0
failed_checks=0
monitoring_start_time=$(date +%s)

# Function to send alert (can be customized)
send_alert() {
    local severity=$1
    local message=$2

    log "ALERT [$severity]: $message"

    # Add your alerting mechanism here (email, Slack, etc.)
    # Example:
    # curl -X POST -H 'Content-type: application/json' \
    #   --data "{\"text\":\"$severity: $message\"}" \
    #   YOUR_SLACK_WEBHOOK_URL
}

# Function to check application health
check_application_health() {
    local check_name="$1"
    local check_url="$2"
    local expected_status="${3:-200}"

    if command -v curl >/dev/null 2>&1; then
        local response_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 "$check_url" 2>/dev/null || echo "000")
        local response_time=$(curl -s -o /dev/null -w "%{time_total}" --connect-timeout 10 --max-time 30 "$check_url" 2>/dev/null || echo "0")

        if [ "$response_code" = "$expected_status" ]; then
            if (( $(echo "$response_time < 5.0" | bc -l) )); then
                log "✓ $check_name (HTTP $response_code, ${response_time}s)"
                return 0
            else
                warning "⚠ $check_name slow response (HTTP $response_code, ${response_time}s)"
                return 2
            fi
        else
            error "✗ $check_name failed (HTTP $response_code, ${response_time}s)"
            return 1
        fi
    else
        warning "⚠ curl not available, skipping $check_name"
        return 2
    fi
}

# Function to check database connectivity
check_database_connectivity() {
    local db_name="$1"
    local db_check_command="$2"

    if eval "$db_check_command" >/dev/null 2>&1; then
        log "✓ $db_name database connectivity"
        return 0
    else
        error "✗ $db_name database connectivity failed"
        return 1
    fi
}

# Function to check service status
check_service_status() {
    local service_name="$1"

    if systemctl is-active --quiet "$service_name" 2>/dev/null; then
        log "✓ $service_name service running"
        return 0
    else
        error "✗ $service_name service not running"
        return 1
    fi
}

# Function to check system resources
check_system_resources() {
    local resource_type="$1"
    local threshold="$2"
    local current_value="$3"

    if (( $(echo "$current_value < $threshold" | bc -l 2>/dev/null || echo "$current_value < $threshold") )); then
        log "✓ $resource_type usage: $current_value (threshold: $threshold)"
        return 0
    else
        warning "⚠ $resource_type usage high: $current_value (threshold: $threshold)"
        return 2
    fi
}

# Function to check error rates in logs
check_error_rates() {
    local log_file="$1"
    local time_window="$2"
    local max_errors="$3"

    if [ -f "$log_file" ]; then
        local error_count=$(tail -n 1000 "$log_file" | grep -c -i "error\|exception\|failed" || echo "0")

        if [ "$error_count" -le "$max_errors" ]; then
            log "✓ Error rate acceptable: $error_count errors (max: $max_errors)"
            return 0
        else
            error "✗ High error rate: $error_count errors (max: $max_errors)"
            return 1
        fi
    else
        warning "⚠ Log file not found: $log_file"
        return 2
    fi
}

# Main monitoring function
run_monitoring_checks() {
    local check_failed=false

    log "Starting monitoring cycle $((total_checks + 1))"

    # 1. Application Health Checks
    check_application_health "Main website" "$BASE_URL"
    [ $? -ne 0 ] && check_failed=true

    check_application_health "API health endpoint" "$BASE_URL/api/health" "200"
    [ $? -ne 0 ] && check_failed=true

    check_application_health "Sitemap" "$BASE_URL/sitemap.xml" "200"
    [ $? -ne 0 ] && check_failed=true

    # 2. Database Connectivity
    check_database_connectivity "Credits" "
    python3 -c \"
import sys
sys.path.insert(0, '/opt/citations/backend/backend')
from database import get_credits
test_result = get_credits('test-token')
print('OK')
\" 2>/dev/null | grep -q 'OK'
    "
    [ $? -ne 0 ] && check_failed=true

    check_database_connectivity "Validations" "
    python3 -c \"
import sys
sys.path.insert(0, '/opt/citations/dashboard')
from database import get_database
db = get_database()
stats = db.get_stats()
db.close()
print('OK')
\" 2>/dev/null | grep -q 'OK'
    "
    [ $? -ne 0 ] && check_failed=true

    # 3. Service Status (if on production server)
    if command -v systemctl >/dev/null 2>&1; then
        check_service_status "citations-backend"
        [ $? -ne 0 ] && check_failed=true

        # Check nginx status
        check_service_status "nginx"
        [ $? -ne 0 ] && check_failed=true

        # Check dashboard service if it exists
        if systemctl list-unit-files | grep -q "citations-dashboard"; then
            check_service_status "citations-dashboard"
            [ $? -ne 0 ] && check_failed=true
        fi
    fi

    # 4. System Resources
    if command -v df >/dev/null 2>&1; then
        local disk_usage=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
        check_system_resources "Disk" 90 "$disk_usage"
        [ $? -eq 1 ] && check_failed=true
    fi

    if command -v free >/dev/null 2>&1; then
        local memory_usage=$(free | grep Mem | awk '{printf "%.0f", ($3/$2)*100}')
        check_system_resources "Memory" 90 "$memory_usage"
        [ $? -eq 1 ] && check_failed=true
    fi

    # 5. Error Rate Monitoring
    if [ -f "/opt/citations/logs/app.log" ]; then
        check_error_rates "/opt/citations/logs/app.log" "10m" 5
        [ $? -ne 0 ] && check_failed=true
    fi

    # 6. Dashboard Metrics (if accessible)
    if command -v curl >/dev/null 2>&1; then
        local dashboard_response=$(curl -s "$BASE_URL/api/dashboard/stats" 2>/dev/null || echo "")
        if [ -n "$dashboard_response" ]; then
            log "✓ Dashboard metrics accessible"
        else
            warning "⚠ Dashboard metrics not accessible"
        fi
    fi

    # Update counters
    total_checks=$((total_checks + 1))
    if [ "$check_failed" = true ]; then
        failed_checks=$((failed_checks + 1))
        consecutive_failures=$((consecutive_failures + 1))
    else
        passed_checks=$((passed_checks + 1))
        consecutive_failures=0
    fi

    log "Cycle complete: $total_checks total, $passed_checks passed, $failed_checks failed"

    # Check if we need to send alerts
    if [ $consecutive_failures -ge $ALERT_THRESHOLD ]; then
        send_alert "CRITICAL" "$consecutive_failures consecutive monitoring failures detected"
    fi
}

# Function to generate final report
generate_final_report() {
    local monitoring_end_time=$(date +%s)
    local duration=$((monitoring_end_time - monitoring_start_time))
    local duration_minutes=$((duration / 60))

    echo ""
    echo "📊 POST-DEPLOYMENT MONITORING REPORT"
    echo "===================================="
    echo "Monitoring Duration: ${duration_minutes} minutes"
    echo "Total Checks: $total_checks"
    echo "Passed: $passed_checks"
    echo "Failed: $failed_checks"
    echo -e "Success Rate: $(echo "scale=1; $passed_checks * 100 / $total_checks" | bc -l)%"

    if [ $failed_checks -eq 0 ]; then
        success "✅ ALL CHECKS PASSED - Deployment appears stable"
        echo ""
        echo "Recommendation: Deployment is stable and monitoring can be scaled back"
    elif [ $consecutive_failures -eq 0 ]; then
        warning "⚠️ INTERMITTENT ISSUES DETECTED"
        echo ""
        echo "Recommendation: Continue monitoring or investigate intermittent failures"
    else
        error "❌ CRITICAL ISSUES DETECTED"
        echo ""
        echo "Recommendation: Investigate immediately - consider rollback if issues persist"
    fi

    echo ""
    echo "Detailed logs available at: $LOG_FILE"
}

# Function to handle cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        error "Monitoring interrupted by signal"
    fi
    generate_final_report
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Start monitoring
echo "🔍 POST-DEPLOYMENT MONITORING"
echo "============================"
echo "Base URL: $BASE_URL"
echo "Monitoring Duration: $((MONITORING_DURATION / 60)) minutes"
echo "Check Interval: $CHECK_INTERVAL seconds"
echo "Alert Threshold: $ALERT_THRESHOLD consecutive failures"
echo "Log File: $LOG_FILE"
echo ""

log "Starting post-deployment monitoring"
log "Monitoring will run for $((MONITORING_DURATION / 60)) minutes"

# Main monitoring loop
while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - monitoring_start_time))

    if [ $elapsed -ge $MONITORING_DURATION ]; then
        log "Monitoring duration completed"
        break
    fi

    run_monitoring_checks

    if [ $elapsed -lt $MONITORING_DURATION ]; then
        sleep $CHECK_INTERVAL
    fi
done

log "Post-deployment monitoring completed successfully"

# Exit with appropriate code
if [ $failed_checks -eq 0 ]; then
    exit 0
elif [ $consecutive_failures -eq 0 ]; then
    exit 1  # Intermittent issues
else
    exit 2  # Critical issues
fi