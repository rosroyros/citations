You are conducting a code review.

## Task Context

### Beads Issue ID: citations-0j28



citations-0j28: P2.1: Create APA inline validation prompt
Status: open
Priority: P1
Type: task
Created: 2026-01-04 11:19
Updated: 2026-01-04 21:28

Description:


## Progress - 2026-01-04
- Created `backend/prompts/validator_prompt_inline_apa.txt`
- Included all APA 7th Edition inline citation rules
- Defined JSON response format with all required fields
- Added examples for each match_status type (matched, mismatch, not_found, format_errors)
- Added additional APA rules: group citations, narrative citations

## Key Decisions
- Expanded examples beyond basic spec to include edge cases like group citations
- Used case-insensitive matching note for author names
- Maintained consistency with existing APA 7 ref-list prompt style

Labels: [needs-review]

Depends on (1):
  → citations-ghf3: Epic: Smart Inline Citation Validation [P1]

Blocks (2):
  ← citations-lh2a: P1.4: Update prompt_manager.py and styles.py [P1 - open]
  ← citations-nqat: P2.4: Create prompt test runner [P1 - open]


### What Was Implemented

Created `backend/prompts/validator_prompt_inline_apa.txt` - a comprehensive prompt for validating APA 7th Edition inline citations against reference lists. The prompt defines JSON input/output format, includes all APA inline citation rules (author/year matching, & vs and, et al., page numbers, group/narrative citations), and provides examples for each match_status type.

### Requirements/Plan

Key requirements from task description:
- Create `backend/prompts/validator_prompt_inline_apa.txt`
- Include all APA 7th Edition inline citation rules
- Define input/output format for LLM
- Include examples of each match_status type (matched, mismatch, not_found, ambiguous)
- Use placeholders `{reference_list}` and `{inline_citations}`

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: d1e61325ef717b5650f68d35f92ecd31fdf7331f
- HEAD_SHA: 4f9a4f8514894cd8f31118d74f90a1339b1eb6e8

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
