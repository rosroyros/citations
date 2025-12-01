You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-ouof

**Beads Issue Summary:**
End-to-end testing for complete gated flow validation

### Current Status

This issue was originally about E2E testing for gated flow validation, but during debugging we discovered a critical database schema regression that prevents citation text from appearing in the operational dashboard.

**What We've Accomplished:**
1. ✅ Original gated flow E2E testing completed successfully (17/17 frontend tests, 30/32 backend tests)
2. ✅ Discovered database schema drift issue during citation text debugging
3. ✅ Applied Claude Oracle's gradual migration strategy locally:
   - Added missing columns: citations_text, completed_at, duration_seconds, token_usage_*
   - Preserved existing validation_status column (critical for gated results)
   - Updated database.py to handle both status and validation_status columns
   - Verified local functionality works correctly

**Current Problem:** We only implemented the fix locally. Production still has the schema mismatch.

### The Question/Problem/Dilemma

**Primary Question:** What's the safest and most effective way to deploy our database schema migration to production?

**Specific Deployment Questions:**
1. Should we use the existing `deployment/scripts/deploy_with_citations.sh` script or our custom `tools/gradual_migration_20251201.py`?
2. Our local changes include updated database.py with compatibility layer - will the production deployment script handle this correctly?
3. Should we commit our database.py changes first, then deploy, or handle both together?

**Current Local Solution:**
- **Migration Script**: `tools/gradual_migration_20251201.py` (Claude's safe approach)
- **Database Code**: Updated `dashboard/database.py` with compatibility for both `status` and `validation_status`
- **Approach**: Gradual migration preserving existing gated results functionality

**Production Environment:**
- VPS: 178.156.161.140 (deploy@)
- Database: `/opt/citations/dashboard/data/validations.db`
- Records: 94 existing validation records
- Current schema: Has `validation_status` (not `status`), missing `citations_text` and other columns

### Relevant Context

**Why This Matters for citations-ouof:**
- This issue depends on dashboard integration (citations-iiqi)
- Citation text display is critical for monitoring gated flow performance
- We can't properly test the complete gated flow without citation analytics working

**Risk Considerations:**
- 94 production validation records must be preserved
- Gated results functionality depends on existing `validation_status` column
- Database downtime affects the entire citation validation system

**Two Potential Approaches:**

**Option A: Use Existing Production Script**
```bash
ssh deploy@178.156.161.140
cd /opt/citations
git pull origin main  # Our database.py changes
./deployment/scripts/deploy_with_citations.sh
```

**Option B: Manual Migration**
```bash
ssh deploy@178.156.161.140
cd /opt/citations
git pull origin main
cp tools/gradual_migration_20251201.py .
python3 gradual_migration_20251201.py
```

### Supporting Information

**Our Local Database Changes:**
- Added 6 missing columns without disrupting existing schema
- Compatibility layer in database.py handles both column naming schemes
- Preserves all existing gated results functionality
- Tested successfully with 94 records

**Production Deployment Script Analysis:**
- `deploy_with_citations.sh` expects database.py to auto-create missing columns
- Includes comprehensive verification and rollback procedures
- Has backup/restore capabilities
- But may not handle the validation_status vs status compatibility issue

**Key Files Modified:**
1. `dashboard/database.py` - Added compatibility layer for status columns
2. `tools/gradual_migration_20251201.py` - Claude's safe migration script

What approach would you recommend for deploying these database changes to production safely?