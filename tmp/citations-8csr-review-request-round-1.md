You are conducting a code review.

## Task Context

### Beads Issue ID: citations-8csr

Add quote test job indicator to validation jobs
Status: in_progress
Priority: P0
Type: feature

Description:


Add quote test job indicator to validation jobs

## Oracle Feedback Summary
Oracle consulted via gemini - identified critical issues with original plan:

### Key Findings:
1. **Steps 1-4 already implemented** in backend/app.py and dashboard/database.py
2. **Critical missing pieces**: Log parser and dashboard query implementation
3. **Detection logic dangerous**: 'test' substring will false positive on legitimate citations

### Changes Implemented:
1. **Backend detection**: Changed from 'test' in first 100 chars to 'testtesttest' anywhere in citations
2. **Database support**: Added is_test_job filter parameter to get_validations() and get_validations_count()
3. **API support**: Added is_test_job query parameter to /api/validations and /api/validations/count endpoints
4. **Frontend optimization**: Simplified filterOutTestJobs() to use database field instead of expensive API calls

### Implementation Details:
- Backend checks for 'testtesttest' (case-insensitive) in request.citations
- Sets is_test_job=True and logs TEST_JOB_DETECTED when found
- Dashboard can now filter by is_test_job=false to exclude test jobs
- No test scripts needed updating - E2E tests use real citations

### Next Steps:
- Test with a citation containing 'testtesttest' to verify end-to-end flow

### What Was Implemented

Added a test job indicator feature that detects citations containing "testtesttest" and marks them as test jobs. The implementation includes:
1. Backend detection logic in the async validation endpoint
2. Database query support for filtering by is_test_job flag
3. API endpoints updated to accept is_test_job filter parameter
4. Frontend optimization to use database flag instead of expensive API calls

### Requirements/Plan

Add a new issue to implement a quote test job indicator for any validation job that includes "testtesttest" in the submitted text. The indicator should be:
- Appended to the job before sending to LLM
- Added to app log
- Parsed by main log parser
- Added to validation table for dashboard
- Used by dashboard to exclude test jobs from display

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 808367c0874e129eae400f065a91667f453087da
- HEAD_SHA: 1d2bf573cf5084f20bb1263b6c2bdc1cca816ae6

Use git commands (git diff, git show, git log, etc.) to examine the changes.

## Review Criteria

Evaluate the implementation against these criteria:

**Adherence to Task:**
- Does implementation match task requirements?
- Were all requirements addressed?
- Any scope creep or missing functionality?

**Security:**
- SQL injection, XSS, command injection vulnerabilities
- Hardcoded secrets or credentials
- Input validation and sanitization

**Code Quality:**
- Follows project standards and patterns
- Clear naming and structure
- Appropriate error handling
- Edge cases covered

**Testing:**
- Tests written and passing
- Coverage adequate
- Tests verify actual behavior
- **Frontend visual/UX changes: Playwright tests REQUIRED for any visual or user interaction changes**

**Performance & Documentation:**
- No obvious performance issues
- Code is self-documenting or commented

## Required Output Format

Provide structured feedback in these categories:

1. **Critical**: Must fix immediately (security, broken functionality, data loss)
2. **Important**: Should fix before merge (bugs, missing requirements, poor patterns)
3. **Minor**: Nice to have (style, naming, optimization opportunities)
4. **Strengths**: What was done well

**IMPORTANT**: Verify implementation matches task requirements above.

Be specific with file:line references for all issues.