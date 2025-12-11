You are conducting a code review.

## Task Context

### Beads Issue ID: iixt

citations-iixt: P3.2: Add tracking to validation endpoint
Status: open
Priority: P1
Type: task
Created: 2025-12-10 22:11
Updated: 2025-12-11 17:59

Description:
## Overview

Add tracking to the validation endpoint to log when users see the pricing table. This is the first event in the upgrade funnel.

**File to modify:** `backend/app.py`
**Function to modify:** `/api/validate` or `/api/validate/async` endpoint

**Why this is needed:** When a validation request is denied due to insufficient credits/access, we show the pricing table. We need to log this event (`pricing_table_shown`) to measure:
- How many users see each pricing variant
- Conversion rate from "pricing shown" to "purchase completed"
- Drop-off at first step of funnel

**Oracle Feedback #5:** Track experiment_variant on this event (and all events) to enable cohort analysis.

### What Was Implemented

Added pricing table tracking to both validation endpoints (/api/validate and /api/validate/async). Implemented log_upgrade_event calls for three scenarios where users see the pricing table: free tier limit reached, zero credits (402 error), and insufficient credits. Added support for X-Experiment-Variant header and created a test script for verification.

### Requirements/Plan

Key requirements from task description:
1. Log pricing_table_shown event when users are shown pricing table
2. Support experiment_variant tracking via X-Experiment-Variant header (optional)
3. Track in both /api/validate and /api/validate/async endpoints
4. Log should include: timestamp, event, token, experiment_variant
5. Should not break validation if logging fails
6. Include metadata with reason for pricing display

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 1b843adb868a1f205bc5595d4cb247f34e841a87
- HEAD_SHA: 5791e70f40259235214cd6ce087a6d8e602d2dfa

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