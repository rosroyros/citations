# Chicago Citation Style Implementation Plan v3 (Final)

**Created:** 2025-12-31
**Last Updated:** 2025-12-31
**Status:** Approved - Ready for Implementation
**Author:** Planning Session with Claude + Oracle Review
**Style:** Chicago Manual of Style 17th Edition (Notes-Bibliography System)

---

## Document Purpose

This is the **final, approved** implementation plan for adding Chicago 17th Edition citation validation. It incorporates feedback from external review (Gemini Pro/Oracle) and is designed for complete handoff - any engineer can implement this with zero prior context.

**Review History:**
- v1: Initial draft
- v2: Added integration points, risk mitigation, monitoring
- v3: Incorporated Oracle feedback (3-em dash rule, footnote detection, label clarity, golden set additions, metric refinements)

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
10. [All Integration Points](#10-all-integration-points)
11. [Risk Mitigation & Rollback](#11-risk-mitigation--rollback)
12. [Out of Scope](#12-out-of-scope)
13. [Success Metrics](#13-success-metrics)
14. [Appendices](#appendices)

---

## 1. Executive Summary

### What We're Building
Add Chicago Manual of Style 17th Edition (Notes-Bibliography system) as a third citation validation style, alongside existing APA 7 and MLA 9.

### Why Chicago?
- **Market gap**: Chicago is the #3 citation style globally. All competitors offer APA/MLA/Chicago as baseline. We're missing it.
- **User demand**: Required for history, humanities, business, fine arts - significant student population.
- **Strategic positioning**: Completes the "Big 3", positions us as comprehensive.

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Which Chicago system? | Notes-Bibliography only | More common for humanities; Author-Date is similar to APA |
| Validate footnotes? | No, bibliography only | Bibliography is the hard part; footnotes follow same format |
| Style ID | `chicago17` | Matches pattern (apa7, mla9) |
| UI Label | `Chicago 17th (Notes-Bib)` | **[Oracle feedback]** Clarifies which system to avoid user confusion |
| Launch threshold | ≥80% accuracy | Proven threshold from MLA launch |
| 3-em dash rule | Accept both formats | **[Oracle feedback]** Don't enforce; accept with or without |

### Success Criteria
- ≥80% accuracy on holdout validation set
- ≥70% recall (avoid MLA v1's 50% recall problem)
- All existing APA/MLA tests still pass
- No regression in system performance

---

## 2. Strategic Context & Decision Rationale

### 2.1 Why Chicago Over Other Styles?

| Style | Pros | Cons | Verdict |
|-------|------|------|---------|
| **Chicago** | #3 globally, completes Big 3 | Complex (2 systems) | ✅ Selected |
| IEEE | Simple format, growing CS market | Niche audience | Next candidate |
| Harvard | UK/Australia market | No single standard | Deferred |
| AMA | Medical standard | Very specialized | Low priority |
| Bluebook | Legal standard | Extremely complex | Not recommended |

### 2.2 Why Notes-Bibliography Only?

Chicago has two systems:

| System | Description | Target Users |
|--------|-------------|--------------|
| **Notes-Bibliography** | Footnotes + Bibliography | Humanities, history, arts |
| **Author-Date** | In-text (Author Year) | Sciences, social sciences |

**Decision**: Notes-Bibliography because:
1. It's the distinctive Chicago system (Author-Date ≈ APA)
2. Humanities is our Chicago target market
3. Bibliography entries are valuable standalone
4. Author-Date can be added later as `chicago17-ad`

### 2.3 Why Bibliography-Only Validation Works

- Students struggle with bibliography formatting, not footnote placement
- Footnote format mirrors bibliography (same elements, different order)
- Many students just want "is my bibliography correct?"
- Same approach we use for APA and MLA

### 2.4 Lessons from MLA Implementation

| Issue | What Happened | How We'll Avoid |
|-------|---------------|-----------------|
| Overly strict v1 | 50% recall | Start lenient, tighten if needed |
| Database sources | False negatives for JSTOR | Explicit "database sources are complete" rule |
| Excessive placeholders | 27/112 had [MISSING: ...] | Only flag REQUIRED elements |
| Contaminated data | LLM might know examples | Use non-primary university sources |

**MLA Results:**
- v1: 74.1% (failed) → v1.1: 83.9% (passed) → Holdout: 89.3%

---

## 3. Technical Architecture Overview

### 3.1 How Styles Work

```
User selects style (frontend)
         ↓
POST /api/validate/async {style: "chicago17"}
         ↓
Backend validates style → styles.py SUPPORTED_STYLES
         ↓
PromptManager loads → prompts/validator_prompt_chicago17_v1.txt
         ↓
LLM validates using prompt rules
         ↓
Results returned with style-specific success message
```

**Key insight**: Style parameter selects which prompt to load. All validation logic is IN the prompt. LLM providers need no Chicago-specific code.

### 3.2 Minimum Required for Launch

```
backend/
├── styles.py                              # Add chicago17 config
├── app.py                                 # Add CHICAGO_ENABLED flag
└── prompts/
    └── validator_prompt_chicago17_v1.txt  # Validation rules

frontend/
└── App.jsx                                # Update FAQ + style init
```

**Everything else is optional/post-launch.**

### 3.3 Style Configuration

**Current** (`backend/styles.py`):
```python
SUPPORTED_STYLES = {
    "apa7": {"label": "APA 7th Edition", ...},
    "mla9": {"label": "MLA 9th Edition", ...}
}
```

**After Chicago**:
```python
SUPPORTED_STYLES = {
    "apa7": {...},
    "mla9": {...},
    "chicago17": {
        "label": "Chicago 17th (Notes-Bib)",  # Clear label per Oracle
        "prompt_file": "validator_prompt_chicago17_v1.txt",
        "success_message": "No Chicago 17 formatting errors detected"
    }
}
```

---

## 4. Phase 1: Research & Rules Documentation

### 4.1 Objectives
- Document all Chicago 17th Edition bibliography rules
- Establish authoritative source hierarchy
- **[Oracle]** Decide stance on 3-em dash rule for repeated authors
- Create structured rules JSON

### 4.2 Authoritative Sources

**Tier 1 - Official (for rules)**:
| Source | URL |
|--------|-----|
| Chicago Manual of Style Online | chicagomanualofstyle.org |
| Turabian Quick Guide | press.uchicago.edu/books/turabian/ |
| Purdue OWL Chicago | owl.purdue.edu/.../chicago_manual_17th_edition/ |

**Tier 2 - Academic (cross-reference)**:
- University of Wisconsin, Indiana, Duke, Illinois

**Important**: Tier 1 for rules only. Do NOT use their examples in test set (contamination risk).

### 4.3 Special Rules to Decide

**[Oracle Feedback] 3-em Dash Rule:**

Chicago allows using three-em dashes (———) to replace repeated author names in bibliographies:
```
Morrison, Toni. Beloved. New York: Knopf, 1987.
———. Song of Solomon. New York: Knopf, 1977.
```

**Decision**: Accept BOTH formats (with or without 3-em dashes). Don't enforce either way.
- Rationale: Some professors require it, others don't
- Our validator should accept valid citations regardless of this stylistic choice

### 4.4 Research Document

**Output**: `docs/chicago-research.md`

**Required Sections**:
1. Overview (history, systems, when used)
2. Notes-Bibliography System (footnote vs bibliography format)
3. Core Elements (author, title, publication, access info)
4. Source Type Formats (books, journals, websites, newspapers, films, etc.)
5. Key Differences from APA/MLA (comparison table)
6. **Special Rules** (3-em dash, "Ibid.", repeated authors)
7. Common Errors to Test
8. Sources Consulted

### 4.5 Structured Rules JSON

**Output**: `backend/pseo/knowledge_base/chicago17/citation_rules.json`

**Target: ~45 rules**:
- Author formatting: 6 rules
- Title formatting: 5 rules
- Publication info: 6 rules
- Punctuation: 5 rules
- URLs/DOIs: 4 rules
- Source-specific: 20 rules

### 4.6 Deliverables
- [ ] `docs/chicago-research.md`
- [ ] `backend/pseo/knowledge_base/chicago17/citation_rules.json`
- [ ] 3-em dash stance documented
- [ ] All Tier 1 sources consulted
- [ ] Rules cross-referenced with Tier 2 sources

---

## 5. Phase 2: Golden Set Creation

### 5.1 Objectives
- Create 200+ test citations (100+ valid, 100+ invalid pairs)
- Source from non-contaminated university libraries
- **[Oracle]** Include 5-10 corporate author examples
- **[Oracle]** Include 5-10 government document examples
- Ensure coverage across all source types

### 5.2 Non-Contaminated Sources

**Why it matters**: LLMs were trained on Purdue OWL, Scribbr, etc. Test examples from those sources may be "remembered" rather than validated.

**Solution**: Use university library guides that are NOT primary citation references.

### 5.3 Target University Sources

| University | URL | Notes |
|------------|-----|-------|
| Ohio State | guides.osu.edu/chicago | Large, comprehensive |
| U of Toronto | guides.library.utoronto.ca | Canadian coverage |
| Penn State | guides.libraries.psu.edu | Extensive guides |
| U of Washington | guides.lib.uw.edu | Major research |
| Boston College | libguides.bc.edu | Strong humanities |
| Georgetown | guides.library.georgetown.edu | History focus |
| UCLA | guides.library.ucla.edu | Major research |
| U of Virginia | guides.lib.virginia.edu | Strong humanities |
| Rice | library.rice.edu | Quality guides |
| Emory | guides.libraries.emory.edu | Good humanities |

### 5.4 Example Distribution

**Target: 224 citations (112 valid + 112 invalid)**

| Source Type | Valid | Invalid | Total |
|-------------|-------|---------|-------|
| Books (single author) | 15 | 15 | 30 |
| Books (multiple authors) | 10 | 10 | 20 |
| Books (edited/chapters) | 8 | 8 | 16 |
| Journal articles | 20 | 20 | 40 |
| Websites | 15 | 15 | 30 |
| Newspaper/Magazine | 10 | 10 | 20 |
| Films/Videos | 6 | 6 | 12 |
| **Corporate authors** | **5** | **5** | **10** |
| **Government documents** | **5** | **5** | **10** |
| Other (interviews) | 4 | 4 | 8 |
| **TOTAL** | **98** | **98** | **196** |

**[Oracle]** Corporate authors and government documents are Chicago pain points - ensure adequate coverage.

### 5.5 Invalid Variant Creation

Each valid citation gets ONE paired invalid variant with a specific error:

| Error Category | Mutations |
|----------------|-----------|
| Author | Initials, wrong order, ampersand, missing period |
| Title | Missing italics, wrong case, missing quotes |
| Publication | Missing place, wrong punctuation, missing publisher |
| Date | Wrong format, wrong position |
| Punctuation | Missing period, comma instead of period |
| Format | Page prefix (pp.), wrong volume format |

**Important**: ONE error per invalid citation for deterministic testing.

### 5.6 File Format

```jsonl
{"citation": "Morrison, Toni. Beloved. New York: Knopf, 1987.", "ground_truth": true, "source_type": "book", "source_url": "https://guides.osu.edu/chicago"}
{"citation": "Morrison, T. Beloved. New York: Knopf, 1987.", "ground_truth": false, "source_type": "book", "error_type": "author_initials", "paired_with": 0}
```

### 5.7 Train/Holdout Split

- 50/50 split maintaining pairs together
- Fixed RANDOM_SEED=42 for reproducibility
- Output: `chicago_test_set.jsonl` + `chicago_holdout_set.jsonl`

### 5.8 Deliverables
- [ ] 8+ university sources verified
- [ ] `chicago_test_set_COMPREHENSIVE.jsonl` (196+ citations)
- [ ] Source URL for each valid citation
- [ ] Error type for each invalid citation
- [ ] 5-10 corporate author examples included
- [ ] 5-10 government document examples included
- [ ] `split_chicago_test_set.py`
- [ ] `chicago_test_set.jsonl` (training)
- [ ] `chicago_holdout_set.jsonl` (holdout)
- [ ] `chicago_test_set_SAMPLE.jsonl` (4-6 quick test)

---

## 6. Phase 3: Prompt Engineering

### 6.1 Objectives
- Create validator prompt following MLA pattern
- Balance strictness vs leniency
- **[Oracle]** Add footnote detection guardrail
- Handle 3-em dash rule explicitly

### 6.2 Prompt Structure

**File**: `backend/prompts/validator_prompt_chicago17_v1.txt`

**Target length**: 100-130 lines

**Sections**:
1. Task description
2. **[NEW] Footnote detection guardrail**
3. Bibliography formats by source type
4. Core rules (authors, titles, publication, punctuation, URLs)
5. **[NEW] 3-em dash handling**
6. Input handling
7. Missing information handling (database sources)
8. Output format

### 6.3 Footnote Detection Guardrail

**[Oracle Feedback]** Users might paste footnotes instead of bibliography entries.

**Add to prompt**:
```
## FOOTNOTE DETECTION

If the input appears to be a footnote rather than a bibliography entry:
- Starts with a number (1. or ¹)
- Has author name in "First Last" order (not inverted)
- Includes page numbers inline

Then output:
"⚠️ This appears to be a footnote, not a bibliography entry. We validate Bibliography/Works Cited entries. Please paste your bibliography entries for validation."

Do NOT attempt to validate footnotes as if they were bibliography entries.
```

### 6.4 3-em Dash Handling

**Add to prompt**:
```
## REPEATED AUTHOR FORMAT

Chicago allows 3-em dashes (———) for repeated authors:
- Valid: ———. Song of Solomon. New York: Knopf, 1977.
- Also valid: Morrison, Toni. Song of Solomon. New York: Knopf, 1977.

Accept BOTH formats. Do not flag as error either way.
The 3-em dash must be followed by a period and space.
```

### 6.5 Key Prompt Principles (from MLA)

1. **Be lenient by default** - Start lenient, tighten if precision suffers
2. **Explicit database handling** - "If ends with database name, it's complete"
3. **Required vs optional** - Only flag MISSING for truly required elements
4. **Clear error descriptions** - State WHAT and HOW to fix
5. **Avoid redundancy** - Keep focused

### 6.6 Deliverables
- [ ] `validator_prompt_chicago17_v1.txt`
- [ ] Footnote detection guardrail included
- [ ] 3-em dash handling included
- [ ] All source type formats documented
- [ ] Database source handling included
- [ ] Output format matches APA/MLA

---

## 7. Phase 4: Testing & Iteration

### 7.1 Test Configuration

```python
MODEL = "gemini-2.0-flash"
TEMPERATURE = 0.0
BATCH_SIZE = 5
RATE_LIMIT_DELAY = 2
```

### 7.2 Metrics

- Accuracy, Precision, Recall, F1
- Confusion matrix (TP, TN, FP, FN)
- Accuracy by source type
- Placeholder usage count

### 7.3 Testing Workflow

```
BASELINE TEST (v1 + training set)
    ↓
Accuracy ≥80%?
    YES → HOLDOUT VALIDATION
    NO  → Analyze failures → Iterate prompt → Retest
    ↓
HOLDOUT VALIDATION (run ONCE)
    ↓
≥80%? → SHIP
<80%? → Review fundamentals
```

### 7.4 Launch Criteria

| Accuracy | Action |
|----------|--------|
| ≥80% | Ship |
| 65-79% | Iterate |
| <65% | Major revision |

### 7.5 Deliverables
- [ ] `test_chicago_prompt_batched.py`
- [ ] `chicago_baseline_results.json`
- [ ] `chicago_baseline_analysis.md` (if iteration)
- [ ] `validator_prompt_chicago17_v1.1.txt` (if iteration)
- [ ] `chicago_holdout_validation_results.json`
- [ ] Holdout ≥80% confirmed

---

## 8. Phase 5: Integration

### 8.1 Backend Changes

**8.1.1 styles.py (REQUIRED)**:
```python
"chicago17": {
    "label": "Chicago 17th (Notes-Bib)",  # [Oracle] Clear label
    "prompt_file": "validator_prompt_chicago17_v1.txt",
    "success_message": "No Chicago 17 formatting errors detected"
}

StyleType = Literal["apa7", "mla9", "chicago17"]
```

**8.1.2 app.py (REQUIRED)**:
```python
CHICAGO_ENABLED = os.getenv('CHICAGO_ENABLED', 'false').lower() == 'true'

# In /api/styles endpoint:
if CHICAGO_ENABLED:
    styles["chicago17"] = SUPPORTED_STYLES["chicago17"]["label"]
```

**8.1.3 Prompt file (REQUIRED)**:
Copy to `backend/prompts/validator_prompt_chicago17_v1.txt`

### 8.2 Frontend Changes

**8.2.1 App.jsx - Style Initialization (REQUIRED)**

**[Oracle]** Current code only handles apa7/mla9:
```javascript
// CURRENT (broken for Chicago)
return savedStyle === 'mla9' ? 'mla9' : 'apa7'

// FIXED (generic)
const validStyles = ['apa7', 'mla9', 'chicago17']
return validStyles.includes(savedStyle) ? savedStyle : 'apa7'
```

**8.2.2 App.jsx - FAQ Update (REQUIRED)**:
```javascript
// CURRENT
"APA 7th Edition and MLA 9th Edition"

// UPDATED
"APA 7th Edition, MLA 9th Edition, and Chicago 17th Edition (Notes-Bibliography)"
```

**8.2.3 StyleSelector.jsx - Mobile Check (RECOMMENDED)**:
Verify 3-tab layout works on mobile. May need scrolling for narrow screens.

### 8.3 Dashboard/Analytics

**8.3.1 telegram_notifier.py (REQUIRED)**:
```python
style_map = {'apa7': 'APA 7', 'mla9': 'MLA 9', 'chicago17': 'Chicago 17'}
```

**8.3.2 Database Schema (RECOMMENDED)**:
```sql
ALTER TABLE validations ADD COLUMN style VARCHAR(20) DEFAULT 'apa7';
```

### 8.4 Tests

**Unit Tests** (`test_styles.py`):
```python
def test_chicago_in_supported_styles():
    assert "chicago17" in SUPPORTED_STYLES

def test_chicago_has_required_fields():
    config = SUPPORTED_STYLES["chicago17"]
    assert all(k in config for k in ["label", "prompt_file", "success_message"])
```

**API Tests** (`test_app.py`):
```python
def test_validate_accepts_chicago():
    response = client.post("/api/validate/async", json={
        "citations": "Morrison, Toni. Beloved. New York: Knopf, 1987.",
        "style": "chicago17"
    })
    assert response.status_code == 200
```

**E2E Tests** (`e2e-chicago-validation.spec.cjs`):
- Can select Chicago style
- Validates Chicago citation correctly
- URL parameter `?style=chicago17` works

### 8.5 Deliverables
- [ ] `styles.py` updated
- [ ] `app.py` feature flag added
- [ ] Prompt file deployed
- [ ] `App.jsx` style init fixed
- [ ] `App.jsx` FAQ updated
- [ ] `telegram_notifier.py` updated
- [ ] Unit tests added
- [ ] API tests added
- [ ] E2E tests created
- [ ] All existing tests pass
- [ ] Mobile 3-tab layout verified

---

## 9. Phase 6: Deployment & Monitoring

### 9.1 Deployment Strategy

1. **Dark launch**: Deploy with CHICAGO_ENABLED=false
2. **Verify**: APA/MLA still work
3. **Enable**: Set CHICAGO_ENABLED=true
4. **Monitor**: 24 hours

### 9.2 Monitoring

| Metric | Where | Alert Threshold |
|--------|-------|-----------------|
| Chicago errors | Logs | >5% error rate |
| Chicago usage | Dashboard | N/A (informational) |
| API latency | Monitoring | >10s p95 |
| User complaints | Support | Any |

### 9.3 Rollback

**Quick**: Set CHICAGO_ENABLED=false (no deploy needed)

**Triggers**:
- Error rate >5%
- Overall system errors increase
- Critical bug

### 9.4 Deliverables
- [ ] Deployed with flag=false
- [ ] APA/MLA verified
- [ ] Flag enabled
- [ ] 24-hour monitoring complete
- [ ] No critical issues

---

## 10. All Integration Points

### Required (12 files)

| File | Change |
|------|--------|
| `backend/styles.py` | Add chicago17 config |
| `backend/app.py` | Add feature flag |
| `backend/prompts/validator_prompt_chicago17_v1.txt` | Create |
| `backend/tests/test_styles.py` | Add tests |
| `backend/tests/test_prompt_manager.py` | Add tests |
| `backend/tests/test_app.py` | Add tests |
| `frontend/frontend/src/App.jsx` | FAQ + init fix |
| `frontend/frontend/tests/e2e/e2e-chicago-validation.spec.cjs` | Create |
| `dashboard/telegram_notifier.py` | Add to style_map |
| `docs/chicago-research.md` | Create |
| Production `.env` | CHICAGO_ENABLED=true |

### Recommended (6 files)

| File | Change |
|------|--------|
| `backend/pseo/knowledge_base/chicago17/citation_rules.json` | Structured rules |
| `backend/citation_logger.py` | Add style to logs |
| Dashboard database | Add style column |
| `README.md` | Update supported styles |
| `.env.example` | Document variable |
| StyleSelector mobile | Verify 3-tab |

### Optional/Post-Launch

- PSEO generator + configs
- MiniChecker Chicago support
- Style-specific analytics dashboard

---

## 11. Risk Mitigation & Rollback

### Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Accuracy <80% | Medium | High | Iterate on training set |
| Golden set contaminated | Low | High | Non-primary sources |
| Frontend 3-tab breaks | Low | Medium | Mobile testing |
| LLM latency | Low | Low | Similar prompt length |
| **[Oracle]** Footnote confusion | Medium | Low | Detection guardrail |
| **[Oracle]** Author-Date confusion | Low | Low | Clear label |

### Rollback Procedure

1. Set CHICAGO_ENABLED=false
2. Restart (or wait for env refresh)
3. Verify removed from /api/styles
4. Investigate and fix

---

## 12. Out of Scope

### Deferred to Post-Launch
- PSEO pages for Chicago
- Author-Date system (`chicago17-ad`)
- MiniChecker Chicago support

### Not Planned
- Footnote validation
- Citation generation
- Bibliography sorting
- In-text citation validation

---

## 13. Success Metrics

### Launch Criteria (Must Have)

| Metric | Target |
|--------|--------|
| Holdout accuracy | ≥80% |
| Existing tests | 100% pass |
| Critical bugs | 0 |
| Feature flag | Works |

### Post-Launch (30 days)

| Metric | Target |
|--------|--------|
| Chicago usage | >5% of validations |
| Error rate | <2% |
| **[Oracle]** Chicago accuracy tickets | <1% of Chicago volume |

### Long-Term (90 days)

| Metric | Target |
|--------|--------|
| Chicago usage | >10% |
| User retention | No decrease |

---

## Appendices

### Appendix A: MLA Methodology Reference

**Sources** (8 universities):
- U of Nevada Reno, U of Portland, U of Maryland UMGC, NW Missouri State
- Florida State College Jacksonville, Seneca Polytechnic, Seminole State, U of Queensland

**Results**: v1: 74.1% → v1.1: 83.9% → Holdout: 89.3%

**Key Fixes**: Database handling, removed redundancy, clarified required vs optional

### Appendix B: Example Citations

**Valid**:
```
Morrison, Toni. Beloved. New York: Knopf, 1987.
Smith, John, and Jane Doe. Research Methods. Chicago: U of Chicago Press, 2020.
Williams, Sarah. "Social Media Impact." Journal of Communication 45, no. 2 (2020): 123-145.
U.S. Department of Labor. "Employment Projections." Bureau of Labor Statistics. 2024. https://bls.gov/projections.
```

**Invalid**:
```
Morrison, T. Beloved. New York: Knopf, 1987.  [initials]
Morrison, Toni. Beloved. Knopf, 1987.  [missing place]
Smith, John & Jane Doe. Research Methods...  [ampersand]
Williams, Sarah. "Social Media." Journal... pp. 123-145.  [pp. prefix]
```

### Appendix C: Authoritative Sources

**Tier 1** (rules):
- chicagomanualofstyle.org
- press.uchicago.edu/books/turabian/
- owl.purdue.edu/.../chicago_manual_17th_edition/

**Tier 2** (cross-reference):
- U of Wisconsin, Indiana, Duke, Illinois

**Tier 3** (golden set):
- Ohio State, U of Toronto, Penn State, U of Washington
- Boston College, Georgetown, UCLA, U of Virginia, Rice, Emory

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2025-12-31 | Initial plan |
| v2 | 2025-12-31 | Integration points, risks, monitoring |
| v3 | 2025-12-31 | Oracle feedback: 3-em dash, footnote detection, label, golden set, metrics |

---

*End of Document*
