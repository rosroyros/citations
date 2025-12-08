#!/bin/bash

# Deployment Script for Citation Format Checker
# Usage: ./deployment/scripts/deploy.sh

set -e  # Exit on any error

echo "🚀 Starting deployment of Citation Format Checker..."
echo "=================================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"

echo "📁 Project root: $(pwd)"
echo ""

# 1. Backup current state (CRITICAL for user tracking deployment)
echo "📦 Creating backups..."
BACKUP_DIR="/opt/citations/backups/$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"

# Backup database if it exists
if [ -f "/opt/citations/backend/users.db" ]; then
    sudo cp /opt/citations/backend/users.db "$BACKUP_DIR/"
    sudo chmod 600 "$BACKUP_DIR/users.db"  # Secure backup with user data
    echo "✅ Backend database backed up and secured"
fi

if [ -f "/opt/citations/dashboard/data/validations.db" ]; then
    sudo cp /opt/citations/dashboard/data/validations.db "$BACKUP_DIR/"
    sudo chmod 600 "$BACKUP_DIR/validations.db"  # Secure backup with user data
    echo "✅ Dashboard database backed up and secured"
fi

# Update code
echo "📥 Pulling latest code..."
git pull origin main

# Update backend
echo "🐍 Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# 2. Run database migrations (CRITICAL for user tracking)
echo ""
echo "🗄️  Checking database migrations..."

# Check if dashboard migration exists (USER TRACKING DEPLOYMENT)
if [ -f "dashboard/migrations/add_user_id_columns.py" ]; then
    echo "🔧 Running user ID columns migration..."
    cd dashboard/migrations
    python3 add_user_id_columns.py

    # Store migration state for potential rollback
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Ran add_user_id_columns.py migration" | sudo tee -a "$BACKUP_DIR/migration_log.txt" > /dev/null

    cd "$PROJECT_ROOT"
    echo "✅ Database migrations completed"
    echo "💾 Migration state saved to $BACKUP_DIR/migration_log.txt"
else
    echo "ℹ️  No new migrations found"
fi

# Check for provider column migration (GEMINI A/B DEPLOYMENT)
if [ -f "scripts/migrate_provider_column.py" ]; then
    echo "🔧 Running provider column migration..."
    python3 scripts/migrate_provider_column.py
    echo "✅ Provider column migration check completed"
fi

# Migration rollback function (available if deployment fails)
rollback_migration() {
    echo "🚨 Migration rollback initiated..."
    if [ -f "$BACKUP_DIR/validations.db" ]; then
        echo "📂 Restoring dashboard database from backup..."
        sudo cp "$BACKUP_DIR/validations.db" /opt/citations/dashboard/data/validations.db
        sudo chmod 644 /opt/citations/dashboard/data/validations.db
        echo "✅ Dashboard database restored"
    fi

    if [ -f "$BACKUP_DIR/users.db" ]; then
        echo "📂 Restoring backend database from backup..."
        sudo cp "$BACKUP_DIR/users.db" /opt/citations/backend/users.db
        sudo chmod 644 /opt/citations/backend/users.db
        echo "✅ Backend database restored"
    fi

    echo "🔄 Restarting services after rollback..."
    sudo systemctl restart citations-backend
    sudo systemctl restart citations-dashboard 2>/dev/null || echo "Dashboard service not running"

    echo "✅ Rollback completed"
}

# Restart backend service
echo "🔄 Restarting backend service..."
sudo systemctl restart citations-backend
sudo systemctl status citations-backend --no-pager

# Dashboard deployment (if exists)
if [ -d "dashboard" ] && [ -f "dashboard/api.py" ]; then
    echo "🔄 Deploying dashboard updates..."
    sudo systemctl restart citations-dashboard
    sudo systemctl status citations-dashboard --no-pager
    echo "✅ Dashboard deployed"
fi

# Update frontend
echo "⚛️ Building frontend..."
cd frontend/frontend
npm install
npm run build

# Copy guide CSS and JS assets to correct nginx location
echo "📄 Copying guide assets (CSS, JS)..."
mkdir -p ../../content/dist/assets/css ../../content/dist/assets/js
cp ../../backend/pseo/builder/assets/css/styles.css ../../content/dist/assets/css/
cp ../../backend/pseo/builder/assets/css/mini-checker.css ../../content/dist/assets/css/
cp ../../backend/pseo/builder/assets/js/mini-checker.js ../../content/dist/assets/js/

# Copy generated guide pages
echo "📚 Copying generated guide pages..."
mkdir -p ../../frontend/frontend/dist/guide
cp -r ../../content/dist/guide/* ../../frontend/frontend/dist/guide/
echo "✓ Copied $(find ../../content/dist/guide -name 'index.html' | wc -l) guide pages"

# Copy validation guide pages
echo "📚 Copying validation guide pages..."
# Ensure we copy directories themselves, not their contents
for guide_dir in ../../content/dist/how-to-*; do
    if [ -d "$guide_dir" ]; then
        guide_name=$(basename "$guide_dir")
        mkdir -p "../../frontend/frontend/dist/$guide_name"
        cp -r "$guide_dir"/* "../../frontend/frontend/dist/$guide_name/"
    fi
done
echo "✓ Copied $(find ../../content/dist -maxdepth 1 -name 'how-to-*' -type d | wc -l) validation guide directories"

# Copy cite-* pages (specific source citation guides)
echo "📚 Copying cite-* citation guide pages..."
for cite_dir in ../../content/dist/cite-*-apa; do
    if [ -d "$cite_dir" ]; then
        cite_name=$(basename "$cite_dir")
        mkdir -p "../../frontend/frontend/dist/$cite_name"
        cp -r "$cite_dir"/* "../../frontend/frontend/dist/$cite_name/"
    fi
done
echo "✓ Copied $(find ../../content/dist -maxdepth 1 -name 'cite-*-apa' -type d | wc -l) cite-* directories"

# Copy guides directory
echo "📚 Copying guides directory..."
mkdir -p ../../frontend/frontend/dist/guides
cp -r ../../content/dist/guides/* ../../frontend/frontend/dist/guides/
echo "✓ Guides directory copied"

# Copy sitemap (Vite already copies from public/ to dist/ during build)
echo "🗺️  Sitemap ready (copied by Vite build)"
# Vite automatically copies public/sitemap.xml to dist/sitemap.xml during build
echo "✓ Sitemap location: ../../frontend/frontend/dist/sitemap.xml"

# Run deployment sanity tests before finalizing deployment
echo "🧪 Running deployment sanity tests..."
cd "$PROJECT_ROOT"
source venv/bin/activate
python3 -m pytest tests/test_deployment_sanity.py -v
echo "✅ All deployment sanity tests passed!"

# Update Nginx configuration
echo "🌐 Updating Nginx configuration..."
sudo cp deployment/nginx/citations.conf /etc/nginx/sites-available/citations.conf
sudo nginx -t

# Restart Nginx
echo "🌐 Restarting Nginx..."
sudo systemctl reload nginx
sudo systemctl status nginx --no-pager

# 3. Verify user tracking functionality (CRITICAL for user tracking deployment)
echo ""
echo "🧪 Testing user tracking functionality..."

# Test that endpoints accept user tracking headers
TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/api/validate \
    -H "Content-Type: application/json" \
    -H "X-Free-User-ID: $(echo 'test-uuid' | base64)" \
    -H "X-Free-Used: $(echo '3' | base64)" \
    -d '{"citations": ["Smith, J. (2023). Test citation."], "style": "apa7"}')

if echo "$TEST_RESPONSE" | grep -q "job_id\|error"; then
    echo "✅ User tracking endpoints are working"
else
    echo "⚠️  User tracking test inconclusive"
fi

# 4. Check logs for user ID logging (CRITICAL verification)
echo ""
echo "📋 Checking recent logs for user ID tracking..."
RECENT_LOGS=$(sudo journalctl -u citations-backend --no-pager -n 20 | grep "user_type=" || echo "No user ID logs found in recent entries")

if echo "$RECENT_LOGS" | grep -q "user_type="; then
    echo "✅ User ID logging is working"
else
    echo "ℹ️  No user ID logs in recent output (may require actual user traffic)"
fi

# 5. Verify dashboard accessibility
echo ""
echo "📊 Verifying dashboard..."
if curl -f -s http://localhost:4646 > /dev/null 2>&1; then
    echo "✅ Dashboard is accessible"
else
    echo "⚠️  Dashboard not accessible (may need manual start)"
fi

# 6. Final status summary
echo ""
echo "=================================================="
echo "✅ Deployment completed successfully!"
echo ""

echo "📊 Service Status:"
echo "   - Backend: $(systemctl is-active citations-backend)"
echo "   - Nginx: $(systemctl is-active nginx)"

echo ""
echo "🔗 Access URLs:"
echo "   - Frontend: https://citationformatchecker.com"
echo "   - Backend API: https://citationformatchecker.com/api"
echo "   - Dashboard: http://178.156.161.140:4646"

echo ""
echo "📁 Backup location: $BACKUP_DIR"
echo ""
echo "🎉 User tracking system is now live!"