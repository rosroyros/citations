# MLA 9 Prompt Baseline Analysis

**Test Date:** 2025-12-28  
**Prompt:** `validator_prompt_mla9_v1.txt`  
**Model:** Gemini 3 Flash Preview  
**Test Set:** `mla9_test_set.jsonl` (112 citations, 56 valid / 56 invalid)

---

## Summary Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Overall Accuracy** | **74.1%** | 83/112 correct |
| True Positives | 28 | Valid citations correctly identified |
| True Negatives | 55 | Invalid citations correctly identified |
| False Positives | 1 | Invalid citations marked valid (missed error) |
| False Negatives | 28 | Valid citations marked invalid (phantom errors) |
| Precision | 96.6% | Very few false positives |
| Recall | 50.0% | Only catching half of valid citations |
| F1 Score | 65.9% | Imbalanced performance |

---

## Launch Criteria Evaluation

| Threshold | Range | Result |
|-----------|-------|--------|
| ✅ Ship | ≥80% | Not met |
| ⚠️ **Iterate** | **65-79%** | **74.1% - CURRENT** |
| ❌ Block | <65% | Not applicable |

**Recommendation: ITERATE** - Manual prompt optimization needed before launch.

---

## Key Findings

### Problem: Overly Strict Validation (50% Recall)

The MLA 9 prompt is **too strict** - it's flagging 28 valid citations as invalid (50% of valid citations have phantom errors). This is the primary issue.

#### Common Phantom Error Patterns:

1. **Missing DOI/URL for Database Sources** (10+ cases)
   - Prompt demands DOI/URL for database citations even when not present in original
   - Example: `_JSTOR._` flagged as needing `[MISSING: DOI or URL]`
   - **Issue:** MLA 9 allows database name alone without URL

2. **Over-correction of Punctuation** (5+ cases)
   - Valid comma+underscore patterns flagged incorrectly
   - Example: `_Friends,_` being flagged

3. **Webinar/Non-Standard Format Confusion** (3+ cases)
   - Webinar citations without URLs flagged as missing info
   - Director attribution requirements misapplied

4. **Film Citation Entry Point** (2+ cases)
   - `Capra, Frank, director.` flagged - prompt prefers `Directed by` format
   - Both are valid MLA 9 patterns

### One Missed Error (High Precision is Good)

Only 1 invalid citation was incorrectly marked valid:
- `Dorris, Michael and Louise Erdrich.` - Missing comma before "and"

This shows the prompt IS catching formatting errors well when it identifies them.

---

## Accuracy by Source Type

| Source Type | Accuracy | Correct/Total | Notes |
|-------------|----------|---------------|-------|
| Book | 85.7% | 24/28 | Strong |
| Film | 83.3% | 5/6 | Strong |
| Website | 76.5% | 13/17 | Moderate |
| Book Chapter | 50.0% | 4/8 | **Needs work** |
| Journal Article | 50.0% | 7/14 | **Needs work** |
| Film (streaming) | 50.0% | 2/4 | **Needs work** |

**Weakest Areas:** Journal articles, book chapters, and streaming films.

---

## Sample Failures

### False Negatives (Valid marked Invalid)

| # | Citation | Incorrect Error Found |
|---|----------|----------------------|
| 3 | Kieffer, Alexandra. "The Debussyist Ear..." _JSTOR._ | Missing DOI/URL |
| 7 | Mabillard, Amanda. _Shakespeare Online,_ ... | Missing page title |
| 11 | Boys, Mary C. "Learning in the Presence..." | Unknown |
| 27 | Butler, Judith. _Gender Trouble._ 1990. Routledge, 1999. | Formatting issue |
| 45 | Capra, Frank, director. _It's a Wonderful Life._ | Entry point issue |

### False Positive (Invalid marked Valid)

| # | Citation | Missed Error |
|---|----------|--------------|
| 6 | Dorris, Michael and Louise Erdrich. _The Crown..._ | Missing comma before "and" |

---

## Optimization Recommendations

### Priority 1: Reduce Phantom Errors on Database Sources
- Clarify that database name alone (e.g., `_JSTOR._`) is valid when no DOI/URL is provided
- Remove requirement to add `[MISSING: DOI or URL]` for database-accessed sources

### Priority 2: Accept Multiple Valid Entry Point Formats
- `Capra, Frank, director.` AND `Directed by Frank Capra,` are both valid
- Don't "correct" one to the other

### Priority 3: Relax Missing Information Warnings
- Only flag truly MISSING information, not "preferred but optional" elements
- Webinars without URLs are acceptable if original doesn't have them

### Priority 4: Punctuation Pattern Updates
- Review comma+underscore patterns that are being incorrectly flagged
- `_Title,_` pattern should remain valid

---

## Files Generated

- **Test Script:** `test_mla9_prompt_batched.py`
- **Raw Results:** `mla9_baseline_results.json` (1390 lines, detailed per-citation results)
- **This Analysis:** `mla9_baseline_analysis.md`

---

## Next Steps

1. **Update `validator_prompt_mla9_v1.txt`** with fixes for the issues above
2. **Re-run baseline test** to measure improvement
3. **Target:** ≥80% accuracy for launch approval
4. **Holdout set available:** `mla9_holdout_set.jsonl` (112 citations) for final validation
