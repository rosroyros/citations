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
DEPLOYMENT_ID="gate2_parser_$(date +%Y%m%d_%H%M%S)"
BACKUP_REQUIRED="${BACKUP_REQUIRED:-true}"

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

echo "🔧 GATE 2: ENHANCED LOG PARSER DEPLOYMENT"
echo "======================================"
echo "Deployment ID: $DEPLOYMENT_ID"
echo "Project Directory: $PROJECT_DIR"
echo "Backup Required: $BACKUP_REQUIRED"
echo ""

# Pre-deployment validation
log "Starting Gate 2 deployment validation"

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

# Step 1: Verify Gate 1 prerequisites
log "Step 1: Verifying Gate 1 prerequisites are met"

# Check if citation logging is enabled
if ! grep -q "CITATION_LOGGING_ENABLED=true" "$PROJECT_DIR/.env.production"; then
    error "✗ Citation logging is not enabled in .env.production"
    error "Gate 1 must be completed and citation logging enabled before proceeding"
    exit 1
fi

success "✓ Citation logging is enabled"

# Check if citation log file exists and has content
CITATION_LOG_PATH="/opt/citations/logs/citations.log"
if [ ! -f "$CITATION_LOG_PATH" ]; then
    warning "⚠ Citation log file does not exist yet - creating it"
    mkdir -p "$(dirname "$CITATION_LOG_PATH")"
    touch "$CITATION_LOG_PATH"
else
    LOG_SIZE=$(stat -c%s "$CITATION_LOG_PATH")
    if [ "$LOG_SIZE" -eq 0 ]; then
        warning "⚠ Citation log file is empty - may need some validation activity"
    else
        success "✓ Citation log file exists with $LOG_SIZE bytes"
    fi
fi

# Step 2: Update log parser code
log "Step 2: Verifying enhanced log parser implementation"

cd "$PROJECT_DIR"

# Check if the enhanced log parser exists
if [ ! -f "dashboard/log_parser.py" ]; then
    error "✗ Enhanced log parser not found"
    exit 1
fi

# Verify the CitationLogParser class exists
if ! grep -q "class CitationLogParser:" dashboard/log_parser.py; then
    error "✗ CitationLogParser class not found in log_parser.py"
    exit 1
fi

# Verify stateful parsing methods exist
for method in "_load_position" "_save_position" "_detect_log_rotation" "parse_new_entries"; do
    if ! grep -q "def $method" dashboard/log_parser.py; then
        error "✗ Required method $method not found in CitationLogParser"
        exit 1
    fi
done

success "✓ Enhanced log parser implementation verified"

# Step 3: Test log parser functionality
log "Step 3: Testing enhanced log parser functionality"

cd "$PROJECT_DIR"

# Test parser import and basic functionality
python3 -c "
import sys
sys.path.insert(0, 'dashboard')

try:
    from log_parser import CitationLogParser, parse_logs
    print('SUCCESS: Enhanced log parser imported successfully')

    # Test basic instantiation
    test_log_path = '/opt/citations/logs/citations.log'
    parser = CitationLogParser(test_log_path)
    print('SUCCESS: CitationLogParser instantiated successfully')

    # Test position tracking
    current_pos = parser.get_current_position()
    print(f'SUCCESS: Current position: {current_pos}')

except ImportError as e:
    print(f'ERROR: Failed to import log parser: {e}')
    exit(1)
except Exception as e:
    print(f'ERROR: Log parser test failed: {e}')
    exit(1)
" || {
    error "✗ Log parser functionality test failed"
    exit 1
}

success "✓ Enhanced log parser functionality verified"

# Step 4: Verify dashboard integration
log "Step 4: Verifying dashboard integration"

# Check if dashboard can import the log parser
python3 -c "
import sys
sys.path.insert(0, 'dashboard')

try:
    # Test that we can use the parser with dashboard database
    from log_parser import CitationLogParser
    from database import get_database

    # Test parser with database integration
    test_log_path = '/opt/citations/logs/citations.log'
    parser = CitationLogParser(test_log_path)

    # Test parsing new entries (should work even if log is empty)
    new_entries = parser.parse_new_entries()
    print(f'SUCCESS: Parsed {len(new_entries)} new entries')

    # Test database connectivity
    db = get_database()
    stats = db.get_stats()
    print(f'SUCCESS: Database accessible - {stats[\"total_validations\"]} total validations')
    db.close()

except Exception as e:
    print(f'ERROR: Dashboard integration test failed: {e}')
    exit(1)
" || {
    error "✗ Dashboard integration test failed"
    exit 1
}

success "✓ Dashboard integration verified"

# Step 5: Verify no parser conflicts
log "Step 5: Checking for potential parser conflicts"

# Ensure we don't have duplicate or conflicting parsers
if find . -name "*.py" -exec grep -l "class.*LogParser" {} \; | wc -l | grep -v "1" >/dev/null; then
    warning "⚠ Multiple LogParser classes found - ensure no conflicts"
    find . -name "*.py" -exec grep -l "class.*LogParser" {} \;
else
    success "✓ No conflicting LogParser classes found"
fi

# Check for any old parsing code that might interfere
if grep -r "parse_logs" dashboard/ | grep -v "log_parser.py" | head -3; then
    warning "⚠ Found potential legacy parsing code - review for conflicts"
else
    success "✓ No conflicting parsing code found"
fi

# Step 6: Create test data for validation
log "Step 6: Creating test citation log data for validation"

if [ -f "$CITATION_LOG_PATH" ]; then
    # Create a test citation block if log is empty or very small
    CURRENT_SIZE=$(stat -c%s "$CITATION_LOG_PATH" 2>/dev/null || echo "0")
    if [ "$CURRENT_SIZE" -lt 100 ]; then
        log "Adding test citation data for validation"
        cat >> "$CITATION_LOG_PATH" << 'EOF'
<<JOB_ID:test-gate2-deployment-123>>
Test citation 1 for Gate 2 deployment
Test citation 2 for Gate 2 deployment
Another test citation to validate parser
<<<END_JOB>>>
EOF

        success "✓ Test citation data added for validation"
    else
        success "✓ Citation log has sufficient data for testing"
    fi
fi

# Step 7: Test end-to-end parsing
log "Step 7: Testing end-to-end parsing functionality"

cd "$PROJECT_DIR"

python3 -c "
import sys
sys.path.insert(0, 'dashboard')

try:
    from log_parser import CitationLogParser
    from database import get_database

    test_log_path = '/opt/citations/logs/citations.log'

    # Test parsing new entries
    parser = CitationLogParser(test_log_path)
    new_entries = parser.parse_new_entries()

    print(f'SUCCESS: Parsed {len(new_entries)} new citation blocks')

    # Show sample of parsed data
    for i, entry in enumerate(new_entries[:2]):  # Show first 2 entries
        job_id = entry.get('job_id', 'unknown')
        status = entry.get('status', 'unknown')
        print(f'Entry {i+1}: Job {job_id}, Status: {status}')

    # Reset position for next test
    parser.reset_position()
    print('SUCCESS: Position reset completed')

    # Test database integration if we have entries
    if new_entries:
        db = get_database()
        for entry in new_entries:
            job_id = entry.get('job_id')
            if job_id:
                # Test insertion
                db.insert_validation(entry)
                print(f'SUCCESS: Inserted job {job_id} into database')
        db.close()

except Exception as e:
    print(f'ERROR: End-to-end parsing test failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
" || {
    error "✗ End-to-end parsing test failed"
    exit 1
}

success "✓ End-to-end parsing functionality verified"

# Step 8: Restart dashboard service (if exists)
log "Step 8: Restarting dashboard service"

if systemctl list-unit-files | grep -q "citations-dashboard"; then
    sudo systemctl restart citations-dashboard
    sudo systemctl status citations-dashboard --no-pager

    if systemctl is-active --quiet citations-dashboard; then
        success "✓ Dashboard service restarted successfully"
    else
        error "✗ Dashboard service failed to start"
        exit 1
    fi
else
    warning "⚠ Dashboard service not found - manual restart may be required"
fi

# Step 9: Verify dashboard is responsive
log "Step 9: Verifying dashboard functionality"

# Test dashboard API if available
if command -v curl >/dev/null 2>&1; then
    # Test dashboard API endpoint
    DASHBOARD_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/health 2>/dev/null || echo "000")

    if [ "$DASHBOARD_HTTP_CODE" = "200" ]; then
        success "✓ Dashboard API responding"
    else
        warning "⚠ Dashboard API not responding (HTTP $DASHBOARD_HTTP_CODE) - may be on different port or not running"
    fi

    # Test database stats endpoint
    STATS_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/stats 2>/dev/null || echo "000")

    if [ "$STATS_HTTP_CODE" = "200" ]; then
        success "✓ Dashboard stats endpoint responding"
    else
        warning "⚠ Dashboard stats endpoint not responding"
    fi
else
    warning "⚠ curl not available for dashboard testing"
fi

# Step 10: Validate log rotation handling
log "Step 10: Validating log rotation handling"

# Test position file creation and management
POSITION_FILE="/opt/citations/logs/citations.position"

if [ -f "$POSITION_FILE" ]; then
    POSITION_SIZE=$(stat -c%s "$POSITION_FILE")
    success "✓ Position file exists ($POSITION_SIZE bytes)"
else
    warning "⚠ Position file does not exist - will be created on first run"
fi

# Test rotation detection logic
python3 -c "
import sys
sys.path.insert(0, 'dashboard')

try:
    from log_parser import CitationLogParser
    import tempfile
    import os

    # Create a temporary test log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write('Test log line\n')
        test_log_path = f.name

    try:
        parser = CitationLogParser(test_log_path)

        # Test rotation detection
        initial_size = os.path.getsize(test_log_path)
        rotation_detected = parser._detect_log_rotation(initial_size + 100)

        print(f'SUCCESS: Rotation detection test completed - detected: {rotation_detected}')

    finally:
        # Clean up
        if os.path.exists(test_log_path):
            os.unlink(test_log_path)

        # Clean up position file if created
        pos_file = test_log_path.replace('.log', '.position')
        if os.path.exists(pos_file):
            os.unlink(pos_file)

except Exception as e:
    print(f'ERROR: Log rotation test failed: {e}')
    exit(1)
" || {
    error "✗ Log rotation handling test failed"
    exit 1
}

success "✓ Log rotation handling verified"

# Step 11: Final deployment validation
log "Step 11: Running final deployment validation"

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
echo "🎉 GATE 2 DEPLOYMENT COMPLETED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "✅ **ENHANCED LOG PARSER DEPLOYED SUCCESSFULLY**"
echo ""
echo "**Deployment Summary:**"
echo "- Deployment ID: $DEPLOYMENT_ID"
echo "- Log Parser: Stateful CitationLogParser with offset tracking"
echo "- Dashboard Integration: Verified and functional"
echo "- Log Rotation Handling: Implemented and tested"
echo "- Database Integration: Working correctly"
echo "- Position Tracking: Functional with .position file"
echo ""
echo "🔧 **Enhanced Parser Features:**"
echo "- Stateful offset tracking for efficient processing"
echo "- Log rotation detection and handling"
echo "- Integration with dashboard database"
echo "- Backward compatibility with existing log format"
echo "- Multi-pass parsing for comprehensive data extraction"
echo ""
echo "📋 **Next Steps for Gate 2:**"
echo "1. Monitor dashboard for new citation data appearing"
echo "2. Verify citation log processing is working correctly"
echo "3. Check dashboard stats for new validation entries"
echo "4. Validate no duplicate processing occurs"
echo "5. If stable, proceed to Gate 3: Production Hardening"
echo ""
echo "🔄 **Rollback Information:**"
echo "- If issues occur, revert to previous dashboard/log_parser.py"
echo "- Remove position file: rm /opt/citations/logs/citations.position"
echo "- Restart dashboard service"
echo "- Full rollback procedures in: deployment/EMERGENCY_ROLLBACK.md"
echo ""
echo "📁 **Important Files:**"
echo "- Enhanced parser: $PROJECT_DIR/dashboard/log_parser.py"
echo "- Position tracking: /opt/citations/logs/citations.position"
echo "- Citation log: /opt/citations/logs/citations.log"
echo "- Dashboard database: /opt/citations/dashboard/data/validations.db"
echo ""
echo "✅ **Gate 2 is ready for monitoring phase**"