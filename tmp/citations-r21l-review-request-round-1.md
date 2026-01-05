You are conducting a code review.

## Task Context

### Beads Issue ID: citations-r21l

citations-r21l: P1.3: Create inline_validator.py module
Status: closed
Priority: P1
Type: task

Description:
## Progress - 2026-01-05

### Implementation Complete

Created backend/inline_validator.py with:
- validate_inline_citations() - Main entry point with MAX_CITATIONS=100 limit enforcement
- _validate_batch() - Validates batches of up to 10 citations per LLM call
- _parse_inline_response() - Parses LLM JSON responses with fallback for errors
- _organize_by_reference() - Groups results by reference index, handles ambiguous citations (MLA)
- _extract_orphans() - Extracts citations with no matching reference
- Helper functions for formatting prompts and responses

### Unit Tests

Created backend/tests/test_inline_validator.py with 19 tests covering:
- Empty citations, max limit enforcement, batching logic
- JSON parsing (code blocks, raw JSON, arrays, invalid JSON fallback)
- Result organization (by matched index, ambiguous citations, initialization)
- Orphan extraction (not_found, null index, ambiguous not orphan)
- Helper formatting functions
- Module constants

All 19 tests pass. 3 pre-existing test failures unrelated to this work remain.

## Key Decisions

- Used existing provider's _call_new_api() / _call_legacy_api() methods for LLM calls
- JSON parsing tries multiple patterns (code block, array, object) before falling back
- Sequential batch processing (parallel deferred to v1.1 per design doc)
- Ambiguous citations added to ALL matched ref indices (MLA same-author-multiple-works case)

### What Was Implemented

Created the inline_validator.py module for the Smart Inline Citation Validation feature. This module handles validating in-text citations against reference lists using LLM calls, with batching (10 per batch), result organization by reference, orphan detection, and ambiguous match handling for MLA style.

### Requirements/Plan

From design doc (docs/plans/2026-01-01-inline-citation-validation-design.md):

Requirements for inline_validator.py:
- Batching inline citations for LLM calls (BATCH_SIZE = 10)
- Parsing LLM responses (JSON format with id, citation_text, match_status, matched_ref_index, etc.)
- Matching inline citations to reference entries
- Identifying orphans (citations with no matching reference)
- Identifying ambiguous matches (MLA case: same author, multiple works)
- MAX_CITATIONS = 100 hard limit with ValueError on exceed
- Sequential batch processing (parallel deferred to v1.1)
- Integration with prompt_manager.load_inline_prompt()
- Integration with existing provider (_call_new_api/_call_legacy_api)
- Unit tests in tests/test_inline_validator.py

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 4862d92
- HEAD_SHA: b724784

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
