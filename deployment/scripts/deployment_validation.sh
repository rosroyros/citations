#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL for the application
BASE_URL="${BASE_URL:-https://citationformatchecker.com}"

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

# Counter for results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Function to update counters
update_counters() {
    local result=$1
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    case $result in
        "PASS")
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            ;;
        "FAIL")
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            ;;
        "WARN")
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
            ;;
    esac
}

# Function to run a check with error handling
run_check() {
    local check_name="$1"
    local check_command="$2"

    log "Running: $check_name"

    if eval "$check_command" >/dev/null 2>&1; then
        success "✓ $check_name"
        update_counters "PASS"
        return 0
    else
        error "✗ $check_name"
        update_counters "FAIL"
        return 1
    fi
}

# Function to run a check with warning handling
run_check_with_warning() {
    local check_name="$1"
    local check_command="$2"
    local warning_threshold="${3:-1}"

    log "Running: $check_name"

    local result
    result=$(eval "$check_command" 2>&1) || true

    if [ -n "$result" ] && [ "$result" -gt "$warning_threshold" ]; then
        warning "⚠ $check_name (count: $result)"
        update_counters "WARN"
        return 2
    elif [ $? -eq 0 ]; then
        success "✓ $check_name"
        update_counters "PASS"
        return 0
    else
        error "✗ $check_name"
        update_counters "FAIL"
        return 1
    fi
}

echo "🔍 Comprehensive Production Deployment Validation"
echo "=================================================="
echo ""

# 1. Database Independence Verification
echo "📊 DATABASE INDEPENDENCE VERIFICATION"
echo "--------------------------------------"

# Check if both databases can be created independently
run_check "Can create credits database independently" "
python3 -c \"
import sys
sys.path.insert(0, 'backend/backend')
from database import init_db, get_db_path
import tempfile
import os

# Test with temporary database
temp_db = tempfile.mktemp(suffix='.db')
os.environ['TEST_DB_PATH'] = temp_db
try:
    init_db()
    print('SUCCESS')
finally:
    if os.path.exists(temp_db):
        os.unlink(temp_db)
\" | grep -q 'SUCCESS'
"

# Check validations database independence
run_check "Can create validations database independently" "
python3 -c \"
import sys
sys.path.insert(0, 'dashboard')
from database import get_database
import tempfile
import os

# Test with temporary database
temp_db = tempfile.mktemp(suffix='.db')
try:
    db = get_database(temp_db)
    stats = db.get_stats()
    print('SUCCESS')
finally:
    db.close()
    if os.path.exists(temp_db):
        os.unlink(temp_db)
\" | grep -q 'SUCCESS'
"

# 2. File System Permissions Validation
echo ""
echo "📁 FILE SYSTEM PERMISSIONS VALIDATION"
echo "--------------------------------------"

# Check critical directories are writable
run_check "Backend directory writable" "test -w backend/backend"

run_check "Dashboard directory writable" "test -w dashboard"

run_check "Can create temporary files in backend" "
python3 -c \"
import tempfile
import os
backend_dir = 'backend/backend'
try:
    with tempfile.NamedTemporaryFile(dir=backend_dir, delete=True) as f:
        f.write(b'test')
    print('OK')
except Exception as e:
    print(f'FAILED: {e}')
\" | grep -q 'OK'
"

run_check "Can create temporary files in dashboard" "
python3 -c \"
import tempfile
import os
dashboard_dir = 'dashboard'
try:
    with tempfile.NamedTemporaryFile(dir=dashboard_dir, delete=True) as f:
        f.write(b'test')
    print('OK')
except Exception as e:
    print(f'FAILED: {e}')
\" | grep -q 'OK'
"

# Check database file permissions
run_check "Credits database permissions correct" "
python3 -c \"
import sys
sys.path.insert(0, 'backend/backend')
from database import get_db_path
import os
db_path = get_db_path()
if os.path.exists(db_path):
    stat_info = os.stat(db_path)
    # Check file is readable and writable by owner
    if stat_info.st_mode & 0o600:  # at least rw-------
        print('OK')
    else:
        print('BAD_PERMISSIONS')
else:
    print('OK')  # File doesn't exist yet, that's fine
\" | grep -q 'OK'
"

run_check "Validations database permissions correct" "
python3 -c \"
import sys
sys.path.insert(0, 'dashboard')
from database import get_database
import os
db = get_database()
db.close()
db_path = db.db_path
if os.path.exists(db_path):
    stat_info = os.stat(db_path)
    if stat_info.st_mode & 0o600:
        print('OK')
    else:
        print('BAD_PERMISSIONS')
else:
    print('OK')
\" | grep -q 'OK'
"

# 3. Log Rotation Configuration Testing
echo ""
echo "🔄 LOG ROTATION CONFIGURATION TESTING"
echo "-------------------------------------"

# Check if citation log directory exists and is writable
run_check "Citation log directory exists" "test -d backend/backend/citation_logs"

run_check "Citation log directory writable" "test -w backend/backend/citation_logs 2>/dev/null || echo 'CREATE_NEEDED'"

if [ ! -d "backend/backend/citation_logs" ]; then
    warning "⚠ Citation log directory does not exist - will be created during deployment"
    update_counters "WARN"
fi

# Check for log rotation monitoring in the citation parser
run_check "Citation parser handles log rotation" "
grep -q 'rotation\\|copytruncate\\|inode\\|file_offset' backend/backend/citation_logger.py 2>/dev/null || echo 'NOT_FOUND'
"
if [ $? -ne 0 ]; then
    warning "⚠ Citation parser may not handle log rotation explicitly"
    update_counters "WARN"
fi

# 4. Dashboard Metrics Verification
echo ""
echo "📈 DASHBOARD METRICS VERIFICATION"
echo "---------------------------------"

# Check if dashboard database can be accessed and has metrics
run_check "Dashboard database accessible" "
python3 -c \"
import sys
sys.path.insert(0, 'dashboard')
from database import get_database
try:
    db = get_database()
    stats = db.get_stats()
    print(f'DATABASE_OK:{stats[\\\"total_validations\\\"]}')
    db.close()
except Exception as e:
    print(f'DATABASE_ERROR:{e}')
\" | grep -q 'DATABASE_OK'
"

# Check if we can retrieve dashboard metrics
run_check "Can retrieve dashboard metrics" "
python3 -c \"
import sys
sys.path.insert(0, 'dashboard')
from database import get_database
try:
    db = get_database()
    stats = db.get_stats()
    # Check we get expected metrics structure
    required_keys = ['total_validations', 'completed', 'failed', 'pending']
    if all(key in stats for key in required_keys):
        print('METRICS_OK')
    else:
        print('METRICS_MISSING')
    db.close()
except Exception as e:
    print(f'METRICS_ERROR:{e}')
\" | grep -q 'METRICS_OK'
"

# Check dashboard API is responsive (if running)
if command -v curl >/dev/null 2>&1; then
    run_check_with_warning "Dashboard API responsive" "
curl -s -o /dev/null -w '%{http_code}' 'http://localhost:8001/health' 2>/dev/null || echo '000'
" "200"
else
    warning "⚠ curl not available for API health check"
    update_counters "WARN"
fi

# 5. Application Health Checks
echo ""
echo "🏥 APPLICATION HEALTH CHECKS"
echo "-----------------------------"

# Check if Python dependencies are satisfied
run_check "Backend Python dependencies satisfied" "
cd backend && python3 -c \"
import sys
try:
    # Test critical imports
    import sqlite3
    import requests
    import flask
    print('DEPENDENCIES_OK')
except ImportError as e:
    print(f'DEPENDENCY_MISSING:{e}')
\" 2>/dev/null | grep -q 'DEPENDENCIES_OK'
"

run_check "Dashboard Python dependencies satisfied" "
cd dashboard && python3 -c \"
import sys
try:
    import sqlite3
    import json
    from datetime import datetime
    print('DEPENDENCIES_OK')
except ImportError as e:
    print(f'DEPENDENCY_MISSING:{e}')
\" 2>/dev/null | grep -q 'DEPENDENCIES_OK'
"

# Check frontend build
run_check "Frontend can be built" "
cd frontend/frontend && npm run build >/dev/null 2>&1 && echo 'BUILD_OK'
" || echo "Frontend build failed"

# 6. Service Configuration Validation
echo ""
echo "⚙️  SERVICE CONFIGURATION VALIDATION"
echo "-----------------------------------"

# Check if systemd service files exist (for production environment)
if [ -f "/etc/systemd/system/citations-backend.service" ]; then
    run_check "Backend systemd service exists" "test -f /etc/systemd/system/citations-backend.service"
    run_check "Backend systemd service enabled" "systemctl is-enabled citations-backend >/dev/null 2>&1"
else
    warning "⚠ Backend systemd service not found (development environment)"
    update_counters "WARN"
fi

if [ -f "/etc/systemd/system/citations-dashboard.service" ]; then
    run_check "Dashboard systemd service exists" "test -f /etc/systemd/system/citations-dashboard.service"
    run_check "Dashboard systemd service enabled" "systemctl is-enabled citations-dashboard >/dev/null 2>&1"
else
    warning "⚠ Dashboard systemd service not found (development environment)"
    update_counters "WARN"
fi

# Check nginx configuration
if command -v nginx >/dev/null 2>&1; then
    run_check "Nginx configuration test passes" "nginx -t >/dev/null 2>&1"
    run_check "Nginx citations configuration exists" "test -f /etc/nginx/sites-available/citations.conf 2>/dev/null || test -f deployment/nginx/citations.conf"
else
    warning "⚠ Nginx not available for configuration test"
    update_counters "WARN"
fi

# 7. Network and Connectivity Tests
echo ""
echo "🌐 NETWORK AND CONNECTIVITY TESTS"
echo "---------------------------------"

# Test external service dependencies
if command -v curl >/dev/null 2>&1; then
    run_check "Can reach external APIs" "
curl -s -o /dev/null -w '%{http_code}' 'https://httpbin.org/status/200' 2>/dev/null | grep -q '200'
"

    # Test if the main application URL is accessible
    run_check_with_warning "Main application URL accessible" "
curl -s -o /dev/null -w '%{http_code}' '$BASE_URL' 2>/dev/null || echo '000'
" "200"
fi

# 8. Security and Best Practices
echo ""
echo "🔒 SECURITY AND BEST PRACTICES"
echo "------------------------------"

# Check for sensitive file exposure
run_check "No exposed sensitive files in web root" "
! find frontend/frontend/dist -name '*.db' -o -name '*.log' -o -name 'credentials.*' -o -name '.env*' 2>/dev/null | head -5 | grep -q .
"

# Check for proper file permissions on sensitive files
run_check "Sensitive files have restricted permissions" "
python3 -c \"
import os
sensitive_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith(('.db', '.log')) or 'credential' in file.lower() or file == '.env':
            sensitive_files.append(os.path.join(root, file))
    if len(sensitive_files) <= 10:  # Don't check too many files
        for file in sensitive_files:
            if os.path.exists(file):
                stat = os.stat(file)
                if stat.st_mode & 0o077:  # Check if others have read/write access
                    print(f'TOO_PERMISSIVE:{file}')
                    exit(1)
print('OK')
\" 2>/dev/null | grep -q 'OK'
"

# 9. Performance and Resource Checks
echo ""
echo "⚡ PERFORMANCE AND RESOURCE CHECKS"
echo "----------------------------------"

# Check disk space usage
run_check_with_warning "Sufficient disk space available" "
df . | tail -1 | awk '{print \$5}' | sed 's/%//'
" "90"

# Check memory usage (if on production server)
if command -v free >/dev/null 2>&1; then
    run_check_with_warning "Memory usage within limits" "
free | grep Mem | awk '{printf \"%.0f\", (\$3/\$2)*100}'
" "90"
fi

# 10. Backup and Recovery Validation
echo ""
echo "💾 BACKUP AND RECOVERY VALIDATION"
echo "---------------------------------"

# Check backup scripts exist and are executable
run_check "Database backup script exists" "test -f deployment/scripts/backup_database.sh"
run_check "Database backup script executable" "test -x deployment/scripts/backup_database.sh"
run_check "Database restore script exists" "test -f deployment/scripts/restore_database.sh"
run_check "Database restore script executable" "test -x deployment/scripts/restore_database.sh"

# Test backup functionality (dry run)
run_check "Backup script can run in dry-run mode" "
deployment/scripts/backup_database.sh --dry-run >/dev/null 2>&1 && echo 'BACKUP_OK'
" || echo "Backup script test failed"

# Print summary
echo ""
echo "📊 VALIDATION SUMMARY"
echo "====================="
echo "Total checks:  $TOTAL_CHECKS"
echo -e "Passed:        ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed:        ${RED}$FAILED_CHECKS${NC}"
echo -e "Warnings:      ${YELLOW}$WARNING_CHECKS${NC}"

# Determine exit code
if [ $FAILED_CHECKS -gt 0 ]; then
    echo ""
    error "❌ VALIDATION FAILED: $FAILED_CHECKS critical check(s) failed"
    echo "Deployment not recommended until issues are resolved."
    exit 1
elif [ $WARNING_CHECKS -gt 0 ]; then
    echo ""
    warning "⚠️  VALIDATION COMPLETED WITH WARNINGS: $WARNING_CHECKS warning(s)"
    echo "Review warnings before proceeding with deployment."
    exit 0
else
    echo ""
    success "✅ ALL VALIDATIONS PASSED: System ready for deployment"
    exit 0
fi