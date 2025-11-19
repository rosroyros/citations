# Action Plan to Achieve 95% Accuracy

## Current State

- **Best Model**: GPT-5-mini_optimized
- **Current Accuracy**: 82.64%
- **Gap to Goal**: 12.36 percentage points
- **Errors to Fix**: 15
- **Error Bias**: too_strict (16/21 are false positives)

## Consistency Test Findings

- **Perfect Agreement Rate**: 81.8%
- **Flip-Flop Citations**: 22
- **Ensemble Gain**: +0.55% (not cost-effective)
- **Variance**: 4.96%

## Recommended Approach

**Primary**: Combined: Prompt Refinement + Higher Reasoning

**Secondary**: Hybrid approach if still short after Phase 2

**Reasoning**: 12.4% gap with high consistency (81.8%) means model logic is sound. Primary issue: too strict (16/21 FP). Prompt refinement + reasoning should bridge gap.

## Immediate Next Actions

1. Review citations-3xo error analysis (21 cases, 16 FP)
2. Add relaxed rules for false positive patterns (DOI, article numbers, dates)
3. Enable reasoning_effort=high for better judgment
4. Test combined approach on validation set
5. Generate synthetic test set for holdout validation

## Implementation Roadmap

### Phase 1: Targeted Prompt Refinement

**Duration**: 1-2 weeks

**Estimated Impact**: +5-8%

**Tasks**:
- Review citations-3xo analysis (21 errors: 16 FP, 5 FN)
- Add rules for false positive patterns (DOI, article numbers, date ranges)
- Relax overly strict validation rules
- Add few-shot examples of valid edge cases
- Test refined prompt on corrected test set

**Success Criteria**: Reduce false positives by 50%+ (8+ errors fixed)

### Phase 2: Enable Enhanced Reasoning

**Duration**: 1 week

**Estimated Impact**: +3-6%

**Tasks**:
- Test GPT-5-mini with reasoning_effort=high
- Measure accuracy improvement vs cost increase
- Check if reasoning reduces flip-flop cases
- Benchmark latency impact
- Decide on cost/benefit tradeoff

**Success Criteria**: Additional +3-6% accuracy gain

### Phase 3: Validate & Iterate

**Duration**: 1 week

**Estimated Impact**: +1-3%

**Tasks**:
- Test combined approach on full test set
- Analyze remaining errors
- Generate synthetic test citations for holdout validation
- Fine-tune based on new error patterns
- Confirm 95%+ on both original and synthetic sets

**Success Criteria**: Achieve 95% on corrected test set + synthetic validation

### Phase 4: Production Deployment

**Duration**: 1 week

**Tasks**:
- Update production validator prompt
- Deploy to staging environment
- Monitor accuracy on real traffic
- A/B test if desired
- Gradual rollout to production

**Success Criteria**: 95% accuracy maintained in production

## Expected Outcome

- Current: 82.64%
- Estimated after improvements: ~92%
- Goal: 95%
- Status: ⚠️ May need additional work

## Approaches Evaluated

### 1. Targeted Prompt Refinement

- **Feasibility**: MEDIUM
- **Estimated Improvement**: 5-8%
- **Cost**: LOW
- **Timeline**: 1-2 weeks
- **Notes**: Primary issue is too strict (16/21 errors are false positives)

**Steps**:
- Manual review of 21 remaining errors (from citations-3xo)
- Add specific rules for top error patterns (DOI, article numbers, date ranges)
- Add few-shot examples of edge cases
- Test refined prompt on validation set

### 2. Ensemble Approach (3x voting)

- **Feasibility**: MEDIUM
- **Estimated Improvement**: 0.5-1%
- **Cost**: HIGH (3x API calls)
- **Timeline**: 1 week
- **Notes**: Consistency test showed only +0.55% gain, efficiency 0.18. NOT cost-effective alone.

**Steps**:
- Implement 3-run validation with temperature=1
- Use majority voting for final decision
- Target flip-flop cases for improvement

### 3. Upgrade to GPT-5-mini with reasoning_effort=high

- **Feasibility**: HIGH
- **Estimated Improvement**: 3-6%
- **Cost**: MEDIUM (2x cost)
- **Timeline**: 1 week
- **Notes**: May improve consistency and accuracy simultaneously

**Steps**:
- Test current prompt with reasoning_effort=high
- Compare accuracy improvement vs cost increase
- Benchmark latency impact
- Measure if it reduces flip-flop cases

### 4. Hybrid Rule-Based + LLM

- **Feasibility**: MEDIUM
- **Estimated Improvement**: 8-12%
- **Cost**: MEDIUM
- **Timeline**: 3-4 weeks
- **Notes**: Addresses false positive issue with deterministic rules for clear cases

**Steps**:
- Implement deterministic checks (DOI regex, author format, etc.)
- Use LLM only for ambiguous cases
- Create multi-stage validation pipeline
- Test accuracy and performance

### 5. Combined: Prompt Refinement + Higher Reasoning

- **Feasibility**: HIGH
- **Estimated Improvement**: 8-14%
- **Cost**: MEDIUM
- **Timeline**: 2-3 weeks
- **Notes**: Best combination of approaches for gap > 10%

**Steps**:
- Refine prompt based on error analysis
- Enable reasoning_effort=high
- Test on corrected test set
- Validate on synthetic citations

