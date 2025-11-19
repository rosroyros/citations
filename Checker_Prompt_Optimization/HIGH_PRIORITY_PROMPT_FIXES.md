# High-Priority Prompt Fixes for GPT-5-mini_optimized

## Overview

These 4 fix categories address **10-12 of the 16 false positives** and would bring accuracy from **82.6% → ~92.5%**

---

## Fix 1: Conference Presentations - Flexible DOI/URL Formats

**Problem**: Model rejects valid conference presentations that use:
- Bare DOI format: `doi:10.1037/con2019-1234`
- URLs to conference programs/materials

**Error Cases**:
- Evans et al. conference with `doi:10.1037/con2019-1234` (bare DOI)
- Cacioppo conference with URL to conference program PDF

**APA 7 Rule**: Both formats are acceptable
- DOI preferred when available (can use `doi:` prefix or `https://doi.org/`)
- URL acceptable for conference materials, abstracts, programs

**Prompt Addition**:
```
### Conference Presentations - DOI/URL Flexibility

Conference presentations are VALID with either:

✓ Bare DOI format:
  [Conference presentation]. Conference Name, Location. doi:10.xxxx/xxxxx

✓ URL format (for conference programs, materials, abstracts):
  [Conference presentation]. Conference Name, Location. https://example.org/program.pdf

✓ HTTPS DOI format:
  [Conference presentation]. Conference Name, Location. https://doi.org/10.xxxx/xxxxx

All three formats are acceptable per APA 7.
```

**Fixes**: 2 errors

---

## Fix 2: "Article" Format - Reinforce Correctness

**Problem**: Model incorrectly flags `Article eXXXXXX` format as invalid

**Error Cases**:
- `_PLoS ONE_, _13_(3), Article e0193972.` (with period after journal name)
- `PLoS ONE, 13(3), Article e0193972.` (without period)

**APA 7 Rule**: "Article XXXXXX" is the CORRECT and PREFERRED format for article numbers (instead of page numbers)

**Prompt Addition**:
```
### Article Numbers (Not Page Numbers)

When a journal uses article numbers instead of page numbers:

✓ CORRECT: Article e0193972
✓ CORRECT: Article 104678
✓ CORRECT: Article XXXX (any alphanumeric format)

This is the PREFERRED APA 7 format. Do NOT flag "Article XXXX" as an error.

Examples:
- Smith, J. (2020). Title. _Journal_, _15_(3), Article e12345. https://doi.org/...
- Jones, A. (2019). Title. _PLoS ONE_, _13_(2), Article 0193972. https://doi.org/...
```

**Fixes**: 2 errors

---

## Fix 3: Classical/Ancient Works - Date Ranges and Optional Original Dates

**Problem**: Model inconsistently handles ancient works:
- Rejects date ranges like "385-378 BCE"
- Requires original publication dates

**Error Cases**:
- Plato without original publication date
- Plato with date range "(Original work published 385-378 BCE)"

**APA 7 Rule**:
- Date ranges are acceptable for classical works
- Original publication date is recommended but NOT required

**Prompt Addition**:
```
### Classical/Ancient Works - Special Cases

For ancient or classical works (Plato, Aristotle, religious texts, etc.):

✓ Date ranges are ACCEPTABLE:
  (Original work published 385-378 BCE)
  (Original work published ca. 385 BCE)

✓ Original publication date is RECOMMENDED but OPTIONAL:
  - WITH: Plato. (1989). Symposium (A. Nehamas, Trans.). Publisher. (Original work published ca. 385 BCE)
  - WITHOUT: Plato. (1989). Symposium (A. Nehamas, Trans.). Publisher.

Both formats are valid. Do not require original publication date for ancient works.

✓ Approximate dates acceptable:
  - "ca. 385 BCE"
  - "385-378 BCE"
  - "4th century BCE"
```

**Fixes**: 2 errors

---

## Fix 4: DOI Format Flexibility

**Problem**: Model too strict on DOI patterns, rejects valid DOI formats

**Error Cases**:
- `doi:10.1037/con2019-1234` (bare format)
- `https://doi.org/10.1234/abcd.5678` (alphanumeric)
- `https://doi.org/10.1234/5678` (simple numeric)

**APA 7 Rule**: DOI format varies widely; if it follows the structure, it's valid

**Prompt Addition**:
```
### DOI Format Validation

DOIs come in MANY valid formats. Accept any DOI that follows these patterns:

✓ Bare format: doi:10.xxxx/xxxxx
✓ HTTPS format: https://doi.org/10.xxxx/xxxxx
✓ HTTP format: http://doi.org/10.xxxx/xxxxx (auto-upgraded to HTTPS)

The suffix (after the slash) can be:
- Purely numeric: 10.1234/5678 ✓
- Alphanumeric: 10.1234/abcd.5678 ✓
- With hyphens: 10.1073/pnas.1910510116 ✓
- Complex: 10.1176/appi.books.9780890420249.dsm-iv-tr ✓

DO NOT validate or restrict DOI suffix patterns. If it follows doi:XX.XXXX/... structure, accept it.

Examples:
- doi:10.1037/con2019-1234 ✓
- https://doi.org/10.1234/5678 ✓
- https://doi.org/10.1371/journal.pone.0193972 ✓
```

**Fixes**: 3 errors

---

## Summary of High-Priority Changes

| Fix | Pattern | Cases Fixed | Accuracy Gain |
|-----|---------|-------------|---------------|
| 1 | Conference DOI/URL formats | 2 | +1.7% |
| 2 | "Article XXXX" format | 2 | +1.7% |
| 3 | Classical works flexibility | 2 | +1.7% |
| 4 | DOI format variations | 3 | +2.5% |
| **TOTAL** | | **9-10** | **+7.4-8.3%** |

**Expected Result**: 82.6% + 8% = **~90.5% accuracy**

(Note: Some overlap possible, so conservative estimate is 90-92% accuracy with just these 4 fixes)

---

## Implementation Strategy

### 1. Add to Existing Prompt
Integrate these 4 sections into the current GPT-5-mini_optimized prompt without removing existing rules.

### 2. Location in Prompt
Add after general APA 7 rules, before specific source type sections:
```
[General APA 7 Rules]
[NEW: Special Cases & Flexibility Rules] ← INSERT HIGH-PRIORITY FIXES HERE
[Specific Source Types: Journal, Book, Web, etc.]
```

### 3. Test on HELD-OUT Set
**CRITICAL**: Do NOT test on the 121-citation validation set used for this analysis.

Options for avoiding overfitting:
- **Option A**: Split the 121 citations: 80 for analysis, 41 for testing
- **Option B**: Use a completely separate test set from the larger dataset
- **Option C**: Create new synthetic test cases covering these patterns

### 4. Validation Approach

```python
# Test on held-out set
held_out_citations = load_held_out_set()  # NOT the 121 used for analysis

results = test_prompt_with_fixes(
    citations=held_out_citations,
    prompt_version="gpt5_mini_optimized_v2_high_priority_fixes"
)

if results['accuracy'] >= 90:
    print("✓ High-priority fixes successful")
    if results['accuracy'] < 95:
        print("→ Proceed to medium-priority fixes")
else:
    print("✗ Fixes may be overfitted or insufficient")
    print("→ Review prompt changes, test on different set")
```

---

## Next Steps After Implementation

1. **Test on held-out set** (NOT the 121 citations)
2. **If accuracy < 90%**: Review prompt integration, may have conflicts with existing rules
3. **If accuracy 90-94%**: Add medium-priority fixes
4. **If accuracy ≥ 95%**: Deploy to production
5. **Monitor**: Track production errors to catch new patterns

---

## Files Referenced

- Full pattern analysis: `MANUAL_ERROR_PATTERN_ANALYSIS.md`
- Error cases: `ERROR_CASES_FOR_REVIEW.txt`
- Current prompt: [Location of GPT-5-mini_optimized prompt]
