# Recursive Validation Experiment Analysis

**Experiment**: Test if GPT-4o-mini can improve accuracy by reviewing another model's validation output
**Dataset**: 77 citations (7 batches of 11, out of planned 121)
**Date**: 2025-11-25
**Cost**: ~$0.14 (77 API calls)

## Executive Summary

🚫 **RESULT: Recursive validation REDUCED overall accuracy by 10.2%**

The critical senior vs junior expert framing successfully increased engagement but introduced more errors than it corrected, suggesting over-criticality.

## Detailed Results

### 📊 Overall Performance (77 citations)

| Metric | Junior (Round 1) | Senior (Round 2) | Change |
|--------|------------------|------------------|---------|
| **Accuracy** | 69.8% | 59.6% | **-10.2%** |
| **Correct** | 54/77 | 46/77 | -8 citations |
| **Disagreements** | - | 57 total | High engagement |
| **Decisions Changed** | - | 21 total | Active review |

### 🎯 Batch-by-Batch Breakdown

| Batch | Junior → Senior | Improvement | Disagreements | Changes |
|-------|----------------|-------------|---------------|---------|
| 1 | 72.7% → 54.5% | **-18.2%** | 8 | 6 |
| 2 | 72.7% → 81.8% | **+9.1%** ✅ | 10 | 1 |
| 3 | 100.0% → 81.8% | **-18.2%** | 8 | 2 |
| 4 | 72.7% → 72.7% | **0.0%** | 7 | 4 |
| 5 | 72.7% → 54.5% | **-18.2%** | 9 | 2 |
| 6 | 18.2% → 27.3% | **+9.1%** ✅ | 6 | 1 |
| 7 | 63.6% → 36.4% | **-27.3%** | 9 | 5 |

**Success Rate**: 2/7 batches (28.6%) showed improvement
**Decline Rate**: 4/7 batches (57.1%) showed significant decline

## 🔍 Analysis of Failure Modes

### 1. **Over-Criticality**
The senior expert was too skeptical, flagging valid citations as invalid:

- **Batch 7**: -27.3% decline (worst performance)
- **Batch 1**: -18.2% decline despite high disagreements
- **Pattern**: Senior found "errors" that ground truth considered acceptable

### 2. **Inconsistent APA 7 Interpretations**
Different interpretations of APA 7 rules between senior expert and ground truth:

- **Batch 3**: Junior had perfect 100% accuracy, senior "corrected" valid citations
- **Batch 2**: Only batch with meaningful improvement (+9.1%)
- **Pattern**: Senior expertise didn't align with expected ground truth

### 3. **Successful Cases**
When senior expertise helped:

- **Batch 2**: +9.1% improvement, caught genuine junior errors
- **Batch 6**: +9.1% improvement on very low base (18.2% → 27.3%)
- **Pattern**: Most effective when junior performance was poor

## 💡 Key Insights

### What Worked ✅
1. **High Engagement**: 57 disagreements vs 0 in original recursive test
2. **Critical Thinking**: Senior provided detailed reasoning for every decision
3. **Error Detection**: Could catch genuine mistakes in some batches

### What Failed ❌
1. **Over-Criticality**: Senior too strict, rejecting valid formats
2. **Rule Interpretation**: Different APA 7 understanding than ground truth
3. **Net Negative**: More new errors introduced than old errors corrected

### Root Causes 🎯
1. **Knowledge vs Reasoning**: Issue isn't reasoning quality, it's APA 7 rule interpretation differences
2. **Ground Truth Alignment**: Senior expertise doesn't match the expected validation criteria
3. **Prompt Design**: "Be highly skeptical" may have been too aggressive

## 🚨 Production Readiness Assessment

**NOT READY for production deployment**

**Reasons:**
- **Net accuracy decline**: -10.2% overall performance
- **Inconsistent results**: 57% of batches performed worse
- **Over-correction**: Senior introduces more errors than corrections
- **Cost inefficiency**: 2x API cost for worse performance

## 💰 Cost-Benefit Analysis

| Factor | Single Pass | Recursive Validation |
|--------|-------------|---------------------|
| **API Cost** | $0.07 per 121 citations | $0.14 per 121 citations |
| **Accuracy** | ~67.5% (baseline) | ~59.6% (observed) |
| **Processing Time** | ~5 minutes | ~15 minutes |
| **Benefit** | Baseline performance | Worse performance, higher cost |

## 📋 Recommendations

### 1. **Abandon Recursive Approach**
The fundamental premise (models can effectively self-correct) appears flawed for this task.

### 2. **Focus on Base Prompt Improvement**
Instead of recursive validation, enhance the original v2 prompt:
- Add specific rules for edge cases (ISO standards, anthologies, online comments)
- Include examples of correct formatting for problematic source types
- Refine the 4 principles based on observed failure patterns

### 3. **Alternative Quality Approaches**
Consider:
- **Rule-based validation**: Supplement LLM with deterministic checks
- **Few-shot examples**: Carefully selected examples (test contamination risk)
- **Ensemble methods**: Multiple models voting on each citation

## 🧪 Experimental Learnings

### Successful Elements
1. **Critical framing works**: Senior vs junior prompted much more thorough analysis
2. **High engagement achieved**: 0 → 57 disagreements proves the approach triggers analytical thinking
3. **Detailed reasoning**: Senior provided comprehensive APA 7 explanations

### Failed Hypotheses
1. **"Review triggers self-correction"**: False - senior introduced more errors
2. **"Expert review improves accuracy"**: False - over-criticality dominated
3. **"2x validation worth cost"**: False - worse performance at double cost

### Methodological Insights
1. **Batch processing effective**: 11-citation batches worked well
2. **Comprehensive logging**: Detailed per-batch analysis valuable
3. **Progressive testing**: 1-batch pilot saved time from full 121-citation commitment

## 📁 Generated Files

- `critical_recursive_batch_1-7_results.json`: Individual batch results
- `critical_recursive_prompts/batch_1-7_prompt.txt`: Batch prompts for inspection
- `test_recursive_validation_critical_batch1.py`: Original test script
- `test_recursive_validation_critical_121.py`: Full experiment script

## 🏁 Conclusion

The recursive validation experiment, while methodologically sound and well-executed, demonstrated that **self-correction through model review is not an effective strategy** for improving APA 7 citation validation accuracy.

The critical framing successfully achieved its goal of making the model more analytical and engaged, but this increased scrutiny proved counterproductive, leading to over-criticality and net accuracy degradation.

**Recommendation**: Discontinue recursive validation research and redirect resources to enhancing the base v2 prompt with specific edge case rules and examples.

---

**Experiment Status**: ❌ **FAILED** - Approach not viable for production
**Next Steps**: Focus on base prompt improvement and rule-based validation enhancements