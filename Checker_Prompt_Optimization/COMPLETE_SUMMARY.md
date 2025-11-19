# Complete Analysis Summary: citations-3xo

## Task Objective
Analyze 21 remaining errors from GPT-5-mini_optimized to identify prompt improvements needed to reach 95% accuracy.

---

## Results Summary

### Error Breakdown
- **Total errors**: 21 / 121 citations
- **False Positives (too strict)**: 16 (76%)
- **False Negatives (too lenient)**: 5 (24%)
- **Current accuracy**: 82.64%
- **Gap to 95% goal**: 12.36 percentage points

**Primary Issue**: Model incorrectly flags VALID citations as invalid

---

## Top Error Patterns Identified

### False Positive Patterns (Model Too Strict)

1. **Conference presentations with flexible DOI/URL formats** (2 cases)
   - Rejects bare DOI: `doi:10.1037/con2019-1234`
   - Rejects URLs to conference programs

2. **"Article XXXX" format** (2 cases)
   - Flags correct "Article e0193972" format as invalid
   - This IS the correct APA 7 format (section 9.25)

3. **Classical/ancient works** (2 cases)
   - Rejects date ranges: "385-378 BCE"
   - Inconsistent on original publication dates

4. **DOI format variations** (3 cases)
   - Too strict on DOI suffix patterns
   - Rejects valid numeric/alphanumeric DOIs

5. **Series with volume numbers** (1 case)
6. **Retrieval dates for dynamic content** (1 case)
7. **Complex government publications** (2 cases)
8. **Various edge cases** (3 cases)

### False Negative Patterns (Model Too Lenient)

1. **Dissertation publication number location** (1 case)
   - Wrong: `(Pub. No. X) [Dissertation, Univ]`
   - Correct: `[Dissertation, Univ]. (Publication No. X)`

2. **Conference location formatting** (1 case)
   - Wrong: `Pasadena, CA`
   - Correct: `Pasadena, California, United States`

3. **Punctuation before URLs** (1 case)
4. **Journal volume formatting** (1 case)
5. **URL accuracy** (1 case)

---

## Proposed High-Priority Fixes

### Fix 1: Conference Presentations - Flexible Formats
Accept both bare DOI (`doi:10.xxxx`) and URLs to conference materials.
**Fixes**: 2 errors (+1.7% accuracy)

### Fix 2: Reinforce "Article XXXX" Format
Explicitly state this is CORRECT APA 7 format.
**Fixes**: 2 errors (+1.7% accuracy)

### Fix 3: Classical Works - Date Flexibility
Allow date ranges and make original publication date optional.
**Fixes**: 2 errors (+1.7% accuracy)

### Fix 4: DOI Format Flexibility
Accept any DOI following `doi:XX.XXXX/...` or `https://doi.org/XX.XXXX/...`
**Fixes**: 3 errors (+2.5% accuracy)

**Expected Impact**: 82.6% → **~90-92% accuracy**

---

## CRITICAL BLOCKERS

### Blocker 1: APA 7 Compliance Verification REQUIRED

**Problem**: We cannot implement fixes without verifying they're APA 7 compliant.

**Critical Questions**:
1. Is bare `doi:10.xxxx` format valid, or must use `https://doi.org/`?
2. Are date ranges like "385-378 BCE" acceptable for classical works?
3. What exact format is required for article numbers?
4. Are our ground truth labels even correct?

**Action Required**:
- Manually verify against APA 7 Publication Manual:
  - Section 9.25 (Article Numbers) - p. 295-296
  - Section 9.34 (DOIs and URLs) - p. 299-301
  - Section 9.42 (Classical Works) - p. 320
  - Section 10.5 (Conference Presentations)

**Risk**: If ground truth is wrong, fixes could make model WORSE

**See**: `PROMPT_FIXES_WITH_APA7_VERIFICATION.md` for detailed verification checklist

---

### Blocker 2: No Holdout Data - Overfitting Risk

**Problem**: All curated citations were used in train/test. We have NO independent validation set.

**Why This Matters**:
- Analyzed 21 errors from 121-citation test set
- Making prompt changes based on these 21 citations
- Testing on same 121 citations = guaranteed overfitting
- Cannot use traditional train/test split

**The Risk**:
- Achieve 100% on 121 citations
- Perform poorly on new citations in production
- Model memorizes examples instead of learning rules

**The Solution**: Generate synthetic test citations

**Approach**:
1. For each error pattern, generate 10 NEW synthetic citations
2. Different authors, titles, dates - SAME APA 7 pattern
3. Tests rule understanding, not memorization
4. Creates 200+ truly independent test cases

**Example**:

Original error case:
```
Evans, A. C., Jr., [...]. (2019, August 8–11). Gun violence [...]
[Conference presentation]. APA 2019 Convention, Chicago, IL, USA.
doi:10.1037/con2019-1234
```

Synthetic variations (completely new):
```
Thompson, R., & Martinez, L. (2022, May 12–15). Neural mechanisms [...]
[Conference presentation]. Cognitive Science Society Annual Meeting,
Toronto, Ontario, Canada. doi:10.1234/css2022-789
```

**Validation Metrics**:
- Before fixes: Should fail on synthetic citations (same patterns as original)
- After fixes: Should pass ≥90% on synthetic citations for fixed patterns
- No regression: Should maintain ≥82% on unfixed patterns

**See**: `OVERFITTING_SOLUTION_NO_HOLDOUT.md` for complete strategy and code

---

## Recommended Implementation Plan

### Phase 1: APA 7 Verification (2-3 days) - URGENT
1. Manually check APA 7 manual for each error pattern
2. Verify ground truth labels are correct
3. Document which fixes are APA 7 compliant
4. Correct any ground truth errors found

**Deliverable**: Verified error list with APA 7 manual citations

---

### Phase 2: Generate Synthetic Test Set (3-5 days)
1. For each verified error pattern, generate 10 synthetic citations
2. Use GPT-4/Claude with provided code template
3. Manually review synthetic citations for quality
4. Label each as valid/invalid per APA 7

**Deliverable**: 200+ synthetic test citations

---

### Phase 3: Baseline Testing (1 day)
1. Test current prompt on synthetic set
2. Verify same error patterns appear
3. Measure baseline accuracy on synthetic set

**Success Criteria**: Should see similar error patterns on synthetic as on original 121

---

### Phase 4: Apply & Test Fixes (2-3 days)
1. Implement ONLY APA 7-verified fixes
2. Test on synthetic set (NOT original 121)
3. Measure improvement

**Success Criteria**:
- ≥90% on synthetic citations for patterns we fixed
- No regression on patterns we didn't fix
- Ready for production if ≥95% overall

---

## Files Generated

### Critical Files (Read First)
1. **PROMPT_FIXES_WITH_APA7_VERIFICATION.md** (9.2K)
   - Each error case with proposed fix
   - Specific APA 7 manual sections to verify
   - Confidence levels per fix
   - **READ BEFORE ANY IMPLEMENTATION**

2. **OVERFITTING_SOLUTION_NO_HOLDOUT.md** (11K)
   - Complete synthetic citation generation strategy
   - Code to generate variations
   - Validation metrics
   - Alternative approaches (unit tests, expert review)

### High-Priority Implementation Guides
3. **HIGH_PRIORITY_PROMPT_FIXES.md** (6.7K)
   - 4 fixes to address 9-10 errors
   - Exact prompt text ready to integrate
   - Expected +8-10% accuracy gain
   - **USE ONLY AFTER APA 7 VERIFICATION**

4. **MANUAL_ERROR_PATTERN_ANALYSIS.md** (11K)
   - Detailed analysis of all 21 error patterns
   - APA 7 rules for each
   - Prioritized fixes with examples

### Supporting Files
5. **ERROR_CASES_FOR_REVIEW.txt** (5.6K)
   - All 21 citations listed for review
   - Separated into FP and FN sections

6. **ERROR_ANALYSIS.md** (6.0K)
   - Summary statistics and breakdown

7. **error_analysis_detailed.json** (439B)
   - Structured data for programmatic access

8. **TESTING_STRATEGY_AVOID_OVERFITTING.md** (7.9K)
   - Original strategy (before realizing no holdout exists)
   - Still useful for general testing principles

---

## Critical Warnings

### ⚠️ DO NOT Implement Fixes Until:
1. ✅ APA 7 compliance verified for each fix
2. ✅ Synthetic test set created (200+ citations)
3. ✅ Baseline testing completed on synthetic set
4. ✅ Validation strategy confirmed

### ⚠️ Risk of Premature Implementation:
- Making model worse if ground truth is wrong
- Overfitting to specific 121 citations
- Production failures on new citations
- Wasted effort if fixes aren't APA 7 compliant

---

## Estimated Impact (After Verification)

### High Priority Fixes Only
- Errors fixed: 9-10 / 21
- Accuracy improvement: +8-10%
- Target accuracy: ~90-92%

### High + Medium Priority Fixes
- Errors fixed: All 21
- Accuracy improvement: +17%
- Target accuracy: ~100% (on test set)
- **But must validate on synthetic to confirm not overfit**

### Realistic Production Target
With synthetic validation: **95%+ accuracy achievable**

---

## Next Actions

### Immediate (This Week)
1. **APA 7 verification session** - Review all error patterns against manual
2. **Correct ground truth** - Fix any mislabeled citations
3. **Generate synthetic test set** - Start with 50 citations for top patterns

### Short Term (Next 2 Weeks)
4. **Baseline test** - Run current prompt on synthetic set
5. **Implement verified fixes** - Only APA 7-compliant changes
6. **Validation test** - Measure on synthetic set
7. **Iterate** - If not at 95%, analyze new errors and repeat

### Success Criteria
- Phase 1 complete: All fixes APA 7 verified
- Phase 2 complete: 200+ synthetic citations ready
- Phase 3 complete: ≥90% on synthetic patterns we fixed
- Phase 4 complete: ≥95% overall accuracy, ready for production

---

## Questions for Discussion

1. **APA 7 Access**: Do we have the official APA 7 Publication Manual (7th ed.)?
2. **Expert Review**: Can we get an APA 7 expert to review our ground truth?
3. **Synthetic Generation**: Should we use GPT-4, Claude, or manual creation?
4. **Timeline**: What's the target date for reaching 95% accuracy?
5. **Production Deployment**: What's the rollout plan once we hit 95%?

---

## Related Tasks

- **citations-715**: Run 3 consistency test cycles on GPT-5-mini_optimized
- **citations-8l4**: Determine next steps to reach 95% accuracy

Both tasks should wait until:
- APA 7 verification complete
- Synthetic test set created
- Overfitting risk mitigated
