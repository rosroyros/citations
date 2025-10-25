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
mkdir -p ../../assets/css ../../assets/js
cp ../../backend/pseo/builder/assets/css/styles.css ../../assets/css/
cp ../../backend/pseo/builder/assets/css/mini-checker.css ../../assets/css/
cp ../../backend/pseo/builder/assets/js/mini-checker.js ../../assets/js/

# Copy generated guide pages
echo "📚 Copying generated guide pages..."
mkdir -p ../../frontend/frontend/dist/guide
cp -r ../../content/dist/guide/* ../../frontend/frontend/dist/guide/
echo "✓ Copied $(find ../../content/dist/guide -name 'index.html' | wc -l) guide pages"

cd ../..

# Restart Nginx
echo "🌐 Restarting Nginx..."
sudo systemctl reload nginx
sudo systemctl status nginx --no-pager

echo "✅ Deployment completed successfully!"