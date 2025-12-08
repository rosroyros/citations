You are conducting a code review.

## Task Context

### Beads Issue ID: 75kj

citations-75kj: Gemini A/B: Backend Routing, Fallback & Logging
Status: in_progress
Priority: P1
Type: task
Created: 2025-12-08 17:49
Updated: 2025-12-08 20:15

Description:
## Context
Once the provider exists, the backend needs to route requests based on the client's preference and handle data storage/logging without altering the database schema.

## Requirements
1. **Routing Logic (`backend/app.py`):**
   - In `validate_citations`, extract `X-Model-Preference` header.
   - **Logic:**
     - `model_b` -> Attempt `GeminiProvider`.
     - `model_a` (or missing/invalid) -> Use `OpenAIProvider`.
   - **Fallback Mechanism (Critical):**
     - Wrap Gemini call in try/catch.
     - If it fails: Log error, switch to `OpenAIProvider` immediately, and mark provider as `model_a` (fallback) for that job.

2. **In-Memory Storage:**
   - When creating the `job` object in `jobs` dict, store the *actual* provider used (internal ID: `model_a` or `model_b`).
   - This ensures `/api/dashboard` (which reads `jobs`) serves the correct data immediately.

3. **Structured Logging:**
   - Emit a structured log line in `app.log` for future parsing/auditing.
   - Format: `logger.info(f"PROVIDER_SELECTION: job_id={job_id} model={internal_id} status=success fallback={bool}")`

### What Was Implemented

Implemented backend routing for Gemini A/B testing with the following changes:
1. Added header-based provider routing via `X-Model-Preference` header
2. Implemented fallback mechanism from Gemini to OpenAI on failure
3. Added storage of actual provider used in the jobs dict for dashboard visibility
4. Added structured logging for provider selection events
5. Updated both sync and async validation endpoints to support routing
6. Added provider field to dashboard API response

### Requirements/Plan

Key requirements from task description:
- Extract `X-Model-Preference` header in `validate_citations`
- Route to Gemini for `model_b`, OpenAI for `model_a` or missing
- Implement try/catch around Gemini calls with fallback to OpenAI
- Store actual provider (`model_a` or `model_b`) in jobs dict
- Add structured logging with format: `PROVIDER_SELECTION: job_id={job_id} model={internal_id} status=success fallback={bool}`

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 9a74ed1fa4d1aa0a3bd1f4dc35394a68d610f170
- HEAD_SHA: 93ec19cb79d6e1135340798242038e33a83a2987

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