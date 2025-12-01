You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-hh1f

citations-hh1f: Bug: Dashboard tokens not displaying - token usage data missing from database
Status: closed
Priority: P2
Type: bug
Created: 2025-12-01 12:11
Updated: 2025-12-01 12:25

## Current Status

**ISSUE PARTIALLY RESOLVED**: We successfully fixed the data pipeline (cron job + database + API) but broke the frontend display with sed commands. Current state:

1. ✅ **Data Pipeline Works**: Token data flows from logs → database → API correctly
2. ✅ **Cron Job Fixed**: PYTHONPATH corrected, parsing 1,235 token logs  
3. ✅ **Database**: 233/300 records have token data (78% coverage)
4. ✅ **API Response**: Returns correct token_usage objects with prompt/completion/total
5. ❌ **Frontend Broken**: JavaScript syntax errors from failed sed commands
6. ❌ **Dashboard Shows**: Still displays '-' instead of token counts

## The Question/Problem/Dilemma

**JavaScript Field Mapping Issue**: Dashboard still shows '-' despite successful backend fixes.

**Technical Problem**: 
- Frontend expects API response format: `{ "validations": [{"job_id": "...", "token_usage": {...}}] }`
- API currently returns: `{ "jobs": [{"id": "...", "token_usage": {...}}] }`

**Broken Attempts**: My sed commands to fix field mappings introduced syntax errors:
```
[Error] SyntaxError: Unexpected token '.'. Expected a ')' or a ',' after a parameter declaration.
[Error] ReferenceError: Can't find variable: loadData
```

**Options Being Considered**:
1. **Fix API Response Format** (Preferred): Change API to return format frontend expects
2. **Fix Frontend JavaScript**: Update frontend to handle current API format
3. **Manual Edit Approach**: Carefully edit files instead of using sed commands

**Specific Blocking Issues**:
- Complex sed commands create syntax errors in Python/JavaScript
- Need to map API fields: jobs→validations, id→job_id, timestamp→created_at, etc.
- Risk of breaking other functionality with mass text replacements

**What specific guidance I need**:
1. **Recommended approach**: Should I fix API or frontend? What's least risky?
2. **Implementation strategy**: How to safely update field mappings without breaking code?
3. **Testing approach**: How to verify JavaScript fixes don't introduce new errors?
4. **Alternative approaches**: Are there simpler solutions I'm overlooking?

## Relevant Context

**Current API Response** (working):
```json
{
  "jobs": [
    {
      "id": "a2542e51-66d5-4b9d-8a48-b35ffabe7aae",
      "timestamp": "2025-12-01T10:15:00Z", 
      "token_usage": {"prompt": 798, "completion": 3972, "total": 4770}
    }
  ]
}
```

**Frontend JavaScript Expects**:
```javascript
updateTable(data.validations.map(validation => {
  const tokens = validation.token_usage ? validation.token_usage.total.toLocaleString() : '-';
  // ... expects validation.job_id, validation.created_at, etc.
```

**Current JavaScript Errors**:
```
[Error] SyntaxError: Unexpected token '.'. Expected a ')' or a ',' after a parameter declaration.
[Error] ReferenceError: Can't find variable: loadData  
```

## Supporting Information

**Backend Infrastructure Works**:
- Token logging: 1,235 entries in production logs
- Cron job: Fixed PYTHONPATH, running every 5 minutes  
- Database: SQLite with token_usage_prompt/completion/total fields
- API: FastAPI endpoint successfully serving token data

**Files Involved**:
- `/opt/citations/dashboard/api.py` (API endpoint)
- `/opt/citations/dashboard/static/index.html` (Frontend JavaScript)
- `/opt/citations/dashboard/data/validations.db` (Database)

**Error Context**: JavaScript errors appear in browser console, preventing dashboard data loading.
