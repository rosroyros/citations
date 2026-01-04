You are conducting a code review.

## Task Context

### Beads Issue ID: citations-prsn

citations-prsn: P2.2: Create MLA inline validation prompt
Status: in_progress
Priority: P1
Type: task
Created: 2026-01-04 11:19
Updated: 2026-01-04 21:41

Description:

## Progress - 2026-01-04
- Created `backend/prompts/validator_prompt_inline_mla.txt` (192 lines)
- Included all MLA 9th Edition inline citation rules
- Implemented ambiguity detection for same-author, multiple-works scenarios
- Defined disambiguation suggestion format with shortened titles
- Added comprehensive examples covering all MLA inline citation patterns

## Key Decisions
- Made prompt more detailed than APA version (192 vs 108 lines) due to MLA's more complex ambiguity rules
- Used explicit disambiguation format: (Author, Short Title page)
- Included 8 specific MLA inline citation rules covering:
  - Author name matching
  - Page number formatting (no p./pp. prefix)
  - Title disambiguation for multiple works
  - "and" vs "&" usage
  - et al. rules
  - Narrative citations
  - No comma between author and page
  - Page range formatting

## Notes
- Testing with golden set blocked by P2.3 (golden set creation)
- Ready for P1.4 (prompt_manager.py integration)

Labels: [needs-review]

### What Was Implemented

Created a new prompt file `backend/prompts/validator_prompt_inline_mla.txt` for MLA 9th Edition inline citation validation. The prompt defines rules for validating in-text citations against Works Cited entries, including MLA-specific formatting rules (no "p." prefix, "and" not "&", no comma between author and page) and ambiguity detection for same-author, multiple-works scenarios.

### Requirements/Plan

From the task description:
- [ ] Create `backend/prompts/validator_prompt_inline_mla.txt`
- [ ] Include all MLA 9th Edition inline citation rules
- [ ] Handle ambiguous matches (same author, multiple works)
- [ ] Define disambiguation suggestion format
- [ ] Test with golden set (P2.3) to achieve ≥80% accuracy

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 969050aca83e049870accee5b08fd94bb92e419f
- HEAD_SHA: 3bb62a4a762a6fd64d2fcd55da691aa224d008ad

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
