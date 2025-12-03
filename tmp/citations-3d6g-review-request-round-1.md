You are conducting a code review.

## Task Context

### Beads Issue ID: citations-3d6g

citations-3d6g: Add detailed timeout instrumentation to diagnose inconsistent OpenAI API timeouts
Status: in_progress
Priority: P1
Type: task

Description:
## Systematic Debugging Session Summary (Dec 2, 2024)

### What We Learned

**Initial False Assumptions (Debunked)**:
- ❌ Connection pool exhaustion over 27 days → Backend restarted 36 times, not long-running
- ❌ Old OpenAI SDK (1.3.0) → Production uses 2.7.1, system python has 1.3.0
- ❌ Timeout parameter ignored → Parameter exists in SDK, but inconsistently enforced

**Root Cause Confirmed**:
Timeout is passed correctly but httpx/httpcore doesn't consistently enforce it during response reading.

### Why Instrumentation is Critical

Without detailed per-attempt logging, we cannot determine:
1. Are some requests inheriting different timeout config?
2. Does model type affect timeout behavior?
3. Does request size correlate with timeout enforcement?
4. Is httpx client state changing between requests?

Current logs only show start/end times, not the actual timeout enforcement mechanism.

### What Was Implemented

I modified `backend/providers/openai_provider.py` to add detailed logging within the retry loop.
- It now calculates and logs the estimated request size (in characters) before the loop.
- Inside the loop, it logs the attempt number, configured timeout, model, and size before the call.
- It measures and logs the exact duration of the call upon success.
- In case of `APITimeoutError` or `RateLimitError`, it logs the specific error type along with the duration and the configured timeout to highlight discrepancies.
- The `max_retries` and `retry_delay` variables were moved up slightly to be available for the loop logic.

### Requirements/Plan

- Log detailed configuration for each request attempt (timeout value, model).
- Log the exact start time and duration of each attempt.
- Log specific timeout enforcement details (elapsed time vs configured timeout) when exceptions occur.
- Estimate and log the request size (number of characters in messages) to see if size correlates with timeouts.

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: f0a798e9a9983963d2fe3bc9106c3ae8e1cc69c9
- HEAD_SHA: e1fdd08e7147d40611f000b4904aa1c5c3a4d739

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
