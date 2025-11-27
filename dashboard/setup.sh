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
sudo cp deployment/systemd/citations-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable citations-dashboard

# Install cron job
echo "⏰ Installing cron job..."
cat <<'EOF' | sudo tee /etc/cron.d/citations-dashboard > /dev/null
# Incremental log parsing every 5 minutes
*/5 * * * * deploy cd /opt/citations && PYTHONPATH=/opt/citations /opt/citations/venv/bin/python3 /opt/citations/dashboard/parse_logs_cron.py >> /opt/citations/logs/dashboard-cron.log 2>&1
EOF
sudo chmod 644 /etc/cron.d/citations-dashboard

# Initialize database
echo "🗄️  Initializing database..."
source venv/bin/activate
PYTHONPATH=/opt/citations python3 -c "from dashboard.database import DatabaseManager; DatabaseManager('/opt/citations/dashboard/data/validations.db')"

# Run initial data load
echo "📊 Loading initial data (last 3 days)..."
PYTHONPATH=/opt/citations python3 dashboard/parse_logs_cron.py --initial --days=3

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
