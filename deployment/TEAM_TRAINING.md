# Team Training Guide: Deployment and Rollback Procedures

This guide provides comprehensive training for team members on deployment and rollback procedures for the citations application.

## 🎯 Training Objectives

After completing this training, team members will be able to:

- ✅ Perform safe deployment procedures
- ✅ Execute emergency rollbacks
- ✅ Troubleshoot deployment issues
- ✅ Monitor system health during and after deployment
- ✅ Maintain documentation and improve procedures

## 📋 Prerequisites

### Required Knowledge
- Basic command line familiarity
- Understanding of git version control
- Basic system administration concepts
- Familiarity with the citations application architecture

### Required Access
- SSH access to production server
- Sudo/administrator privileges on production system
- Access to monitoring and alerting tools
- Communication channel access (Slack, email, etc.)

## 🏗️ System Architecture Overview

### Application Components

```
┌─────────────────────────────────────────────────────────┐
│                    Citations Application                 │
├─────────────────────────────────────────────────────────┤
│  Frontend (React)                                      │
│  ├── Static files served by Nginx                      │
│  └── Build artifacts in frontend/frontend/dist         │
├─────────────────────────────────────────────────────────┤
│  Backend (Python/Flask)                                │
│  ├── citations-backend service (systemd)              │
│  ├── SQLite databases                                  │
│  │   ├── credits.db (user credits/orders)             │
│  │   └── validations.db (dashboard data)              │
│  └── Citation logging system                           │
├─────────────────────────────────────────────────────────┤
│  Dashboard (Python)                                    │
│  ├── citations-dashboard service (systemd)            │
│  ├── Validation tracking                               │
│  └── Metrics and analytics                            │
├─────────────────────────────────────────────────────────┤
│  Infrastructure                                        │
│  ├── Nginx reverse proxy                              │
│  ├── systemd service management                       │
│  └── Log rotation                                      │
└─────────────────────────────────────────────────────────┘
```

### Key File Locations

- **Application**: `/opt/citations/`
- **Databases**:
  - `/opt/citations/backend/backend/credits.db`
  - `/opt/citations/dashboard/data/validations.db`
- **Configuration**: `/opt/citations/deployment/`
- **Logs**: `/var/log/citations/` and application-specific log directories
- **Backups**: `/opt/citations/backups/`

## 🚀 Deployment Procedures

### Pre-Deployment Checklist

#### 1. Environment Preparation
```bash
# SSH to production server
ssh deploy@178.156.161.140

# Navigate to project directory
cd /opt/citations

# Check current git status
git status
git log --oneline -5
```

#### 2. Backup Creation
```bash
# Create comprehensive pre-deployment backup
./deployment/scripts/pre_deployment_backup.sh

# Verify backup was created
ls -la /opt/citations/backups/
```

#### 3. Validation Testing
```bash
# Run deployment validation before starting
./deployment/scripts/deployment_validation.sh

# Address any critical failures before proceeding
```

### Standard Deployment Process

#### Step 1: Update Code
```bash
# Pull latest changes
git pull origin main

# Verify the correct commit is checked out
git log --oneline -1
```

#### Step 2: Update Backend
```bash
# Activate virtual environment
source venv/bin/activate

# Update Python dependencies
pip install -r requirements.txt

# Test database connectivity
python3 -c "
import sys
sys.path.insert(0, 'backend/backend')
from database import init_db
init_db()
print('Database OK')
"
```

#### Step 3: Update Frontend
```bash
# Navigate to frontend directory
cd frontend/frontend

# Install dependencies
npm install

# Build production assets
npm run build

# Verify build success
ls -la dist/
```

#### Step 4: Update Configuration
```bash
# Copy updated nginx configuration
sudo cp deployment/nginx/citations.conf /etc/nginx/sites-available/
sudo nginx -t  # Test configuration syntax
```

#### Step 5: Restart Services
```bash
# Restart backend service
sudo systemctl restart citations-backend
sudo systemctl status citations-backend --no-pager

# Restart dashboard service (if exists)
if systemctl list-unit-files | grep -q "citations-dashboard"; then
    sudo systemctl restart citations-dashboard
    sudo systemctl status citations-dashboard --no-pager
fi

# Reload nginx
sudo systemctl reload nginx
```

#### Step 6: Verification
```bash
# Run deployment validation
./deployment/scripts/deployment_validation.sh

# Test basic functionality
curl -I https://citationformatchecker.com
curl -I https://citationformatchecker.com/api/health
```

### Post-Deployment Monitoring

#### Start Monitoring Script
```bash
# Start 30-minute monitoring (default)
./deployment/scripts/post_deployment_monitoring.sh

# Or customize duration
MONITORING_DURATION=3600 ./deployment/scripts/post_deployment_monitoring.sh  # 1 hour
```

#### Manual Verification Checklist
- [ ] Main website loads correctly
- [ ] Citation submission works
- [ ] Dashboard accessible and functional
- [ ] No error spikes in logs
- [ ] Database operations working
- [ ] Performance metrics normal

## 🔄 Emergency Rollback Procedures

### When to Rollback

**Immediate Rollback Required:**
- Complete service outage
- Database corruption
- Critical security vulnerability
- Major functionality broken

**Consider Rollback:**
- Performance degradation >50%
- Error rate >10%
- User complaints increasing rapidly

### Rollback Decision Process

1. **Assess Impact (2 minutes)**
   - What's broken?
   - How many users affected?
   - Is there a quick fix?

2. **Consult Team (5 minutes)**
   - Notify stakeholders
   - Get developer input
   - Check for known issues

3. **Make Decision (1 minute)**
   - Rollback now vs. investigate
   - Choose rollback level
   - Plan rollback steps

### Level 1: Configuration Rollback (Fast)

**Use Case**: Simple configuration issues
**Time**: 2-5 minutes

```bash
# Identify problematic change
git log --oneline -10

# Reset to previous commit
git reset --hard <previous-commit-hash>

# Restart affected services
sudo systemctl restart citations-backend
sudo systemctl reload nginx

# Verify rollback
curl -I https://citationformatchecker.com
```

### Level 2: Full Code Rollback

**Use Case**: Code changes, minor schema issues
**Time**: 5-15 minutes

```bash
# Create emergency backup first (if not already done)
./deployment/scripts/backup_database.sh --emergency

# Roll back code
git fetch origin
git checkout <stable-tag-or-commit>

# Rebuild frontend
cd frontend/frontend
npm install
npm run build
cd ../..

# Update backend
source venv/bin/activate
pip install -r requirements.txt

# Restart all services
sudo systemctl restart citations-backend
sudo systemctl restart citations-dashboard  # if running
sudo systemctl reload nginx

# Verify with full validation
./deployment/scripts/deployment_validation.sh
```

### Level 3: Database Rollback

**Use Case**: Database corruption, major schema issues
**Time**: 15-30 minutes
**⚠️ Warning**: May result in data loss

```bash
# Stop all services
sudo systemctl stop citations-backend
sudo systemctl stop citations-dashboard

# Export current data (if possible)
python3 -c "
import sys
sys.path.insert(0, 'dashboard')
from database import get_database
import json
from datetime import datetime

db = get_database()
recent_data = db.get_validations(limit=1000)
with open(f'emergency_export_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.json', 'w') as f:
    json.dump(recent_data, f, indent=2)
print('Emergency export completed')
"

# Restore databases
./deployment/scripts/restore_database.sh /opt/citations/backups/<latest-backup>.sql
./deployment/scripts/restore_database.sh --validations /opt/citations/backups/<validations-backup>.sql

# Roll back code to matching version
git checkout <tag-matching-backup>

# Rebuild and restart services
# (Same as Level 2 rollback)

# Verify extensively
./deployment/scripts/deployment_validation.sh
```

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### Service Won't Start
```bash
# Check service status
sudo systemctl status citations-backend

# View service logs
sudo journalctl -u citations-backend -f

# Check configuration
python3 -c "
import sys
sys.path.insert(0, 'backend/backend')
try:
    from app import app
    print('Configuration OK')
except Exception as e:
    print(f'Configuration error: {e}')
"
```

#### Database Connection Issues
```bash
# Test database access
python3 -c "
import sys
sys.path.insert(0, 'backend/backend')
from database import get_db_path, init_db
print(f'Database path: {get_db_path()}')
init_db()
print('Database accessible')
"

# Check file permissions
ls -la backend/backend/credits.db
ls -la dashboard/data/validations.db

# Fix permissions if needed
sudo chown deploy:deploy backend/backend/credits.db
sudo chown deploy:deploy dashboard/data/validations.db
sudo chmod 640 backend/backend/credits.db
sudo chmod 640 dashboard/data/validations.db
```

#### Frontend Build Issues
```bash
# Clear npm cache
cd frontend/frontend
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for build errors
npm run build 2>&1 | tee build.log
```

#### Nginx Configuration Issues
```bash
# Test nginx configuration
sudo nginx -t

# Check nginx syntax
sudo nginx -T

# View nginx error log
sudo tail -f /var/log/nginx/error.log

# Reload nginx
sudo systemctl reload nginx
```

### Performance Issues

#### High Memory Usage
```bash
# Check memory usage
free -h
top

# Restart service to free memory
sudo systemctl restart citations-backend

# Check for memory leaks
sudo journalctl -u citations-backend | grep -i memory
```

#### High Disk Usage
```bash
# Check disk usage
df -h
du -sh /opt/citations/*

# Clean up old backups
find /opt/citations/backups -name "*.db" -mtime +30 -delete

# Clean up logs
sudo journalctl --vacuum-time=7d
```

#### Database Performance
```bash
# Check database size
ls -lh backend/backend/credits.db
ls -lh dashboard/data/validations.db

# Vacuum database
sqlite3 backend/backend/credits.db "VACUUM;"
sqlite3 dashboard/data/validations.db "VACUUM;"

# Check database integrity
sqlite3 backend/backend/credits.db "PRAGMA integrity_check;"
sqlite3 dashboard/data/validations.db "PRAGMA integrity_check;"
```

## 📊 Monitoring and Alerting

### Key Metrics to Monitor

#### Application Health
- HTTP response codes
- Response times
- Error rates
- User session counts

#### System Health
- CPU usage
- Memory usage
- Disk usage
- Network connectivity

#### Database Health
- Connection success rates
- Query performance
- Database size growth
- Transaction rates

### Manual Monitoring Commands

```bash
# Application health
curl -s -o /dev/null -w "%{http_code}, %{time_total}" https://citationformatchecker.com

# Service status
sudo systemctl status citations-backend --no-pager
sudo systemctl status nginx --no-pager

# System resources
top -b -n 1 | head -20
df -h
free -h

# Recent errors
sudo journalctl -u citations-backend --since "1 hour ago" | grep -i error
tail -100 /var/log/citations/app.log | grep -i error
```

### Alert Thresholds

- **Critical**: Service down, error rate >20%, response time >10s
- **Warning**: Error rate 5-20%, response time 5-10s, memory >80%
- **Info**: Error rate 1-5%, response time 2-5s, memory >60%

## 📋 Documentation and Communication

### Incident Documentation

For every deployment issue or rollback, document:

1. **Incident Details**
   - Date and time
   - Deployment version
   - Symptoms observed
   - Users affected

2. **Root Cause**
   - What went wrong
   - Why it happened
   - Contributing factors

3. **Resolution**
   - Steps taken
   - Time to resolve
   - Final outcome

4. **Prevention**
   - How to prevent recurrence
   - Process improvements needed
   - Additional monitoring required

### Communication Templates

#### Initial Incident Alert
```
🚨 INCIDENT ALERT - Citations Application
Issue: [Brief description of issue]
Impact: [Number of affected users, functionality affected]
Time: [Current time]
Status: [Investigating/Rollback initiated/Resolved]
Updates to follow in this thread.
```

#### Resolution Update
```
✅ INCIDENT RESOLVED - Citations Application
Issue: [Brief description of issue]
Resolution: [What was done to fix it]
Duration: [Total incident duration]
Impact: [Final assessment of user impact]
Prevention: [Steps to prevent recurrence]
```

## 🎓 Training Exercises

### Exercise 1: Deployment Simulation

**Objective**: Practice standard deployment procedure

**Tasks**:
1. Set up staging environment
2. Create pre-deployment backup
3. Perform deployment
4. Run validation checks
5. Start monitoring

**Expected Time**: 30 minutes

### Exercise 2: Emergency Rollback

**Objective**: Practice emergency rollback procedures

**Tasks**:
1. Simulate deployment failure
2. Assess situation and choose rollback level
3. Execute rollback procedure
4. Verify system recovery
5. Document incident

**Expected Time**: 20 minutes

### Exercise 3: Troubleshooting

**Objective**: Practice troubleshooting common issues

**Scenarios**:
- Service won't start
- Database connection issues
- Frontend build failures
- Performance degradation

**Expected Time**: 45 minutes

### Exercise 4: Monitoring and Alerting

**Objective**: Practice system monitoring

**Tasks**:
1. Set up monitoring checks
2. Identify performance issues
3. Respond to alerts
4. Analyze system metrics

**Expected Time**: 25 minutes

## 📚 Reference Materials

### Quick Reference Commands

```bash
# Deployment
./deployment/scripts/deployment_validation.sh
./deployment/scripts/pre_deployment_backup.sh
./deployment/scripts/post_deployment_monitoring.sh

# Rollback
git reset --hard <commit-hash>
./deployment/scripts/restore_database.sh <backup-file>

# Monitoring
curl -I https://citationformatchecker.com
sudo systemctl status citations-backend
./deployment/scripts/deployment_validation.sh
```

### Emergency Contacts

- **DevOps Lead**: [Name, Phone, Email]
- **Backend Developer**: [Name, Phone, Email]
- **Frontend Developer**: [Name, Phone, Email]
- **System Administrator**: [Name, Phone, Email]

### Important Files

- **Deployment validation**: `/opt/citations/deployment/scripts/deployment_validation.sh`
- **Rollback procedures**: `/opt/citations/deployment/EMERGENCY_ROLLBACK.md`
- **Service configs**: `/etc/systemd/system/citations-*.service`
- **Nginx config**: `/etc/nginx/sites-available/citations.conf`

## ✅ Certification Checklist

Team members are certified to perform deployments when they can:

- [ ] Explain the system architecture and components
- [ ] Perform a complete deployment without assistance
- [ ] Execute all three levels of rollback procedures
- [ ] Troubleshoot common deployment issues
- [ ] Monitor system health during deployment
- [ ] Document incidents and improvements
- [ ] Complete all training exercises successfully
- [ ] Demonstrate understanding of emergency procedures

## 📈 Continuous Improvement

### Monthly Activities

- [ ] Review deployment procedures and update documentation
- [ ] Conduct rollback drills in staging environment
- [ ] Analyze deployment metrics and identify trends
- [ ] Update training materials based on lessons learned

### Quarterly Activities

- [ ] Full system deployment rehearsal
- [ ] Emergency response simulation
- [ ] Review and update monitoring thresholds
- [ ] Team skills assessment and additional training

---

**Training Last Updated**: [Date]
**Next Review Date**: [Date + 3 months]
**Training Version**: 1.0

*This training guide should be updated quarterly or after any major system changes.*