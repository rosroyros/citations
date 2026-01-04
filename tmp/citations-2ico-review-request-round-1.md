You are conducting a code review.

## Task Context

### Beads Issue ID: citations-2ico

**Issue:** P1.2: Create parsing.py module
**Status:** in_progress
**Priority:** P1

### What Was Implemented

Created `backend/parsing.py` module (167 lines) with three core functions for Phase 1 of the Inline Citation Validation epic:

1. **convert_docx_to_html()**: Converts DOCX files to HTML using mammoth library, preserves semantic formatting (<em>, <strong>), raises ValueError for unparseable files

2. **split_document()**: Splits body text from reference list using header detection, detects 8 header variants (References, Bibliography, Works Cited, etc.) case-insensitively in <h1>, <h2>, <h3>, or <strong> tags, uses LAST match (references at document end), returns (body_html, refs_html, found_header) tuple, backward compatible (no header = refs only)

3. **scan_inline_citations()**: Finds inline citations using regex patterns, strips HTML before scanning, supports APA, MLA, and Chicago styles with permissive patterns (false positives OK, LLM will filter), returns list of {id, text, position} dicts

### Requirements/Plan

From design doc (`docs/plans/2026-01-01-inline-citation-validation-design.md`):

**Core Requirements:**
- Create `backend/parsing.py` module with three functions
- `convert_docx_to_html(file_bytes: bytes) -> str` - Convert DOCX to HTML preserving formatting
- `split_document(html: str) -> Tuple[str, str, bool]` - Split into body and refs using header heuristic
- `scan_inline_citations(body_html: str, style: str) -> List[Dict]` - Find inline citations with regex

**Implementation Details:**
- Use mammoth library for DOCX→HTML conversion
- Header keywords: references, reference list, bibliography, works cited, literature cited, sources, sources cited, references cited
- Header detection in <h1>, <h2>, <h3>, or <strong> tags, case-insensitive
- Use LAST match (refs at end of document)
- If no header found, treat entire content as ref-list only (backward compat)
- APA pattern: `\([A-Za-z][A-Za-z\s&.,]+\d{4}[a-z]?\)` - matches (Smith, 2019), (Smith & Jones, 2019), (Smith et al., 2019a)
- MLA pattern: `\([A-Za-z][A-Za-z\s]+\d+(?:-\d+)?\)` - matches (Smith 12), (Smith 42-45), (Smith and Jones 12)
- Strip HTML tags before regex scanning
- Patterns intentionally permissive (false positives OK, false negatives bad)

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: f414f87b51045f915d21a20150a3892ad7a5d75f
- HEAD_SHA: 7475ec7718dee1b40ff91b8080d6636cc37472f5

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
