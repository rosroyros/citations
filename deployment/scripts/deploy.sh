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

# Copy guide CSS assets to correct nginx location
echo "📄 Copying guide CSS assets..."
mkdir -p ../../assets/css
cp ../../backend/pseo/builder/assets/css/styles.css ../../assets/css/
cp ../../backend/pseo/builder/assets/css/mini-checker.css ../../assets/css/
cd ../..

# Restart Nginx
echo "🌐 Restarting Nginx..."
sudo systemctl reload nginx
sudo systemctl status nginx --no-pager

echo "✅ Deployment completed successfully!"