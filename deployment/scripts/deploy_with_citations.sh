#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting Citations Feature Deployment..."

# Pre-deployment backup
echo "📦 Creating pre-deployment backup..."
./deployment/scripts/backup_database.sh pre-deployment

if [ $? -ne 0 ]; then
    echo "❌ Pre-deployment backup failed"
    exit 1
fi

echo "✅ Pre-deployment backup completed"

# Update code
echo "📥 Pulling latest code..."
git pull origin main

# Update backend
echo "🐍 Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Test database migration locally first
echo "🧪 Testing database migration locally..."
cd dashboard
python3 -c "
from database import get_database
import tempfile
test_db = tempfile.mktemp(suffix='.db')
try:
    with get_database(test_db) as db:
        schema = db.get_table_schema('validations')
        if 'citations_text TEXT' in schema:
            print('✅ citations_text column exists')
        else:
            print('❌ citations_text column missing')
            exit(1)
finally:
    import os
    if os.path.exists(test_db):
        os.unlink(test_db)
print('✅ Migration test passed')
"
cd ..

if [ $? -ne 0 ]; then
    echo "❌ Local migration test failed"
    exit 1
fi

# Check current database state
echo "🔍 Checking current database state..."
if [ -f "dashboard/data/validations.db" ]; then
    sqlite3 dashboard/data/validations.db "PRAGMA table_info(validations);" | grep citations_text > /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ citations_text column already exists in production database"
    else
        echo "⚠️  citations_text column missing - will be added during migration"
    fi
else
    echo "⚠️  Production database not found - will be created"
fi

echo "🔄 Deploying updates..."

# Restart backend service
echo "🔄 Restarting backend service..."
sudo systemctl restart citations-backend
sudo systemctl status citations-backend --no-pager

# Dashboard deployment
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

cd ../..

# Update Nginx configuration
echo "🌐 Updating Nginx configuration..."
sudo cp deployment/nginx/citations.conf /etc/nginx/sites-available/citations.conf
sudo nginx -t

# Restart Nginx
echo "🌐 Restarting Nginx..."
sudo systemctl reload nginx
sudo systemctl status nginx --no-pager

# Post-deployment verification
echo "🧪 Running post-deployment verification..."

# Verify database migration
echo "🔍 Verifying database migration..."
cd dashboard
python3 -c "
from database import get_database
try:
    db = get_database()
    schema = db.get_table_schema('validations')
    if 'citations_text TEXT' in schema:
        print('✅ citations_text column exists in production')

        # Test inserting data with citations
        import tempfile
        test_data = {
            'job_id': 'deployment_test_' + str(int(time.time())),
            'created_at': '2025-11-28T10:00:00Z',
            'user_type': 'test',
            'status': 'completed',
            'citations_text': 'Test citation for deployment verification'
        }

        db.insert_validation(test_data)
        result = db.get_validation(test_data['job_id'])
        if result and result.get('citations_text'):
            print('✅ citations_text insertion/retrieval working')
        else:
            print('❌ citations_text insertion/retrieval failed')
            exit(1)
    else:
        print('❌ citations_text column missing from production')
        exit(1)
finally:
    db.close()
"

if [ $? -ne 0 ]; then
    echo "❌ Post-deployment verification failed"
    echo "🔄 Rolling back deployment..."
    # Use emergency backup from pre-deployment
    LATEST_BACKUP=$(ls -t /opt/citations/backups/pre-deployment/validations_pre_deploy_*.db | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        echo "🔄 Restoring from: $LATEST_BACKUP"
        ./deployment/scripts/restore_database.sh "$LATEST_BACKUP"
    fi
    exit 1
fi

cd ..

# Test dashboard API
echo "🌐 Testing dashboard API..."
curl -s http://localhost:8000/api/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Dashboard API responding"
else
    echo "⚠️  Dashboard API not responding - may need manual check"
fi

# Run deployment sanity tests
echo "🧪 Running deployment sanity tests..."
source venv/bin/activate
python3 -m pytest tests/test_deployment_sanity.py -v

echo "✅ All deployment sanity tests passed!"

echo ""
echo "🎉 Citations feature deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "   ✅ Pre-deployment backup created"
echo "   ✅ Database migration verified"
echo "   ✅ Backend service restarted"
echo "   ✅ Dashboard service restarted"
echo "   ✅ Frontend built and deployed"
echo "   ✅ Nginx configuration updated"
echo "   ✅ Post-deployment verification passed"
echo "   ✅ Sanity tests passed"
echo ""
echo "🔗 Next Steps:"
echo "   1. Monitor system performance"
echo "   2. Check dashboard functionality"
echo "   3. Verify citations display in job details"
echo "   4. Monitor logs for any issues"
echo ""
echo "📊 Monitoring Commands:"
echo "   sudo systemctl status citations-backend"
echo "   sudo systemctl status citations-dashboard"
echo "   sudo journalctl -u citations-backend -f"
echo "   sudo journalctl -u citations-dashboard -f"