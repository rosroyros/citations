# Citation Checker Prompt Optimization Process

**Last Updated:** October 21, 2025
**Status:** Active workflow for maintaining and improving citation validation

---

## Overview

This document describes the complete process for adding/changing citations in the dataset and re-optimizing the citation validator prompt using DSPy + MIPROv2.

---

## Dataset Structure

### Location
```
backend/pseo/optimization/datasets/
├── valid_citations_clean_final.jsonl       # 62 valid citations
└── invalid_citations_standardized.jsonl    # 53 invalid citations
```

### Format Requirements

**Valid Citations (valid_citations_clean_final.jsonl):**
```json
{
  "citation_text": "Author, A. (2020). Article title. _Journal Name_, 10(2), 123-456.",
  "source_type": "journal article",
  "metadata": {
    "url": "https://owl.purdue.edu/...",
    "section": "Journal Articles"
  }
}
```

**Invalid Citations (invalid_citations_standardized.jsonl):**
```json
{
  "citation_text": "Author, A. and Author, B. (2020). Title...",
  "source_type": "journal article",
  "errors": [
    {
      "component": "authors",
      "problem": "Using 'and' instead of '&' before final author",
      "correction": "Should use '&' in reference list"
    }
  ]
}
```

**Critical Format Notes:**
- **Italics:** Use underscores `_text_` (NOT `[ITALIC]text[/ITALIC]`)
- **Components:** Must be lowercase from standardized list (authors, title, journal, doi, publisher, date, volume, issue, pages, format)
- **Encoding:** UTF-8
- **Format:** JSONL (one JSON object per line)

---

## Workflow: Adding/Changing Citations

### Step 1: Modify Dataset Files

**Add Valid Citation:**
```bash
# Edit file directly
nano backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl

# Add new line in correct format
{"citation_text": "...", "source_type": "journal article", "metadata": {...}}
```

**Add Invalid Citation:**
```bash
# Edit file directly
nano backend/pseo/optimization/datasets/invalid_citations_standardized.jsonl

# Add new line with errors
{"citation_text": "...", "source_type": "...", "errors": [...]}
```

**Important:** Ensure italics use underscores `_text_`, not `[ITALIC]` tags.

### Step 2: Verify Data Quality

**Check for format consistency:**
```bash
cd /Users/roy/Documents/Projects/citations
source venv/bin/activate

# Verify no [ITALIC] tags remain
grep -c "\[ITALIC\]" backend/pseo/optimization/datasets/*.jsonl
# Should return 0 for both files

# Count citations
wc -l backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl
wc -l backend/pseo/optimization/datasets/invalid_citations_standardized.jsonl
```

### Step 3: Run Optimization

**Execute MIPROv2 optimization:**
```bash
source venv/bin/activate
python3 backend/pseo/optimization/run_gepa_final.py 2>&1 | tee backend/pseo/optimization/latest_optimization.log
```

**What this does:**
1. Loads both dataset files (valid + invalid)
2. Shuffles and splits: 70% train, 15% validation, 15% test (seed=42 for reproducibility)
3. Evaluates baseline validator on validation set
4. Runs MIPROv2 optimization to improve prompt
5. Evaluates optimized validator on test set
6. Saves optimized model to `backend/pseo/optimization/optimized_prompts/gepa_optimized_validator.json`

**Expected duration:** 5-10 minutes

### Step 4: Generate Test Predictions

**Run predictions on test set:**
```bash
python3 backend/pseo/optimization/get_test_predictions.py
```

**What this does:**
1. Loads test set (same 15% split as optimization)
2. Loads optimized validator from previous step
3. Runs predictions on all 18 test citations
4. Saves results to `backend/pseo/optimization/test_predictions.json`
5. Reports accuracy

### Step 5: Generate HTML Report

**Create visual report:**
```bash
python3 backend/pseo/optimization/generate_citation_report.py
```

**Output:** `backend/pseo/optimization/citation_dataset_report.html`

**View in browser:**
```
file:///Users/roy/Documents/Projects/citations/backend/pseo/optimization/citation_dataset_report.html
```

**Report includes:**
- Dataset overview (train/val/test splits)
- All citations organized by set
- Test set predictions with ground truth comparison
- Color-coded correct/incorrect predictions

---

## Key Files & Their Purposes

| File | Purpose | Updated By |
|------|---------|------------|
| `valid_citations_clean_final.jsonl` | Valid citation examples | Manual editing |
| `invalid_citations_standardized.jsonl` | Invalid citation examples | Manual editing |
| `run_gepa_final.py` | Main optimization script | Development |
| `get_test_predictions.py` | Generate test predictions | Automated (Step 4) |
| `generate_citation_report.py` | Create HTML report | Automated (Step 5) |
| `test_predictions.json` | Cached test predictions | `get_test_predictions.py` |
| `gepa_optimized_validator.json` | Optimized model weights | `run_gepa_final.py` |
| `citation_dataset_report.html` | Visual report | `generate_citation_report.py` |

---

## Evaluation Metrics

### Metric: Balanced 50/50 Score

Defined in `dspy_validator.py:citation_validator_metric()`:

**Components:**
1. **Citation-level (50%):** Correct valid/invalid classification
2. **Error-level (50%):** F1 score on error component matching

**Scoring:**
- Both agree valid → 1.0
- Both agree invalid + errors match → 0.5 + 0.5×F1
- Disagree on validity → 0.0

**Why this metric:**
Prevents gaming by over-flagging or under-flagging citations. Forces model to be accurate on both classification AND error detection.

### Reported Metrics

From `run_gepa_final.py` output:
```
Baseline Metrics:
  Citation Accuracy: 44.44%
  Error Detection F1: 45.28%

Optimized Metrics:
  Citation Accuracy: 44.44%
  Error Detection F1: 38.10%
```

**Note:** Error Detection F1 only counts invalid citations (valid citations have no errors to detect).

---

## Common Issues & Solutions

### Issue: Predictions Show Wrong Format

**Symptom:** HTML report shows underscores but predictions complain about `[ITALIC]` tags

**Cause:** Stale `test_predictions.json` from before format conversion

**Solution:**
```bash
# Regenerate predictions
python3 backend/pseo/optimization/get_test_predictions.py

# Regenerate report
python3 backend/pseo/optimization/generate_citation_report.py
```

### Issue: Dataset Has Mixed Formats

**Symptom:** Some citations use `[ITALIC]`, others use `_text_`

**Cause:** Incomplete conversion

**Solution:**
```bash
# Convert all [ITALIC] tags to underscores
python3 backend/pseo/optimization/convert_italic_tags_to_markdown.py
```

### Issue: Low Optimization Performance

**Symptom:** Optimized model performs worse than baseline

**Possible causes:**
1. **Insufficient data:** Need more diverse examples (aim for 100+ each)
2. **Data quality:** Errors in ground truth labels
3. **Metric mismatch:** Optimization metric doesn't match evaluation goals

**Solutions:**
- Add more citations with diverse error types
- Manually review dataset for labeling errors
- Adjust metric weights in `dspy_validator.py`

---

## Data Collection Guidelines

### Valid Citations

**Sources:**
- Purdue OWL (https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/)
- APA official examples
- Published academic papers

**Requirements:**
- Must be 100% correct per APA 7th edition
- Include diverse source types (journal, book, webpage, etc.)
- Include edge cases (multiple authors, translations, etc.)

### Invalid Citations

**Error injection strategies:**
1. **Component errors:** Wrong author format, missing DOI, etc.
2. **Format errors:** Spacing, punctuation, capitalization
3. **Common mistakes:** "and" vs "&", title case vs sentence case

**Requirements:**
- Each error must have component, problem, correction
- Components must use standardized names (lowercase)
- Errors should be realistic (common student mistakes)

---

## Split Configuration

**Current split (seed=42):**
- Training: 70% (80 citations)
- Validation: 15% (17 citations)
- Test: 15% (18 citations)

**Defined in:** `run_gepa_final.py:prepare_gepa_dataset()`

**Important:** Random shuffle ensures balanced valid/invalid ratio in each split.

---

## Optimization Algorithm

**MIPROv2 (Multi-prompt Instruction Proposal)**

**Configuration:**
```python
MIPROv2(
    metric=citation_validator_metric,
    auto="light",  # light/medium/heavy
    init_temperature=1.0
)
```

**What it does:**
1. Generates 10 prompt variants
2. Tests each on validation set
3. Selects best performer
4. Iteratively refines prompts
5. Returns optimized validator

**Note:** Using "light" mode for faster iteration. Can use "heavy" for better results with longer runtime.

---

## Next Steps for Improvement

1. **Expand dataset to 200+ citations** (100+ each valid/invalid)
2. **Add more error types** (currently missing: reference list order, hanging indent, etc.)
3. **Balance source types** (more books, webpages, reports)
4. **Experiment with "medium" or "heavy" optimization** for better results
5. **A/B test different metrics** to find optimal balance

---

## Questions?

**Documentation:** This file
**Code location:** `backend/pseo/optimization/`
**Contact:** Check project README
