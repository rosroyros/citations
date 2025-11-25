# V2 Validator Prompt - Final Performance Analysis

**Date**: 2025-01-25  
**Test Set**: 121 citations (corrected test set)  
**Rounds**: 3 per configuration for consistency testing

## Executive Summary

The V2 validator prompt shows **+11% improvement on GPT-4o-mini** (57% → 68%), making it the recommended production configuration. However, it performs **-5% worse on 5mini-medium** compared to the current prompt, suggesting the current prompt is already well-optimized for higher reasoning levels.

## Complete Results

### Current Prompt Baselines (for comparison)
- **5mini + Low**: 74.38%
- **5mini + Medium**: 80.17%
- **4o-mini**: ~57%

### V2 Prompt Results

| Configuration | Round 1 | Round 2 | Round 3 | Average | Std Dev | vs Baseline | Change |
|--------------|---------|---------|---------|---------|---------|-------------|--------|
| **GPT-4o-mini** | 68.60% | 68.60% | 66.94% | **68.04%** | 0.78% | 57% | **+11.0%** ✅ |
| **5mini + Low** | 76.03% | 75.21% | 72.73% | **74.66%** | 1.40% | 74.38% | **+0.3%** |
| **5mini + Medium** | 76.03% | 73.55% | 76.03% | **75.21%** | 1.17% | 80.17% | **-5.0%** ❌ |

### Consistency Analysis

All configurations show good consistency across rounds:
- **4o-mini**: Excellent (0.78% std dev, ~1% variance)
- **5mini-low**: Good (1.40% std dev, ~3% variance)
- **5mini-med**: Good (1.17% std dev, ~3% variance)

## Key Technical Insights

### 1. Response Parsing Logic (CRITICAL)

The v2 prompt returns structured output that requires different parsing than simple keyword matching:

**Correct Parsing** (from `backend/providers/openai_provider.py:227-243`):
```python
# Check for explicit "no errors" marker
if '✓ No APA 7 formatting errors detected' in response_text:
    is_valid = True
# Check for error markers
elif '❌' in response_text:
    is_valid = False
# Fallback: check for "no errors" text
elif 'no apa 7 formatting errors' in response_text.lower():
    is_valid = True
else:
    is_valid = False
```

**Why This Matters**: Initially got 40% accuracy by checking if response "started with" or "contained" the word "valid". The v2 response includes "VALIDATION RESULTS:" at the start, which matched this check and inverted all results.

### 2. V2 Prompt Structure

The v2 prompt uses 4 principle-based rules:
1. Format Flexibility Over Rigidity
2. Source-Type Specific Requirements
3. Component-Level Validation
4. Pragmatic Standards Application

This structure works well with simpler models (4o-mini) but appears to confuse higher reasoning models (5mini-medium performed worse).

### 3. Cost-Performance Trade-offs

**GPT-4o-mini + V2**:
- Speed: ~6 seconds/citation
- Cost: Lowest
- Accuracy: 68.04%
- **Best value**: 11% improvement over baseline

**5mini + Low + V2**:
- Speed: ~60 seconds/citation (10x slower)
- Cost: Medium
- Accuracy: 74.66%
- **Marginal gain**: Only 6.6% better than 4o-mini, at 10x cost/time

**5mini + Medium + Current**:
- Speed: ~60 seconds/citation
- Cost: Medium
- Accuracy: 80.17%
- **Best accuracy**: Keep current prompt for this config

## Recommendations

### ✅ DEPLOY: V2 Prompt with GPT-4o-mini

**Rationale**:
- +11% improvement is significant
- Fastest execution time (~6 sec/citation)
- Lowest cost
- Good consistency (0.78% std dev)
- 68% accuracy is acceptable for most use cases

**Implementation**:
```python
# In backend/providers/openai_provider.py
PROMPT_FILE = 'backend/prompts/validator_prompt_v2.txt'
DEFAULT_MODEL = 'gpt-4o-mini'
```

### ❌ DON'T DEPLOY: V2 Prompt with 5mini-medium

**Rationale**:
- 5% regression vs current prompt
- 10x slower and more expensive than 4o-mini
- Only 7% better than 4o-mini with v2
- Current prompt performs better (80.17%)

**Keep**: Current prompt for 5mini-medium if higher accuracy is needed

### ⚠️ MONITOR: V2 Prompt with 5mini-low

**Rationale**:
- Essentially identical performance (+0.3%)
- No clear advantage over current prompt
- Much slower/costlier than 4o-mini
- Use 5mini-medium with current prompt if you need >68% accuracy

## Test Artifacts

### Test Scripts Created
- `test_v2_5mini_low_full.py` - 5mini + reasoning_effort=low
- `test_v2_5mini_med_full.py` - 5mini + reasoning_effort=medium
- `test_v2_4omini_full.py` - 4o-mini (no reasoning_effort)

### Output Files
- `GPT-4o-mini_v2_default_round{1-3}_detailed_121.jsonl`
- `GPT-5-mini_v2_low_round{1-3}_detailed_121.jsonl`
- `GPT-5-mini_v2_medium_round{1-3}_detailed_121.jsonl`

### Summary Files
- `v2_4omini_summary.json` (68.04% avg)
- `v2_5mini_low_summary.json` (74.66% avg)
- `v2_5mini_medium_summary.json` (75.21% avg)

### Logs
- `v2_4omini_full.log` (completed ~45 min)
- `v2_5mini_low_full.log` (completed ~3 hours)
- `v2_5mini_med_full.log` (completed ~3 hours)

## Next Steps

1. ✅ Deploy v2 prompt with 4o-mini to production
2. Update backend to use `validator_prompt_v2.txt`
3. Monitor production accuracy metrics
4. Keep current prompt available for 5mini-medium if higher accuracy needed
