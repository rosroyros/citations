You are conducting a code review.

## Task Context

### Beads Issue ID: citations-nqat

**Title:** P2.4: Create prompt test runner

**Status:** closed

**Description:**

## Progress - 2026-01-04
- Created `Checker_Prompt_Optimization/test_inline_prompt.py`
- Supports APA/MLA styles and train/holdout sets
- Implements categorization by error type (perfect_match, year_mismatch, author_spelling, etc.)
- Uses production config: gemini-3-flash-preview, temp=0.0, thinking_budget=1024
- 80% accuracy threshold with exit code 0 (pass) or 1 (fail)
- CLI verified: `--style apa|mla`, `--set train|holdout`, `--verbose`
- Data loading and categorization tested successfully on 50 APA train cases

## Key Decisions
- Used single-citation batching (one API call per test case) for simplicity
- Categorization based on expected.match_status and errors array
- Exit codes enable CI/CD integration (pass/fail based on accuracy threshold)

**Labels:** [needs-review]

**Dependencies:**
- P2.1: Create APA inline validation prompt [closed]
- P2.2: Create MLA inline validation prompt [closed]
- P2.3: Create golden sets for inline validation [closed]

**Blocks:**
- P2.5: Iterate prompts to ≥80% accuracy [open]

### What Was Implemented

Created `Checker_Prompt_Optimization/test_inline_prompt.py`, a standalone Python test runner script for validating inline citation validation prompts against golden sets. The script:

1. Loads golden set test cases from JSONL files (`inline_apa_train.jsonl`, `inline_mla_holdout.jsonl`, etc.)
2. Runs each test case against the LLM (Gemini 3 Flash) using the inline validation prompts
3. Parses LLM JSON responses and compares against expected results
4. Categorizes results by error type (perfect_match, year_mismatch, author_spelling, et_al_usage, not_found, multi_citation, narrative_citation)
5. Calculates overall accuracy and per-category accuracy
6. Exits with code 0 if accuracy ≥80%, code 1 if below threshold
7. Supports CLI arguments: `--style {apa,mla}`, `--set {train,holdout}`, `--verbose`

### Requirements/Plan

**Original Requirements:**
- Create `Checker_Prompt_Optimization/test_inline_prompt.py`
- Load golden set from JSONL files
- Run prompt against test cases via LLM API
- Calculate accuracy, precision, recall, F1 by error category
- Support both APA and MLA styles
- Support train vs holdout set selection
- Generate detailed report with per-category breakdown

**Implementation Approach (from issue):**
- Single-citation batching (simpler than parallel)
- Categorization based on expected.match_status and errors array
- Production config: gemini-3-flash-preview, temp=0.0, thinking_budget=1024
- 80% accuracy threshold with proper exit codes for CI/CD integration
- Async API calls with retry logic and rate limit handling

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 1c51d3e3325c6b17a610c06bc069b779b8eb42d9
- HEAD_SHA: a7aecb2cf2bd8a01cd934d0cc46699b890b75286

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
