# Emergency Rollback Procedures

This document outlines emergency rollback procedures for the citations application in case of deployment failures or critical issues.

## 🚨 Emergency Contact Information

- **Primary Contact**: [System Administrator]
- **Backup Contact**: [DevOps Lead]
- **Application Owner**: [Product Manager]

## 📋 Pre-Rollback Checklist

Before initiating any rollback, verify the following:

1. **Issue Confirmation**
   - [ ] Confirm the issue is deployment-related
   - [ ] Document the specific failure symptoms
   - [ ] Check if issue affects all users or specific features
   - [ ] Verify issue severity (critical vs. non-critical)

2. **Impact Assessment**
   - [ ] Estimate number of affected users
   - [ ] Identify critical business functions impacted
   - [ ] Determine rollback urgency level

3. **Communication**
   - [ ] Notify stakeholders about potential service interruption
   - [ ] Prepare user-facing communications
   - [ ] Set up monitoring during rollback process

## 🔄 Rollback Procedures

### Level 1: Configuration Rollback (Fastest)

Use for configuration issues, minor bugs, or when code changes are minimal.

**Time Estimate**: 2-5 minutes

**Steps**:
1. **SSH to production server**
   ```bash
   ssh deploy@178.156.161.140
   cd /opt/citations
   ```

2. **Identify the problematic commit**
   ```bash
   git log --oneline -10  # Show recent commits
   # Note the commit hash before the problematic change
   ```

3. **Roll back to previous commit**
   ```bash
   git reset --hard <previous-commit-hash>
   ```

4. **Restart services**
   ```bash
   sudo systemctl restart citations-backend
   sudo systemctl restart citations-dashboard  # if running
   ```

5. **Verify rollback**
   ```bash
   # Test basic functionality
   curl -I https://citationformatchecker.com
   ```

### Level 2: Full Code Rollback

Use for significant code changes, database schema issues, or when configuration rollback is insufficient.

**Time Estimate**: 5-15 minutes

**Steps**:
1. **Create emergency backup** (if not already exists)
   ```bash
   cd /opt/citations
   ./deployment/scripts/backup_database.sh --emergency
   ```

2. **Roll back code**
   ```bash
   git fetch origin
   git checkout <previous-stable-tag-or-branch>
   # Or use specific commit hash
   git reset --hard <stable-commit-hash>
   ```

3. **Rebuild frontend**
   ```bash
   cd frontend/frontend
   npm install
   npm run build
   cd ../..
   ```

4. **Update backend dependencies**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Restart all services**
   ```bash
   sudo systemctl restart citations-backend
   sudo systemctl restart citations-dashboard  # if running
   sudo systemctl reload nginx
   ```

6. **Verify application health**
   ```bash
   ./deployment/scripts/deployment_validation.sh
   ```

### Level 3: Database Rollback (Critical)

Use for database schema issues, data corruption, or migration failures.

**⚠️ WARNING**: This can result in data loss. Use only as last resort.

**Time Estimate**: 15-30 minutes

**Prerequisites**:
- Recent database backup available
- Backup integrity verified
- Stakeholder approval obtained

**Steps**:
1. **Stop all application services**
   ```bash
   sudo systemctl stop citations-backend
   sudo systemctl stop citations-dashboard  # if running
   ```

2. **Create emergency data export** (if possible)
   ```bash
   # Export recent validation data
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

   db.close()
   print('Emergency export completed')
   "
   ```

3. **Identify appropriate backup**
   ```bash
   # List available backups
   ls -la /opt/citations/backups/

   # Choose the most recent backup before the problematic deployment
   # Note the backup filename
   ```

4. **Restore database**
   ```bash
   # Restore credits database
   ./deployment/scripts/restore_database.sh /opt/citations/backups/<credits-backup-file>.sql

   # Restore validations database
   ./deployment/scripts/restore_database.sh --validations /opt/citations/backups/<validations-backup-file>.sql
   ```

5. **Roll back code to matching version**
   ```bash
   git checkout <tag-matching-backup>
   # Rebuild and restart services (same as Level 2)
   ```

6. **Verify data integrity**
   ```bash
   # Check database connectivity
   python3 -c "
   import sys
   sys.path.insert(0, 'backend/backend')
   from database import init_db, get_credits

   # Test basic database operations
   init_db()
   print('Credits database OK')

   # Test validations database
   sys.path.insert(0, 'dashboard')
   from database import get_database
   db = get_database()
   stats = db.get_stats()
   print(f'Validations database OK - {stats[\"total_validations\"]} records')
   db.close()
   "
   ```

7. **Restart services and verify**
   ```bash
   sudo systemctl start citations-backend
   sudo systemctl start citations-dashboard  # if running
   sudo systemctl reload nginx

   # Run full validation
   ./deployment/scripts/deployment_validation.sh
   ```

## 🔍 Post-Rollback Verification

### Essential Health Checks

1. **Application Accessibility**
   ```bash
   # Main site
   curl -I https://citationformatchecker.com

   # API endpoints
   curl -I https://citationformatchecker.com/api/health

   # Static assets
   curl -I https://citationformatchecker.com/static/css/main.css
   ```

2. **Database Connectivity**
   ```bash
   # Test credits database
   python3 -c "import sys; sys.path.insert(0, 'backend/backend'); from database import get_credits; print('Credits DB OK')"

   # Test validations database
   python3 -c "import sys; sys.path.insert(0, 'dashboard'); from database import get_database; db=get_database(); print('Validations DB OK'); db.close()"
   ```

3. **Service Status**
   ```bash
   sudo systemctl status citations-backend --no-pager
   sudo systemctl status citations-dashboard --no-pager  # if applicable
   sudo systemctl status nginx --no-pager
   ```

4. **Core Functionality Testing**
   - Manual test: Submit a citation validation
   - Manual test: Check dashboard loading
   - Manual test: Verify user registration/login (if applicable)

### Automated Verification

Run the deployment validation script:
```bash
./deployment/scripts/deployment_validation.sh
```

The script should report:
- ✅ All critical checks passed
- ⚠️ Any warnings to review
- ❌ No critical failures

## 📊 Rollback Success Criteria

A rollback is considered successful when:

1. **Service Availability**
   - [ ] Main application responds to HTTP requests
   - [ ] All critical user functions work
   - [ ] Error rates return to normal levels

2. **Data Integrity**
   - [ ] Databases are accessible and responsive
   - [ ] No data corruption detected
   - [ ] Recent data (if preserved) is consistent

3. **System Health**
   - [ ] All services running normally
   - [ ] No critical errors in logs
   - [ ] Performance metrics within acceptable ranges

4. **Validation Script**
   - [ ] Deployment validation passes all critical checks
   - [ ] Any warnings are documented and understood

## 🚨 Emergency Scenarios

### Scenario A: Complete Service Outage

**Symptoms**: All services down, no response from application

**Immediate Actions**:
1. Check server status: `ssh deploy@178.156.161.140 "systemctl status"`
2. Restart services: `sudo systemctl restart citations-backend nginx`
3. If restart fails: proceed with Level 2 rollback
4. Check system resources: `df -h`, `free -h`

### Scenario B: Database Connection Errors

**Symptoms**: Application loads but database operations fail

**Immediate Actions**:
1. Check database files: `ls -la backend/backend/credits.db dashboard/data/validations.db`
2. Test database connectivity manually
3. Check for file corruption: `sqlite3 backend/backend/credits.db ".schema"`
4. If corruption detected: proceed with Level 3 rollback

### Scenario C: Critical Functional Bug

**Symptoms**: Application works but core functionality is broken

**Immediate Actions**:
1. Identify when the bug was introduced
2. Check recent deployments: `git log --oneline -10`
3. Perform Level 1 or Level 2 rollback based on severity
4. Test functionality thoroughly after rollback

### Scenario D: Performance Degradation

**Symptoms**: Application is extremely slow or unresponsive

**Immediate Actions**:
1. Check system resources: `top`, `df -h`, `free -h`
2. Check service logs for errors
3. Monitor database query performance
4. If recent deployment: rollback to previous version
5. If resource exhaustion: add resources or optimize

## 📋 Rollback Documentation

After any rollback, complete the following:

1. **Incident Report**
   - Date and time of rollback
   - Root cause analysis
   - Steps taken during rollback
   - Duration of service interruption
   - Impact on users/business

2. **Post-Mortem Actions**
   - [ ] Schedule post-mortem meeting
   - [ ] Update deployment procedures
   - [ ] Add additional monitoring/alerting
   - [ ] Update rollback documentation
   - [ ] Plan permanent fix for root cause

3. **Communication Update**
   - [ ] Notify all stakeholders of resolution
   - [ ] Update incident ticket with status
   - [ ] Document lessons learned
   - [ ] Share improvements with team

## 🛠️ Prevention and Preparation

### Regular Maintenance

1. **Daily**
   - [ ] Monitor application health
   - [ ] Check service logs
   - [ ] Verify backup completion

2. **Weekly**
   - [ ] Test backup restoration in staging
   - [ ] Review rollback procedures
   - [ ] Update emergency contacts

3. **Monthly**
   - [ ] Full rollback drill in staging environment
   - [ ] Update documentation
   - [ ] Review and improve monitoring

### Rollback Preparation

1. **Always maintain**:
   - Recent, tested database backups
   - Previous stable application versions tagged
   - Current rollback documentation
   - Up-to-date emergency contact information

2. **Before any deployment**:
   - Run deployment validation script
   - Create fresh backup
   - Verify rollback procedures
   - Prepare rollback plan

3. **Monitoring setup**:
   - Application performance monitoring
   - Database performance metrics
   - Service health checks
   - User experience monitoring

## 📞 Emergency Contacts and Escalation

### Primary Rollback Team
- **DevOps Lead**: [Name, Phone, Email]
- **Backend Developer**: [Name, Phone, Email]
- **Frontend Developer**: [Name, Phone, Email]
- **Database Administrator**: [Name, Phone, Email]

### Escalation Contacts
- **CTO**: [Name, Phone, Email]
- **Product Manager**: [Name, Phone, Email]
- **Customer Support Lead**: [Name, Phone, Email]

### External Contacts
- **Hosting Provider**: [Provider, Support Phone]
- **CDN Provider**: [Provider, Support Phone]
- **DNS Provider**: [Provider, Support Phone]

---

**Last Updated**: [Date]
**Version**: 1.0
**Review Date**: [Schedule next review date]

*This document should be reviewed and updated quarterly or after any major system changes.*