# Request for Plan Review: Chicago Citation Style Implementation

## Context

We're building a citation validation tool that currently supports APA 7th Edition and MLA 9th Edition. We're planning to add Chicago 17th Edition (Notes-Bibliography system) as our third style.

The attached plan is comprehensive (~1500 lines) and covers:
- Strategic rationale for Chicago
- Technical architecture
- 6-phase implementation approach
- Golden set creation methodology
- Prompt engineering
- Testing strategy
- Integration points (28 files identified)
- Deployment and monitoring
- Risk mitigation

## What We Need

Please review this plan critically and provide feedback on:

1. **Gaps or Oversights**: Are there any critical aspects we've missed? Any integration points, edge cases, or considerations that aren't covered?

2. **Risk Assessment**: Are our identified risks comprehensive? Any hidden risks we haven't considered?

3. **Simplification Opportunities**: Are there ways to simplify the implementation without sacrificing quality? Are we over-engineering anything?

4. **Testing Strategy**: Is our approach to golden set creation and validation sound? Any improvements to suggest?

5. **Technical Concerns**: Any architectural issues, potential bugs, or technical debt we might be creating?

6. **Sequence/Dependencies**: Are the phases correctly ordered? Any dependencies we've missed?

7. **Success Metrics**: Are our metrics appropriate? Anything missing?

8. **General Feedback**: Any other observations, suggestions, or concerns?

## Key Decisions We've Made (Challenge These If Needed)

- Notes-Bibliography only (not Author-Date)
- Bibliography validation only (not footnotes)
- 80% accuracy threshold for launch
- Feature flag approach for rollout
- Golden set from non-primary university sources
- PSEO pages deferred to post-launch

---

# THE PLAN

Below is the complete Chicago implementation plan (v2):

---

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
### 4.2 Journal Articles
### 4.3 Websites
### 4.4 Newspaper/Magazine Articles
### 4.5 Other Sources

## 5. Key Differences from APA/MLA

## 6. Common Errors to Test

## 7. Sources Consulted
```

### 4.4 Structured Rules Document

**Output**: `backend/pseo/knowledge_base/chicago17/citation_rules.json`

**Rule Categories** (target ~45 rules):
- Author formatting: 6 rules
- Title formatting: 5 rules
- Publication info: 6 rules
- Punctuation: 5 rules
- URLs/DOIs: 4 rules
- Source-specific: 20 rules

---

## 5. Phase 2: Golden Set Creation

### 5.1 Objectives
- Create 200+ test citations (100+ valid, 100+ invalid pairs)
- Source examples from non-contaminated university libraries
- Ensure coverage across all source types

### 5.2 Why Non-Contaminated Sources Matter

**Problem**: LLMs were trained on common citation guides. If our test examples come from Purdue OWL or Scribbr, the LLM may "remember" them rather than actually validating.

**Solution**: Source examples from university library guides that are:
- Not primary citation references
- Have real Chicago examples
- Recently updated (2020+)

### 5.3 Target University Sources

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

### 5.4 Example Distribution

**Target: 224 citations total (112 valid + 112 invalid)**

| Source Type | Valid | Invalid | Total |
|-------------|-------|---------|-------|
| Books (single author) | 15 | 15 | 30 |
| Books (multiple authors) | 10 | 10 | 20 |
| Books (edited/chapters) | 8 | 8 | 16 |
| Journal articles | 20 | 20 | 40 |
| Websites | 15 | 15 | 30 |
| Newspaper/Magazine | 10 | 10 | 20 |
| Films/Videos | 6 | 6 | 12 |
| Other | 6 | 6 | 12 |
| **TOTAL** | **90** | **90** | **180** |

### 5.5 Invalid Variant Creation

Each valid citation gets ONE paired invalid variant with a specific, controlled error:
- Author errors (initials, wrong order, ampersand)
- Title errors (missing italics, wrong case)
- Publication errors (missing place, wrong punctuation)
- Date errors
- Punctuation errors
- Format errors (page prefix)

**Important**: Only ONE error per invalid citation for deterministic testing.

---

## 6. Phase 3: Prompt Engineering

### 6.1 Objectives
- Create validator prompt following proven MLA pattern
- Balance strictness vs leniency
- Handle edge cases explicitly

### 6.2 Key Prompt Principles (from MLA learnings)

1. **Be lenient by default** - MLA v1 was too strict (50% recall)
2. **Explicit database handling** - "If citation ends with database name, it's complete"
3. **Required vs optional** - Only flag MISSING for truly required elements
4. **Clear error descriptions** - State WHAT is wrong and HOW to fix
5. **Avoid rule redundancy** - Keep prompt focused

### 6.3 Prompt Structure

Target length: 100-130 lines (MLA v1.1 is 110 lines)

Sections:
- Task description
- Bibliography formats by source type
- Core rules (authors, titles, publication info, punctuation, URLs)
- Input handling
- Missing information handling
- Output format

---

## 7. Phase 4: Testing & Iteration

### 7.1 Test Configuration

```python
MODEL = "gemini-2.0-flash"
TEMPERATURE = 0.0
BATCH_SIZE = 5
```

### 7.2 Metrics to Capture

- Accuracy, Precision, Recall, F1
- Confusion matrix
- Accuracy by source type
- Placeholder usage

### 7.3 Testing Workflow

1. Baseline test (v1 + training set) → Target ≥80%
2. If <80%: Analyze failures, iterate prompt
3. Holdout validation (run ONCE) → Must be ≥80% to ship

### 7.4 Launch Criteria

| Accuracy | Action |
|----------|--------|
| ≥80% | Ship |
| 65-79% | Iterate |
| <65% | Major revision |

---

## 8. Phase 5: Integration

### 8.1 Backend Changes (Required)

1. `backend/styles.py` - Add chicago17 config
2. `backend/app.py` - Add CHICAGO_ENABLED feature flag
3. `backend/prompts/validator_prompt_chicago17_v1.txt` - Create

### 8.2 Frontend Changes

1. `App.jsx` - Update FAQ, fix style initialization for 3+ styles
2. `StyleSelector.jsx` - Verify 3-tab handling (should work, data-driven)

### 8.3 Dashboard/Analytics

1. `telegram_notifier.py` - Add to style_map
2. Database schema - Add style column (recommended)

### 8.4 Tests (Required)

- Unit tests for styles module
- API tests for Chicago validation
- E2E tests for style selection

---

## 9. Phase 6: Deployment & Monitoring

### 9.1 Deployment Strategy

1. Dark launch (CHICAGO_ENABLED=false)
2. Deploy, verify APA/MLA work
3. Enable Chicago (CHICAGO_ENABLED=true)
4. Monitor for 24 hours

### 9.2 Rollback Plan

**Quick fix**: Set CHICAGO_ENABLED=false (no code deploy needed)

**Triggers**:
- Error rate >5%
- Overall system error rate increases
- Critical bug in style selection

---

## 10. All Integration Points (Complete List)

**Total: 28 integration points, 12 required, 16 recommended/optional**

### Backend (14 files)
- `styles.py` - REQUIRED
- `app.py` - REQUIRED
- `prompts/validator_prompt_chicago17_v1.txt` - REQUIRED
- `tests/test_styles.py` - REQUIRED
- `tests/test_prompt_manager.py` - REQUIRED
- `tests/test_app.py` - REQUIRED
- Others: Optional

### Frontend (6 files)
- `App.jsx` - REQUIRED (FAQ + init)
- `e2e-chicago-validation.spec.cjs` - REQUIRED
- Others: Verify/Optional

### Dashboard (3 files)
- `telegram_notifier.py` - REQUIRED
- Others: Recommended

### Documentation (3 files)
- `docs/chicago-research.md` - REQUIRED
- Others: Recommended

### Deployment (2 files)
- Production `.env` - REQUIRED

---

## 11. Risk Mitigation & Rollback

### Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Prompt accuracy <80% | Medium | High | Iterate on training set |
| Golden set contaminated | Low | High | Use non-primary sources |
| Frontend breaks with 3 tabs | Low | Medium | Test on mobile |
| LLM latency increases | Low | Low | Similar prompt length |

### Rollback Procedure

1. Set CHICAGO_ENABLED=false
2. Restart application
3. Verify Chicago removed from /api/styles
4. Investigate and fix

---

## 12. Simplification Opportunities

### What We're NOT Doing

- Footnote validation
- Author-Date system
- PSEO pages at launch
- Custom error messages
- Per-style rate limits
- Per-style pricing

### Reuse Opportunities

- Copy MLA test scripts, change file names
- Follow MLA prompt structure
- Copy MLA E2E tests, update selectors
- Same feature flag pattern

---

## 13. Out of Scope (Deferred)

### Deferred to Post-Launch
- Chicago PSEO pages
- Chicago Author-Date
- MiniChecker Chicago support
- Style-specific analytics dashboard

### Not Planned
- Footnote validation
- Citation generation
- Bibliography sorting
- In-text citation validation

---

## 14. Success Metrics

### Launch Criteria (Must Have)
- Holdout accuracy ≥80%
- All existing tests pass
- No critical bugs
- Feature flag works

### Post-Launch (30 days)
- Chicago usage >5% of validations
- Error rate <2%
- User complaints <5

### Long-Term (90 days)
- Chicago usage >10%
- User retention stable
- SEO traffic (if PSEO added)

---

## Appendix: MLA Methodology Reference

### MLA Golden Set Sources (8 universities)
- University of Nevada, Reno
- University of Portland
- University of Maryland UMGC
- NW Missouri State
- Florida State College Jacksonville
- Seneca Polytechnic
- Seminole State College
- University of Queensland

### MLA Prompt Evolution
- v1: 74.1% accuracy (failed)
- v1.1: 83.9% accuracy (passed)
- Holdout: 89.3% (shipped)

### Key Fixes in v1.1
1. Explicit database source handling
2. Removed redundant rule sections
3. Clarified required vs optional elements
4. Reduced prompt length (160 → 110 lines)

---

*End of Plan*
