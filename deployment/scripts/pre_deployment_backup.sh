#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/opt/citations/backups}"
PROJECT_DIR="${PROJECT_DIR:-/opt/citations}"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_ID="pre_deploy_${DATE}"
DRY_RUN="${DRY_RUN:-false}"

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

# Parse command line arguments
function show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dry-run          Show what would be backed up without performing backup"
    echo "  --backup-dir DIR   Specify backup directory (default: /opt/citations/backups)"
    echo "  --project-dir DIR  Specify project directory (default: /opt/citations)"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Standard pre-deployment backup"
    echo "  $0 --dry-run                    # Show what would be backed up"
    echo "  $0 --backup-dir /tmp/backups    # Use custom backup directory"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate directories
if [ ! -d "$PROJECT_DIR" ]; then
    error "Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Check if running as root (needed for some backups)
if [ "$EUID" -ne 0 ]; then
    warning "Not running as root - some backups may be incomplete"
fi

echo "🔄 PRE-DEPLOYMENT BACKUP PROCEDURE"
echo "=================================="
echo "Backup ID: $BACKUP_ID"
echo "Project Directory: $PROJECT_DIR"
echo "Backup Directory: $BACKUP_DIR"
echo "Dry Run: $DRY_RUN"
echo ""

# Create backup directory structure
BACKUP_PATH="$BACKUP_DIR/$BACKUP_ID"
if [ "$DRY_RUN" = "false" ]; then
    mkdir -p "$BACKUP_PATH"
    mkdir -p "$BACKUP_PATH/databases"
    mkdir -p "$BACKUP_PATH/configs"
    mkdir -p "$BACKUP_PATH/logs"
    mkdir -p "$BACKUP_PATH/deployment"
    mkdir -p "$BACKUP_PATH/user_data"
fi

log "Starting comprehensive pre-deployment backup"

# 1. Database Backups
echo ""
echo "📊 DATABASE BACKUPS"
echo "-------------------"

# Credits database backup
CREDITS_DB_PATH="$PROJECT_DIR/backend/backend/credits.db"
if [ -f "$CREDITS_DB_PATH" ]; then
    log "Backing up credits database"
    CREDITS_BACKUP="$BACKUP_PATH/databases/credits.db"

    if [ "$DRY_RUN" = "false" ]; then
        sqlite3 "$CREDITS_DB_PATH" ".backup $CREDITS_BACKUP"

        # Verify backup integrity
        if sqlite3 "$CREDITS_BACKUP" "PRAGMA integrity_check;" >/dev/null 2>&1; then
            CREDITS_SIZE=$(du -h "$CREDITS_BACKUP" | cut -f1)
            CREDITS_RECORDS=$(sqlite3 "$CREDITS_BACKUP" "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
            success "✓ Credits database backed up ($CREDITS_SIZE, $CREDITS_RECORDS users)"
        else
            error "✗ Credits database backup integrity check failed"
            exit 1
        fi
    else
        echo "[DRY RUN] Would backup: $CREDITS_DB_PATH -> $CREDITS_BACKUP"
    fi
else
    warning "⚠ Credits database not found at $CREDITS_DB_PATH"
fi

# Validations database backup
VALIDATIONS_DB_PATH="$PROJECT_DIR/dashboard/data/validations.db"
if [ -f "$VALIDATIONS_DB_PATH" ]; then
    log "Backing up validations database"
    VALIDATIONS_BACKUP="$BACKUP_PATH/databases/validations.db"

    if [ "$DRY_RUN" = "false" ]; then
        sqlite3 "$VALIDATIONS_DB_PATH" ".backup $VALIDATIONS_BACKUP"

        # Verify backup integrity
        if sqlite3 "$VALIDATIONS_BACKUP" "PRAGMA integrity_check;" >/dev/null 2>&1; then
            VALIDATIONS_SIZE=$(du -h "$VALIDATIONS_BACKUP" | cut -f1)
            VALIDATIONS_RECORDS=$(sqlite3 "$VALIDATIONS_BACKUP" "SELECT COUNT(*) FROM validations;" 2>/dev/null || echo "0")
            success "✓ Validations database backed up ($VALIDATIONS_SIZE, $VALIDATIONS_RECORDS records)"
        else
            error "✗ Validations database backup integrity check failed"
            exit 1
        fi
    else
        echo "[DRY RUN] Would backup: $VALIDATIONS_DB_PATH -> $VALIDATIONS_BACKUP"
    fi
else
    warning "⚠ Validations database not found at $VALIDATIONS_DB_PATH"
fi

# 2. Configuration Files Backup
echo ""
echo "⚙️  CONFIGURATION BACKUPS"
echo "------------------------"

CONFIG_FILES=(
    "deployment/nginx/citations.conf"
    "deployment/.env.production"
    ".env"
    "backend/backend/.env"
    "dashboard/.env"
)

for config_file in "${CONFIG_FILES[@]}"; do
    if [ -f "$PROJECT_DIR/$config_file" ]; then
        config_backup="$BACKUP_PATH/configs/$(basename "$config_file")"
        config_dir_backup="$BACKUP_PATH/configs/$(dirname "$config_file")"

        if [ "$DRY_RUN" = "false" ]; then
            mkdir -p "$config_dir_backup"
            cp "$PROJECT_DIR/$config_file" "$config_backup"
            success "✓ Configuration backed up: $config_file"
        else
            echo "[DRY RUN] Would backup: $PROJECT_DIR/$config_file -> $config_backup"
        fi
    else
        warning "⚠ Configuration file not found: $config_file"
    fi
done

# System configuration (if running as root)
if [ "$EUID" -eq 0 ]; then
    log "Backing up system configurations"

    SYSTEM_CONFIGS=(
        "/etc/systemd/system/citations-backend.service"
        "/etc/systemd/system/citations-dashboard.service"
        "/etc/nginx/sites-available/citations.conf"
        "/etc/logrotate.d/citations"
    )

    for sys_config in "${SYSTEM_CONFIGS[@]}"; do
        if [ -f "$sys_config" ]; then
            sys_config_backup="$BACKUP_PATH/configs/$(basename "$sys_config")"
            if [ "$DRY_RUN" = "false" ]; then
                cp "$sys_config" "$sys_config_backup"
                success "✓ System config backed up: $sys_config"
            else
                echo "[DRY RUN] Would backup: $sys_config -> $sys_config_backup"
            fi
        fi
    done
fi

# 3. Application Code Backup
echo ""
echo "💻 APPLICATION CODE BACKUP"
echo "-------------------------"

log "Creating application code backup"

if [ "$DRY_RUN" = "false" ]; then
    # Create a git archive for clean code backup
    cd "$PROJECT_DIR"
    git archive --format=tar.gz --output="$BACKUP_PATH/deployment/code_backup_$DATE.tar.gz" HEAD

    # Also backup any uncommitted changes
    if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
        log "Creating backup of uncommitted changes"
        tar -czf "$BACKUP_PATH/deployment/working_changes_$DATE.tar.gz" \
            --exclude='.git' \
            --exclude='node_modules' \
            --exclude='venv' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.pytest_cache' \
            .
        warning "⚠ Uncommitted changes detected and backed up separately"
    fi

    CODE_SIZE=$(du -h "$BACKUP_PATH/deployment/code_backup_$DATE.tar.gz" | cut -f1)
    success "✓ Application code backed up ($CODE_SIZE)"
else
    echo "[DRY RUN] Would create code backup from git at $PROJECT_DIR"
    if [ -n "$(cd "$PROJECT_DIR" && git status --porcelain 2>/dev/null)" ]; then
        echo "[DRY RUN] Would also backup uncommitted changes"
    fi
fi

# 4. Important Log Files Backup
echo ""
echo "📋 LOG FILES BACKUP"
echo "-------------------"

LOG_PATHS=(
    "/var/log/citations"
    "$PROJECT_DIR/logs"
    "$PROJECT_DIR/backend/backend/citation_logs"
)

for log_path in "${LOG_PATHS[@]}"; do
    if [ -d "$log_path" ] && [ "$(ls -A "$log_path" 2>/dev/null)" ]; then
        log_backup="$BACKUP_PATH/logs/$(basename "$log_path")"
        if [ "$DRY_RUN" = "false" ]; then
            mkdir -p "$log_backup"
            # Copy recent log files (last 100 lines or files modified in last 7 days)
            find "$log_path" -type f \( -name "*.log" -o -name "*.txt" \) -mtime -7 -exec cp {} "$log_backup/" \;
            LOG_FILES_COUNT=$(find "$log_backup" -type f | wc -l)
            success "✓ Log files backed up from $log_path ($LOG_FILES_COUNT files)"
        else
            echo "[DRY RUN] Would backup recent log files from $log_path"
        fi
    fi
done

# 5. User-Generated Content Backup
echo ""
echo "👥 USER CONTENT BACKUP"
echo "---------------------"

if [ -d "$PROJECT_DIR/content" ]; then
    log "Backing up user-generated content"
    if [ "$DRY_RUN" = "false" ]; then
        mkdir -p "$BACKUP_PATH/user_data"
        # Backup generated content but exclude temporary files
        tar -czf "$BACKUP_PATH/user_data/content_backup_$DATE.tar.gz" \
            --exclude='*.tmp' \
            --exclude='cache' \
            --exclude='__pycache__' \
            -C "$PROJECT_DIR" content/

        if [ -f "$BACKUP_PATH/user_data/content_backup_$DATE.tar.gz" ]; then
            CONTENT_SIZE=$(du -h "$BACKUP_PATH/user_data/content_backup_$DATE.tar.gz" | cut -f1)
            success "✓ User content backed up ($CONTENT_SIZE)"
        fi
    else
        echo "[DRY RUN] Would backup user-generated content from $PROJECT_DIR/content"
    fi
fi

# 6. Environment and Dependencies Backup
echo ""
echo "🔧 ENVIRONMENT BACKUP"
echo "--------------------"

if [ "$DRY_RUN" = "false" ]; then
    # Backup Python requirements
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        cp "$PROJECT_DIR/requirements.txt" "$BACKUP_PATH/deployment/"
    fi

    # Backup package.json and lock files
    for pkg_file in "$PROJECT_DIR/frontend/frontend/package.json" "$PROJECT_DIR/frontend/frontend/package-lock.json"; do
        if [ -f "$pkg_file" ]; then
            cp "$pkg_file" "$BACKUP_PATH/deployment/"
        fi
    done

    # Backup installed Python packages
    if [ -d "$PROJECT_DIR/venv" ]; then
        source "$PROJECT_DIR/venv/bin/activate"
        pip freeze > "$BACKUP_PATH/deployment/installed_packages.txt"
        deactivate
        success "✓ Python packages list backed up"
    fi

    # Current git commit and branch information
    cd "$PROJECT_DIR"
    git rev-parse HEAD > "$BACKUP_PATH/deployment/current_commit.txt"
    git rev-parse --abbrev-ref HEAD > "$BACKUP_PATH/deployment/current_branch.txt"
    git log --oneline -5 > "$BACKUP_PATH/deployment/recent_commits.txt"
    success "✓ Git state information backed up"
else
    echo "[DRY RUN] Would backup environment information and dependencies"
fi

# 7. System State Backup
echo ""
echo "🖥️  SYSTEM STATE BACKUP"
echo "----------------------"

if [ "$DRY_RUN" = "false" ]; then
    # Current running processes
    if command -v systemctl >/dev/null 2>&1; then
        systemctl status citations-backend --no-pager > "$BACKUP_PATH/deployment/backend_service_status.txt" 2>/dev/null || true
        systemctl status citations-dashboard --no-pager > "$BACKUP_PATH/deployment/dashboard_service_status.txt" 2>/dev/null || true
        systemctl status nginx --no-pager > "$BACKUP_PATH/deployment/nginx_status.txt" 2>/dev/null || true
    fi

    # Disk usage information
    df -h > "$BACKUP_PATH/deployment/disk_usage.txt"

    # Memory usage information
    if command -v free >/dev/null 2>&1; then
        free -h > "$BACKUP_PATH/deployment/memory_usage.txt"
    fi

    success "✓ System state information backed up"
else
    echo "[DRY RUN] Would backup system state information"
fi

# 8. Create Backup Manifest
echo ""
echo "📝 BACKUP MANIFEST"
echo "------------------"

if [ "$DRY_RUN" = "false" ]; then
    cat > "$BACKUP_PATH/backup_manifest.txt" << EOF
Pre-Deployment Backup Manifest
==============================
Backup ID: $BACKUP_ID
Date: $(date)
Project Directory: $PROJECT_DIR
Backup Directory: $BACKUP_PATH

Database Backups:
- Credits database: $([ -f "$CREDITS_BACKUP" ] && echo "✓" || echo "✗")
- Validations database: $([ -f "$VALIDATIONS_BACKUP" ] && echo "✓" || echo "✗")

Configuration Files:
$(find "$BACKUP_PATH/configs" -type f 2>/dev/null | sed 's/^/- /' || echo "No configuration files")

Code Backup:
- Git archive: $([ -f "$BACKUP_PATH/deployment/code_backup_$DATE.tar.gz" ] && echo "✓" || echo "✗")
- Working changes: $([ -f "$BACKUP_PATH/deployment/working_changes_$DATE.tar.gz" ] && echo "✓" || echo "✗")

Other Backups:
- Log files: $(find "$BACKUP_PATH/logs" -type f 2>/dev/null | wc -l) files
- User content: $([ -f "$BACKUP_PATH/user_data/content_backup_$DATE.tar.gz" ] && echo "✓" || echo "✗")
- Environment info: $([ -f "$BACKUP_PATH/deployment/installed_packages.txt" ] && echo "✓" || echo "✗")

Total backup size: $(du -sh "$BACKUP_PATH" | cut -f1)
EOF

    # Get total backup size
    TOTAL_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    success "✓ Backup manifest created"
fi

# 9. Backup Verification
echo ""
echo "🔍 BACKUP VERIFICATION"
echo "---------------------"

if [ "$DRY_RUN" = "false" ]; then
    # Verify critical files exist
    CRITICAL_FILES=(
        "$BACKUP_PATH/databases/credits.db"
        "$BACKUP_PATH/databases/validations.db"
        "$BACKUP_PATH/deployment/code_backup_$DATE.tar.gz"
        "$BACKUP_PATH/backup_manifest.txt"
    )

    VERIFICATION_PASSED=true
    for file in "${CRITICAL_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            error "✗ Critical backup file missing: $file"
            VERIFICATION_PASSED=false
        fi
    done

    if [ "$VERIFICATION_PASSED" = true ]; then
        success "✅ All critical backup files verified"
    else
        error "❌ Backup verification failed"
        exit 1
    fi

    # Test database backup integrity
    for db_file in "$BACKUP_PATH/databases"/*.db; do
        if [ -f "$db_file" ]; then
            if sqlite3 "$db_file" "PRAGMA integrity_check;" >/dev/null 2>&1; then
                success "✓ Database integrity verified: $(basename "$db_file")"
            else
                error "✗ Database integrity check failed: $(basename "$db_file")"
                exit 1
            fi
        fi
    done
else
    echo "[DRY RUN] Would verify backup integrity and critical files"
fi

# 10. Backup Summary
echo ""
echo "📊 BACKUP SUMMARY"
echo "=================="

if [ "$DRY_RUN" = "false" ]; then
    echo "Backup ID: $BACKUP_ID"
    echo "Total Size: $(du -sh "$BACKUP_PATH" | cut -f1)"
    echo "Location: $BACKUP_PATH"
    echo ""

    echo "Backup Contents:"
    echo "- Databases: $(find "$BACKUP_PATH/databases" -type f 2>/dev/null | wc -l) files"
    echo "- Configurations: $(find "$BACKUP_PATH/configs" -type f 2>/dev/null | wc -l) files"
    echo "- Logs: $(find "$BACKUP_PATH/logs" -type f 2>/dev/null | wc -l) files"
    echo "- Deployment artifacts: $(find "$BACKUP_PATH/deployment" -type f 2>/dev/null | wc -l) files"

    if [ -d "$BACKUP_PATH/user_data" ]; then
        echo "- User data: $(find "$BACKUP_PATH/user_data" -type f 2>/dev/null | wc -l) files"
    fi
else
    echo "[DRY RUN MODE] - No actual files were created"
    echo ""
    echo "Would backup:"
    echo "- Databases from: $PROJECT_DIR/backend/backend/ and $PROJECT_DIR/dashboard/data/"
    echo "- Configuration files from deployment and root directories"
    echo "- Application code via git archive"
    echo "- Recent log files"
    echo "- User-generated content"
    echo "- Environment and system state information"
fi

echo ""
echo "✅ PRE-DEPLOYMENT BACKUP COMPLETED SUCCESSFULLY"

# Create simple restore script
if [ "$DRY_RUN" = "false" ]; then
    cat > "$BACKUP_PATH/restore.sh" << EOF
#!/bin/bash
# Simple restore script for backup $BACKUP_ID
set -e

BACKUP_DIR="$BACKUP_PATH"
PROJECT_DIR="$PROJECT_DIR"

echo "🔄 Restoring from backup: $BACKUP_ID"

# Restore databases
if [ -f "$BACKUP_DIR/databases/credits.db" ]; then
    echo "Restoring credits database..."
    cp "$BACKUP_DIR/databases/credits.db" "$PROJECT_DIR/backend/backend/credits.db"
fi

if [ -f "$BACKUP_DIR/databases/validations.db" ]; then
    echo "Restoring validations database..."
    cp "$BACKUP_DIR/databases/validations.db" "$PROJECT_DIR/dashboard/data/validations.db"
fi

echo "✅ Database restore completed"
echo "⚠️  You may need to restart services and restore configuration files manually"
EOF

    chmod +x "$BACKUP_PATH/restore.sh"
    success "✓ Restore script created: $BACKUP_PATH/restore.sh"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Review backup contents and verification results"
echo "2. Proceed with deployment"
echo "3. If issues occur, use restore.sh to recover databases"
echo "4. Monitor system health after deployment"
echo ""
echo "📍 Backup location: $BACKUP_PATH"
echo "🔄 Restore command: $BACKUP_PATH/restore.sh"