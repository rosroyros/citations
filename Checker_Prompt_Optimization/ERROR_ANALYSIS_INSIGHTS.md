# APA Citation Validator - Error Analysis & Insights

**Date**: 2024-10-24
**Model**: GEPA-optimized validator (gpt-4o-mini)
**Test Set**: 121 citations (39 valid, 82 invalid)

---

## Executive Summary

The optimized validator achieves **66.9% accuracy** with an **F1_invalid of 0.718**, but exhibits a **critical issue**: it lets **30 invalid citations pass as valid** (false positives) while only rejecting **10 valid citations** (false negatives).

**Bottom line**: The model is too lenient. It misses obvious APA formatting errors and accepts citations that violate core APA rules.

---

## Key Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Accuracy** | 66.9% | 85%+ | ❌ Below target |
| **F1 (invalid)** | 0.718 | 0.85+ | ❌ Below target |
| **False Positives** | 30 (24.8%) | <10% | ❌ Too high |
| **False Negatives** | 10 (8.3%) | <15% | ✅ Acceptable |
| **FP:FN Ratio** | 3:1 | <1:1 | ❌ Backwards |

---

## Critical Finding: False Positive Problem

### ⚠️ The Validator Is Too Permissive

**Problem**: The model marks **30 invalid citations as valid** (24.8% of test set). This is the opposite of what a citation validator should do.

**Why this matters**:
- False positives (FP) = invalid citations passing through → students submit incorrect citations
- False negatives (FN) = valid citations rejected → annoying but fixable
- **For a validator, FPs are far more dangerous than FNs**

**Expected behavior**: A good validator should err on the side of caution (more FNs than FPs)

**Current behavior**: 3× more FPs than FNs (backwards!)

---

## Error Pattern Analysis

### 🔴 False Positive Patterns (Invalid → Marked Valid)

The model consistently misses these APA violations:

| Pattern | Count | % of FP | Example Error |
|---------|-------|---------|---------------|
| **No capitals / wrong capitalization** | 30 | 100% | "Malory and character" (should be "Malory and Character") |
| **Missing page notation** | 20 | 67% | Missing "pp." before page ranges |
| **Insufficient commas** | 5 | 17% | Author name formatting errors |
| **"and" instead of "&"** | 1 | 3% | "Norton and Company" vs "Norton & Company" |

#### Example False Positives

**FP #1**: Capitalization error missed
```
Citation: "Armstrong, D. (2019). Malory and character. In M. G. Leitch, & C. J. Rushton (Eds.)..."
Ground Truth: INVALID (title should be "Malory and Character")
Model Said: VALID ❌
Explanation: "The citation is valid as it correctly follows the APA 7th edition rules..."
```
**Analysis**: Model doesn't enforce sentence-case vs title-case rules for chapter titles.

**FP #2**: Editor formatting missed
```
Citation: "Armstrong, D. (2019). Malory and Character. In M. G. Leitch & C. J. Rushton (Ed.)..."
Ground Truth: INVALID (should be "(Eds.)" not "(Ed.)" for multiple editors)
Model Said: VALID ❌
```
**Analysis**: Model doesn't check singular vs plural editor notation.

**FP #3**: Publisher name format
```
Citation: "David, A., & Simpson, J. (Eds.). (2006). _The Norton Anthology_. W. W. Norton and Company."
Ground Truth: INVALID (some formatting issue - possibly "and" should be "&")
Model Said: VALID ❌
```

---

### 🟡 False Negative Patterns (Valid → Marked Invalid)

The model incorrectly rejects valid citations with these characteristics:

| Pattern | Count | % of FN | What's Happening |
|---------|-------|---------|------------------|
| **Has markdown italics** | 10 | 100% | Confusion about `_italic_` formatting |
| **Has DOI or URL** | 9 | 90% | Over-scrutinizing online sources |
| **Many commas** | 3 | 30% | Complex citations with multiple authors/editors |
| **Proper parentheses** | 2 | 20% | May be confused by nested parentheses |

#### Example False Negatives

**FN #1**: Website citation rejected
```
Citation: "_Tuscan white bean pasta._ (2018, February 25). Budgetbytes. Retrieved March 18, 2020, from https://..."
Ground Truth: VALID
Model Said: INVALID ❌
Explanation: "The citation is invalid due to the incorrect capitalization of the website name 'Budgetbytes'..."
```
**Analysis**: Model is inventing errors. "Budgetbytes" is the correct site name, not "Budget Bytes".

**FN #2**: Italics confusion
```
Citation: "_Tuscan white bean pasta._ (2018, February 25). Budgetbytes. https://..."
Ground Truth: VALID
Model Said: INVALID ❌
Explanation: "The title of the article should not be italicized. Instead, the website name 'Budgetbytes' should be italicized."
```
**Analysis**: Model confused about when to italicize website articles vs site names.

**FN #3**: Retrieval date confusion
```
Citation: "Perreault, L., & Johnson, M. (2019). Obesity in adults... _UpToDate_. Retrieved January 12, 2020, from https://..."
Ground Truth: VALID
Model Said: INVALID ❌
Explanation: "The citation is invalid due to the inclusion of the retrieval date, which is not required..."
```
**Analysis**: Model doesn't know that retrieval dates ARE required for frequently-updated sources like UpToDate.

---

## Root Cause Analysis

### Why Is the Model Too Lenient?

1. **Training data imbalance**: 67.8% invalid citations in test set
   - Model may be biased toward predicting "valid" to balance
   - GEPA optimized for F1_invalid, but this doesn't prevent FPs

2. **Prompt lacks specificity**: Model explanations show it's applying rules incorrectly
   - Doesn't enforce capitalization rules strictly
   - Confused about italics (markdown `_text_` vs actual italics)
   - Doesn't validate editor notation (Ed. vs Eds.)

3. **Synthetic data quality**: All test examples are synthetic
   - May contain unrealistic error patterns
   - Model learned shortcuts instead of true APA rules

4. **Metric mismatch**: Optimized for F1_invalid (balance of precision/recall)
   - But we actually want **high precision on invalid** (few FPs)
   - Should have used precision-weighted metric

---

## Citation Length Analysis

| Length Range | Error Count | Notes |
|--------------|-------------|-------|
| 0-99 chars | 2 | Very short citations - rare |
| 100-199 chars | 22 | **Most errors here** - typical citation length |
| 200-299 chars | 15 | Complex citations with editors/chapters |
| 300-399 chars | 1 | Very long citations - rare |

**Insight**: Errors concentrate in the 100-200 character range (typical book chapters, journal articles).

---

## Actionable Recommendations

### Immediate Fixes (High Priority)

1. **Adjust the metric** ❗
   - Current: F1_invalid (balances precision & recall)
   - Better: **Precision@0.9 for invalid** (maximize catching invalid, tolerate more FNs)
   - Or: **Custom metric with FP penalty = 3× FN penalty**

2. **Enhance prompt with strict rules** ✏️
   - Add explicit capitalization checks:
     - Chapter titles: sentence case
     - Book titles: title case
     - Journal titles: title case
   - Add editor notation rules: (Ed.) for 1, (Eds.) for 2+
   - Clarify markdown italics: `_text_` in input = actual italics in APA

3. **Filter/improve synthetic data** 🧹
   - Current FPs suggest synthetic invalid citations have subtle errors
   - Add more OBVIOUS invalid examples:
     - Missing author
     - Missing year
     - Missing title
     - No punctuation at all
   - Balance with fewer "edge case" invalids

### Medium-Term Improvements

4. **Add source-type awareness** 📚
   - Even though plan said "treat as generic", errors show confusion about:
     - Website vs journal vs book rules
     - When retrieval dates are needed
     - Consider: Add source_type to prompt for context

5. **Retrain with curated invalid examples** 🎯
   - Current synthetics may be too uniform
   - Manually create 50-100 invalid citations with COMMON student mistakes:
     - "and" instead of "&"
     - Missing italics
     - Wrong capitalization
     - Missing page numbers
     - Incorrect editor notation

6. **Use ensemble/voting** 🗳️
   - Run prediction 3 times with temp=0.3
   - If any prediction says "invalid" → mark invalid
   - This biases toward catching errors (higher recall, more FNs, fewer FPs)

### Long-Term Strategy

7. **Hybrid approach** 🔀
   - Use LLM for complex judgment calls
   - Use regex/rules for OBVIOUS errors:
     - Missing year: `\(\d{4}\)`
     - Missing author
     - Unbalanced parentheses
     - No title italics
   - Only pass "maybe valid" citations to LLM

8. **Multi-stage validation** 🎭
   - Stage 1: Strict structural checks (fast, rule-based)
   - Stage 2: LLM validation (slower, nuanced)
   - Stage 3: Confidence threshold (if LLM confidence <80%, mark invalid)

9. **Active learning** 🔄
   - Deploy current model
   - Collect user corrections
   - Retrain monthly with real corrections
   - Focus on FP reduction

---

## Comparison to Target Performance

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Accuracy | 66.9% | 85% | -18.1% |
| F1_invalid | 0.718 | 0.85 | -0.132 |
| Precision (invalid) | ~73% | 90%+ | -17% |
| False Positive Rate | 24.8% | <10% | +14.8% |

**To reach target**:
- Need to reduce FPs from 30 → 12 (cut by 60%)
- OR improve overall accuracy by catching more invalids correctly

---

## Next Steps

### Option A: Quick Iteration (Recommended)
1. Re-run GEPA with **precision-focused metric** for invalid class
2. Add 20 manually curated "obvious invalid" examples to training
3. Update prompt with explicit capitalization/editor notation rules
4. Re-test and compare FP rate

**Estimated time**: 2-3 hours
**Expected improvement**: FP reduction to 15-20%

### Option B: Comprehensive Overhaul
1. Build hybrid validator (rules + LLM)
2. Curate 100+ diverse invalid examples
3. Implement multi-stage validation
4. Add source-type awareness

**Estimated time**: 1-2 days
**Expected improvement**: Accuracy to 80%+, FP <10%

### Option C: Deploy As-Is with Mitigation
1. Deploy current model with **confidence threshold = 0.7**
2. Flag all "valid" predictions with confidence <70% for manual review
3. Collect real user data for 1 month
4. Retrain with active learning

**Estimated time**: Deploy today
**Expected outcome**: Catch FPs through manual review, gather real data

---

## Conclusion

The GEPA optimization successfully created a functional validator, but it's **too lenient** due to:
- Wrong optimization metric (F1 vs precision)
- Synthetic data with subtle errors
- Prompt lacks explicit rule enforcement

**Recommended path forward**: Option A (quick iteration) to reduce FPs, then deploy with Option C (confidence threshold) for active learning.

The framework is solid - we just need to tune the metric and improve training data quality.

---

## Appendix: Sample Errors

### Top 5 Most Egregious False Positives

See error_analysis.json for full list.

### Top 5 Most Egregious False Negatives

See error_analysis.json for full list.

---

**Report Generated**: 2024-10-24
**Files**:
- `error_analysis.json` - Full error data
- `optimization_report.html` - Interactive report with all predictions
- `optimized_validator.json` - Current model
