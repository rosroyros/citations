You are conducting a code review.

## Task Context

### Beads Issue ID: citations-0o2

Status: closed
Priority: P0
Type: task

Description:
## Objective
Write integration tests using real OpenAI API to verify end-to-end functionality.

## Tasks
- [ ] Create tests/test_async_jobs_integration.py
- [ ] Test: Small batch (2 citations) with real LLM completes in ~30s
- [ ] Test: Paid user with X-User-Token header (verify credits deducted)
- [ ] Test: Free user with X-Free-Used header (verify partial results)
- [ ] Test: Retry logic on OpenAI timeout (simulate with timeout=1s)
- [ ] Test: Concurrent jobs (create 3 jobs simultaneously, all complete)
- [ ] Create tests/fixtures/test_citations.py (small/medium/large batch fixtures)

## Files
- Create: tests/test_async_jobs_integration.py
- Create: tests/fixtures/test_citations.py
- Reference: docs/plans/2025-11-21-async-polling-timeout-fix-design.md (Testing section)

## Environment
- Run locally only (not in CI/CD due to cost)
- Requires: OPENAI_API_KEY in environment
- Uses real OpenAI API (costs ~0.01 per test run)

## Verification
Run: pytest tests/test_async_jobs_integration.py -m integration -v
Expected: All tests pass in 2-5 minutes

## Dependencies
Requires: citations-si1, citations-6pl (backend + retry logic must be implemented)

### What Was Implemented

Created comprehensive integration test suite with real OpenAI API calls. Implemented tests/test_async_jobs_integration.py with 5 integration tests covering async job processing, credit management, partial results, retry logic, and concurrent jobs. Also created tests/fixtures/test_citations.py with reusable test citation data. Applied TDD methodology with RED-GREEN-REFACTOR cycles. All tests pass (5 passed, 0 failed in 3:29 total).

### Requirements/Plan

Key requirements from task description and design document:

From design document (Integration Tests section):
- ✅ Small batch (2 citations) completes in ~30s
- ✅ Paid user with X-User-Token header (credits deducted)
- ✅ Free user with X-Free-Used header (partial results)
- ✅ Retry logic on OpenAI timeout
- ✅ Concurrent jobs (create 3 jobs simultaneously, all complete)

From task description:
- ✅ Create tests/test_async_jobs_integration.py
- ✅ Create tests/fixtures/test_citations.py (small/medium/large batch fixtures)
- ✅ Real OpenAI API integration (costs ~0.01 per test run)
- ✅ Run: pytest tests/test_async_jobs_integration.py -m integration -v

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 1cd721c44e00057a5dc675e10cb420766a76d5d3
- HEAD_SHA: 341b3e63cdc57cdcfe2116fe5af10276d717c70f

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