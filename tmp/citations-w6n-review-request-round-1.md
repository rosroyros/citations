You are conducting a code review.

## Task Context

### Beads Issue ID: citations-w6n

citations-w6n: Improve validation table header summary to show accurate citation counts and handle partial results
Status: closed
Priority: P1
Type: feature

### What Was Implemented

Fixed junior developer's w6n implementation with three improvements: (1) Replaced naive citation parsing with LLM-based counting plus fallback, (2) Created comprehensive test suite with 18 passing backend tests and E2E visual regression tests for desktop/mobile, (3) Simplified UI based on user feedback - changed from verbose "X submitted (Y processed • Z remaining)" to clean "X citations • Y perfect • Z need fixes • N remaining" with clickable partial indicator that scrolls to upgrade banner.

### Requirements/Plan

**Original Requirements:**
- Show accurate citation counts in validation table header for both full and partial results
- Display submitted vs processed vs remaining citation breakdowns for partial results
- Handle free tier limit scenarios (partial results when user hits 10 citation cap)
- Ensure proper visual indicators for partial results state

**User Feedback Refinements:**
- Use "citations" consistently (not "submitted")
- Simplify format - remove verbose "(X processed • Y remaining)" breakdown
- Add "remaining" as 4th stat with red/warning color
- Make "⚠️ Partial" clickable to scroll to upgrade banner
- Ensure keyboard accessibility

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 022f75eabce0a32d48344181dcbc6f72234fa3a2
- HEAD_SHA: 9ee651b4174305c2191116201e5e054df556caaf

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
- XSS risks from dangerouslySetInnerHTML usage

**Code Quality:**
- Follows project standards and patterns (React, FastAPI, Pytest)
- Clear naming and structure
- Appropriate error handling
- Edge cases covered

**Testing:**
- Tests written and passing
- Coverage adequate
- Tests verify actual behavior
- E2E tests properly structured

**Performance & Documentation:**
- No obvious performance issues
- Code is self-documenting or commented
- Accessibility (ARIA, keyboard navigation)

**Specific Concerns to Check:**
- Backend citation counting accuracy (LLM-based vs fallback)
- Frontend accessibility (clickable partial indicator, keyboard nav)
- Mobile responsive behavior
- Test coverage for new features

## Required Output Format

Provide structured feedback in these categories:

1. **Critical**: Must fix immediately (security, broken functionality, data loss)
2. **Important**: Should fix before merge (bugs, missing requirements, poor patterns)
3. **Minor**: Nice to have (style, naming, optimization opportunities)
4. **Strengths**: What was done well

**IMPORTANT**: Verify implementation matches task requirements above.

Be specific with file:line references for all issues.
