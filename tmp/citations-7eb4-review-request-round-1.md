You are conducting a code review.

## Task Context

### Beads Issue ID: citations-7eb4

**Issue:** P2.3: Create golden sets for inline validation
**Status:** in_progress
**Priority:** P1
**Type:** task

**Description:**

This is the third task for Phase 2 (LLM Prompts) of the Inline Citation Validation epic.

**Epic:** citations-ghf3 (Smart Inline Citation Validation)
**Design Doc:** `docs/plans/2026-01-01-inline-citation-validation-design.md`

## Background

Golden sets are the foundation of prompt development. They provide:
1. Training data for iterating on prompts
2. Holdout data for final validation (prevent overfitting)
3. Reproducible benchmarks for measuring accuracy

We need 100 test cases per style (APA and MLA), split 50/50 between train and holdout.

## Requirements

- [x] Create `inline_apa_train.jsonl` with 50 APA test cases
- [x] Create `inline_apa_holdout.jsonl` with 50 APA test cases
- [x] Create `inline_mla_train.jsonl` with 50 MLA test cases
- [x] Create `inline_mla_holdout.jsonl` with 50 MLA test cases
- [x] Cover all error categories (see below)
- [x] Include edge cases and tricky scenarios

### Implementation Details

**File Location:** `Checker_Prompt_Optimization/` directory (same as existing prompt test files)

**File Format (JSONL):**
Each line is a JSON object with:
- `inline_citation`: The in-text citation to validate
- `ref_list`: Array of reference entries
- `expected`: Object with `match_status`, `matched_ref_index`, `errors`

### Required Test Categories (10+ cases each)

| Category | APA Example | MLA Example |
|----------|-------------|-------------|
| Perfect match | (Smith, 2019) → matches | (Smith 15) → matches |
| Year mismatch | (Smith, 2019) → ref says 2020 | N/A for MLA |
| Author spelling | (Smyth, 2019) → ref says Smith | (Smyth 15) → ref says Smith |
| Not in refs | (Brown, 2021) → not found | (Brown 15) → not found |
| Et al. correct | (Smith et al., 2019) → 3+ authors | N/A for MLA |
| Et al. wrong | (Smith et al., 2019) → 2 authors | N/A for MLA |
| Multiple citations | (Smith, 2019; Jones, 2020) | N/A |
| Narrative style | Smith (2019) said... | Smith writes... (15) |
| Ambiguous match | N/A | (Smith 15) → 2 Smith works |
| With title | N/A | (Smith, "Title" 15) → correct work |
| Page format | (Smith, 2019, p. 15) | (Smith 15-20) |

### What Was Implemented

Created 4 JSONL golden set files in `Checker_Prompt_Optimization/` directory:
- `inline_apa_train.jsonl` - 50 APA 7th edition training cases
- `inline_apa_holdout.jsonl` - 50 APA 7th edition holdout cases
- `inline_mla_train.jsonl` - 50 MLA 9th edition training cases
- `inline_mla_holdout.jsonl` - 50 MLA 9th edition holdout cases

Total: 200 test cases covering all required error categories plus edge cases:
- Corporate/organization authors (NSF, CDC, WHO, UN, etc.)
- Name variants (van, De, Mc, O'Brien, St.)
- Years with letters (2019a, 2019b, 2020a, 2020b)
- Special elements (Figure, Table, Chapter, pp, para, §)
- Editions, volumes, translations
- Forthcoming, n.d., DOI citations

All files validated as proper JSONL format with exactly 50 test cases each.

## Code Changes to Review

Review the git changes between these commits:
- **BASE_SHA:** e0ddfa80a439cb5bfd3400f25d6a10bdae48ee07
- **HEAD_SHA:** ccde1f3634384240a9e6fca1393e875573b9a8aa

Use git commands (git diff, git show, git log, etc.) to examine the changes.

## Review Criteria

Evaluate the implementation against these criteria:

**Adherence to Task:**
- Does implementation match task requirements?
- Were all 4 files created with exactly 50 test cases each?
- Are all required error categories covered?
- Is the JSONL format correct?
- Are the test cases realistic and useful for prompt development?

**Data Quality:**
- Are test cases clear and unambiguous?
- Do expected results match the citation/reference pairs?
- Is there good balance between positive (matched) and negative (error) cases?
- Are edge cases properly represented?

**Completeness:**
- All required categories covered (perfect match, year mismatch, author spelling, not_found, et al., multiple citations, narrative, ambiguous, with_title, page_format)?
- APA and MLA both covered adequately?
- Train/holdout split is 50/50?

**Project Standards:**
- Files in correct location (`Checker_Prompt_Optimization/`)
- JSONL format matches existing test files in directory
- Naming consistent with project conventions

## Required Output Format

Provide structured feedback in these categories:

1. **Critical**: Must fix immediately (security, broken functionality, data loss, malformed data)
2. **Important**: Should fix before merge (bugs, missing requirements, poor data quality)
3. **Minor**: Nice to have (style, naming, optimization opportunities)
4. **Strengths**: What was done well

**IMPORTANT**: Verify implementation matches task requirements above.

Be specific with file:line references for all issues.
