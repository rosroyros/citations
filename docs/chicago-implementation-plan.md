# Chicago Citation Style Implementation Plan

**Created:** 2025-12-31
**Status:** Draft - Pending Review
**Style:** Chicago Manual of Style 17th Edition (Notes-Bibliography System)

---

## Executive Summary

This plan details how to add Chicago citation validation to our citation checker, following the proven methodology used for MLA 9. Chicago is the #3 most-used citation style after APA and MLA, used primarily in history, humanities, business, and fine arts.

**Key Decision:** Start with **Notes-Bibliography system only** (footnotes + bibliography). The Author-Date system can be added later as a separate style variant.

**Success Criteria:** ≥80% accuracy on holdout validation set before production deployment.

---

## Table of Contents

1. [Background & Rationale](#1-background--rationale)
2. [Chicago Style Overview](#2-chicago-style-overview)
3. [Phase 1: Research & Rules Documentation](#phase-1-research--rules-documentation)
4. [Phase 2: Golden Set Creation](#phase-2-golden-set-creation)
5. [Phase 3: Prompt Engineering](#phase-3-prompt-engineering)
6. [Phase 4: Testing & Iteration](#phase-4-testing--iteration)
7. [Phase 5: Integration & Deployment](#phase-5-integration--deployment)
8. [File Checklist](#file-checklist)
9. [Authoritative Sources](#authoritative-sources)
10. [Lessons Learned from MLA](#lessons-learned-from-mla)

---

## 1. Background & Rationale

### Why Chicago?

**Market Position:**
- Chicago is the **#3 citation style** after APA and MLA
- All major competitors (EasyBib, CitationMachine, Scribbr) offer APA/MLA/Chicago as baseline
- We're missing a style users expect from a comprehensive citation tool

**Target Audience:**
- History students and researchers
- Business and economics students
- Fine arts and humanities
- Academic publishing in humanities disciplines

**Strategic Value:**
- Completes the "Big 3" offering
- Positions us as comprehensive, not limited
- Captures significant undergraduate population

### Why Notes-Bibliography First?

Chicago has **two distinct systems**:

| System | Use Case | Complexity |
|--------|----------|------------|
| Notes-Bibliography | Humanities, history, arts | Higher (footnotes + bibliography) |
| Author-Date | Sciences, social sciences | Lower (similar to APA) |

**Decision:** Start with Notes-Bibliography because:
1. It's the more common Chicago system for humanities (our target)
2. Author-Date is very similar to APA (less differentiation)
3. We can validate bibliography entries without requiring footnotes
4. Adding Author-Date later is straightforward

### Reference List Validation is Valuable Standalone

Chicago Notes-Bibliography uses footnotes for in-text citations and a bibliography for the full reference list. **Validating the bibliography alone provides significant value** because:
- Bibliography formatting is the complex part students struggle with
- Footnotes follow bibliography formatting (validate one, understand both)
- Many students just need "is my bibliography correct?"

---

## 2. Chicago Style Overview

### Notes-Bibliography System Structure

**Footnote (in-text):**
```
1. Toni Morrison, Beloved (New York: Knopf, 1987), 45.
```

**Bibliography Entry:**
```
Morrison, Toni. Beloved. New York: Knopf, 1987.
```

### Key Differences from APA/MLA

| Element | APA 7 | MLA 9 | Chicago NB |
|---------|-------|-------|------------|
| Author Format | Last, F. M. | Last, First. | Last, First. |
| Title Format | Sentence case | Title Case + italics | Title Case + italics |
| Publisher | Publisher. | Publisher, | Place: Publisher, |
| Date Position | (Year). | Year. | Year. |
| Page Numbers | p./pp. | pp. | No prefix |

### Source Types to Support (Priority Order)

1. **Books** (single author, multiple authors, edited)
2. **Journal Articles** (print and online)
3. **Websites** (with and without authors)
4. **Newspaper/Magazine Articles**
5. **Book Chapters/Anthologies**
6. **Films/Videos**
7. **Interviews**
8. **Government Documents**

---

## Phase 1: Research & Rules Documentation

### Step 1.1: Create Chicago Research Document

**Output:** `docs/chicago-research.md`

**Authoritative Sources to Consult:**

**Primary (Official):**
- Chicago Manual of Style Online: https://www.chicagomanualofstyle.org
- University of Chicago Press: https://press.uchicago.edu/books/turabian/turabian_citationguide.html
- Purdue OWL Chicago: https://owl.purdue.edu/owl/research_and_citation/chicago_manual_17th_edition/

**Secondary (University Libraries - for cross-reference):**
- University of Wisconsin-Madison Writing Center
- Indiana University Bloomington Libraries
- Duke University Libraries
- Cornell University Library
- University of Illinois Library

**Research Document Structure:**
```markdown
# Chicago Manual of Style 17th Edition Research

## 1. Overview
- History and purpose
- Notes-Bibliography vs Author-Date systems
- When to use each system

## 2. Core Elements (Notes-Bibliography)
- Author
- Title
- Publication Information
- Access Information

## 3. Source Type Formats
### 3.1 Books
### 3.2 Journal Articles
### 3.3 Websites
### 3.4 Newspaper/Magazine Articles
### 3.5 Book Chapters
### 3.6 Films/Videos
### 3.7 Interviews
### 3.8 Government Documents

## 4. Common Error Patterns
- Punctuation mistakes
- Capitalization errors
- Date formatting issues
- Publisher location handling

## 5. Chicago vs MLA vs APA Comparison Table

## 6. Sources Consulted (with URLs)
```

### Step 1.2: Create Formal Rules Document

**Output:** `backend/pseo/knowledge_base/chicago17/citation_rules.json`

**Structure (following MLA pattern):**
```json
{
  "style": "chicago17",
  "system": "notes-bibliography",
  "version": "17th Edition",
  "rules": [
    {
      "rule_id": "CHI17-R1.1",
      "source": "Chicago Manual of Style 17th Edition, Section 14.18",
      "category": "author_formatting",
      "description": "Single author: Last, First.",
      "examples": [
        {
          "type": "correct",
          "citation": "Morrison, Toni. Beloved. New York: Knopf, 1987."
        },
        {
          "type": "incorrect",
          "citation": "Morrison, T. Beloved. New York: Knopf, 1987.",
          "error_reason": "First name abbreviated to initial"
        }
      ],
      "common_errors": ["Using initials instead of full names"],
      "affected_source_types": ["all"]
    }
  ]
}
```

**Rule Categories to Document:**

1. **Author Formatting (R1.x)** - 5-6 rules
   - Single author format
   - Two authors (and vs comma)
   - Three authors
   - Four+ authors (first author et al.)
   - Corporate/organizational authors
   - No author (start with title)

2. **Title Formatting (R2.x)** - 4-5 rules
   - Title Case for all titles
   - Italics for books, journals
   - Quotation marks for articles, chapters
   - Subtitle handling (colon + space)

3. **Publication Information (R3.x)** - 5-6 rules
   - Place of publication (required for books)
   - Publisher name formatting
   - Date formats (year only vs full date)
   - Edition information

4. **Punctuation (R4.x)** - 5-6 rules
   - Period after author block
   - Period after title
   - Colon after place of publication
   - Comma after publisher
   - Period at end

5. **URL/Access Information (R5.x)** - 3-4 rules
   - URL format (no http://)
   - DOI preferred when available
   - Access date format

6. **Source-Specific Rules (Bx, Jx, Wx, etc.)** - 15-20 rules
   - Books (B1-B5)
   - Journal articles (J1-J5)
   - Websites (W1-W3)
   - Newspapers (N1-N3)
   - Films (F1-F2)
   - etc.

**Total: ~40-50 rules**

---

## Phase 2: Golden Set Creation

### Step 2.1: Identify Non-Contaminated University Sources

**CRITICAL:** Avoid sources that LLMs were likely trained on (Purdue OWL, Scribbr, EasyBib).

**Target: 8-10 University Library Guides**

**Candidate Sources (to verify):**

| University | Potential URL | Notes |
|------------|---------------|-------|
| Ohio State University | guides.osu.edu/chicago | Large public university |
| University of Toronto | guides.library.utoronto.ca | Canadian, comprehensive |
| University of Washington | guides.lib.uw.edu/research/citations | Major research university |
| Penn State | guides.libraries.psu.edu | Extensive citation guides |
| University of Colorado | libguides.colorado.edu | Western US coverage |
| Boston College | libguides.bc.edu | Strong humanities program |
| Georgetown University | guides.library.georgetown.edu | History/policy focus |
| UCLA | guides.library.ucla.edu | Major research university |
| Rice University | library.rice.edu | Smaller but high quality |
| University of Virginia | guides.lib.virginia.edu | Strong humanities |

**Verification Criteria:**
- NOT a primary citation guide source (avoid Purdue, Cornell, etc.)
- Has real Chicago examples (not just descriptions)
- Examples cover multiple source types
- Recently updated (2020 or later)

### Step 2.2: Extract & Verify Examples

**Process:**
1. Visit each university guide
2. Extract 15-25 correctly formatted Chicago bibliography entries
3. Document source URL for each citation
4. Cross-reference with Chicago Manual rules
5. Flag any questionable examples for manual review

**Target Distribution:**
| Source Type | Valid Examples | Invalid Variants | Total |
|-------------|----------------|------------------|-------|
| Books | 20 | 20 | 40 |
| Journal Articles | 20 | 20 | 40 |
| Websites | 15 | 15 | 30 |
| Newspaper/Magazine | 10 | 10 | 20 |
| Book Chapters | 10 | 10 | 20 |
| Films/Videos | 8 | 8 | 16 |
| Interviews | 5 | 5 | 10 |
| Government Docs | 5 | 5 | 10 |
| **TOTAL** | **93** | **93** | **186** |

**Stretch Goal:** 112 valid + 112 invalid = 224 (matching MLA)

### Step 2.3: Create Invalid Variants

**Error Mutation Types to Apply:**

Each valid citation gets ONE paired invalid variant with a specific error:

1. **Author Errors**
   - Initials instead of full name: `Morrison, T.` → `Morrison, Toni.`
   - Wrong author order: `First Last` → `Last, First`
   - Ampersand instead of "and": `Smith & Jones` → `Smith and Jones`

2. **Title Errors**
   - Missing italics: `Beloved` → `_Beloved_`
   - Wrong case: `beloved` → `Beloved`
   - Missing quotation marks on articles

3. **Publication Errors**
   - Missing place: `Knopf, 1987` → `New York: Knopf, 1987`
   - Wrong date format: `1987` → `87`
   - Missing publisher

4. **Punctuation Errors**
   - Comma instead of period after title
   - Missing colon after place
   - Missing final period

5. **Format Errors**
   - Page numbers with "p." prefix (not Chicago style)
   - Missing volume/issue formatting

### Step 2.4: Create Test Set Files

**Output Files:**

```
Checker_Prompt_Optimization/
├── chicago_test_set_COMPREHENSIVE.jsonl  # All 186-224 citations
├── chicago_test_set.jsonl                # 50% for training (~93-112)
├── chicago_holdout_set.jsonl             # 50% for validation (~93-112)
└── chicago_test_set_SAMPLE.jsonl         # 4-6 examples for quick testing
```

**File Format:**
```jsonl
{"citation": "Morrison, Toni. Beloved. New York: Knopf, 1987.", "ground_truth": true, "source_type": "book", "source_url": "https://guides.library.xyz.edu/chicago"}
{"citation": "Morrison, T. Beloved. New York: Knopf, 1987.", "ground_truth": false, "source_type": "book", "error_type": "author_initials"}
```

### Step 2.5: Split Script

**Create:** `Checker_Prompt_Optimization/split_chicago_test_set.py`

```python
#!/usr/bin/env python3
"""Split Chicago comprehensive test set into training and holdout sets."""

import json
import random
from pathlib import Path

RANDOM_SEED = 42  # Reproducibility

def split_chicago_test_set():
    # Load comprehensive set
    comprehensive_file = Path(__file__).parent / "chicago_test_set_COMPREHENSIVE.jsonl"

    with open(comprehensive_file) as f:
        citations = [json.loads(line) for line in f]

    # Group into valid/invalid pairs
    # ... (same logic as MLA split script)

    # Shuffle and split 50/50
    random.seed(RANDOM_SEED)
    # ... split logic

    # Write output files
    # chicago_test_set.jsonl (training)
    # chicago_holdout_set.jsonl (validation)

if __name__ == "__main__":
    split_chicago_test_set()
```

---

## Phase 3: Prompt Engineering

### Step 3.1: Create Initial Prompt (v1)

**Output:** `backend/prompts/validator_prompt_chicago17_v1.txt`

**Structure (following MLA pattern):**

```
# CHICAGO MANUAL OF STYLE 17TH EDITION - BIBLIOGRAPHY VALIDATOR

You are an expert Chicago citation validator. Your task is to check bibliography entries for formatting errors according to the Chicago Manual of Style 17th Edition (Notes-Bibliography system).

## INSTRUCTIONS

For each citation provided, you will:
1. Identify the source type (book, journal article, website, etc.)
2. Check against Chicago 17th Edition rules
3. List any formatting errors found
4. Provide a corrected citation

## SOURCE TYPE FORMATS

### Books (Single Author)
Format: Last, First. _Title: Subtitle_. Place: Publisher, Year.
Example: Morrison, Toni. _Beloved_. New York: Knopf, 1987.

### Books (Two Authors)
Format: Last, First, and First Last. _Title_. Place: Publisher, Year.
Example: Smith, John, and Jane Doe. _Research Methods_. Chicago: University of Chicago Press, 2020.

### Books (Three Authors)
Format: Last, First, First Last, and First Last. _Title_. Place: Publisher, Year.

### Books (Four+ Authors)
Format: Last, First, et al. _Title_. Place: Publisher, Year.

### Journal Articles
Format: Last, First. "Article Title." _Journal Name_ Volume, no. Issue (Year): Pages. URL or DOI.
Example: Smith, John. "Research Findings." _Journal of Studies_ 45, no. 2 (2020): 123-145.

### Websites
Format: Last, First. "Page Title." Website Name. Last modified Date. URL.
OR: "Page Title." Website Name. Accessed Date. URL.

### Newspaper/Magazine Articles
Format: Last, First. "Article Title." _Publication Name_, Month Day, Year.

### Book Chapters
Format: Last, First. "Chapter Title." In _Book Title_, edited by Editor Name, Pages. Place: Publisher, Year.

### Films
Format: _Title_. Directed by Director Name. Place: Studio, Year.

## CORE RULES

### Author Formatting
- Use full first names, not initials
- First author: Last, First
- Second author: and First Last (not inverted)
- Three authors: Last, First, First Last, and First Last
- Four+ authors: Last, First, et al.

### Title Formatting
- All titles use Title Case
- Book/journal titles: italics
- Article/chapter titles: quotation marks
- Subtitles: separated by colon and space

### Publication Information
- Books REQUIRE place of publication
- Format: Place: Publisher, Year.
- Colon after place, comma after publisher

### Punctuation
- Period after author name(s)
- Period after title
- Period at end of citation
- NO "p." or "pp." before page numbers

## FORMATTING NOTES

- Markdown notation: _text_ indicates italics
- Ignore leading numbers (1., 2., etc.) in input
- Validate each citation independently

## HANDLING MISSING INFORMATION

CRITICAL: Never fabricate bibliographic data.

If information appears missing:
1. First, verify it's actually required (not optional)
2. If truly missing and required, use: [MISSING: element name]
3. Common optional elements: DOI, access date, edition

DATABASE SOURCES: If a citation ends with a database name (e.g., _JSTOR_, _ProQuest_), the citation is complete. Do NOT add [MISSING: URL].

## OUTPUT FORMAT

For each citation, output:

CITATION [N]:
[Original citation text]

SOURCE TYPE: [type]

ERRORS FOUND:
✓ No errors detected
OR
❌ [Error 1 description]
❌ [Error 2 description]

CORRECTED CITATION:
[Corrected version if errors found, or "N/A - citation is correct"]

---
```

**Target Length:** ~120-150 lines

### Step 3.2: Key Prompt Principles (from MLA learnings)

1. **Be specific about optional vs required elements**
   - Don't flag missing DOIs if URL is present
   - Don't flag missing access dates for stable sources

2. **Database source handling**
   - Citations ending with database name are complete
   - Don't add [MISSING: URL] for database sources

3. **Avoid over-strictness**
   - Accept minor variations that are technically correct
   - Focus on clear errors, not style preferences

4. **Clear error descriptions**
   - Specify WHAT is wrong and HOW to fix it
   - Reference the specific rule violated

---

## Phase 4: Testing & Iteration

### Step 4.1: Create Test Script

**Output:** `Checker_Prompt_Optimization/test_chicago_prompt_batched.py`

**Configuration:**
```python
MODEL = "gemini-3-flash-preview"
TEMPERATURE = 0.0
THINKING_BUDGET = 1024
BATCH_SIZE = 5
RATE_LIMIT_DELAY = 2  # seconds between batches
```

**Metrics to Capture:**
- Overall accuracy
- Precision (TP / (TP + FP))
- Recall (TP / (TP + FN))
- F1 Score
- Confusion matrix (TP, TN, FP, FN)
- Accuracy by source type
- Placeholder usage count

### Step 4.2: Baseline Testing

**Command:**
```bash
cd Checker_Prompt_Optimization
python3 test_chicago_prompt_batched.py
```

**Output:** `chicago_baseline_results.json`

**Launch Criteria:**
| Accuracy | Action |
|----------|--------|
| ≥80% | Ship |
| 65-79% | Iterate |
| <65% | Major revision needed |

### Step 4.3: Analyze Baseline Results

**Output:** `chicago_baseline_analysis.md`

**Analysis Questions:**
1. Which source types have lowest accuracy?
2. What are the most common false negatives (valid marked invalid)?
3. What are the most common false positives (invalid marked valid)?
4. Is the prompt too strict or too lenient?
5. Are placeholders being overused?

### Step 4.4: Prompt Iteration (v1 → v1.1)

Based on baseline analysis:
1. Identify specific rule clarifications needed
2. Reduce/remove redundant sections
3. Clarify edge cases
4. Create `validator_prompt_chicago17_v1.1.txt`

### Step 4.5: Comparison Testing

**Script:** `test_chicago_v1.1_comparison.py`

Compare v1 vs v1.1 on same training set:
- Track improvement in accuracy
- Track changes in precision/recall
- Document what fixed what

### Step 4.6: Holdout Validation (Final Gate)

**Script:** `test_chicago_holdout_validation.py`

**CRITICAL:** Only run this ONCE after prompt is stable.

**Output:** `chicago_holdout_validation_results.json`

**Success Criteria:** ≥80% accuracy on holdout set

---

## Phase 5: Integration & Deployment

### Step 5.1: Update Style Configuration

**File:** `backend/styles.py`

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
    },
    "chicago17": {
        "label": "Chicago 17th Edition",
        "prompt_file": "validator_prompt_chicago17_v1.1.txt",
        "success_message": "No Chicago 17 formatting errors detected"
    }
}

StyleType = Literal["apa7", "mla9", "chicago17"]
```

### Step 5.2: Add Feature Flag

**File:** `backend/app.py`

```python
CHICAGO_ENABLED = os.getenv('CHICAGO_ENABLED', 'false').lower() == 'true'
```

Update `/api/styles` endpoint:
```python
@app.get("/api/styles")
async def get_available_styles():
    styles = {"apa7": SUPPORTED_STYLES["apa7"]["label"]}

    if MLA_ENABLED:
        styles["mla9"] = SUPPORTED_STYLES["mla9"]["label"]

    if CHICAGO_ENABLED:
        styles["chicago17"] = SUPPORTED_STYLES["chicago17"]["label"]

    return {"styles": styles, "default": DEFAULT_STYLE}
```

### Step 5.3: Update Tests

**File:** `backend/tests/test_styles.py`

Add Chicago to existing tests:
```python
def test_supported_styles_has_expected_keys(self):
    assert "apa7" in SUPPORTED_STYLES
    assert "mla9" in SUPPORTED_STYLES
    assert "chicago17" in SUPPORTED_STYLES
```

### Step 5.4: PSEO Pages (Optional - Phase 2)

If creating Chicago-specific landing pages:

1. Create `backend/pseo/builder/chicago_generator.py`
2. Create configs:
   - `backend/pseo/configs/chicago_specific_sources.json`
   - `backend/pseo/configs/chicago_source_type_guides.json`
   - `backend/pseo/configs/chicago_mega_guides.json`
3. Create generation script: `backend/pseo/scripts/generate_chicago_pages.py`

### Step 5.5: Deployment Checklist

```
[ ] 1. Prompt file in backend/prompts/
[ ] 2. styles.py updated
[ ] 3. Feature flag added to app.py
[ ] 4. Tests passing
[ ] 5. CHICAGO_ENABLED=true in production .env
[ ] 6. Deploy and verify
[ ] 7. Monitor accuracy in production
```

---

## File Checklist

### Research & Documentation
- [ ] `docs/chicago-research.md` - Comprehensive research document
- [ ] `docs/chicago-rules.md` - Formal rules specification (optional)
- [ ] `backend/pseo/knowledge_base/chicago17/citation_rules.json` - Structured rules

### Golden Set
- [ ] `Checker_Prompt_Optimization/chicago_test_set_COMPREHENSIVE.jsonl` - All citations
- [ ] `Checker_Prompt_Optimization/chicago_test_set.jsonl` - Training set
- [ ] `Checker_Prompt_Optimization/chicago_holdout_set.jsonl` - Holdout set
- [ ] `Checker_Prompt_Optimization/chicago_test_set_SAMPLE.jsonl` - Quick test samples
- [ ] `Checker_Prompt_Optimization/split_chicago_test_set.py` - Split script

### Prompts
- [ ] `backend/prompts/validator_prompt_chicago17_v1.txt` - Initial prompt
- [ ] `backend/prompts/validator_prompt_chicago17_v1.1.txt` - Optimized prompt (if needed)

### Test Scripts
- [ ] `Checker_Prompt_Optimization/test_chicago_prompt_batched.py` - Baseline testing
- [ ] `Checker_Prompt_Optimization/test_chicago_v1.1_comparison.py` - Comparison testing
- [ ] `Checker_Prompt_Optimization/test_chicago_holdout_validation.py` - Final validation

### Results
- [ ] `Checker_Prompt_Optimization/chicago_baseline_results.json`
- [ ] `Checker_Prompt_Optimization/chicago_baseline_analysis.md`
- [ ] `Checker_Prompt_Optimization/chicago_v1.1_comparison_results.json` (if iterated)
- [ ] `Checker_Prompt_Optimization/chicago_holdout_validation_results.json`

### Integration
- [ ] `backend/styles.py` - Add chicago17 config
- [ ] `backend/app.py` - Add CHICAGO_ENABLED flag
- [ ] `backend/tests/test_styles.py` - Update tests
- [ ] `backend/tests/test_prompt_manager.py` - Update tests

---

## Authoritative Sources

### Primary Sources (for Rules)

| Source | URL | Use For |
|--------|-----|---------|
| Chicago Manual Online | https://www.chicagomanualofstyle.org | Official rules |
| Purdue OWL Chicago | https://owl.purdue.edu/owl/research_and_citation/chicago_manual_17th_edition/ | Rule explanations |
| Turabian Quick Guide | https://press.uchicago.edu/books/turabian/turabian_citationguide.html | Simplified reference |

### Secondary Sources (for Cross-Reference)

| Source | URL |
|--------|-----|
| University of Wisconsin | https://writing.wisc.edu/handbook/documentation/docchicago/ |
| Indiana University | https://libraries.indiana.edu/chicago-citation-style |
| Duke University | https://library.duke.edu/research/citing/chicago |

### Golden Set Sources (Non-Contaminated)

Target 8-10 university library guides that have real Chicago examples but are NOT primary citation references:

| University | URL to Verify |
|------------|---------------|
| Ohio State | guides.osu.edu/chicago |
| University of Toronto | guides.library.utoronto.ca |
| Penn State | guides.libraries.psu.edu |
| Boston College | libguides.bc.edu |
| Georgetown | guides.library.georgetown.edu |
| UCLA | guides.library.ucla.edu |
| Rice University | library.rice.edu |
| University of Virginia | guides.lib.virginia.edu |

---

## Lessons Learned from MLA

### What Worked Well

1. **Controlled mutations for invalid examples** - Each valid citation paired with ONE specific error
2. **Separate training/holdout sets** - Prevents overfitting
3. **80% accuracy threshold** - Clear ship/no-ship criteria
4. **Iterative prompt refinement** - v1 → v1.1 based on analysis
5. **Database source handling** - Explicit guidance prevents false negatives

### What to Avoid

1. **Overly strict validation** - MLA v1 had 50% recall (too strict)
2. **Excessive placeholder usage** - Only flag REQUIRED missing elements
3. **Redundant rule sections** - Streamlined prompt performed better
4. **Training on contaminated data** - Avoid examples from Purdue OWL, etc.

### Key Metrics to Watch

| Metric | Target | MLA v1 | MLA v1.1 |
|--------|--------|--------|----------|
| Accuracy | ≥80% | 74.1% | 83.9% |
| Recall | ≥70% | 50% | 70% |
| Precision | ≥90% | 96.6% | 95%+ |
| False Negatives | <20 | 28 | 17 |

---

## Beads Issue Tracking

Create the following issues to track implementation:

```bash
# Epic
bd create --title="Add Chicago 17th Edition Citation Style" --type=epic --priority=2

# Phase 1 tasks
bd create --title="Research Chicago 17th Edition rules" --type=task --priority=2
bd create --title="Create formal Chicago rules document (JSON)" --type=task --priority=2

# Phase 2 tasks
bd create --title="Identify non-contaminated Chicago example sources" --type=task --priority=2
bd create --title="Create Chicago golden test set (200+ citations)" --type=task --priority=2
bd create --title="Create Chicago test/holdout split script" --type=task --priority=3

# Phase 3 tasks
bd create --title="Create Chicago validator prompt v1" --type=task --priority=2
bd create --title="Create Chicago baseline test script" --type=task --priority=2

# Phase 4 tasks
bd create --title="Run Chicago baseline testing and analysis" --type=task --priority=2
bd create --title="Iterate Chicago prompt to v1.1 if needed" --type=task --priority=2
bd create --title="Run Chicago holdout validation" --type=task --priority=1

# Phase 5 tasks
bd create --title="Integrate Chicago style into backend" --type=task --priority=2
bd create --title="Deploy Chicago style to production" --type=task --priority=2
```

---

## Appendix: Example Chicago Citations

### Valid Examples (for reference)

**Book (Single Author):**
```
Morrison, Toni. Beloved. New York: Knopf, 1987.
```

**Book (Two Authors):**
```
Smith, John, and Jane Doe. Research Methods in the Social Sciences. Chicago: University of Chicago Press, 2020.
```

**Book (Four+ Authors):**
```
Johnson, Mark, et al. Collaborative Research Approaches. Boston: Academic Press, 2019.
```

**Journal Article:**
```
Williams, Sarah. "The Impact of Social Media on Political Discourse." Journal of Communication Studies 45, no. 2 (2020): 123-145.
```

**Website:**
```
"Citation Styles Guide." University Library. Last modified January 15, 2024. https://library.university.edu/citations.
```

**Newspaper Article:**
```
Thompson, James. "Economic Outlook for 2024." New York Times, December 28, 2023.
```

**Book Chapter:**
```
Brown, Emily. "Data Analysis Techniques." In Research Methods Handbook, edited by Michael Green, 45-78. London: Sage Publications, 2021.
```

**Film:**
```
The Godfather. Directed by Francis Ford Coppola. Hollywood: Paramount Pictures, 1972.
```

### Invalid Examples (with errors)

**Author Initials (Wrong):**
```
Morrison, T. Beloved. New York: Knopf, 1987.
```
Error: First name abbreviated to initial

**Missing Place (Wrong):**
```
Morrison, Toni. Beloved. Knopf, 1987.
```
Error: Missing place of publication

**Wrong Punctuation (Wrong):**
```
Morrison, Toni. Beloved, New York: Knopf, 1987.
```
Error: Comma after title instead of period

**Page Number Prefix (Wrong):**
```
Williams, Sarah. "The Impact of Social Media." Journal of Communication Studies 45, no. 2 (2020): pp. 123-145.
```
Error: Chicago doesn't use "pp." prefix
