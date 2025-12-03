You are conducting a code review.

## Task Context

### Beads Issue ID: citations-pw2g

citations-pw2g: Fix: Dashboard log parser missing REVEAL_EVENT support
Status: closed
Priority: P0
Type: bug

## Context
The 'click to reveal' gating feature is working on the frontend and backend (logging the event), but the data is not appearing in the dashboard.
Investigation revealed that the `dashboard/log_parser.py` is missing the logic to parse the `REVEAL_EVENT` log entries.
As a result, the reveal status is never extracted from the logs and never makes it into the dashboard database.

## Requirements
- [x] Update `dashboard/log_parser.py` to parse `REVEAL_EVENT` lines.
- [x] Extract `job_id`, `outcome`, and `timestamp`.
- [x] Ensure this data is merged into the job record returned by the parser.
- [x] Verify that the data ingestion pipeline (whatever calls the parser) saves this to the database.

### What Was Implemented

I updated the dashboard data pipeline to correctly process "click to reveal" events. This involved:
1. Updating `dashboard/database.py` to add `results_revealed`, `results_revealed_at`, and `results_gated` columns to the `validations` table and providing a method to update these fields.
2. Modifying `dashboard/log_parser.py` to parse `REVEAL_EVENT` log lines and extract gating status from completion logs.
3. Updating `dashboard/cron_parser.py` to handle partial job updates (reveal-only events) by updating existing records instead of trying to insert incomplete new ones.

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: c8cd1033a6730f478b8fea6c9abe5f2dd25e1e12
- HEAD_SHA: 17c1088f980e5f68b8fe8cfaca31b28eca40bb63

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
