You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-8csr

Title: Add quote test job indicator to validation jobs
Status: open
Priority: P0
Type: feature

### Current Status

We have explored the codebase and identified the complete flow of validation jobs:
1. Jobs are created at POST /api/validate/async endpoint (backend/app.py:886-959)
2. Jobs are stored in-memory with fields like status, user_type, provider, etc.
3. Jobs are sent to LLM providers (OpenAI/Gemini) via background processing
4. App logs capture job events in structured format
5. Dashboard parses logs and stores in SQLite validations table
6. Current test exclusion logic fetches citations and checks for "test" in dashboard

### The Question/Problem/Dilemma

User wants to add a quote test job indicator with these requirements:
- Add indicator to any validation job that includes "test" in the first 100 characters
- Append `[TEST_JOB_DETECTED]` to the job BEFORE sending to LLM
- Add this to app log
- Parse this in main log parser
- Add to validation table for dashboard
- Adapt dashboard to use this field instead of current citation-based filtering

We've designed a 6-part approach:
1. Detection in POST endpoint - check raw request body's citations field (first 100 chars of concatenated string)
2. Add `is_test_job` boolean field to job storage
3. Log `TEST_JOB_DETECTED: job_id={job_id} indicator=[TEST_JOB_DETECTED]` to app.log
4. Add `is_test_job BOOLEAN DEFAULT FALSE` column to validations table
5. Update log parser to recognize TEST_JOB_DETECTED pattern and set database field
6. Simplify dashboard filtering to use `is_test_job` field directly

### Relevant Context

Key technical details:
- System uses FastAPI backend with in-memory job storage (TTL 30min)
- Dashboard at port 4646 uses SQLite with validations table
- Current test exclusion is inefficient - fetches all citations per job
- Jobs already have metadata fields like user_type, provider, token_usage
- Log parser already extracts structured data from app.log
- Dashboard frontend filters with JavaScript `filterOutTestJobs()` function

### Supporting Information

Key files involved:
- `backend/app.py` - POST endpoint (lines 886-959) and job creation
- `dashboard/log_parser.py` - parses app.log into database
- `dashboard/database.py` - validations table schema (lines 45-66)
- `dashboard/static/index.html` - frontend filtering (lines 1510-1540)

Current job structure includes:
```python
{
    'status': 'pending',
    'created_at': timestamp,
    'user_type': 'paid'/'free',
    'provider': 'openai'/'gemini',
    'token': token,
    'free_used': count,
    'model_preference': 'model_a'/'model_b'
}
```