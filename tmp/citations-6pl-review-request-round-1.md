You are conducting a code review.

## Task Context

### Beads Issue ID: citations-6pl

citations-6pl: feat: add OpenAI retry logic with exponential backoff
Status: in_progress
Priority: P0
Type: feature
Created: 2025-11-21 21:12
Updated: 2025-11-21 22:57

Description:


## Progress - 2025-11-21
- ✅ Implemented retry logic with exponential backoff in OpenAI provider
- ✅ Added comprehensive test suite with 6 test cases covering all retry scenarios
- ✅ Refactored code to extract reusable retry helper method
- ✅ Verified all tests pass and no existing functionality is broken

## Key Implementation Details
- **Retry Logic**: 3 max attempts with exponential backoff (2s, 4s, 8s delays)
- **Retryable Errors**: APITimeoutError and RateLimitError
- **Non-Retryable Errors**: AuthenticationError and APIError (fail immediately)
- **Logging**: Warning level for retry attempts with detailed messages
- **Error Handling**: Clear ValueError with user-friendly message after max retries

## Files Modified
- Modified: backend/providers/openai_provider.py (validate_citations method, lines 32-119)
- Added: tests/test_retry_logic.py (comprehensive test suite)

## Testing
- All 6 retry logic tests pass
- Existing provider tests still pass
- Verified proper exception handling order (specific errors before generic APIError)


Labels: [async-frontend-processing backend needs-review]

Dependents (2):
  [blocks] citations-0o2: test: write integration tests with real LLM [P0]
  [parent-child] citations-ry7: feat: implement citation batching to avoid timeout issues [P1]

### What Was Implemented

Implemented OpenAI retry logic with exponential backoff in the `validate_citations` method. Added a retry loop that attempts up to 3 times with exponential delays (2s, 4s, 8s) for transient errors (APITimeoutError and RateLimitError). Created a helper method `_handle_retry_error` to centralize retry logic and added comprehensive test suite with 6 test cases covering all retry scenarios, non-retry scenarios, and logging.

### Requirements/Plan

**Original Task Requirements:**
- Add retry loop (max 3 attempts) to validate_citations()
- Implement exponential backoff (2s, 4s, 8s)
- Retry on APITimeoutError and RateLimitError
- Don't retry on AuthenticationError or APIError
- Log retry attempts with warning level
- Raise ValueError with clear message after max retries

**Implementation Notes:**
- Use asyncio.sleep() for backoff (async context)
- Retry formula: wait_time = retry_delay * (2 ** attempt)
- Log each retry: "OpenAI API error (attempt X/3): <error>. Retrying in Ys..."
- After max retries: raise ValueError("Request timed out after multiple retries. Please try again later.")

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 94fe904b6b2422267b60d5707c4e80e0eb08bff1
- HEAD_SHA: 8d53e615a639280c63cd2e3f1c4ed9b3e12eac74

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