# Overfitting Solution: When No Holdout Data Exists

## The Problem

You've correctly identified that:
- The 121-citation test set was held out during prompt development
- But ALL other curated citations were used in training/tuning
- We have NO additional unseen citations to validate against
- This means we cannot use traditional train/test split for validation

**This is a critical problem**: Any changes based on analyzing the 121 citations will be overfit to that exact set.

---

## Why Traditional Solutions Won't Work

### ❌ Option 1: Split the 121 citations
**Problem**: We've already analyzed all 21 errors. We're contaminated.
- We know exactly which citations fail
- Splitting won't help - we've already seen them all

### ❌ Option 2: Sample from larger dataset
**Problem**: All other citations were used during prompt development
- They've been seen by the model during training
- Not a true holdout set

### ❌ Option 3: Cross-validation
**Problem**: Doesn't solve overfitting to specific examples
- We're not doing statistical learning
- We're making rule-based prompt changes

---

## Solution 1: Generate New Synthetic Citations (Recommended)

### Approach
Create completely NEW citations that test the same APA 7 rules but with different content.

### Why This Works
- Tests rule understanding, not memorization
- Can generate unlimited test cases
- Truly independent of training data

### Process

**Step 1: For each error pattern, generate 10 NEW synthetic citations**

Example - Conference Presentation Pattern:

**Original Error Case** (from 121 test set):
```
Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., &
Márquez-Greene, N. (2019, August 8–11). Gun violence: An event on the
power of community [Conference presentation]. APA 2019 Convention,
Chicago, IL, USA. doi:10.1037/con2019-1234
```

**Synthetic Variations** (completely new):
```
1. Thompson, R., & Martinez, L. (2022, May 12–15). Neural mechanisms of
   language acquisition [Conference presentation]. Cognitive Science
   Society Annual Meeting, Toronto, Ontario, Canada. doi:10.1234/css2022-789

2. Lee, J., Park, S., Kim, H., & Chen, W. (2021, July 20–23). Machine
   learning approaches to climate modeling [Conference presentation].
   International Conference on Machine Learning, Virtual. doi:10.5678/icml2021-456

3. [8 more variations with different authors, titles, locations, DOIs]
```

**Key Properties**:
- Different authors, titles, dates, locations
- SAME pattern: Conference presentation with bare `doi:` format
- If model accepts these, it learned the RULE, not memorized the example

**Step 2: Generate 10 synthetic citations for each of the 21 error patterns**
- Total: 210 completely new test citations
- Cover all patterns we identified
- Zero contamination

**Step 3: Test prompt changes on synthetic set**
- Baseline (no changes): Should fail on patterns we identified
- With fixes: Should pass on patterns we fixed
- Success metric: ≥90% on synthetic patterns we explicitly addressed

---

## Solution 2: Crowdsource Real-World Citations

### Approach
Collect new citations from real academic papers published recently.

### Process

**Step 1: Sample from recent publications**
- ArXiv papers from last 3 months (post-training)
- Recent journal articles (2024-2025)
- Conference proceedings (2024-2025)

**Step 2: Extract reference lists**
- Use PDF parsing
- Extract 100-200 citations
- Manually verify they're APA 7 format

**Step 3: Manual labeling**
- Review each citation for APA 7 compliance
- Label as valid/invalid
- Document specific issues

**Pros**:
- Real-world citations
- Completely unseen by model
- Tests production scenarios

**Cons**:
- Time-consuming (manual review required)
- May not cover all error patterns we identified
- Need to verify APA 7 compliance ourselves

---

## Solution 3: Pattern-Based Unit Tests

### Approach
Instead of full citations, create minimal test cases for each APA 7 rule.

### Example

**Rule**: Article numbers use "Article XXXX" format

**Unit Tests**:
```
✓ VALID: Smith, J. (2020). Title. Journal, 15(3), Article e12345. doi:...
✓ VALID: Jones, A. (2019). Title. PLoS ONE, 13(2), Article 0193972. doi:...
✗ INVALID: Brown, K. (2020). Title. Journal, 15(3), e12345. doi:... [Missing "Article"]
✗ INVALID: White, L. (2020). Title. Journal, 15(3), Pages e12345. doi:... [Wrong word]
```

**Rule**: Conference presentations can use bare DOI

**Unit Tests**:
```
✓ VALID: Author (2020). Title [Conference presentation]. Conference, Location. doi:10.xxxx/xxxxx
✓ VALID: Author (2020). Title [Conference presentation]. Conference, Location. https://doi.org/10.xxxx/xxxxx
✗ INVALID: Author (2020). Title [Conference presentation]. Conference, Location. 10.xxxx/xxxxx [Missing prefix]
```

### Process

**Step 1: Create 5-10 unit tests per rule**
- Positive examples (should pass)
- Negative examples (should fail)
- Edge cases

**Step 2: Test prompt changes**
- Before fixes: Unit tests should match our hypothesis
- After fixes: Should pass all positive tests, fail all negative tests

**Pros**:
- Fast to create
- Targeted testing
- Clear pass/fail criteria

**Cons**:
- Doesn't test complex interactions
- May miss edge cases in full citations

---

## Solution 4: Human Expert Review (Gold Standard)

### Approach
Have APA 7 experts manually review the 21 error cases and our proposed fixes.

### Process

**Step 1: Expert verification of ground truth**
For each of the 21 error cases:
1. Show citation to APA 7 expert
2. Ask: "Is this citation valid per APA 7?"
3. If expert disagrees with ground truth, update it
4. Document which APA 7 rule applies

**Step 2: Expert review of proposed fixes**
For each proposed prompt change:
1. Show the fix to APA 7 expert
2. Ask: "Is this guidance correct per APA 7?"
3. Verify against official APA 7 manual
4. Adjust fixes as needed

**Step 3: Expert-generated test cases**
Ask expert to create:
- 10 citations for each pattern (similar to synthetic approach)
- Mix of valid and invalid
- Covering edge cases they know from experience

**Pros**:
- Highest confidence in correctness
- May catch issues we missed
- Expert knowledge of edge cases

**Cons**:
- Requires access to APA 7 expert
- Time-consuming
- Expensive

---

## Recommended Hybrid Approach

### Phase 1: APA 7 Verification (Week 1)
**Goal**: Ensure our ground truth and fixes are correct

1. Manual verification against APA 7 manual
2. Check each error case against official examples
3. Verify proposed fixes are APA 7 compliant
4. Correct any ground truth errors

**Deliverable**: Verified error list with APA 7 citations

---

### Phase 2: Synthetic Test Generation (Week 1-2)
**Goal**: Create independent test set

1. For each verified error pattern, generate 10 synthetic citations
2. Use GPT-4 or Claude to generate variations
3. Manually review synthetic citations for quality
4. Label each as valid/invalid per APA 7

**Deliverable**: 200+ synthetic test citations

---

### Phase 3: Unit Test Creation (Week 2)
**Goal**: Focused testing of specific rules

1. Create 5 unit tests per pattern
2. Mix positive and negative examples
3. Document expected behavior

**Deliverable**: 100+ unit tests

---

### Phase 4: Validation (Week 2-3)
**Goal**: Test prompt changes

1. **Baseline test** (no changes):
   - Run on synthetic set
   - Should fail on patterns we identified
   - Measure accuracy

2. **Apply high-priority fixes**:
   - Update prompt
   - Run on synthetic set
   - Measure improvement

3. **Unit test validation**:
   - Run unit tests
   - Verify rule-level behavior

4. **Success criteria**:
   - Synthetic set: ≥90% on patterns we fixed
   - Unit tests: 100% pass on tests for rules we fixed
   - No regression: ≥82% on original patterns

---

## Code: Generate Synthetic Citations

```python
import json
from openai import OpenAI

client = OpenAI()

def generate_synthetic_citation(pattern_description, apa7_rule, original_example):
    """Generate synthetic citation matching a pattern"""

    prompt = f"""You are an APA 7 citation expert. Generate a completely NEW citation that:

1. Follows this APA 7 pattern: {pattern_description}
2. Matches this rule: {apa7_rule}
3. Is similar in structure to this example, but with completely different content:
   {original_example}

Requirements:
- Different authors (use realistic names from various cultures)
- Different title (realistic academic topic)
- Different publication details (year, location, etc.)
- SAME structural pattern and APA 7 formatting

Generate ONLY the citation, nothing else."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0  # Higher for variety
    )

    return response.choices[0].message.content.strip()

# Example usage
pattern = "Conference presentation with bare DOI format"
rule = "Conference presentations can use doi:10.xxxx/xxxxx format"
original = """Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., & Márquez-Greene, N. (2019, August 8–11). Gun violence: An event on the power of community [Conference presentation]. APA 2019 Convention, Chicago, IL, USA. doi:10.1037/con2019-1234"""

# Generate 10 variations
synthetic_citations = []
for i in range(10):
    citation = generate_synthetic_citation(pattern, rule, original)
    synthetic_citations.append({
        'citation': citation,
        'pattern': pattern,
        'is_valid': True,  # We know it should be valid
        'source': 'synthetic',
        'pattern_id': 'fp_conference_bare_doi'
    })
    print(f"{i+1}. {citation}\\n")

# Save
with open('synthetic_test_set_conference_bare_doi.jsonl', 'w') as f:
    for item in synthetic_citations:
        f.write(json.dumps(item) + '\\n')
```

---

## Validation Metrics

### For Synthetic Citations
- **Pattern coverage**: Each of 21 patterns has ≥10 synthetic examples
- **Before fixes**: Should see same errors on synthetic as on original
- **After fixes**: Should fix ≥90% of synthetic citations for addressed patterns
- **No regression**: Should maintain ≥82% on patterns we didn't fix

### For Unit Tests
- **100% pass rate** on positive tests for rules we fixed
- **100% fail rate** on negative tests
- **No regression** on tests for rules we didn't change

---

## Risk Mitigation

### What if synthetic citations show no improvement?
**Interpretation**: Our fixes are overfitted to exact examples, didn't learn rules
**Action**: Revise fixes to be more general, test again

### What if synthetic citations show regression?
**Interpretation**: New rules conflict with existing rules
**Action**: Review prompt for conflicts, adjust integration

### What if synthetic citations are not realistic?
**Action**: Manual review and filtering, regenerate low-quality ones

---

## Timeline

| Week | Activity | Deliverable |
|------|----------|-------------|
| 1 | APA 7 verification | Verified error list |
| 1 | Generate synthetic citations (100) | Synthetic test set v1 |
| 2 | Create unit tests (50) | Unit test suite |
| 2 | Test baseline on synthetic | Baseline metrics |
| 2 | Apply fixes, test on synthetic | Validation results |
| 3 | Iterate if needed | Final prompt |

---

## Conclusion

**Given that we have no true holdout data**, the best approach is:

1. ✅ **Synthetic citation generation** - Creates truly independent test cases
2. ✅ **Unit test creation** - Focused validation of specific rules
3. ✅ **APA 7 expert verification** - Ensures correctness
4. ❌ **Traditional train/test split** - Won't work, data already seen

**Recommended first step**: Generate 100 synthetic citations (10 per major pattern) and test current prompt to establish baseline.
