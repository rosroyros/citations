#!/bin/bash
set -e

echo "🚀 Setting up Citations Dashboard..."

# Verify we're in the right directory
if [ ! -f "dashboard/api.py" ]; then
    echo "❌ Error: Must run from /opt/citations directory"
    exit 1
fi

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p dashboard/data
mkdir -p dashboard/static

# Install systemd service
echo "⚙️  Installing systemd service..."
sudo cp dashboard/citations-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable citations-dashboard

# Install cron job
echo "⏰ Installing cron job..."
sudo cp dashboard/citations-dashboard.cron /etc/cron.d/citations-dashboard
sudo chmod 644 /etc/cron.d/citations-dashboard

# Run initial data load
echo "📊 Loading initial data (last 3 days)..."
source venv/bin/activate
python3 dashboard/parse_logs_cron.py --initial --days=3

# Start dashboard service
echo "🚀 Starting dashboard service..."
sudo systemctl start citations-dashboard
sudo systemctl status citations-dashboard --no-pager

# Verify
echo ""
echo "✅ Dashboard setup complete!"
echo ""
echo "📍 Dashboard URL: http://$(hostname -I | awk '{print $1}'):4646"
echo "🔍 Service status: sudo systemctl status citations-dashboard"
echo "📋 Cron logs: tail -f /opt/citations/logs/dashboard-cron.log"
echo "🗄️  Database: /opt/citations/dashboard/data/validations.db"
echo ""
echo "⚠️  Remember to update deploy.sh to handle dashboard updates!"
