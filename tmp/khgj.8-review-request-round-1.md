You are conducting a code review.

## Task Context

### Beads Issue ID: khgj.8

citations-khgj.8: Update Backend Fallback for 4-Variant Assignment
Status: open
Priority: P2
Type: task
Created: 2025-12-17 14:12
Updated: 2025-12-18 11:42

Description:

## Context
Backend app.py has fallback logic that assigns a variant if the frontend does not provide one. Currently assigns "1" or "2". Must be updated to use the new 4-variant scheme.

## Why This Matters
If a user somehow reaches the backend without frontend variant assignment (edge case: API calls, old cached app), the backend should still assign a valid 4-variant ID.

## Pre-Research Findings

**File**: backend/app.py
**Lines to modify**: 947 AND 1412 (TWO locations!)

### Location 1: /api/validate endpoint (line 947)
```python
if not experiment_variant:
    experiment_variant = random.choice(["1", "2"])
```

### Location 2: /api/validate/async endpoint (line 1412)
```python
if not experiment_variant:
    experiment_variant = random.choice(["1", "2"])
```

## Implementation

Change BOTH locations to:
```python
valid_variants = ["1.1", "1.2", "2.1", "2.2"]
if not experiment_variant or experiment_variant not in valid_variants:
    experiment_variant = random.choice(valid_variants)
```

Note: We also validate existing variant value in case old "1"/"2" comes through.

## Verification
1. Call /api/validate/async without X-Experiment-Variant header
2. Check logs for "Assigned missing experiment variant: X.X"
3. Verify X.X is one of 1.1, 1.2, 2.1, 2.2

## Dependencies
None - standalone change

## Files
- MODIFY: backend/app.py (lines 947 AND 1412)

### What Was Implemented

Updated both /api/validate and /api/validate/async endpoints in backend/app.py to use a 4-variant scheme (1.1, 1.2, 2.1, 2.2) instead of the old 2-variant scheme (1, 2). The code now validates that any provided variant is in the valid list and reassigns old variant values to new ones.

### Requirements/Plan

Key requirements from task description:
1. Update fallback logic in TWO locations in backend/app.py (lines 947 and 1412)
2. Change from 2-variant scheme ["1", "2"] to 4-variant scheme ["1.1", "1.2", "2.1", "2.2"]
3. Add validation to ensure existing variant values are in the valid list
4. Handle old "1"/"2" values by reassigning them to new variants
5. Log when fallback assignment occurs

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 69e7a836084402470ae3bf38a33015c8c9a06dcd
- HEAD_SHA: c39913b7c1283ec079894585e32be69caca0e4fd

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