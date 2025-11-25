You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-uqp6

Experiment: Temperature Ensemble Voting for Citation Validation
Status: open
Priority: P1
Type: task
Created: 2025-11-25 21:38
Updated: 2025-11-25 21:38

Description:
## Context

Current baseline (gpt-4o-mini + v2 prompt): 67.77% accuracy
Goal: Improve accuracy by capturing model uncertainty on boundary cases

## Hypothesis

The model at temp=0 makes deterministic but sometimes incorrect decisions. On difficult citations, the model is uncertain but forced to commit. By sampling multiple times at higher temperature and using majority voting, we can:
1. Identify citations where the model is uncertain (high variance)
2. Get more reliable decisions through voting
3. Improve accuracy on boundary cases

## Implementation Plan

### Phase 1: Measure Variance (Diagnostic)

**Goal:** Confirm that high-variance citations correlate with errors

**Method:**
```python
# Test on 30 citations (mix of correct/incorrect from baseline)
for citation in sample_30:
    samples = []
    for i in range(5):
        response = validate(citation, model='gpt-4o-mini', temp=0.7)
        decision = parse_decision(response)
        samples.append(decision)

    variance = len(set(samples)) > 1
    agreement = samples.count(mode(samples)) / 5

    record({
        'citation': citation,
        'samples': samples,
        'variance': variance,
        'agreement': agreement,
        'baseline_correct': baseline_correct[citation]
    })
```

**Success criteria:**
- High-variance citations have lower baseline accuracy than low-variance
- Example: High-variance <50% correct, Low-variance >80% correct

### Current Status

**Progress Made:**
1. ✅ Created Phase 1 diagnostic script: `competitive_benchmark/test_ensemble_voting_phase1.py`
2. ✅ Implemented temperature sampling with ensemble voting logic
3. ⏳ Ready to run Phase 1 test to verify variance correlates with errors

**Script Features:**
- Loads baseline GPT-4o-mini results from 121 citations
- Selects balanced sample (15 correct, 15 incorrect from baseline)
- Runs 5 temperature samples per citation at temp=0.7
- Calculates variance, agreement, and majority decision
- Provides comprehensive analysis including:
  - Baseline accuracy by variance level
  - Ensemble vs baseline comparison
  - Agreement level breakdown
  - Key finding: variance correlation with errors

**Files Created:**
- `competitive_benchmark/test_ensemble_voting_phase1.py` - Main diagnostic script

**Files Referenced:**
- `competitive_benchmark/GPT-4o-mini_baseline_detailed_121.jsonl` - Baseline results
- `../Checker_Prompt_Optimization/test_set_121_corrected.jsonl` - Test set with ground truth
- `../backend/prompts/validator_prompt_v2.txt` - Validation prompt

### The Question/Problem/Dilemma

User wants to focus on: "review the script and any related work/steps we've done"

I'm seeking technical guidance on:

1. **Script Validation:** Is the Phase 1 diagnostic approach sound? Any improvements or potential issues?

2. **Methodology Review:**
   - Is temperature=0.7 appropriate for inducing variance?
   - Are 5 samples sufficient for meaningful ensemble voting?
   - Is the balanced sample selection approach appropriate?

3. **Success Metrics:**
   - Are the success criteria (20% accuracy gap between high/low variance) reasonable?
   - What constitutes "strong" vs "moderate" correlation?

4. **Next Steps:**
   - If Phase 1 shows correlation, should I proceed immediately to full 121-citation test?
   - Any variations to test before scaling up?

5. **Technical Considerations:**
   - Cost optimization strategies for full 121-citation test
   - Any pitfalls in the parsing or ensemble logic?
   - Alternative approaches to measuring uncertainty?

### Relevant Context

**Constraints:**
- Budget conscious: Each full 121-citation test costs ~$0.09
- Time sensitive: Need efficient iteration
- Production readiness: Latency <10s per citation if successful

**Dependencies:**
- Baseline accuracy: 67.77% (GPT-4o-mini)
- Success thresholds: Tier 1 (+3-5%), Tier 2 (+5-8%), Tier 3 (+8%+)
- Future experiments depend on this: cascade with confidence scores

### Supporting Information

**Script Implementation Details:**
- Uses OpenAI GPT-4o-mini with temperature=0.7
- Parses decisions using existing robust parsing logic
- Balanced sample: 15 baseline correct, 15 baseline incorrect
- Comprehensive output format with variance/agreement metrics
- Progress reporting every 10 citations

**Key Analysis Features:**
- Compares baseline accuracy by variance level
- Measures ensemble vs baseline improvement
- Provides agreement level breakdown (high/medium/low)
- Clear success/failure criteria with recommendations