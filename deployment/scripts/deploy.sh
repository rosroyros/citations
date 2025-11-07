#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting deployment..."

# Update code
echo "📥 Pulling latest code..."
git pull origin main

# Update backend
echo "🐍 Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Restart backend service
echo "🔄 Restarting backend service..."
sudo systemctl restart citations-backend
sudo systemctl status citations-backend --no-pager

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

# Copy sitemap
echo "🗺️  Copying sitemap..."
cp ../../content/dist/sitemap.xml ../../frontend/frontend/dist/sitemap.xml
echo "✓ Sitemap copied"

# Run deployment sanity tests before finalizing deployment
echo "🧪 Running deployment sanity tests..."
source venv/bin/activate
python3 -m pytest tests/test_deployment_sanity.py -v
echo "✅ All deployment sanity tests passed!"

cd ../..

# Update Nginx configuration
echo "🌐 Updating Nginx configuration..."
sudo cp deployment/nginx/citations.conf /etc/nginx/sites-available/citations.conf
sudo nginx -t

# Restart Nginx
echo "🌐 Restarting Nginx..."
sudo systemctl reload nginx
sudo systemctl status nginx --no-pager

echo "✅ Deployment completed successfully!"