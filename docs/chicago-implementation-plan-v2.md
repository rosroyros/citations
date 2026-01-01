# Chicago Citation Style Implementation Plan v2

**Created:** 2025-12-31
**Status:** Ready for External Review
**Author:** Planning Session with Claude
**Style:** Chicago Manual of Style 17th Edition (Notes-Bibliography System)

---

## Document Purpose

This is a comprehensive implementation plan for adding Chicago 17th Edition citation validation to our citation checker tool. It's designed to be handed off to any engineer with zero prior context - all decisions, rationale, file paths, and integration points are documented.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Strategic Context & Decision Rationale](#2-strategic-context--decision-rationale)
3. [Technical Architecture Overview](#3-technical-architecture-overview)
4. [Phase 1: Research & Rules Documentation](#4-phase-1-research--rules-documentation)
5. [Phase 2: Golden Set Creation](#5-phase-2-golden-set-creation)
6. [Phase 3: Prompt Engineering](#6-phase-3-prompt-engineering)
7. [Phase 4: Testing & Iteration](#7-phase-4-testing--iteration)
8. [Phase 5: Integration](#8-phase-5-integration)
9. [Phase 6: Deployment & Monitoring](#9-phase-6-deployment--monitoring)
10. [All Integration Points (Complete List)](#10-all-integration-points-complete-list)
11. [Risk Mitigation & Rollback](#11-risk-mitigation--rollback)
12. [Simplification Opportunities](#12-simplification-opportunities)
13. [Out of Scope (Deferred)](#13-out-of-scope-deferred)
14. [Success Metrics](#14-success-metrics)
15. [File Checklist](#15-file-checklist)
16. [Appendix A: MLA Methodology Reference](#appendix-a-mla-methodology-reference)
17. [Appendix B: Example Citations](#appendix-b-example-citations)
18. [Appendix C: Authoritative Sources](#appendix-c-authoritative-sources)

---

## 1. Executive Summary

### What We're Building
Add Chicago Manual of Style 17th Edition (Notes-Bibliography system) as a third citation validation style, alongside existing APA 7 and MLA 9.

### Why Chicago?
- **Market gap**: Chicago is the #3 citation style globally. All major competitors (EasyBib, Scribbr, CitationMachine) offer APA/MLA/Chicago as baseline. We're missing it.
- **User demand**: Required for history, humanities, business, fine arts students - significant undergraduate population.
- **Strategic positioning**: Completes the "Big 3" offering, positions us as comprehensive.

### Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Which Chicago system? | Notes-Bibliography only | More common for humanities; Author-Date is similar to APA (less differentiation) |
| Validate footnotes too? | No, bibliography only | Bibliography is the hard part; footnotes follow same format; valuable standalone |
| Style ID | `chicago17` | Matches pattern (apa7, mla9); includes edition number |
| Launch threshold | ≥80% accuracy | Proven threshold from MLA launch |

### Success Criteria
- ≥80% accuracy on holdout validation set
- ≥70% recall (avoid MLA v1's 50% recall problem)
- All existing APA/MLA tests still pass
- No regression in system performance

### Estimated Effort
- **Phase 1-2 (Research + Golden Set)**: Highest effort - manual curation
- **Phase 3-4 (Prompt + Testing)**: Medium effort - iterative
- **Phase 5-6 (Integration + Deploy)**: Low effort - pattern exists

---

## 2. Strategic Context & Decision Rationale

### 2.1 Why Chicago Over Other Styles?

We evaluated multiple citation styles for the next addition:

| Style | Pros | Cons | Verdict |
|-------|------|------|---------|
| **Chicago** | #3 globally, completes Big 3, large market | Complex (2 systems) | ✅ Selected |
| IEEE | Simple format, growing CS market | Niche audience | Next candidate |
| Harvard | UK/Australia market | No single standard (varies by institution) | Deferred |
| AMA | Medical field standard | Very specialized niche | Low priority |
| Bluebook | Legal standard | Extremely complex, small market | Not recommended |

**Decision**: Chicago first because it fills a competitive gap. IEEE is a good follow-up due to simplicity and growing tech market.

### 2.2 Why Notes-Bibliography Only?

Chicago has two systems:

| System | Description | Target Users |
|--------|-------------|--------------|
| **Notes-Bibliography** | Footnotes + Bibliography at end | Humanities, history, arts |
| **Author-Date** | In-text (Author Year) + References | Sciences, social sciences |

**Decision**: Start with Notes-Bibliography because:
1. It's the distinctive Chicago system (Author-Date is basically APA)
2. Humanities is our target market for Chicago
3. We can validate bibliography entries standalone - that's the hard part
4. Author-Date can be added later as `chicago17-ad` if needed

### 2.3 Why Bibliography-Only Validation is Valuable

Some might ask: "Can you validate Chicago without footnotes?"

**Yes, and it's the most valuable part:**
- Students struggle with bibliography formatting, not footnote placement
- Footnote format mirrors bibliography format (same elements, different order)
- If bibliography is correct, footnotes are usually correct
- Many students just want "is my Works Cited page correct?"

This is the same approach we use for APA and MLA - we validate the reference list, not in-text citations.

### 2.4 Learning from MLA Implementation

MLA was added in December 2025. Key lessons:

| Issue | What Happened | How We'll Avoid |
|-------|---------------|-----------------|
| Overly strict v1 | 50% recall - flagged valid citations as invalid | Start with lenient prompt, tighten if needed |
| Database sources | False negatives for JSTOR/ProQuest citations | Explicit "database sources are complete" rule |
| Excessive placeholders | 27/112 citations had [MISSING: ...] | Only flag REQUIRED elements |
| Contaminated test data | Risk of LLM knowing examples | Use non-primary university sources |

**MLA Results for Reference:**
- v1: 74.1% accuracy (failed 80% threshold)
- v1.1: 83.9% accuracy (passed)
- Holdout: 89.3% accuracy (no overfitting)

---

## 3. Technical Architecture Overview

### 3.1 How Styles Work in Our System

```
User selects style (frontend)
         ↓
Request includes style param → POST /api/validate/async {style: "chicago17"}
         ↓
Backend validates style → styles.py SUPPORTED_STYLES
         ↓
PromptManager loads prompt → prompts/validator_prompt_chicago17_v1.txt
         ↓
LLM validates citations using loaded prompt
         ↓
Results returned with style-specific success message
```

**Key insight**: The style parameter just selects which prompt file to load. All validation logic is IN the prompt itself. The LLM providers (Gemini/OpenAI) don't need any Chicago-specific code.

### 3.2 Files That Define a Style

For each style, we have:

```
backend/
├── styles.py                           # Style registry (MUST update)
├── prompts/
│   └── validator_prompt_chicago17_v1.txt  # Validation rules (MUST create)
└── pseo/
    ├── builder/
    │   └── chicago_generator.py        # PSEO page generator (OPTIONAL)
    ├── configs/
    │   ├── chicago_specific_sources.json   # PSEO configs (OPTIONAL)
    │   ├── chicago_source_type_guides.json
    │   └── chicago_mega_guides.json
    └── knowledge_base/
        └── chicago17/
            └── citation_rules.json     # Structured rules (OPTIONAL but recommended)
```

**Minimum required for launch**: styles.py + prompt file + feature flag
**Everything else**: Nice to have, can add post-launch

### 3.3 Current Style Configuration

**File**: `backend/styles.py`

```python
SUPPORTED_STYLES: Dict[str, Dict[str, str]] = {
    "apa7": {
        "label": "APA 7th Edition",
        "prompt_file": "validator_prompt_v3_no_hallucination.txt",
        "success_message": "No APA 7 formatting errors detected"
    },
    "mla9": {
        "label": "MLA 9th Edition",
        "prompt_file": "validator_prompt_mla9_v1.1.txt",
        "success_message": "No MLA 9 formatting errors detected"
    }
}

StyleType = Literal["apa7", "mla9"]
DEFAULT_STYLE: StyleType = "apa7"
```

**After Chicago**:
```python
SUPPORTED_STYLES: Dict[str, Dict[str, str]] = {
    "apa7": {...},
    "mla9": {...},
    "chicago17": {
        "label": "Chicago 17th Edition",
        "prompt_file": "validator_prompt_chicago17_v1.txt",
        "success_message": "No Chicago 17 formatting errors detected"
    }
}

StyleType = Literal["apa7", "mla9", "chicago17"]
```

---

## 4. Phase 1: Research & Rules Documentation

### 4.1 Objectives
- Document all Chicago 17th Edition bibliography rules
- Create structured rules JSON for future reference
- Establish authoritative source hierarchy

### 4.2 Authoritative Sources (Hierarchy)

**Tier 1 - Official Sources (for rules definition)**:
| Source | URL | Use For |
|--------|-----|---------|
| Chicago Manual of Style Online | https://www.chicagomanualofstyle.org | Official rules, edge cases |
| Turabian Quick Guide | https://press.uchicago.edu/books/turabian/turabian_citationguide.html | Simplified reference |
| Purdue OWL Chicago | https://owl.purdue.edu/owl/research_and_citation/chicago_manual_17th_edition/ | Rule explanations with examples |

**Tier 2 - Academic Sources (for cross-reference)**:
- University of Wisconsin Writing Center
- Indiana University Libraries
- Duke University Libraries
- University of Illinois Library

**Important**: Tier 1 sources are for RULE DEFINITION. Do NOT use their examples in the golden test set (contamination risk - LLMs may have seen them).

### 4.3 Research Document

**Output**: `docs/chicago-research.md`

**Required Sections**:
```markdown
# Chicago Manual of Style 17th Edition Research

## 1. Overview
- Brief history (Chicago is the oldest US style guide, since 1906)
- Notes-Bibliography vs Author-Date explanation
- When each system is used

## 2. Notes-Bibliography System
- Footnote format (for reference, not validation)
- Bibliography format (our validation target)
- Relationship between footnote and bibliography entries

## 3. Core Elements
- Author (formatting rules)
- Title (capitalization, italics, quotes)
- Publication information (place, publisher, date)
- Access information (URLs, DOIs, access dates)

## 4. Source Type Formats
### 4.1 Books
- Single author
- Multiple authors (2, 3, 4+)
- Edited volumes
- Chapters in edited volumes
- E-books

### 4.2 Journal Articles
- Print journals
- Online journals
- DOI handling

### 4.3 Websites
- With author
- Without author
- Access date requirements

### 4.4 Newspaper/Magazine Articles
- Print
- Online

### 4.5 Other Sources
- Films/videos
- Interviews
- Government documents
- Dissertations

## 5. Key Differences from APA/MLA
| Element | APA 7 | MLA 9 | Chicago NB |
|---------|-------|-------|------------|
| Author | Last, F. M. | Last, First. | Last, First. |
| Title case | Sentence | Title | Title |
| Publisher location | No | No | Yes (required) |
| Date position | After author | End | End |
| Page prefix | p./pp. | pp. | None |

## 6. Common Errors to Test
- [List 15-20 common student errors]

## 7. Sources Consulted
- [All URLs with access dates]
```

### 4.4 Structured Rules Document

**Output**: `backend/pseo/knowledge_base/chicago17/citation_rules.json`

**Structure**:
```json
{
  "style": "chicago17",
  "system": "notes-bibliography",
  "edition": "17th",
  "last_updated": "2025-12-31",
  "rules": [
    {
      "rule_id": "CHI17-A1",
      "category": "author",
      "source": "CMOS 17th, Section 14.18",
      "description": "Single author: Last, First.",
      "format": "Last, First.",
      "examples": {
        "correct": ["Morrison, Toni."],
        "incorrect": [
          {"text": "Morrison, T.", "error": "Initials instead of full name"},
          {"text": "Toni Morrison.", "error": "Not inverted"}
        ]
      }
    }
  ]
}
```

**Rule Categories** (target ~45 rules):
- Author formatting: 6 rules (single, 2, 3, 4+, corporate, no author)
- Title formatting: 5 rules (case, italics, quotes, subtitles)
- Publication info: 6 rules (place, publisher, date, edition)
- Punctuation: 5 rules (periods, commas, colons)
- URLs/DOIs: 4 rules
- Source-specific: 20 rules (books, journals, websites, etc.)

### 4.5 Deliverables Checklist

- [ ] `docs/chicago-research.md` created
- [ ] `backend/pseo/knowledge_base/chicago17/citation_rules.json` created
- [ ] All Tier 1 sources consulted
- [ ] Rules cross-referenced with at least 2 Tier 2 sources
- [ ] Common error patterns documented

---

## 5. Phase 2: Golden Set Creation

### 5.1 Objectives
- Create 200+ test citations (100+ valid, 100+ invalid pairs)
- Source examples from non-contaminated university libraries
- Ensure coverage across all source types

### 5.2 Why Non-Contaminated Sources Matter

**Problem**: LLMs (including the ones we use for validation) were trained on common citation guides. If our test examples come from Purdue OWL or Scribbr, the LLM may "remember" them rather than actually validating.

**Solution**: Source examples from university library guides that are:
- Not primary citation references (not Purdue, Cornell, etc.)
- Have real Chicago examples (not just rule descriptions)
- Recently updated (2020+)

### 5.3 Target University Sources

**MLA used these universities successfully**:
- University of Nevada, Reno
- University of Portland
- University of Maryland (UMGC)
- NW Missouri State
- Florida State College Jacksonville
- Seneca Polytechnic
- Seminole State College
- University of Queensland

**For Chicago, target these (verify they have Chicago guides)**:

| University | URL to Check | Notes |
|------------|--------------|-------|
| Ohio State University | guides.osu.edu/chicago | Large, likely comprehensive |
| University of Toronto | guides.library.utoronto.ca | Canadian, good coverage |
| Penn State | guides.libraries.psu.edu | Extensive guides |
| University of Washington | guides.lib.uw.edu | Major research university |
| Boston College | libguides.bc.edu | Strong humanities |
| Georgetown University | guides.library.georgetown.edu | History focus |
| UCLA | guides.library.ucla.edu | Major research university |
| University of Virginia | guides.lib.virginia.edu | Strong humanities |
| Rice University | library.rice.edu | Quality guides |
| Emory University | guides.libraries.emory.edu | Good humanities coverage |

**Verification Process**:
1. Visit each URL
2. Confirm Chicago 17th Edition guide exists
3. Confirm real examples (not just descriptions)
4. Confirm multiple source types covered
5. Note last updated date

### 5.4 Example Distribution

**Target: 224 citations total (112 valid + 112 invalid)**

| Source Type | Valid | Invalid | Total | Notes |
|-------------|-------|---------|-------|-------|
| Books (single author) | 15 | 15 | 30 | Core format |
| Books (multiple authors) | 10 | 10 | 20 | 2, 3, 4+ authors |
| Books (edited/chapters) | 8 | 8 | 16 | Anthology format |
| Journal articles | 20 | 20 | 40 | Print + online |
| Websites | 15 | 15 | 30 | With/without author |
| Newspaper/Magazine | 10 | 10 | 20 | Print + online |
| Films/Videos | 6 | 6 | 12 | |
| Other (interviews, govt) | 6 | 6 | 12 | |
| **TOTAL** | **90** | **90** | **180** | Minimum |
| **Stretch** | **112** | **112** | **224** | Match MLA |

### 5.5 Invalid Variant Creation (Controlled Mutations)

Each valid citation gets ONE paired invalid variant with a specific, controlled error.

**Error Types to Apply**:

| Error Category | Specific Mutations |
|----------------|-------------------|
| **Author** | Initials (T. instead of Toni), wrong order (First Last), ampersand (&), missing period |
| **Title** | Missing italics, wrong case (sentence vs title), missing quotes on articles |
| **Publication** | Missing place, wrong punctuation (comma vs colon), missing publisher |
| **Date** | Wrong format, wrong position |
| **Punctuation** | Missing final period, comma instead of period, missing colon |
| **Format** | Page prefix (pp.), wrong volume format |

**Important**: Only ONE error per invalid citation. This makes testing deterministic.

### 5.6 File Format

**File**: `Checker_Prompt_Optimization/chicago_test_set_COMPREHENSIVE.jsonl`

```jsonl
{"citation": "Morrison, Toni. Beloved. New York: Knopf, 1987.", "ground_truth": true, "source_type": "book", "source_url": "https://guides.osu.edu/chicago"}
{"citation": "Morrison, T. Beloved. New York: Knopf, 1987.", "ground_truth": false, "source_type": "book", "error_type": "author_initials", "paired_with": 0}
{"citation": "Smith, John. \"Article Title.\" Journal Name 45, no. 2 (2020): 123-145.", "ground_truth": true, "source_type": "journal", "source_url": "https://guides.osu.edu/chicago"}
{"citation": "Smith, John. \"Article Title.\" Journal Name 45, no. 2 (2020): pp. 123-145.", "ground_truth": false, "source_type": "journal", "error_type": "page_prefix", "paired_with": 2}
```

### 5.7 Train/Holdout Split

**Script**: `Checker_Prompt_Optimization/split_chicago_test_set.py`

```python
#!/usr/bin/env python3
"""Split Chicago test set into training and holdout sets.

Maintains valid/invalid pairs together, then splits pairs 50/50.
Uses fixed random seed for reproducibility.
"""

import json
import random
from pathlib import Path

RANDOM_SEED = 42

def main():
    input_file = Path(__file__).parent / "chicago_test_set_COMPREHENSIVE.jsonl"

    with open(input_file) as f:
        citations = [json.loads(line) for line in f]

    # Group into pairs (valid + invalid)
    pairs = []
    i = 0
    while i < len(citations):
        if citations[i]["ground_truth"]:
            pairs.append((citations[i], citations[i+1] if i+1 < len(citations) else None))
            i += 2
        else:
            i += 1

    # Shuffle pairs
    random.seed(RANDOM_SEED)
    random.shuffle(pairs)

    # Split 50/50
    mid = len(pairs) // 2
    train_pairs = pairs[:mid]
    holdout_pairs = pairs[mid:]

    # Flatten and write
    train = [c for pair in train_pairs for c in pair if c]
    holdout = [c for pair in holdout_pairs for c in pair if c]

    with open(Path(__file__).parent / "chicago_test_set.jsonl", "w") as f:
        for c in train:
            f.write(json.dumps(c) + "\n")

    with open(Path(__file__).parent / "chicago_holdout_set.jsonl", "w") as f:
        for c in holdout:
            f.write(json.dumps(c) + "\n")

    print(f"Training set: {len(train)} citations")
    print(f"Holdout set: {len(holdout)} citations")

if __name__ == "__main__":
    main()
```

### 5.8 Deliverables Checklist

- [ ] 8+ university sources verified and documented
- [ ] `chicago_test_set_COMPREHENSIVE.jsonl` created (180+ citations)
- [ ] Source URL documented for each valid citation
- [ ] Error type documented for each invalid citation
- [ ] `split_chicago_test_set.py` created and tested
- [ ] `chicago_test_set.jsonl` generated (training)
- [ ] `chicago_holdout_set.jsonl` generated (holdout)
- [ ] `chicago_test_set_SAMPLE.jsonl` created (4-6 for quick testing)

---

## 6. Phase 3: Prompt Engineering

### 6.1 Objectives
- Create validator prompt following proven MLA pattern
- Balance strictness (catch errors) vs leniency (don't flag valid citations)
- Handle edge cases explicitly

### 6.2 Prompt Structure

**File**: `backend/prompts/validator_prompt_chicago17_v1.txt`

**Target length**: 100-130 lines (MLA v1.1 is 110 lines)

```
# CHICAGO MANUAL OF STYLE 17TH EDITION - BIBLIOGRAPHY VALIDATOR

You are an expert Chicago citation validator. Validate bibliography entries according to the Chicago Manual of Style 17th Edition (Notes-Bibliography system).

## TASK

For each citation:
1. Identify source type (book, journal article, website, etc.)
2. Check formatting against Chicago 17th Edition rules
3. Report errors found (if any)
4. Provide corrected citation (if errors found)

## BIBLIOGRAPHY FORMATS BY SOURCE TYPE

### Books (Single Author)
Format: Last, First. _Title_. Place: Publisher, Year.
Example: Morrison, Toni. _Beloved_. New York: Knopf, 1987.

### Books (Two Authors)
Format: Last, First, and First Last. _Title_. Place: Publisher, Year.
Note: Only first author is inverted. Use "and" (not "&").

### Books (Three Authors)
Format: Last, First, First Last, and First Last. _Title_. Place: Publisher, Year.

### Books (Four or More Authors)
Format: Last, First, et al. _Title_. Place: Publisher, Year.
Note: List only first author followed by "et al."

### Edited Books
Format: Last, First, ed. _Title_. Place: Publisher, Year.
For multiple editors: Last, First, and First Last, eds.

### Book Chapters
Format: Last, First. "Chapter Title." In _Book Title_, edited by Editor Name, Pages. Place: Publisher, Year.

### Journal Articles
Format: Last, First. "Article Title." _Journal Name_ Volume, no. Issue (Year): Pages.
With DOI: Add DOI at end.
Example: Smith, John. "Research Study." _Journal of Studies_ 45, no. 2 (2020): 123-145.

### Websites
With author: Last, First. "Page Title." Website Name. Month Day, Year. URL.
Without author: "Page Title." Website Name. Accessed Month Day, Year. URL.

### Newspaper/Magazine Articles
Format: Last, First. "Article Title." _Publication_, Month Day, Year.

### Films
Format: _Title_. Directed by First Last. Place: Studio, Year.

## CORE RULES

### Authors
- Use FULL first names (not initials): "Toni" not "T."
- First author only is inverted (Last, First)
- Use "and" between authors, not "&"
- Four+ authors: first author et al.

### Titles
- Use Title Case for ALL titles
- Books, journals, films: italics (_text_)
- Articles, chapters, web pages: quotation marks ("text")
- Subtitles: colon + space, maintain Title Case

### Publication Information
- Books REQUIRE place of publication
- Format: Place: Publisher, Year.
- Colon after place, comma after publisher

### Punctuation
- Period after author(s)
- Period after title
- Period at end of citation
- NO "p." or "pp." before page numbers in bibliography

### URLs and DOIs
- DOI preferred when available
- URLs: include full URL (https:// included)
- Access dates: only required for undated web sources

## INPUT HANDLING

- Markdown: _text_ = italics, "text" = quotation marks
- Ignore leading list markers (1., 2., -, •) in input
- Validate each citation independently

## MISSING INFORMATION

CRITICAL: Never fabricate bibliographic data.

Only flag REQUIRED missing elements:
- Books: author, title, place, publisher, year
- Journals: author, title, journal name, volume, year, pages
- Websites: title, website name, URL

Do NOT flag as missing:
- DOI (if URL present)
- Access date (for dated sources)
- Issue number (if volume present)

DATABASE SOURCES: If citation ends with database name (e.g., _JSTOR_, _ProQuest_), it is COMPLETE. Do not add [MISSING: URL].

## OUTPUT FORMAT

For each citation:

CITATION [N]:
[original text]

SOURCE TYPE: [book/journal/website/etc.]

ERRORS FOUND:
✓ No errors detected
OR
❌ [Specific error description]
❌ [Another error if multiple]

CORRECTED CITATION:
[corrected version]
OR
N/A - citation is correct

---
[Repeat for each citation]
```

### 6.3 Key Prompt Principles (from MLA learnings)

1. **Be lenient by default** - MLA v1 was too strict (50% recall). Start lenient, tighten if precision suffers.

2. **Explicit database handling** - "If citation ends with database name, it's complete" prevents false negatives on JSTOR/ProQuest sources.

3. **Required vs optional** - Only flag MISSING for truly required elements. Optional elements (DOI when URL present, issue when volume present) should not trigger errors.

4. **Clear error descriptions** - Each error should state WHAT is wrong and imply HOW to fix it.

5. **Avoid rule redundancy** - MLA v1.1 removed redundant sections. Keep prompt focused.

### 6.4 Deliverables Checklist

- [ ] `validator_prompt_chicago17_v1.txt` created
- [ ] All source type formats documented
- [ ] Core rules section complete
- [ ] Missing information handling explicit
- [ ] Output format matches APA/MLA pattern
- [ ] Prompt reviewed against MLA v1.1 for consistency

---

## 7. Phase 4: Testing & Iteration

### 7.1 Objectives
- Achieve ≥80% accuracy on training set
- Validate on holdout set (run only once)
- Document what worked and what didn't

### 7.2 Test Script

**File**: `Checker_Prompt_Optimization/test_chicago_prompt_batched.py`

**Configuration** (match MLA testing):
```python
MODEL = "gemini-2.0-flash"  # or current production model
TEMPERATURE = 0.0  # Deterministic
BATCH_SIZE = 5  # Citations per API call
RATE_LIMIT_DELAY = 2  # Seconds between batches
MAX_RETRIES = 5
THINKING_BUDGET = 1024  # If using thinking model
```

**Script should**:
1. Load prompt and test set
2. Call API in batches
3. Parse responses to determine valid/invalid classification
4. Compare to ground truth
5. Calculate metrics
6. Output detailed results JSON

### 7.3 Metrics to Capture

```json
{
  "prompt_version": "v1",
  "test_set": "chicago_test_set.jsonl",
  "timestamp": "2025-01-XX",
  "total_citations": 112,
  "metrics": {
    "accuracy": 0.XXX,
    "precision": 0.XXX,
    "recall": 0.XXX,
    "f1_score": 0.XXX
  },
  "confusion_matrix": {
    "true_positives": XX,
    "true_negatives": XX,
    "false_positives": XX,
    "false_negatives": XX
  },
  "accuracy_by_source_type": {
    "book": 0.XXX,
    "journal": 0.XXX,
    "website": 0.XXX
  },
  "placeholder_usage": {
    "total": XX,
    "by_type": {}
  },
  "failures": [
    {"citation": "...", "expected": true, "got": false, "reason": "..."}
  ]
}
```

### 7.4 Testing Workflow

```
┌─────────────────────────────────────────────────────┐
│  1. BASELINE TEST (v1 prompt + training set)        │
│     - Run test_chicago_prompt_batched.py            │
│     - Output: chicago_baseline_results.json         │
│     - Target: ≥80% accuracy                         │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Accuracy ≥80%?       │
            └───────────────────────┘
                   │           │
                  YES          NO
                   │           │
                   │           ▼
                   │  ┌─────────────────────────────────┐
                   │  │  2. ANALYZE FAILURES            │
                   │  │     - chicago_baseline_analysis.md│
                   │  │     - Identify patterns         │
                   │  │     - Categorize FP/FN          │
                   │  └─────────────────────────────────┘
                   │           │
                   │           ▼
                   │  ┌─────────────────────────────────┐
                   │  │  3. ITERATE PROMPT (v1 → v1.1)  │
                   │  │     - Fix identified issues     │
                   │  │     - Retest on training set    │
                   │  │     - Repeat until ≥80%         │
                   │  └─────────────────────────────────┘
                   │           │
                   ▼           ▼
┌─────────────────────────────────────────────────────┐
│  4. HOLDOUT VALIDATION (final prompt + holdout set) │
│     - Run ONCE only (no iteration after this)       │
│     - Output: chicago_holdout_validation_results.json│
│     - Must be ≥80% to ship                          │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Holdout ≥80%?        │
            └───────────────────────┘
                   │           │
                  YES          NO
                   │           │
                   ▼           ▼
              SHIP IT     Review test set quality
                          or prompt fundamentals
```

### 7.5 Analysis Document Template

**File**: `Checker_Prompt_Optimization/chicago_baseline_analysis.md`

```markdown
# Chicago Baseline Analysis

## Summary
- Prompt version: v1
- Accuracy: XX.X%
- Status: [PASS/ITERATE/BLOCK]

## Confusion Matrix
|              | Predicted Valid | Predicted Invalid |
|--------------|-----------------|-------------------|
| Actually Valid   | TP: XX          | FN: XX            |
| Actually Invalid | FP: XX          | TN: XX            |

## Key Findings

### False Negatives (Valid marked Invalid) - XX total
These are the most important to fix (hurts user experience).

Pattern 1: [Description]
- Example: [citation]
- Reason: [why prompt flagged it incorrectly]
- Fix: [suggested prompt change]

Pattern 2: ...

### False Positives (Invalid marked Valid) - XX total
Less critical but still important.

Pattern 1: ...

## Accuracy by Source Type
| Source Type | Accuracy | Notes |
|-------------|----------|-------|
| Books       | XX%      |       |
| Journals    | XX%      |       |
| Websites    | XX%      |       |

## Recommendations for v1.1
1. [Specific change]
2. [Specific change]
3. [Specific change]
```

### 7.6 Deliverables Checklist

- [ ] `test_chicago_prompt_batched.py` created
- [ ] `chicago_baseline_results.json` generated
- [ ] `chicago_baseline_analysis.md` written (if iteration needed)
- [ ] `validator_prompt_chicago17_v1.1.txt` created (if iteration needed)
- [ ] `chicago_holdout_validation_results.json` generated
- [ ] Holdout accuracy ≥80% confirmed

---

## 8. Phase 5: Integration

### 8.1 Backend Changes

#### 8.1.1 styles.py (REQUIRED)

**File**: `backend/styles.py`

```python
# Add to SUPPORTED_STYLES dict
"chicago17": {
    "label": "Chicago 17th Edition",
    "prompt_file": "validator_prompt_chicago17_v1.txt",  # or v1.1
    "success_message": "No Chicago 17 formatting errors detected"
}

# Update type hint
StyleType = Literal["apa7", "mla9", "chicago17"]
```

#### 8.1.2 app.py - Feature Flag (REQUIRED)

**File**: `backend/app.py`

```python
# Add near line 43 (with other feature flags)
CHICAGO_ENABLED = os.getenv('CHICAGO_ENABLED', 'false').lower() == 'true'

# Update /api/styles endpoint (around line 755)
@app.get("/api/styles")
async def get_available_styles():
    styles = {"apa7": SUPPORTED_STYLES["apa7"]["label"]}

    if MLA_ENABLED:
        styles["mla9"] = SUPPORTED_STYLES["mla9"]["label"]

    if CHICAGO_ENABLED:
        styles["chicago17"] = SUPPORTED_STYLES["chicago17"]["label"]

    return {"styles": styles, "default": DEFAULT_STYLE}
```

#### 8.1.3 Prompt File (REQUIRED)

**Copy to**: `backend/prompts/validator_prompt_chicago17_v1.txt`

### 8.2 Frontend Changes

#### 8.2.1 StyleSelector.jsx - Verify 3+ Style Handling

**File**: `frontend/frontend/src/components/StyleSelector.jsx`

**Check**: Component fetches from `/api/styles` and renders tabs dynamically. Should work with 3 styles, but verify:
- Tab overflow on mobile (3 tabs may need scrolling)
- Tab widths balanced

**Likely no changes needed** - component is data-driven.

#### 8.2.2 App.jsx - Verify Style Initialization

**File**: `frontend/frontend/src/App.jsx`

**Current code** (lines 112-116):
```javascript
const savedStyle = localStorage.getItem('citation_checker_style')
return savedStyle === 'mla9' ? 'mla9' : 'apa7'
```

**Update to**:
```javascript
const savedStyle = localStorage.getItem('citation_checker_style')
const validStyles = ['apa7', 'mla9', 'chicago17']
return validStyles.includes(savedStyle) ? savedStyle : 'apa7'
```

#### 8.2.3 MiniChecker.jsx - Add Style Support (NICE TO HAVE)

**File**: `frontend/frontend/src/components/MiniChecker.jsx`

**Current**: Hardcoded to `apa7` (line 44)

**Options**:
1. Keep as-is (MiniChecker always uses APA)
2. Add prop: `style={props.style || 'apa7'}`
3. Read from data attribute for PSEO pages

**Recommendation**: Option 1 for now, enhance later for Chicago PSEO pages.

#### 8.2.4 FAQ Update (REQUIRED)

**File**: `frontend/frontend/src/App.jsx` (around line 1018)

**Current**:
```javascript
"What citation styles does this tool support?"
"APA 7th Edition and MLA 9th Edition"
```

**Update to**:
```javascript
"What citation styles does this tool support?"
"APA 7th Edition, MLA 9th Edition, and Chicago 17th Edition"
```

### 8.3 Database/Analytics Changes

#### 8.3.1 Validation Logging - Add Style Column (RECOMMENDED)

**File**: Check dashboard database schema

**Current**: Logs job_id, user_type, citation_count, status

**Add**: `style` column for per-style metrics

```sql
ALTER TABLE validations ADD COLUMN style VARCHAR(20) DEFAULT 'apa7';
```

#### 8.3.2 Telegram Notifier (REQUIRED)

**File**: `dashboard/telegram_notifier.py` (line 100)

**Current**:
```python
style_map = {'apa7': 'APA 7', 'mla9': 'MLA 9'}
```

**Update**:
```python
style_map = {'apa7': 'APA 7', 'mla9': 'MLA 9', 'chicago17': 'Chicago 17'}
```

### 8.4 Tests

#### 8.4.1 Unit Tests (REQUIRED)

**File**: `backend/tests/test_styles.py`

```python
def test_supported_styles_has_chicago(self):
    assert "chicago17" in SUPPORTED_STYLES

def test_chicago_has_required_fields(self):
    config = SUPPORTED_STYLES["chicago17"]
    assert "label" in config
    assert "prompt_file" in config
    assert "success_message" in config

def test_get_chicago_config(self):
    config = get_style_config("chicago17")
    assert config["label"] == "Chicago 17th Edition"
```

**File**: `backend/tests/test_prompt_manager.py`

```python
def test_load_chicago_prompt(self):
    pm = PromptManager()
    prompt = pm.load_prompt("chicago17")
    assert len(prompt) > 0
    assert "Chicago" in prompt
```

#### 8.4.2 API Tests (REQUIRED)

**File**: `backend/tests/test_app.py`

```python
def test_styles_endpoint_includes_chicago_when_enabled(self, monkeypatch):
    monkeypatch.setenv("CHICAGO_ENABLED", "true")
    # Reimport app or use test client
    response = client.get("/api/styles")
    assert "chicago17" in response.json()["styles"]

def test_validate_accepts_chicago_style(self):
    response = client.post("/api/validate/async", json={
        "citations": "Morrison, Toni. Beloved. New York: Knopf, 1987.",
        "style": "chicago17"
    })
    assert response.status_code == 200
```

#### 8.4.3 E2E Tests (REQUIRED)

**File**: `frontend/frontend/tests/e2e/e2e-chicago-validation.spec.cjs`

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Chicago Citation Validation', () => {
  test('can select Chicago style', async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="style-tab-chicago17"]');
    expect(await page.locator('[data-testid="style-tab-chicago17"]').getAttribute('aria-selected')).toBe('true');
  });

  test('validates Chicago citation correctly', async ({ page }) => {
    await page.goto('/?style=chicago17');
    await page.fill('[data-testid="citation-input"]', 'Morrison, Toni. Beloved. New York: Knopf, 1987.');
    await page.click('[data-testid="validate-button"]');
    await expect(page.locator('[data-testid="validation-result"]')).toContainText('No Chicago 17 formatting errors');
  });
});
```

### 8.5 Deliverables Checklist

- [ ] `backend/styles.py` updated
- [ ] `backend/app.py` feature flag added
- [ ] `backend/prompts/validator_prompt_chicago17_v1.txt` deployed
- [ ] `frontend/frontend/src/App.jsx` FAQ updated
- [ ] `frontend/frontend/src/App.jsx` style initialization updated
- [ ] `dashboard/telegram_notifier.py` style_map updated
- [ ] `backend/tests/test_styles.py` Chicago tests added
- [ ] `backend/tests/test_prompt_manager.py` Chicago tests added
- [ ] `backend/tests/test_app.py` Chicago API tests added
- [ ] E2E tests created
- [ ] All existing tests still pass

---

## 9. Phase 6: Deployment & Monitoring

### 9.1 Deployment Checklist

```
PRE-DEPLOYMENT
[ ] All tests pass locally
[ ] Prompt file committed to repo
[ ] styles.py changes committed
[ ] Feature flag code committed
[ ] E2E tests pass

DEPLOYMENT
[ ] Set CHICAGO_ENABLED=false initially (dark launch)
[ ] Deploy to production
[ ] Verify existing APA/MLA still work
[ ] Run smoke test with Chicago (internal only)
[ ] Set CHICAGO_ENABLED=true
[ ] Verify Chicago appears in style selector
[ ] Run full E2E test suite

POST-DEPLOYMENT
[ ] Monitor error rates for 24 hours
[ ] Check validation accuracy in production
[ ] Review user feedback if any
[ ] Update sitemap if PSEO pages added
```

### 9.2 Monitoring

**Metrics to Watch**:

| Metric | Where to Check | Alert Threshold |
|--------|----------------|-----------------|
| Chicago validation errors | Application logs | >5% error rate |
| Chicago usage % | Dashboard | N/A (informational) |
| API latency | Monitoring | >10s p95 |
| User complaints | Support channel | Any |

**First 24 Hours**:
- Check logs for validation errors specifically for `style=chicago17`
- Verify no increase in overall error rates
- Check that Chicago validations complete successfully

### 9.3 Rollback Plan

**If issues arise**:

1. **Quick fix**: Set `CHICAGO_ENABLED=false` in environment
   - Chicago disappears from style selector
   - Existing APA/MLA unaffected
   - No code deploy needed

2. **Full rollback**: Revert commits if code issues
   - Revert styles.py changes
   - Revert app.py feature flag
   - Redeploy

### 9.4 Deliverables Checklist

- [ ] Deployment completed
- [ ] CHICAGO_ENABLED=true in production
- [ ] 24-hour monitoring completed
- [ ] No critical issues identified
- [ ] Rollback plan documented and tested

---

## 10. All Integration Points (Complete List)

This is the comprehensive list of every file/component that touches citation styles:

### Backend (14 files)

| File | Change Type | Required? |
|------|-------------|-----------|
| `backend/styles.py` | Add chicago17 config | ✅ Yes |
| `backend/app.py` | Add feature flag, update /api/styles | ✅ Yes |
| `backend/prompts/validator_prompt_chicago17_v1.txt` | Create new file | ✅ Yes |
| `backend/prompt_manager.py` | No changes (data-driven) | No |
| `backend/providers/gemini_provider.py` | No changes (uses prompt_manager) | No |
| `backend/providers/openai_provider.py` | No changes | No |
| `backend/tests/test_styles.py` | Add Chicago tests | ✅ Yes |
| `backend/tests/test_prompt_manager.py` | Add Chicago tests | ✅ Yes |
| `backend/tests/test_app.py` | Add Chicago API tests | ✅ Yes |
| `backend/pseo/knowledge_base/chicago17/` | Create directory + rules JSON | Recommended |
| `backend/pseo/builder/chicago_generator.py` | Create for PSEO pages | Optional (Phase 2) |
| `backend/pseo/configs/chicago_*.json` | Create for PSEO pages | Optional (Phase 2) |
| `backend/pseo/scripts/generate_chicago_pages.py` | Create for PSEO pages | Optional (Phase 2) |
| `backend/citation_logger.py` | Add style to logs | Recommended |

### Frontend (6 files)

| File | Change Type | Required? |
|------|-------------|-----------|
| `frontend/frontend/src/App.jsx` | Update FAQ, style init | ✅ Yes |
| `frontend/frontend/src/components/StyleSelector.jsx` | Verify 3-tab handling | Verify only |
| `frontend/frontend/src/components/MiniChecker.jsx` | Add style prop | Optional |
| `frontend/frontend/src/utils/analytics.js` | No changes (style already tracked) | No |
| `frontend/frontend/tests/e2e/e2e-chicago-validation.spec.cjs` | Create new test | ✅ Yes |
| `frontend/frontend/src/utils/errorMessages.js` | No changes needed | No |

### Dashboard/Monitoring (3 files)

| File | Change Type | Required? |
|------|-------------|-----------|
| `dashboard/telegram_notifier.py` | Add to style_map | ✅ Yes |
| Dashboard database schema | Add style column | Recommended |
| Dashboard queries | Add Chicago to style breakdown | Recommended |

### Documentation (3 files)

| File | Change Type | Required? |
|------|-------------|-----------|
| `docs/chicago-research.md` | Create | ✅ Yes |
| `README.md` | Update supported styles | Recommended |
| `CLAUDE.md` | Update if relevant | Optional |

### Environment/Deployment (2 files)

| File | Change Type | Required? |
|------|-------------|-----------|
| Production `.env` | Add CHICAGO_ENABLED=true | ✅ Yes |
| `.env.example` | Document new variable | Recommended |

**Total: 28 integration points, 12 required, 16 recommended/optional**

---

## 11. Risk Mitigation & Rollback

### 11.1 Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Prompt accuracy <80% | Medium | High | Iterate on training set before holdout |
| Golden set contaminated | Low | High | Use non-primary university sources |
| Frontend breaks with 3 tabs | Low | Medium | Test on mobile, add scrolling if needed |
| LLM latency increases | Low | Low | Chicago prompt similar length to MLA |
| User confusion | Low | Low | Clear labeling, FAQ update |

### 11.2 Rollback Triggers

Immediately rollback if:
- Error rate >5% for Chicago validations
- Overall system error rate increases
- Critical bug in style selection
- User-reported data loss or corruption

### 11.3 Rollback Procedure

1. **Set CHICAGO_ENABLED=false** in production environment
2. Restart application (or wait for env refresh)
3. Verify Chicago no longer appears in /api/styles
4. Investigate issue
5. Fix and redeploy when ready

---

## 12. Simplification Opportunities

### 12.1 What We're NOT Doing (Intentionally)

| Feature | Why Not |
|---------|---------|
| Footnote validation | Bibliography is the valuable part; footnotes follow same format |
| Author-Date system | Too similar to APA; can add later as `chicago17-ad` |
| PSEO pages at launch | Can add post-launch; not blocking |
| Custom error messages | Generic messages work; style context is clear |
| Per-style rate limits | No need; same limits for all |
| Per-style pricing | No need; same credit cost |

### 12.2 Reuse Opportunities

| Component | Reuse |
|-----------|-------|
| Test scripts | Copy MLA scripts, change file names |
| Split script | Identical logic to MLA |
| Prompt structure | Follow MLA v1.1 pattern |
| E2E tests | Copy MLA tests, update selectors |
| Feature flag pattern | Identical to MLA_ENABLED |

### 12.3 Future Simplifications (Post-Chicago)

If adding more styles (e.g., IEEE):
- Consider style metadata in JSON instead of hardcoded
- Consider prompt template with style-specific rules injected
- Consider unified test script that takes style as parameter

---

## 13. Out of Scope (Deferred)

### 13.1 Deferred to Post-Launch

| Item | Reason |
|------|--------|
| Chicago PSEO pages | Not blocking; add when validation proven |
| Chicago Author-Date | Different system; separate feature |
| MiniChecker Chicago support | Low priority; main checker works |
| Style-specific analytics dashboard | Nice to have; can query manually |

### 13.2 Not Planned

| Item | Reason |
|------|--------|
| Footnote validation | Out of scope for reference list validator |
| Citation generation | We validate, not generate |
| Bibliography sorting | Out of scope |
| In-text citation validation | Out of scope |

---

## 14. Success Metrics

### 14.1 Launch Criteria (Must Have)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Holdout accuracy | ≥80% | test_chicago_holdout_validation.py |
| All existing tests pass | 100% | pytest + playwright |
| No critical bugs | 0 | Manual testing |
| Feature flag works | Yes | Toggle test |

### 14.2 Post-Launch Success (30 days)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Chicago usage | >5% of validations | Dashboard |
| Error rate | <2% | Logs |
| User complaints | <5 | Support channel |
| Accuracy (production) | >80% | Spot check |

### 14.3 Long-Term Success (90 days)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Chicago usage | >10% of validations | Dashboard |
| User retention | No decrease | Analytics |
| SEO traffic (if PSEO added) | >0 | Google Analytics |

---

## 15. File Checklist

### Phase 1: Research
- [ ] `docs/chicago-research.md`
- [ ] `backend/pseo/knowledge_base/chicago17/citation_rules.json`

### Phase 2: Golden Set
- [ ] `Checker_Prompt_Optimization/chicago_test_set_COMPREHENSIVE.jsonl`
- [ ] `Checker_Prompt_Optimization/chicago_test_set.jsonl`
- [ ] `Checker_Prompt_Optimization/chicago_holdout_set.jsonl`
- [ ] `Checker_Prompt_Optimization/chicago_test_set_SAMPLE.jsonl`
- [ ] `Checker_Prompt_Optimization/split_chicago_test_set.py`

### Phase 3: Prompt
- [ ] `backend/prompts/validator_prompt_chicago17_v1.txt`
- [ ] `backend/prompts/validator_prompt_chicago17_v1.1.txt` (if needed)

### Phase 4: Testing
- [ ] `Checker_Prompt_Optimization/test_chicago_prompt_batched.py`
- [ ] `Checker_Prompt_Optimization/chicago_baseline_results.json`
- [ ] `Checker_Prompt_Optimization/chicago_baseline_analysis.md` (if iteration)
- [ ] `Checker_Prompt_Optimization/chicago_holdout_validation_results.json`

### Phase 5: Integration
- [ ] `backend/styles.py` - updated
- [ ] `backend/app.py` - feature flag added
- [ ] `frontend/frontend/src/App.jsx` - FAQ + init updated
- [ ] `dashboard/telegram_notifier.py` - style_map updated
- [ ] `backend/tests/test_styles.py` - Chicago tests
- [ ] `backend/tests/test_prompt_manager.py` - Chicago tests
- [ ] `backend/tests/test_app.py` - Chicago API tests
- [ ] `frontend/frontend/tests/e2e/e2e-chicago-validation.spec.cjs`

### Phase 6: Deployment
- [ ] Production `.env` - CHICAGO_ENABLED=true
- [ ] Deployment completed
- [ ] Monitoring confirmed

---

## Appendix A: MLA Methodology Reference

### How MLA Golden Set Was Created

**Sources Used** (8 universities):
- University of Nevada, Reno (guides.library.unr.edu/mlacitation)
- University of Portland (libguides.up.edu/mla)
- University of Maryland UMGC (libguides.umgc.edu/mla-examples)
- NW Missouri State (libguides.nwmissouri.edu/mla)
- Florida State College Jacksonville (guides.fscj.edu/MLA9)
- Seneca Polytechnic (library.senecapolytechnic.ca/mla)
- Seminole State College (libguides.seminolestate.edu/mla)
- University of Queensland (guides.library.uq.edu.au/referencing/mla9)

**Why These Sources**:
- NOT primary citation guides (avoided Purdue OWL, Scribbr, EasyBib)
- Have real examples (not just rules)
- Recently updated
- Cover multiple source types

**Test Set Size**: 224 citations (112 valid + 112 invalid)

**Split**: 50/50 training/holdout using RANDOM_SEED=42

### MLA Prompt Evolution

| Version | Accuracy | Key Changes |
|---------|----------|-------------|
| v1 | 74.1% | Initial comprehensive prompt |
| v1.1 | 83.9% | Streamlined, fixed database handling, clarified missing data |
| Holdout | 89.3% | No changes, just validation |

**Key Fixes in v1.1**:
1. Added explicit database source handling
2. Removed redundant rule sections
3. Clarified required vs optional elements
4. Reduced prompt length (160 → 110 lines)

---

## Appendix B: Example Citations

### Valid Chicago Bibliography Examples

**Book (Single Author)**:
```
Morrison, Toni. Beloved. New York: Knopf, 1987.
```

**Book (Two Authors)**:
```
Smith, John, and Jane Doe. Research Methods. Chicago: University of Chicago Press, 2020.
```

**Book (Four+ Authors)**:
```
Johnson, Mark, et al. Collaborative Research. Boston: Academic Press, 2019.
```

**Edited Book**:
```
Williams, Sarah, ed. Modern Essays. New York: Norton, 2021.
```

**Book Chapter**:
```
Brown, Emily. "Data Analysis." In Research Handbook, edited by Michael Green, 45-78. London: Sage, 2021.
```

**Journal Article**:
```
Williams, Sarah. "Social Media Impact." Journal of Communication 45, no. 2 (2020): 123-145.
```

**Journal Article with DOI**:
```
Chen, David. "Climate Patterns." Environmental Science 12, no. 4 (2023): 234-256. https://doi.org/10.1234/example.
```

**Website (with author)**:
```
Thompson, Lisa. "Citation Guide." University Library. January 15, 2024. https://library.edu/citations.
```

**Website (without author)**:
```
"Style Guidelines." Chicago Manual. Accessed December 31, 2025. https://chicagomanualofstyle.org/guidelines.
```

**Newspaper Article**:
```
Martinez, Carlos. "Economic Forecast." New York Times, December 28, 2023.
```

**Film**:
```
The Godfather. Directed by Francis Ford Coppola. Hollywood: Paramount Pictures, 1972.
```

### Invalid Examples (with errors)

**Author initials** (wrong):
```
Morrison, T. Beloved. New York: Knopf, 1987.
```
Error: First name abbreviated to initial

**Missing place** (wrong):
```
Morrison, Toni. Beloved. Knopf, 1987.
```
Error: Missing place of publication

**Wrong punctuation** (wrong):
```
Morrison, Toni. Beloved, New York: Knopf, 1987.
```
Error: Comma after title instead of period

**Ampersand** (wrong):
```
Smith, John & Jane Doe. Research Methods. Chicago: University of Chicago Press, 2020.
```
Error: Ampersand instead of "and"

**Page prefix** (wrong):
```
Williams, Sarah. "Social Media Impact." Journal of Communication 45, no. 2 (2020): pp. 123-145.
```
Error: Chicago doesn't use "pp." prefix in bibliography

---

## Appendix C: Authoritative Sources

### Tier 1: Official Sources (for rules)

| Source | URL | Notes |
|--------|-----|-------|
| Chicago Manual of Style Online | https://www.chicagomanualofstyle.org | Subscription required; definitive source |
| Turabian Quick Guide | https://press.uchicago.edu/books/turabian/turabian_citationguide.html | Free; simplified Chicago |
| Purdue OWL Chicago | https://owl.purdue.edu/owl/research_and_citation/chicago_manual_17th_edition/ | Free; comprehensive |

### Tier 2: Cross-Reference Sources

| Source | URL |
|--------|-----|
| University of Wisconsin | https://writing.wisc.edu/handbook/documentation/docchicago/ |
| Indiana University | https://libraries.indiana.edu/chicago-citation-style |
| Duke University | https://library.duke.edu/research/citing/chicago |
| University of Illinois | https://www.library.illinois.edu/hpnl/tutorials/chicago/ |

### Tier 3: Golden Set Sources (non-contaminated)

**Target universities to verify for Chicago guides:**

| University | URL to Check |
|------------|--------------|
| Ohio State | guides.osu.edu/chicago |
| University of Toronto | guides.library.utoronto.ca |
| Penn State | guides.libraries.psu.edu |
| University of Washington | guides.lib.uw.edu |
| Boston College | libguides.bc.edu |
| Georgetown | guides.library.georgetown.edu |
| UCLA | guides.library.ucla.edu |
| University of Virginia | guides.lib.virginia.edu |
| Rice University | library.rice.edu |
| Emory University | guides.libraries.emory.edu |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2025-12-31 | Initial plan |
| v2 | 2025-12-31 | Added integration points, risk mitigation, simplification opportunities, monitoring, complete file list |

---

*End of Document*
