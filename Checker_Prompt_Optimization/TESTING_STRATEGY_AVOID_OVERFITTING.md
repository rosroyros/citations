# Testing Strategy: Avoiding Overfitting

## The Overfitting Problem

**Risk**: We analyzed 21 specific errors from the 121-citation test set. If we:
1. Make prompt changes based on these 21 citations
2. Test on the SAME 121 citations

We may achieve 100% on this set but perform poorly on new citations (overfitting).

---

## Strategy: Held-Out Test Sets

### Option 1: Split Current Test Set (QUICK - Recommended First)

**Approach**:
1. Split 121 citations into:
   - **Development set**: 80 citations (analyze errors, tune prompt)
   - **Held-out test set**: 41 citations (NEVER look at until final test)

2. Re-analyze errors using ONLY the 80 development citations
3. Make prompt changes based on 80-citation patterns
4. Test final prompt on 41 held-out citations

**Pros**:
- Quick to implement
- Same distribution as current test set
- Can implement immediately

**Cons**:
- Smaller sample sizes (80/41 split)
- Already contaminated (we've seen all 121 citations)

**Recommendation**: Use this for INITIAL validation, then proceed to Option 2 or 3

---

### Option 2: Use Larger Dataset (BETTER - Recommended)

**Approach**:
1. We have larger datasets available:
   - `final_merged_dataset_v2_CORRECTED.jsonl` (hundreds of citations)
   - `manualy_curated_citations_raw_20251023.jsonl`

2. Process:
   - **Training/Analysis set**: Current 121 citations (analyze patterns)
   - **Validation set**: Sample 100 NEW citations from larger dataset
   - **Held-out test set**: Sample 50 MORE citations (never touch until final)

3. Workflow:
   ```
   Analyze 121 citations → Make prompt changes
   ↓
   Test on Validation set (100 new citations)
   ↓
   If accuracy < 95%: Iterate on prompt with validation feedback
   ↓
   Final test on Held-out set (50 citations)
   ```

**Pros**:
- Truly independent test sets
- Larger sample size
- More realistic evaluation

**Cons**:
- Need to create/label new test sets
- Takes more time

**Recommendation**: Best approach for production-ready prompt

---

### Option 3: Synthetic Expansion (BEST - Most Robust)

**Approach**:
Create NEW synthetic citations that test the SAME patterns we identified, but with different content.

**Process**:
1. For each of the 21 error patterns identified, generate 5 new synthetic citations
2. This creates 105 new test cases covering the same patterns
3. Test prompt changes on these synthetic citations

**Example - Conference Presentation Pattern**:

Original error case:
```
Evans, A. C., Jr., et al. (2019, August 8–11). Gun violence: An event on the
power of community [Conference presentation]. APA 2019 Convention, Chicago,
IL, USA. doi:10.1037/con2019-1234
```

Synthetic variations:
```
1. Smith, J., Jones, A., & Lee, K. (2020, March 15–18). Climate change
   adaptation strategies [Conference presentation]. International Psychology
   Conference, Boston, MA, USA. doi:10.1037/ipc2020-5678

2. Garcia, M., & Rodriguez, P. (2021, June 5–7). Digital literacy in education
   [Conference presentation abstract]. Educational Research Summit,
   Seattle, WA, USA. https://edresearch.org/summit2021/program.pdf

3. [etc. - 3 more variations]
```

**Pros**:
- Tests pattern recognition, not memorization
- Can generate unlimited test cases
- Highly controlled (test specific patterns)

**Cons**:
- Synthetic citations may not represent real-world edge cases
- Requires effort to generate quality synthetics

**Recommendation**: Use alongside Option 2 for comprehensive validation

---

## Recommended Multi-Stage Testing Process

### Stage 1: Quick Validation (Day 1)

**Goal**: Verify prompt changes don't break existing correct validations

1. Randomly split 121 citations: 80 dev / 41 held-out
2. Apply high-priority fixes based on 80-citation analysis
3. Test on 41 held-out citations
4. **Success criteria**: Accuracy ≥ 85% on held-out

**Time**: 1 day

---

### Stage 2: Independent Validation (Week 1)

**Goal**: Test on truly independent citations

1. Sample 100 new citations from larger dataset
2. Manually review and correct ground truth
3. Test prompt with high-priority fixes
4. **Success criteria**: Accuracy ≥ 90%

If < 90%:
- Analyze new errors
- Determine if new patterns or overfitting
- Adjust prompt accordingly

**Time**: 3-5 days

---

### Stage 3: Synthetic Pattern Testing (Week 2)

**Goal**: Verify pattern learning, not memorization

1. Generate 5 synthetic citations for each error pattern (105 total)
2. Test prompt on synthetic set
3. **Success criteria**: Accuracy ≥ 90% on patterns we explicitly fixed

If < 90% on patterns we fixed:
- Prompt changes ineffective or poorly integrated
- May have conflicts with existing rules

**Time**: 2-3 days

---

### Stage 4: Final Held-Out Test (Week 2)

**Goal**: Production readiness assessment

1. Sample 50 completely new citations (never seen)
2. Manually verify ground truth
3. Run final prompt version
4. **Success criteria**: Accuracy ≥ 95%

**Time**: 2 days

---

## Implementation Code

### Split Current Test Set

```python
import json
import random
from pathlib import Path

# Load 121 citations
test_file = Path('Checker_Prompt_Optimization/validation_set_CORRECTED.jsonl')
citations = []
with open(test_file, 'r') as f:
    for line in f:
        citations.append(json.loads(line))

# Shuffle and split
random.seed(42)  # Reproducible split
random.shuffle(citations)

dev_set = citations[:80]
held_out_set = citations[80:]

# Save splits
with open('Checker_Prompt_Optimization/dev_set_80.jsonl', 'w') as f:
    for item in dev_set:
        f.write(json.dumps(item) + '\\n')

with open('Checker_Prompt_Optimization/held_out_set_41.jsonl', 'w') as f:
    for item in held_out_set:
        f.write(json.dumps(item) + '\\n')

print(f"✓ Dev set: 80 citations")
print(f"✓ Held-out set: 41 citations")
```

### Sample from Larger Dataset

```python
# Load larger dataset
full_dataset = []
with open('Checker_Prompt_Optimization/final_merged_dataset_v2_CORRECTED.jsonl', 'r') as f:
    for line in f:
        full_dataset.append(json.loads(line))

# Get citations NOT in current test set
current_test_citations = set(c['citation'] for c in citations)
available = [c for c in full_dataset if c['citation'] not in current_test_citations]

print(f"Available for sampling: {len(available)} citations")

# Sample validation and held-out sets
random.shuffle(available)
validation_set = available[:100]
final_held_out = available[100:150]

# Save
with open('Checker_Prompt_Optimization/validation_set_100.jsonl', 'w') as f:
    for item in validation_set:
        f.write(json.dumps(item) + '\\n')

with open('Checker_Prompt_Optimization/final_held_out_50.jsonl', 'w') as f:
    for item in final_held_out:
        f.write(json.dumps(item) + '\\n')
```

---

## Red Flags for Overfitting

Watch for these warning signs:

1. **Perfect accuracy on development set, poor on validation**
   - 100% on 121 citations, 75% on new citations
   - Clear overfitting

2. **Pattern-specific failures**
   - Fix works on original error case but fails on synthetic variation
   - Too specific to exact wording

3. **Regression on correct validations**
   - New rules break previously correct citations
   - Conflicting rules

4. **Accuracy variance across sets**
   - 95% on one set, 80% on another similar set
   - Unstable prompt

---

## Success Metrics

| Stage | Test Set | Target Accuracy | Interpretation |
|-------|----------|-----------------|----------------|
| 1 | Held-out 41 | ≥ 85% | Changes don't break existing |
| 2 | Validation 100 | ≥ 90% | Generalizes to new citations |
| 3 | Synthetic 105 | ≥ 90% | Learns patterns, not memorizes |
| 4 | Final 50 | ≥ 95% | Production ready |

---

## Recommendation

**Immediate next steps**:

1. **Today**: Implement Stage 1 (quick validation with 80/41 split)
2. **This week**: Implement Stage 2 (sample 100 from larger dataset)
3. **If Stage 2 passes**: Implement high-priority fixes in production
4. **Continue**: Stages 3 & 4 for comprehensive validation

This ensures we don't overfit while still making rapid progress toward 95% accuracy goal.
