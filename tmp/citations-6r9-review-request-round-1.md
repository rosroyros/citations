You are conducting a code review.

## Task Context

### Beads Issue ID: citations-6r9

**Title:** Analytics Phase 1-2: Fix Event Naming and Add Critical Conversion Tracking

**Status:** in_progress
**Priority:** P1
**Type:** feature

**Description:**

Current analytics has critical naming confusion between product actions ("Check My Citations") and conversion actions ("Upgrade Now") using the same `cta_clicked` event. Additionally, missing key conversion tracking events make it impossible to analyze user behavior and optimize conversion funnels.

### What Was Implemented

Replaced generic `cta_clicked` event with specific conversion events (`validation_started`, `upgrade_clicked`), added new tracking for mini checker interactions, free limit reached, partial results viewed, and validation attempts. Enhanced existing events with interface_source parameter for better differentiation.

### Requirements/Plan

**Phase 1: Fix Event Naming**
- Replace trackCTAClick('Check My Citations') with validation_started event (interface_source, form_content_length)
- Replace trackCTAClick('Upgrade Now') with upgrade_clicked event (trigger_location, citations_locked)
- Add mini_checker_validated event (citation_length, validation_successful)
- Add mini_checker_to_main_clicked event

**Phase 2: Add Missing Events**
- Add free_limit_reached event (current_usage, limit, attempted_citations)
- Add partial_results_viewed event (citations_shown, citations_locked, user_type)
- Add validation_attempted event (form_content_length, interface_source)
- Enhance citation_validated with interface_source parameter

**Success Criteria:**
- Clear conversion funnel: validation_started → citation_validated → upgrade_clicked → purchase
- Interface differentiation: mini_checker vs main_page events
- All tests updated for new event names
- No regression in existing analytics

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: c1920c8fbbeee02bf943f1c42b7d1c552c89116f
- HEAD_SHA: 0df9ba81d965e5eeaf0b16a0e0bddaccbd75b7fd

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
