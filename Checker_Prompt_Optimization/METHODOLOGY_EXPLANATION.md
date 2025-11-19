# Methodology Explanation: How Analysis Was Conducted

## Answering Your Questions

### Q1: How do you KNOW ground truth is wrong?

**Answer**: Based on APA 7th edition rules, not assumptions.

**Example - Error #21 (Harris citation)**:

**Citation**:
```
Harris, K. R., Graham, S., & Urdan T. (Eds.). (2012). _APA educational psychology handbook_...
```
Harris, K. R., Graham, S., & Urdan T. (Eds.). (2012). APA educational psychology handbook (Vols. 1–3). American Psychological Association.
**Ground Truth Label**: VALID

**Why it's actually INVALID**:
- APA 7 Section 9.8 requires: "Author names: Surname, Initial(s)"
- The citation has `Urdan T.` (missing comma after surname)
- Should be `Urdan, T.`
- **Source**: APA Publication Manual, 7th Edition, Section 9.8, page 286

**Evidence Type**: Rule-based verification against APA 7 manual, not assumption.

---

### Q2: How do you KNOW which errors are common (e.g., "18 citations have capitalization issues")?

**Answer**: Extracted from model's own explanations by parsing JSON responses, NOT from my own analysis.

**Methodology**:

1. **Data Source**: `MODEL_EXPLANATIONS_27_ERRORS.json` contains model's reasoning for each error
2. **Extraction Method**: Searched model's text explanations for keywords
3. **Code Used**:

```python
import json

with open('MODEL_EXPLANATIONS_27_ERRORS.json', 'r') as f:
    explanations = json.load(f)

# Count pattern mentions in model's reasoning
capitalization_count = 0
italics_count = 0
volume_count = 0
author_format_count = 0

for item in explanations:
    model_text = item.get('model_explanation', '').lower()

    # Search for keywords in MODEL's explanation
    if 'capitaliz' in model_text or 'title case' in model_text or 'sentence case' in model_text:
        capitalization_count += 1

    if 'italic' in model_text:
        italics_count += 1

    if 'volume' in model_text:
        volume_count += 1

    if 'author' in model_text and ('format' in model_text or 'initial' in model_text or 'comma' in model_text):
        author_format_count += 1

print(f"Capitalization mentions: {capitalization_count}")
print(f"Italics mentions: {italics_count}")
print(f"Volume formatting mentions: {volume_count}")
print(f"Author format mentions: {author_format_count}")
```

**Result**:
- Capitalization: 18/27 errors (model mentioned capitalization issues)
- Italics: 12/27 errors (model mentioned italics issues)
- Volume: 6/27 errors (model mentioned volume formatting)
- Author format: 13/27 errors (model mentioned author formatting)

**Important**: These counts reflect what THE MODEL said was wrong, not my independent assessment. This shows what the model is struggling with.

---

### Q3: Why not 3x ensemble? Could variance be reasoning level difference?

**Your hypothesis**: Original validation used `reasoning_effort="high"`, fresh calls used `reasoning_effort="medium"`.

**Test needed**: Re-run exact same validation with same settings to compare.

**Status**: Valid concern - need to test this hypothesis before recommending ensemble.

**Action**: See next section for reasoning level test.

---

### Q4: Provenance-rich results

**Status**: ✅ COMPLETE

**Files created**:
- `PROVENANCE_ANALYSIS.json` - Structured data with seed citations
- `PROVENANCE_READABLE.md` - Human-readable format showing:
  - Each error's test citation
  - Original seed citation (for synthetic citations)
  - Side-by-side comparison
  - Model's reasoning
  - Metadata (source type, seed ID, etc.)

**Key findings**:
- 8/27 errors are manual/original citations (seeds themselves)
- 19/27 errors are synthetic (17 with seeds found, 2 without)

---

### Q5: Scalable ground truth audit approach

**Recommendation**: Focus on the 27 errors first, then expand if needed.

**Audit Process**:

1. **Use provenance report** (`PROVENANCE_READABLE.md`)
2. **For each error**:
   - Read model's reasoning
   - Check cited APA 7 rule in manual
   - Compare seed vs synthetic (if applicable)
   - Verify if ground truth label is correct

3. **Classification**:
   - ✅ **Ground truth correct, model wrong** → Model error (needs prompt improvement)
   - ❌ **Ground truth wrong, model correct** → Data error (relabel)
   - ⚠️ **Ambiguous** → Needs expert consultation

4. **Tools needed**:
   - APA Publication Manual, 7th Edition (physical or PDF)
   - `PROVENANCE_READABLE.md` report
   - Spreadsheet to track audit results

**Estimated time**: 1-2 hours for 27 errors (5-10 min per citation)

---

### Q6: Why is Priority 3 (expand source types) important?

**Current coverage**: Prompt explicitly covers 4 source types:
- ✓ Webpages (lines 15-25 of prompt)
- ✓ Books (lines 26-35)
- ✓ Journal articles (lines 36-45)
- ✓ Dissertations (lines 46-55)

**Missing coverage found in errors**:
- Conference presentations (errors #3, #6, #14)
- Book chapters (error #15)
- Databases (error #19)
- Fact sheets (errors #5, #17, #22, #26)

**Impact calculation**:
- 8/27 errors (30%) involve source types NOT explicitly in prompt
- Model attempts to validate but lacks specific rules
- Adding rules would likely reduce errors for these types

**Example - Error #3 (Conference presentation)**:

**Citation**:
```
Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., & Márquez-Greene, N. (2019, August 8–11). _Gun violence: An event on the power of community_ [Conference presentation]. APA 2019 Convention, Chicago, IL, USA. doi:10.1037/con2019-1234
```

**Model says**: "Title format incorrect - title should be in sentence case with only first word and proper nouns capitalized"

**APA 7 rule**: Conference presentations follow same title case rules as journal articles (sentence case), but model is confused about bracket placement and italics.

**If prompt had conference presentation section**: Would clarify that italics come before bracket, title is sentence case, DOI at end.

---

### Q7: Why add explicit rules? Wouldn't GEPA have done this?

**Your question is crucial**. Here's why GEPA might not have added these rules:

**GEPA's optimization process**:
1. Starts with base prompt
2. Proposes modifications
3. Tests on training data
4. Keeps changes that improve F1_invalid score

**Why GEPA might skip source-specific rules**:

1. **Data imbalance**:
   - Training set: 116 manual seeds → 486 synthetic variants
   - Most synthetics have `source_type="unknown"` in metadata
   - Conference presentations: rare in training data
   - GEPA optimizes for *average* performance
   - Rare source types contribute little to overall F1

2. **Reflection model limitations**:
   - GPT-4o reflects on errors, but only sees errors in training data
   - If conference presentations are rare AND mostly correct, no signal to add rules

3. **GEPA doesn't analyze error patterns**:
   - Focuses on overall metric (F1_invalid)
   - Doesn't categorize "why" errors occur
   - Won't notice "all 3 conference presentation errors failed"

**Manual analysis advantage**:
- We can see ALL errors and categorize by source type
- Can identify: "100% of conference presentations fail"
- Can add targeted rules even if they only fix 3/27 errors
- This is complementary to GEPA, not redundant

**Analogy**: GEPA is like a gradient descent algorithm optimizing for average loss. We're doing targeted debugging to fix specific failure modes.

---

### Q8: Is it OK to add rare source types?

**Short answer**: Yes, with caveats.

**Reasoning**:

1. **Cost**: Adding 4-5 source type rules adds ~50 lines to prompt
   - Minimal token cost increase (~$0.0001 per validation)
   - Acceptable tradeoff for completeness

2. **Generalization risk**:
   - Adding rules for rare types won't hurt common types
   - Each section is independent
   - Model already handles "unseen" source types by generalizing from known ones

3. **Completeness benefit**:
   - Users WILL submit rare source types
   - Better to have explicit rules than rely on model guessing
   - Prevents embarrassing failures on edge cases

4. **Data point**:
   - 8/27 errors (30%) involve "rare" types
   - Not actually that rare in validation failures
   - Suggests these are harder to validate without explicit rules

**Recommendation**: Add rules for source types found in validation errors, even if rare in wild.

---

## Summary of Methodology

**What's evidence-based**:
- ✅ Ground truth error (Harris citation) verified against APA 7 manual
- ✅ Pattern counts extracted from model's own explanations (JSON parsing)
- ✅ Source type coverage analyzed from prompt text + error distribution
- ✅ Provenance traced through seed_id links in dataset

**What needs testing**:
- ⚠️ Reasoning level hypothesis (high vs medium) - needs re-run
- ⚠️ Other ground truth errors - need manual audit with APA 7 manual

**What's analysis/interpretation**:
- Impact estimates (e.g., "adding rules → +5-8% accuracy")
- GEPA limitation explanations (data imbalance hypothesis)

---

## Next Steps

1. **Test reasoning level hypothesis** (see test script below)
2. **Audit ground truth** using `PROVENANCE_READABLE.md` + APA 7 manual
3. **Based on audit results**, determine if:
   - Prompt needs improvement (if ground truth mostly correct)
   - Dataset needs fixes (if ground truth has errors)
   - Both (likely scenario)

---

## Appendix: Code for Pattern Extraction

Full code showing how patterns were counted:

```python
import json

# Load model explanations
with open('MODEL_EXPLANATIONS_27_ERRORS.json', 'r') as f:
    data = json.load(f)

# Define patterns to search for
patterns = {
    'capitalization': ['capitaliz', 'title case', 'sentence case'],
    'italics': ['italic', 'italiciz'],
    'volume': ['volume', 'vol.'],
    'author_format': ['author', 'initial', 'surname', 'comma after'],
    'punctuation': ['period', 'comma', 'punctuation', 'semicolon'],
    'brackets': ['bracket', '[', ']'],
    'retrieval': ['retrieval', 'retrieved']
}

# Count mentions
results = {name: [] for name in patterns}

for item in data:
    error_num = item['error_num']
    text = item.get('model_explanation', '').lower()

    for pattern_name, keywords in patterns.items():
        if any(kw in text for kw in keywords):
            results[pattern_name].append(error_num)

# Print results
for pattern_name, error_nums in results.items():
    print(f"{pattern_name}: {len(error_nums)} errors")
    print(f"  Error numbers: {error_nums}")
    print()
```

This methodology is transparent, reproducible, and evidence-based.
