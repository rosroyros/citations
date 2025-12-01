You are providing technical guidance and problem solving assistance with detailed system analysis.

## Issue Context
### Beads Issue ID: citations-ouof

**Beads Issue Summary:**
This issue is about end-to-end testing for gated flow validation, but during debugging we discovered a critical database schema mismatch that's preventing citation text from appearing in the operational dashboard.

### Current Status

**Problem Discovered**: The citation text functionality in the operational dashboard has regressed. After systematic debugging, I found that:

1. **Code is Working Correctly**:
   - `dashboard/log_parser.py` properly extracts citation text from logs
   - `dashboard/cron_parser.py` correctly maps fields to database schema
   - `dashboard/api.py` correctly maps database fields to API response
   - Dashboard HTML has comprehensive citation display functionality

2. **Root Cause**: Database schema mismatch
   - Current database schema has `validation_status` instead of `status`
   - Missing critical columns: `citations_text`, `completed_at`, `duration_seconds`, `token_usage_*`
   - Database migration fails because it assumes columns exist
   - 94 records exist but can't store citation data properly

3. **Current Database Schema**:
   ```
   job_id TEXT
   user_type TEXT
   citation_count INTEGER
   validation_status TEXT  ← Should be 'status'
   created_at TIMESTAMP
   results_gated BOOLEAN
   gated_at TIMESTAMP
   results_ready_at TIMESTAMP
   results_revealed_at TIMESTAMP
   time_to_reveal_seconds INTEGER
   gated_outcome TEXT
   error_message TEXT
   ```

4. **Expected Schema** (from database.py):
   ```
   job_id TEXT PRIMARY KEY
   created_at TEXT NOT NULL
   completed_at TEXT        ← MISSING
   duration_seconds REAL    ← MISSING
   citation_count INTEGER
   token_usage_prompt INTEGER   ← MISSING
   token_usage_completion INTEGER ← MISSING
   token_usage_total INTEGER     ← MISSING
   user_type TEXT NOT NULL
   status TEXT NOT NULL     ← Exists as 'validation_status'
   error_message TEXT
   citations_text TEXT     ← MISSING
   ```

### The Question/Problem/Dilemma

**Primary Issue**: How should we fix the database schema mismatch without breaking existing functionality?

**Secondary Concerns**:
1. Will our fix impact the gated results functionality that this issue is testing?
2. How do we ensure we don't break the 94 existing validation records?
3. What's the safest migration strategy for production?

**Current Fix Options Considered**:
1. **Database Migration**: Add missing columns, rename `validation_status` → `status`
2. **Fresh Database**: Delete and recreate, losing 94 records
3. **Schema Adapter**: Modify code to work with both schemas

**Specific Request for Analysis**:
Please provide detailed analysis of:
1. Which fix approach is safest for the broader citation validation system?
2. How will this impact the gated results flow testing?
3. What are the risks to the operational dashboard functionality?
4. Should we proceed with migration, and if so, what precautions are needed?

### Relevant Context

**System Architecture**:
- Citation validation is the core functionality
- Gated results is a newer feature built on top of citation validation
- Operational dashboard provides monitoring and analytics
- Database stores validation results with citation text for display

**Recent Changes**:
- Recent commits added citation text extraction functionality (fa51f5a)
- Database schema creation code was updated but migration failed
- The system appears to have an old schema that never got properly migrated

**Dependencies**:
This issue depends on citations-xnp6 (main gated results feature) and citations-2gij (backend API), suggesting the schema issues could impact the gated flow testing.

### Supporting Information

**Error Evidence**:
```
sqlite3.OperationalError: no such column: status
sqlite3.OperationalError: no such column: citations_text
```

**Code Evidence**:
- `database.py:82`: Tries to create index on non-existent 'status' column
- `database.py:180`: Tries to insert 'citations_text' field that doesn't exist
- Current schema suggests this is an old gating-focused database, not the full validation schema

**Production Considerations**:
- System appears to be in production with 94 validation records
- Gated results functionality may be depending on current schema
- Any schema change needs to preserve existing functionality

Please provide concrete guidance on the safest approach to resolve this schema mismatch while ensuring we don't break the citation validation system or the gated results functionality we're testing.