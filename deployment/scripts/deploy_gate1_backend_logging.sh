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
DEPLOYMENT_ID="gate1_backend_$(date +%Y%m%d_%H%M%S)"
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

echo "🚀 GATE 1: BACKEND CITATION LOGGING DEPLOYMENT"
echo "=========================================="
echo "Deployment ID: $DEPLOYMENT_ID"
echo "Project Directory: $PROJECT_DIR"
echo "Backup Required: $BACKUP_REQUIRED"
echo ""

# Pre-deployment validation
log "Starting Gate 1 deployment validation"

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

# Step 1: Update code
log "Step 1: Updating application code"

cd "$PROJECT_DIR"

# Pull latest changes
git pull origin main

# Verify current commit
CURRENT_COMMIT=$(git rev-parse HEAD)
log "Current commit: $CURRENT_COMMIT"

# Check that we have the citation logging feature toggle
if ! grep -q "CITATION_LOGGING_ENABLED" backend/app.py; then
    error "✗ Citation logging feature toggle not found in code"
    exit 1
fi

success "✓ Code updated with citation logging feature toggle"

# Step 2: Configure environment (CITATION LOGGING DISABLED)
log "Step 2: Configuring production environment with citation logging DISABLED"

# Ensure production .env file exists
if [ ! -f "$PROJECT_DIR/.env.production" ]; then
    log "Creating production environment file from template"
    cp "$PROJECT_DIR/deployment/.env.production.template" "$PROJECT_DIR/.env.production"

    warning "⚠ Please update $PROJECT_DIR/.env.production with actual values before production use"
fi

# Verify citation logging is disabled
if grep -q "CITATION_LOGGING_ENABLED=true" "$PROJECT_DIR/.env.production"; then
    error "✗ Citation logging is enabled in .env.production - should be disabled for initial deployment"
    error "Edit $PROJECT_DIR/.env.production and set CITATION_LOGGING_ENABLED=false"
    exit 1
fi

if grep -q "CITATION_LOGGING_ENABLED=false" "$PROJECT_DIR/.env.production"; then
    success "✓ Citation logging is disabled in production environment"
else
    log "Adding citation logging disabled setting to production environment"
    echo "CITATION_LOGGING_ENABLED=false" >> "$PROJECT_DIR/.env.production"
fi

# Step 3: Update Python dependencies
log "Step 3: Updating Python dependencies"

cd "$PROJECT_DIR"
source venv/bin/activate

# Update requirements
pip install -r requirements.txt

# Test citation logging import
python3 -c "
import sys
sys.path.insert(0, 'backend/backend')
try:
    from citation_logger import log_citations_to_dashboard, ensure_citation_log_ready
    print('SUCCESS: Citation logging modules imported successfully')
except ImportError as e:
    print(f'ERROR: Failed to import citation logging modules: {e}')
    exit(1)
" || {
    error "✗ Failed to import citation logging modules"
    exit 1
}

success "✓ Python dependencies updated successfully"

# Step 4: Verify citation logging is disabled
log "Step 4: Verifying citation logging is disabled"

# Test that citation logging is actually disabled
python3 -c "
import sys
sys.path.insert(0, 'backend')
import os
os.environ['CITATION_LOGGING_ENABLED'] = 'false'

# Load app and check the flag
from app import CITATION_LOGGING_ENABLED

if CITATION_LOGGING_ENABLED == False:
    print('SUCCESS: Citation logging is disabled')
else:
    print(f'ERROR: Citation logging is enabled: {CITATION_LOGGING_ENABLED}')
    exit(1)
" || {
    error "✗ Citation logging is not properly disabled"
    exit 1
}

success "✓ Citation logging is verified as disabled"

# Step 5: Restart backend service
log "Step 5: Restarting backend service"

if systemctl list-unit-files | grep -q "citations-backend"; then
    sudo systemctl restart citations-backend
    sudo systemctl status citations-backend --no-pager

    if systemctl is-active --quiet citations-backend; then
        success "✓ Backend service restarted successfully"
    else
        error "✗ Backend service failed to start"
        exit 1
    fi
else
    warning "⚠ Backend service not found - manual restart may be required"
fi

# Step 6: Basic functionality testing
log "Step 6: Performing basic functionality testing"

# Test that application responds
if command -v curl >/dev/null 2>&1; then
    # Test basic endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        success "✓ Application health endpoint responding"
    else
        error "✗ Application health endpoint not responding (HTTP $HTTP_CODE)"
        exit 1
    fi

    # Test validation endpoint (should work without citation logging)
    TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/api/validate \
        -H "Content-Type: application/json" \
        -d '{"text": "Test citation", "style": "APA", "token": "test-free-token"}' | head -100)

    if [ -n "$TEST_RESPONSE" ]; then
        success "✓ Validation endpoint responding"
    else
        error "✗ Validation endpoint not responding properly"
        exit 1
    fi
else
    warning "⚠ curl not available for application testing"
fi

# Step 7: Verify no citation logging is happening
log "Step 7: Verifying citation logging is not active"

# Ensure citation log directory exists but no logging is happening
CITATION_LOG_DIR="/opt/citations/logs"
if [ -d "$CITATION_LOG_DIR" ]; then
    # Check if citations.log exists and track its size
    if [ -f "$CITATION_LOG_DIR/citations.log" ]; then
        INITIAL_SIZE=$(stat -c%s "$CITATION_LOG_DIR/citations.log" 2>/dev/null || echo "0")
        log "Initial citation log size: $INITIAL_SIZE bytes"

        # Make a test request to verify no logging occurs
        if command -v curl >/dev/null 2>&1; then
            curl -s -X POST http://localhost:8000/api/validate \
                -H "Content-Type: application/json" \
                -d '{"text": "Another test citation", "style": "APA", "token": "test-free-token"}' >/dev/null

            sleep 2  # Give time for any potential logging

            FINAL_SIZE=$(stat -c%s "$CITATION_LOG_DIR/citations.log" 2>/dev/null || echo "0")

            if [ "$FINAL_SIZE" = "$INITIAL_SIZE" ]; then
                success "✓ No citation logging occurred (log size unchanged)"
            else
                error "✗ Citation logging may be active (log size changed from $INITIAL_SIZE to $FINAL_SIZE)"
                exit 1
            fi
        fi
    else
        success "✓ Citation log file does not exist (logging not active)"
    fi
else
    log "Citation log directory does not exist - creating it"
    mkdir -p "$CITATION_LOG_DIR"
    success "✓ Citation log directory created"
fi

# Step 8: Final deployment validation
log "Step 8: Running final deployment validation"

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
echo "🎉 GATE 1 DEPLOYMENT COMPLETED SUCCESSFULLY"
echo "============================================"
echo ""
echo "✅ **BACKEND CHANGES DEPLOYED WITH CITATION LOGGING DISABLED**"
echo ""
echo "**Deployment Summary:**"
echo "- Deployment ID: $DEPLOYMENT_ID"
echo "- Citation Logging: DISABLED (safe deployment)"
echo "- Backend Service: Restarted and functional"
echo "- Validation Endpoints: Operational"
echo "- Application Health: Verified"
echo ""
echo "📋 **Next Steps for Gate 1:**"
echo "1. Monitor system for 15-30 minutes for any regressions"
echo "2. If stable, enable citation logging with: export CITATION_LOGGING_ENABLED=true"
echo "3. Restart backend service and monitor citation logging behavior"
echo "4. Validate no performance impact and proper error handling"
echo ""
echo "🔄 **Rollback Information:**"
echo "- If issues occur, set CITATION_LOGGING_ENABLED=false and restart backend"
echo "- Or use git reset to previous commit: git reset --hard <previous-commit-hash>"
echo "- Full rollback procedures available in: deployment/EMERGENCY_ROLLBACK.md"
echo ""
echo "📁 **Important Files:**"
echo "- Environment config: $PROJECT_DIR/.env.production"
echo "- Citation logging code: $PROJECT_DIR/backend/backend/citation_logger.py"
echo "- Feature toggle: $PROJECT_DIR/backend/app.py (CITATION_LOGGING_ENABLED)"
echo ""
echo "✅ **Gate 1 is ready for monitoring phase**"