You are conducting a code review.

## Task Context

### Beads Issue ID: citations-ugmo

citations-ugmo: P1.2: Write database migration script
Status: in_progress
Priority: P1
Type: task
Created: 2025-12-10 22:05
Updated: 2025-12-11 11:00

Description:

## Overview

Create database migration script to add new tables (user_passes, daily_usage) and columns (experiment_variant, product_id) for A/B test.

**File to create:** `backend/migrations/add_pricing_tables.py`

**Why this is needed:** Phase 1 creates database schema WITHOUT deploying code changes. Tables exist but are unused. This allows safe rollback if issues arise.

## Critical Oracle Feedback

**Oracle #3:** Use Unix timestamps (INTEGER) not date strings (TEXT) for timezone handling
**Oracle #6:** Add UNIQUE constraint on order_id for idempotency (prevents double-grants)

## Complete Implementation

Create `backend/migrations/add_pricing_tables.py` with this exact code:

[Python code provided in issue - creates user_passes table with UNIQUE order_id, daily_usage table, adds columns to validations table]

## Verification Steps

1. **Make script executable and run locally**
2. **Verify tables created with correct schemas**
3. **Check indexes exist**
4. **Test idempotency (run twice - should not error)**

## Success Criteria

- ✅ Migration script runs without errors
- ✅ `user_passes` table created with UNIQUE order_id constraint
- ✅ `daily_usage` table created with composite primary key
- ✅ Index on `user_passes(token, expiration_timestamp)` exists
- ✅ `validations.experiment_variant` column added
- ✅ `validations.product_id` column added
- ✅ Running migration twice is idempotent (no errors)

### What Was Implemented

Created a database migration script that:
1. Creates `user_passes` table with token as primary key, UNIQUE order_id constraint, and Unix timestamps
2. Creates `daily_usage` table with composite primary key for tracking daily citations
3. Adds `experiment_variant` and `product_id` columns to validations table
4. Handles two separate databases (credits.db and validations.db)
5. Includes proper error handling and idempotency checks

### Requirements/Plan

Key requirements from task description:
- Create migration script at backend/migrations/add_pricing_tables.py
- Use Unix timestamps (INTEGER) not date strings (Oracle #3)
- Add UNIQUE constraint on order_id for idempotency (Oracle #6)
- Migration must be safe to run multiple times (IF NOT EXISTS)
- Add experiment_variant and product_id columns to validations table
- Create index on user_passes(token, expiration_timestamp)

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 8b004941f475f6877eb2bb83b9a3579a4b46ba25
- HEAD_SHA: a2f0c8b065692ebf18c5376a0b955f6fca79456e

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