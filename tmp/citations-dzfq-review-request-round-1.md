You are conducting a code review.

## Task Context

### Beads Issue ID: citations-dzfq

## Goal
Consolidate fragmented event tracking ( vs ) into a single, robust source of truth: **UPGRADE_WORKFLOW**.

## Why?
1.  **Fragmented Data**: Currently,  logs  (JSON) for financial data and  (String) for the Dashboard.
2.  **Missing Link**: Financial webhooks lack the , making it impossible to link Revenue to UX sessions.
3.  **Duplication**: We are maintaining two parsers ( vs ).

## The Solution
1.  **Unified Format**: All events (Frontend & Backend) will use the Dashboard's key-value string format:
    `UPGRADE_WORKFLOW: job_id=X event=Y variant=Z ...`
2.  **Dual Source**:
    *   **Webhooks** (Backend) -> Log `purchase_completed` (The Financial Truth).
    *   **Frontend** -> Logs `success` (The UX Truth).
    *   Both are valid and necessary for different views (Audit vs Flow).
3.  **Dashboard Continuity**: We map `purchase_completed` -> `success` in `log_parser.py` so the Dashboard's Green Checkmark ✅ works seamlessly for both
 event types.

## Implementation Standard
*   **Regex**: `r'UPGRADE_WORKFLOW: job_id=([a-f0-9-]+|None) event=(\w+)(?: variant=(\w+))?(?: product_id=([\w_]+))?(?: amount_cents=(\d+))?'`
*   **Mapping**:
    *   `locked` -> Lock 🔒
    *   `clicked_upgrade` -> Cart 🛒
    *   `checkout_started` -> Card 💳
    *   `purchase_completed` -> Check ✅

### What Was Implemented

Refactored the upgrade event tracking system to use a unified `UPGRADE_WORKFLOW` string format.
- **Frontend**: Updated `PricingTablePasses.jsx`, `PricingTableCredits.tsx`, `UpgradeModal.jsx`, and `Success.jsx` to retrieve `job_id` from URL/storage and include it in `create-checkout` API calls and success event logging.
- **Backend**: Updated `app.py` to log events in the new `UPGRADE_WORKFLOW` format, extract `job_id` from checkout requests, and propagate it to webhooks (`log_upgrade_event` updated).
- **Analytics**: Updated `analytics.py` to parse the new log format using regex, maintaining backward compatibility for legacy JSON events.
- **Cleanup**: Legacy `UPGRADE_EVENT` JSON logging moved to debug level.

### Requirements/Plan

1.  **Unified Format**: `UPGRADE_WORKFLOW: job_id=... event=... variant=... product_id=... amount_cents=...`
2.  **Job ID Propagation**: Frontend -> Backend (create-checkout) -> Polar -> Webhook -> Logs.
3.  **Regex Parsing**: Analytics must parse the new format robustly.
4.  **Verification**: Tests should confirm the parser works for both new and legacy formats.

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 2e0cf876fae21b5a627912b25b252918cbc23487
- HEAD_SHA: 62a13f4c46689aafed8cc94312529c15ff05236e

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
