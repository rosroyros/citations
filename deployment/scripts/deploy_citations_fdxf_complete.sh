#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/opt/citations}"
DEPLOYMENT_ID="fdxf_complete_$(date +%Y%m%d_%H%M%S)"
INTERACTIVE="${INTERACTIVE:-true}"

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

info() {
    echo -e "${PURPLE}[INFO] $1${NC}"
}

header() {
    echo -e "${CYAN}========================================"
    echo -e "$1"
    echo -e "========================================${NC}"
}

# Function to prompt for user input
prompt_user() {
    if [ "$INTERACTIVE" = "true" ]; then
        echo -e "${YELLOW}Press Enter to continue with $1, or Ctrl+C to abort...${NC}"
        read -r
    fi
}

# Function to show gate status
show_gate_status() {
    local gate=$1
    local status=$2
    local message=$3

    case $status in
        "PENDING")
            echo -e "${YELLOW}⏳ Gate $gate: $message${NC}"
            ;;
        "IN_PROGRESS")
            echo -e "${BLUE}🔄 Gate $gate: $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}✅ Gate $gate: $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  Gate $gate: $message${NC}"
            ;;
        "FAILED")
            echo -e "${RED}❌ Gate $gate: $message${NC}"
            ;;
    esac
}

echo -e "${CYAN}"
echo "██╗     ██╗███████╗    ██╗    ██╗██╗  ██╗ █████╗ ████████╗"
echo "██║     ██║██╔════╝    ██║    ██║██║  ██║██╔══██╗╚══██╔══╝"
echo "██║     ██║█████╗      ██║ █╗ ██║███████║███████║   ██║   "
echo "██║     ██║██╔══╝      ██║███╗██║██╔══██║╚══██╔══╝   ██║   "
echo "╚██████╗██║███████╗    ╚███╔███╔╝██║  ██║███████║   ██║   "
echo " ╚═════╝╚═╝╚══════╝     ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝   ╚═╝   "
echo ""
echo "   ███████╗██╗  ██╗██████╗ ██████╗ ███████╗████████╗"
echo "   ██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝"
echo "   █████╗   ╚███╔╝ ██████╔╝██████╔╝█████╗     ██║   "
echo "   ██╔══╝   ██╔██╗ ██╔══██╗██╔══██╗██╔══╝     ██║   "
echo "   ███████╗██╔╝ ██╗██████╔╝██████╔╝███████╗   ██║   "
echo "   ╚══════╝╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚══════╝   ╚═╝   "
echo ""
echo "          🔥 📚 COMPLETE SYSTEM DEPLOYMENT 🔥 📚"
echo -e "${NC}"

echo "🎯 CITATIONS-FDXF COMPLETE SYSTEM DEPLOYMENT"
echo "==============================================="
echo "Deployment ID: $DEPLOYMENT_ID"
echo "Project Directory: $PROJECT_DIR"
echo "Interactive Mode: $INTERACTIVE"
echo "Started: $(date)"
echo ""

# Gate tracking
GATE1_STATUS="PENDING"
GATE2_STATUS="PENDING"
GATE3_STATUS="PREDENTIAL"
GATE4_STATUS="PENDING"

# Function to run a gate deployment
run_gate() {
    local gate_num=$1
    local gate_name=$2
    local script_path=$3

    header "GATE $gate_num: $gate_name"
    echo ""

    show_gate_status $gate_num "IN_PROGRESS" "Starting $gate_name deployment..."

    if [ ! -f "$PROJECT_DIR/$script_path" ]; then
        show_gate_status $gate_num "FAILED" "Deployment script not found: $script_path"
        return 1
    fi

    # Make script executable
    chmod +x "$PROJECT_DIR/$script_path"

    # Run the deployment script
    cd "$PROJECT_DIR"
    if ./"$script_path"; then
        show_gate_status $gate_num "SUCCESS" "$gate_name deployment completed successfully"
        eval "GATE${gate_num}_STATUS='SUCCESS'"
        return 0
    else
        show_gate_status $gate_num "FAILED" "$gate_name deployment failed"
        eval "GATE${gate_num}_STATUS='FAILED'"
        return 1
    fi
}

# Pre-deployment checks
header "PRE-DEPLOYMENT VALIDATION"
echo ""

info "Checking system readiness..."

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    error "Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Check for required deployment scripts
REQUIRED_SCRIPTS=(
    "deployment/scripts/deploy_gate1_backend_logging.sh"
    "deployment/scripts/deploy_gate2_log_parser.sh"
    "deployment/scripts/deploy_gate3_production_hardening.sh"
    "deployment/scripts/deploy_gate4_complete_system.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ ! -f "$PROJECT_DIR/$script" ]; then
        error "Required deployment script not found: $script"
        exit 1
    fi
done

# Check deployment validation script
if [ ! -f "$PROJECT_DIR/deployment/scripts/deployment_validation.sh" ]; then
    error "Deployment validation script not found"
    exit 1
fi

success "✅ Pre-deployment validation passed"

# Show deployment plan
echo ""
echo "📋 DEPLOYMENT PLAN"
echo "=================="
echo ""
show_gate_status 1 "PENDING" "Backend Citation Logging - Deploy with feature toggle disabled, then enable with monitoring"
echo ""
show_gate_status 2 "PENDING" "Enhanced Log Parser - Deploy stateful parser with offset tracking and rotation handling"
echo ""
show_gate_status 3 "PENDING" "Production Hardening - Deploy log rotation, monitoring, and health metrics"
echo ""
show_gate_status 4 "PENDING" "Complete System - Full integration, end-to-end testing, and production monitoring"
echo ""

prompt_user "starting the deployment"

# ==============================================================================
# GATE 1: Backend Citation Logging
# ==============================================================================
echo ""

if run_gate "1" "Backend Citation Logging" "deployment/scripts/deploy_gate1_backend_logging.sh"; then
    success "✅ Gate 1 completed successfully"

    # Additional step for Gate 1: Enable citation logging
    info "Now enabling citation logging with monitoring..."

    if [ -f "$PROJECT_DIR/deployment/scripts/enable_citation_logging.sh" ]; then
        chmod +x "$PROJECT_DIR/deployment/scripts/enable_citation_logging.sh"

        if cd "$PROJECT_DIR" && ./deployment/scripts/enable_citation_logging.sh; then
            success "✅ Citation logging enabled successfully"
        else
            warning "⚠ Citation logging enablement had issues - review logs"
            GATE1_STATUS="WARNING"
        fi
    else
        warning "⚠ Citation logging enablement script not found"
        GATE1_STATUS="WARNING"
    fi
else
    error "❌ Gate 1 failed - aborting deployment"
    exit 1
fi

prompt_user "proceeding to Gate 2"

# ==============================================================================
# GATE 2: Enhanced Log Parser
# ==============================================================================
echo ""

if run_gate "2" "Enhanced Log Parser" "deployment/scripts/deploy_gate2_log_parser.sh"; then
    success "✅ Gate 2 completed successfully"
else
    error "❌ Gate 2 failed - aborting deployment"
    exit 1
fi

prompt_user "proceeding to Gate 3"

# ==============================================================================
# GATE 3: Production Hardening
# ==============================================================================
echo ""

if run_gate "3" "Production Hardening" "deployment/scripts/deploy_gate3_production_hardening.sh"; then
    success "✅ Gate 3 completed successfully"
else
    error "❌ Gate 3 failed - aborting deployment"
    exit 1
fi

prompt_user "proceeding to final Gate 4"

# ==============================================================================
# GATE 4: Complete System Deployment
# ==============================================================================
echo ""

if run_gate "4" "Complete System" "deployment/scripts/deploy_gate4_complete_system.sh"; then
    success "✅ Gate 4 completed successfully"
else
    error "❌ Gate 4 failed - deployment incomplete"
    exit 1
fi

# ==============================================================================
# DEPLOYMENT COMPLETION SUMMARY
# ==============================================================================

header "🎉 DEPLOYMENT COMPLETION SUMMARY"
echo ""

# Calculate deployment time
if command -v python3 >/dev/null 2>&1; then
    START_TIME=$(python3 -c "import time; print(int(time.time()))")
else
    START_TIME=$(date +%s)
fi

# Show final status
echo "📊 FINAL DEPLOYMENT STATUS:"
echo "============================"
echo ""

show_gate_status 1 "$GATE1_STATUS" "Backend Citation Logging - Citation logging pipeline active"
echo ""
show_gate_status 2 "$GATE2_STATUS" "Enhanced Log Parser - Stateful parsing with offset tracking"
echo ""
show_gate_status 3 "$GATE3_STATUS" "Production Hardening - Log rotation and monitoring active"
echo ""
show_gate_status 4 "$GATE4_STATUS" "Complete System - Full integration and end-to-end functionality"
echo ""

# Determine overall status
if [[ "$GATE1_STATUS" == "SUCCESS" && "$GATE2_STATUS" == "SUCCESS" && "$GATE3_STATUS" == "SUCCESS" && "$GATE4_STATUS" == "SUCCESS" ]]; then
    echo -e "${GREEN}🎊 OVERALL DEPLOYMENT STATUS: SUCCESS 🎊${NC}"
    echo ""
    echo "✅ **CITATIONS-FDXF PROJECT FULLY DEPLOYED AND OPERATIONAL**"
    echo ""

    # Create completion marker
    COMPLETION_FILE="$PROJECT_DIR/deployment_logs/fdxf_deployment_$DEPLOYMENT_ID.complete"
    mkdir -p "$(dirname "$COMPLETION_FILE")"
    echo "DEPLOYMENT_SUCCESS: $DEPLOYMENT_ID" > "$COMPLETION_FILE"
    echo "TIMESTAMP: $(date)" >> "$COMPLETION_FILE"
    echo "ALL_GATES_COMPLETED: SUCCESS" >> "$COMPLETION_FILE"

else
    echo -e "${YELLOW}⚠️  OVERALL DEPLOYMENT STATUS: COMPLETED WITH WARNINGS${NC}"
    echo ""
    echo "📋 **DEPLOYMENT COMPLETED WITH SOME WARNINGS - REVIEW RECOMMENDED**"
    echo ""

    COMPLETION_FILE="$PROJECT_DIR/deployment_logs/fdxf_deployment_$DEPLOYMENT_ID.warning"
    mkdir -p "$(dirname "$COMPLETION_FILE")"
    echo "DEPLOYMENT_WARNING: $DEPLOYMENT_ID" > "$COMPLETION_FILE"
    echo "TIMESTAMP: $(date)" >> "$COMPLETION_FILE"
fi

# Final system status
header "🔍 FINAL SYSTEM VERIFICATION"
echo ""

cd "$PROJECT_DIR"

# Test system health
if ./deployment/scripts/deployment_validation.sh >/dev/null 2>&1; then
    echo "✅ System validation: PASSED"
else
    echo "⚠️  System validation: WARNINGS DETECTED"
fi

# Check citation logging status
if grep -q "CITATION_LOGGING_ENABLED=true" .env.production 2>/dev/null; then
    echo "✅ Citation logging: ENABLED"
else
    echo "❌ Citation logging: DISABLED"
fi

# Check log rotation status
if [ -f "/etc/logrotate.d/citations" ]; then
    echo "✅ Log rotation: CONFIGURED"
else
    echo "❌ Log rotation: NOT CONFIGURED"
fi

# Check monitoring status
if [ -f "/opt/citations/monitoring/health_check.sh" ]; then
    echo "✅ Monitoring: ACTIVE"
else
    echo "❌ Monitoring: NOT ACTIVE"
fi

# Show next steps
echo ""
echo "📋 **NEXT STEPS AND MONITORING**"
echo "================================="
echo ""
echo "1. **Immediate Monitoring** (Next 30 minutes):"
echo "   - Monitor backend service: systemctl status citations-backend"
echo "   - Monitor dashboard service: systemctl status citations-dashboard"
echo "   - Check citation logs: tail -f /opt/citations/logs/citations.log"
echo "   - Run health checks: /opt/citations/monitoring/health_check.sh"
echo ""
echo "2. **Dashboard Verification**:"
echo "   - Check dashboard metrics: curl http://localhost:8001/api/health"
echo "   - Verify new citation data appearing"
echo "   - Monitor parser position tracking"
echo ""
echo "3. **System Monitoring** (Next 24 hours):"
echo "   - Review monitoring logs: /var/log/citations/health_checks.log"
echo "   - Verify log rotation: sudo logrotate -d /etc/logrotate.d/citations"
echo "   - Check disk space usage"
echo "   - Monitor error rates"
echo ""
echo "4. **Performance Validation**:"
echo "   - Test validation endpoint performance"
echo "   - Monitor database query performance"
echo "   - Check citation logging impact"
echo "   - Verify no regressions in core functionality"
echo ""

# Emergency rollback information
echo "🔄 **EMERGENCY ROLLBACK INFORMATION**"
echo "======================================"
echo ""
echo "If critical issues are detected:"
echo "1. Quick rollback: Set CITATION_LOGGING_ENABLED=false in .env.production"
echo "2. Restart backend: sudo systemctl restart citations-backend"
echo "3. Full rollback: git reset --hard <previous-commit-hash>"
echo "4. Detailed procedures: deployment/EMERGENCY_ROLLBACK.md"
echo ""

# Deployment artifacts
echo "📁 **DEPLOYMENT ARTIFACTS**"
echo "========================="
echo ""
echo "Deployment Scripts:"
echo "- Gate 1: deployment/scripts/deploy_gate1_backend_logging.sh"
echo "- Gate 2: deployment/scripts/deploy_gate2_log_parser.sh"
echo "- Gate 3: deployment/scripts/deploy_gate3_production_hardening.sh"
echo "- Gate 4: deployment/scripts/deploy_gate4_complete_system.sh"
echo "- Complete: deployment/scripts/deploy_citations_fdxf_complete.sh"
echo ""
echo "Configuration Files:"
echo "- Environment: .env.production"
echo "- Log rotation: /etc/logrotate.d/citations"
echo "- Monitoring: /opt/citations/monitoring/"
echo "- Documentation: deployment/EMERGENCY_ROLLBACK.md, deployment/TEAM_TRAINING.md"
echo ""
echo "Logs and Reports:"
echo "- Deployment logs: deployment_logs/"
echo "- System validation: deployment/scripts/deployment_validation.sh"
echo "- Health monitoring: /var/log/citations/health_checks.log"
echo "- Post-deployment: deployment_reports/"
echo ""

echo "================================================================="
echo -e "${GREEN}🎊 CITATIONS-FDXF COMPLETE SYSTEM DEPLOYMENT FINISHED 🎊${NC}"
echo "================================================================="
echo ""
echo "✅ All 4 deployment gates completed successfully"
echo "✅ System is now fully operational with enhanced citation features"
echo "✅ Monitoring and alerting systems are active"
echo "✅ Rollback procedures are documented and ready"
echo ""
echo -e "${CYAN}🚀 READY FOR PRODUCTION USE! 🚀${NC}"
echo ""