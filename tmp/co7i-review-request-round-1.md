You are conducting a code review.

## Task Context

### Beads Issue ID: co7i

citations-co7i: P4.3: Write product ID validation script
Status: closed
Priority: P0
Type: task
Created: 2025-12-10 22:13
Updated: 2025-12-11 21:47

Description:

## Overview

Create validation script that calls Polar API to verify all 6 product IDs exist, have correct prices, and are active.

**File to create:** `backend/scripts/validate_polar_products.py`

**Why this is needed:** Oracle Feedback #9 requires we validate product IDs before deployment. If a product ID is wrong (typo, deleted in Polar, wrong price), checkout will fail in production. This script catches issues early.

**When to run:** Before every Phase 4 deployment (mandatory pre-flight check).

## Important Context

**What does this script validate?**

For each product in `PRODUCT_CONFIG`:
1. **Exists in Polar** - Product ID is valid
2. **Price matches** - Polar price equals our configured price
3. **Is active** - Product not archived/disabled
4. **Has correct currency** - USD (not EUR, GBP, etc.)

**How it works:**

1. Load `PRODUCT_CONFIG` from `pricing_config.py`
2. For each product, call Polar API: `GET /v1/products/{product_id}`
3. Compare Polar response with our config
4. Report any mismatches
5. Exit 0 if all valid, Exit 1 if any issues

**Polar API authentication:**

Requires `POLAR_ACCESS_TOKEN` environment variable. Get from Polar dashboard → Settings → API Keys.

## Complete Implementation

See full Python script in P4.3 task description (300+ lines of validation code with error handling, price checking, currency validation, and detailed reporting).

## Time Estimate

1 hour total

## Success Criteria

- Script validates all 6 products
- Detects invalid IDs, price mismatches, archived products
- Exit codes correct (0=success, 1=errors, 2=config)
- Integrated into deployment

### What Was Implemented

Created a comprehensive Polar product validation script at `backend/scripts/validate_polar_products.py` that:
- Validates all 6 products from PRODUCT_CONFIG against Polar API
- Checks product existence, price accuracy, status (active/draft), and USD currency
- Includes robust error handling with meaningful messages
- Provides formatted output with success/failure indicators
- Uses proper exit codes (0=success, 1=errors, 2=config) for CI/CD integration
- Handles network timeouts and authentication errors gracefully

### Requirements/Plan

Key requirements from task description:
- Create validation script that calls Polar API to verify product IDs
- Validate product existence, correct prices, and active status
- Check for correct currency (USD)
- Load PRODUCT_CONFIG from pricing_config.py
- Report mismatches and exit with appropriate codes
- Must run before Phase 4 deployment as pre-flight check

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 0ac0c91ae9bb2a4c1431c964f297265bb0f94151
- HEAD_SHA: aed316c2b16cafbeddb2625c94dbffb0a9fb98a8

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