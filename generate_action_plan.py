#!/usr/bin/env python3
"""
Generate action plan to reach 95% accuracy based on:
1. Analysis results from citations-0bx
2. Consistency test results from citations-715
"""

import json
from pathlib import Path

# Load analysis results
with open("Checker_Prompt_Optimization/corrected_results/analysis_report.json", 'r') as f:
    analysis = json.load(f)

# Load consistency test results
with open("Checker_Prompt_Optimization/consistency_test_results.json", 'r') as f:
    consistency = json.load(f)

print("="*80)
print("CURRENT STATE")
print("="*80)
print(f"Best Model: {analysis['summary']['best_model']}")
print(f"Best Accuracy: {analysis['summary']['best_accuracy']}%")
print(f"Gap to Goal: {analysis['summary']['gap_to_goal']} percentage points")
print(f"Errors to Fix: {analysis['summary']['errors_to_fix']}")
print(f"Error Bias: {analysis['error_analysis']['bias']}")

print("\n" + "="*80)
print("CONSISTENCY TEST FINDINGS")
print("="*80)

for model_name, model_data in consistency.items():
    if model_name.startswith("gpt"):
        print(f"\n{model_data['model']}:")
        print(f"  Avg Accuracy: {model_data['avg_accuracy']:.2f}%")
        run_accs = [f"{acc:.2f}%" for acc in model_data['run_accuracies']]
        print(f"  Run Accuracies: {run_accs}")
        print(f"  Perfect Agreement: {model_data['perfect_agreement_rate']:.2f}%")
        print(f"  Ensemble Accuracy: {model_data['ensemble_accuracy']:.2f}%")
        print(f"  Ensemble Gain: {model_data['accuracy_gain']:+.2f}%")
        print(f"  Efficiency (gain/cost): {model_data['efficiency']:.3f}")
        print(f"  Partial Disagreements: {len(model_data['partial_disagreements'])}")

# Key insights from consistency test
consistency_insights = {
    "high_agreement": consistency['gpt-5-mini']['perfect_agreement_rate'] > 80,
    "ensemble_helps": consistency['gpt-5-mini']['accuracy_gain'] > 0,
    "ensemble_worthwhile": consistency['gpt-5-mini']['efficiency'] > 0.5,
    "flip_flop_citations": len(consistency['gpt-5-mini']['partial_disagreements']),
    "variance": max(consistency['gpt-5-mini']['run_accuracies']) - min(consistency['gpt-5-mini']['run_accuracies'])
}

print("\n" + "="*80)
print("CONSISTENCY INSIGHTS")
print("="*80)
print(f"High Agreement (>80%): {consistency_insights['high_agreement']}")
print(f"Ensemble Provides Gain: {consistency_insights['ensemble_helps']}")
print(f"Ensemble Cost-Effective: {consistency_insights['ensemble_worthwhile']}")
print(f"Flip-Flop Citations: {consistency_insights['flip_flop_citations']}")
print(f"Accuracy Variance: {consistency_insights['variance']:.2f}%")

current_acc = analysis['summary']['best_accuracy']
gap = analysis['summary']['gap_to_goal']

# Evaluate potential approaches
approaches = []

# Approach 1: Targeted Prompt Refinement
approaches.append({
    "name": "Targeted Prompt Refinement",
    "feasibility": "HIGH" if gap <= 10 else "MEDIUM",
    "estimated_improvement": "5-8%",
    "cost": "LOW",
    "time": "1-2 weeks",
    "steps": [
        "Manual review of 21 remaining errors (from citations-3xo)",
        "Add specific rules for top error patterns (DOI, article numbers, date ranges)",
        "Add few-shot examples of edge cases",
        "Test refined prompt on validation set"
    ],
    "notes": "Primary issue is too strict (16/21 errors are false positives)"
})

# Approach 2: Ensemble Validation (3x voting)
approaches.append({
    "name": "Ensemble Approach (3x voting)",
    "feasibility": "MEDIUM",
    "estimated_improvement": "0.5-1%",
    "cost": "HIGH (3x API calls)",
    "time": "1 week",
    "steps": [
        "Implement 3-run validation with temperature=1",
        "Use majority voting for final decision",
        "Target flip-flop cases for improvement"
    ],
    "notes": f"Consistency test showed only +0.55% gain, efficiency 0.18. NOT cost-effective alone."
})

# Approach 3: Higher reasoning model
approaches.append({
    "name": "Upgrade to GPT-5-mini with reasoning_effort=high",
    "feasibility": "HIGH",
    "estimated_improvement": "3-6%",
    "cost": "MEDIUM (2x cost)",
    "time": "1 week",
    "steps": [
        "Test current prompt with reasoning_effort=high",
        "Compare accuracy improvement vs cost increase",
        "Benchmark latency impact",
        "Measure if it reduces flip-flop cases"
    ],
    "notes": "May improve consistency and accuracy simultaneously"
})

# Approach 4: Hybrid Rule-Based + LLM
approaches.append({
    "name": "Hybrid Rule-Based + LLM",
    "feasibility": "MEDIUM",
    "estimated_improvement": "8-12%",
    "cost": "MEDIUM",
    "time": "3-4 weeks",
    "steps": [
        "Implement deterministic checks (DOI regex, author format, etc.)",
        "Use LLM only for ambiguous cases",
        "Create multi-stage validation pipeline",
        "Test accuracy and performance"
    ],
    "notes": "Addresses false positive issue with deterministic rules for clear cases"
})

# Approach 5: Prompt + Reasoning
approaches.append({
    "name": "Combined: Prompt Refinement + Higher Reasoning",
    "feasibility": "HIGH",
    "estimated_improvement": "8-14%",
    "cost": "MEDIUM",
    "time": "2-3 weeks",
    "steps": [
        "Refine prompt based on error analysis",
        "Enable reasoning_effort=high",
        "Test on corrected test set",
        "Validate on synthetic citations"
    ],
    "notes": "Best combination of approaches for gap > 10%"
})

print("\n" + "="*80)
print("POTENTIAL APPROACHES")
print("="*80)

for i, approach in enumerate(approaches, 1):
    print(f"\n{i}. {approach['name']}")
    print(f"   Feasibility: {approach['feasibility']}")
    print(f"   Est. Improvement: {approach['estimated_improvement']}")
    print(f"   Cost: {approach['cost']}")
    print(f"   Timeline: {approach['time']}")
    print(f"   Notes: {approach['notes']}")

# Generate recommendation based on current state
recommendation = {
    "primary_approach": None,
    "secondary_approaches": [],
    "immediate_actions": [],
    "reasoning": ""
}

# Given 12.4% gap with high consistency (81.8%) and clear error bias (76% FP),
# combined prompt + reasoning approach is optimal
if gap <= 5:
    recommendation["primary_approach"] = "Targeted Prompt Refinement"
    recommendation["secondary_approaches"] = ["Higher reasoning model"]
    recommendation["immediate_actions"] = [
        "Review 21 error cases from citations-3xo analysis",
        "Add rules for top 3 false positive patterns",
        "Test GPT-5-mini with reasoning_effort=high",
        "Validate improvements on corrected test set"
    ]
    recommendation["reasoning"] = "Close to goal. Targeted improvements + reasoning likely sufficient."

elif gap <= 15 and consistency_insights['high_agreement']:
    # High consistency means model logic is sound, just needs better rules
    recommendation["primary_approach"] = "Combined: Prompt Refinement + Higher Reasoning"
    recommendation["secondary_approaches"] = ["Hybrid approach if still short after Phase 2"]
    recommendation["immediate_actions"] = [
        "Review citations-3xo error analysis (21 cases, 16 FP)",
        "Add relaxed rules for false positive patterns (DOI, article numbers, dates)",
        "Enable reasoning_effort=high for better judgment",
        "Test combined approach on validation set",
        "Generate synthetic test set for holdout validation"
    ]
    recommendation["reasoning"] = f"12.4% gap with high consistency ({consistency['gpt-5-mini']['perfect_agreement_rate']:.1f}%) means model logic is sound. Primary issue: too strict (16/21 FP). Prompt refinement + reasoning should bridge gap."

else:
    recommendation["primary_approach"] = "Hybrid Rule-Based + LLM"
    recommendation["secondary_approaches"] = ["Different model architecture", "Fine-tuning"]
    recommendation["immediate_actions"] = [
        "Identify deterministic validation rules",
        "Implement rule-based pre-checks",
        "Use LLM for semantic validation only",
        "Consider testing Claude Sonnet",
        "Generate synthetic test set for validation"
    ]
    recommendation["reasoning"] = "Large gap with low consistency requires architectural change. Pure LLM approach insufficient."

# Add ensemble consideration
if consistency_insights['flip_flop_citations'] > 30 and not consistency_insights['ensemble_worthwhile']:
    recommendation["warnings"] = [
        f"{consistency_insights['flip_flop_citations']} flip-flop cases indicate model instability",
        "Ensemble not cost-effective (+0.55% for 3x cost)",
        "Focus on improving base prompt rather than ensemble voting"
    ]
elif consistency_insights['ensemble_worthwhile']:
    recommendation["secondary_approaches"].append("Ensemble voting for production")

print("\n" + "="*80)
print("RECOMMENDED ACTION PLAN")
print("="*80)
print(f"\nPrimary Approach: {recommendation['primary_approach']}")
if recommendation['secondary_approaches']:
    print(f"Secondary Approaches: {', '.join(recommendation['secondary_approaches'])}")

print("\nImmediate Next Actions:")
for i, action in enumerate(recommendation['immediate_actions'], 1):
    print(f"  {i}. {action}")

print(f"\nReasoning: {recommendation['reasoning']}")

if 'warnings' in recommendation:
    print("\n⚠️  WARNINGS:")
    for warning in recommendation['warnings']:
        print(f"  - {warning}")

# Generate detailed roadmap
roadmap = {
    "goal": "Achieve 95% accuracy on APA 7 citation validation",
    "current_state": {
        "accuracy": current_acc,
        "gap": gap,
        "error_bias": "too_strict",
        "consistency": consistency_insights
    },
    "approach": recommendation["primary_approach"],
    "phases": []
}

# Phase 1: Error Analysis & Prompt Refinement
roadmap["phases"].append({
    "phase": 1,
    "name": "Targeted Prompt Refinement",
    "duration": "1-2 weeks",
    "tasks": [
        "Review citations-3xo analysis (21 errors: 16 FP, 5 FN)",
        "Add rules for false positive patterns (DOI, article numbers, date ranges)",
        "Relax overly strict validation rules",
        "Add few-shot examples of valid edge cases",
        "Test refined prompt on corrected test set"
    ],
    "success_criteria": "Reduce false positives by 50%+ (8+ errors fixed)",
    "estimated_impact": "+5-8%"
})

# Phase 2: Enable Higher Reasoning
roadmap["phases"].append({
    "phase": 2,
    "name": "Enable Enhanced Reasoning",
    "duration": "1 week",
    "tasks": [
        "Test GPT-5-mini with reasoning_effort=high",
        "Measure accuracy improvement vs cost increase",
        "Check if reasoning reduces flip-flop cases",
        "Benchmark latency impact",
        "Decide on cost/benefit tradeoff"
    ],
    "success_criteria": "Additional +3-6% accuracy gain",
    "estimated_impact": "+3-6%"
})

# Phase 3: Validation & Iteration
roadmap["phases"].append({
    "phase": 3,
    "name": "Validate & Iterate",
    "duration": "1 week",
    "tasks": [
        "Test combined approach on full test set",
        "Analyze remaining errors",
        "Generate synthetic test citations for holdout validation",
        "Fine-tune based on new error patterns",
        "Confirm 95%+ on both original and synthetic sets"
    ],
    "success_criteria": "Achieve 95% on corrected test set + synthetic validation",
    "estimated_impact": "+1-3%"
})

# Phase 4: Production deployment
roadmap["phases"].append({
    "phase": 4,
    "name": "Production Deployment",
    "duration": "1 week",
    "tasks": [
        "Update production validator prompt",
        "Deploy to staging environment",
        "Monitor accuracy on real traffic",
        "A/B test if desired",
        "Gradual rollout to production"
    ],
    "success_criteria": "95% accuracy maintained in production"
})

print("\n" + "="*80)
print("IMPLEMENTATION ROADMAP")
print("="*80)

total_improvement = 0
for phase in roadmap["phases"]:
    print(f"\nPhase {phase['phase']}: {phase['name']} ({phase['duration']})")
    print("  Tasks:")
    for task in phase['tasks']:
        print(f"    - {task}")
    print(f"  Success Criteria: {phase['success_criteria']}")
    if 'estimated_impact' in phase:
        print(f"  Estimated Impact: {phase['estimated_impact']}")
        # Extract numeric impact
        if '+' in phase['estimated_impact']:
            impact_str = phase['estimated_impact'].split('+')[1].split('-')[0].strip('%')
            total_improvement += float(impact_str)

print(f"\n📊 Total Estimated Improvement: +{int(total_improvement)}% (from {current_acc}% to ~{current_acc + total_improvement}%)")
print(f"🎯 Goal: 95% accuracy")
print(f"✅ Expected Outcome: {'ACHIEVABLE' if current_acc + total_improvement >= 95 else 'MAY NEED ADDITIONAL WORK'}")

# Save action plan
output = {
    "recommendation": recommendation,
    "roadmap": roadmap,
    "approaches_evaluated": approaches,
    "consistency_insights": consistency_insights,
    "analysis_summary": analysis
}

output_file = Path("Checker_Prompt_Optimization/ACTION_PLAN.json")
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

# Save markdown version
md_file = Path("Checker_Prompt_Optimization/ACTION_PLAN.md")
with open(md_file, 'w') as f:
    f.write("# Action Plan to Achieve 95% Accuracy\n\n")

    f.write("## Current State\n\n")
    f.write(f"- **Best Model**: {analysis['summary']['best_model']}\n")
    f.write(f"- **Current Accuracy**: {current_acc}%\n")
    f.write(f"- **Gap to Goal**: {gap} percentage points\n")
    f.write(f"- **Errors to Fix**: {analysis['summary']['errors_to_fix']}\n")
    f.write(f"- **Error Bias**: {analysis['error_analysis']['bias']} (16/21 are false positives)\n\n")

    f.write("## Consistency Test Findings\n\n")
    f.write(f"- **Perfect Agreement Rate**: {consistency['gpt-5-mini']['perfect_agreement_rate']:.1f}%\n")
    f.write(f"- **Flip-Flop Citations**: {consistency_insights['flip_flop_citations']}\n")
    f.write(f"- **Ensemble Gain**: +{consistency['gpt-5-mini']['accuracy_gain']:.2f}% (not cost-effective)\n")
    f.write(f"- **Variance**: {consistency_insights['variance']:.2f}%\n\n")

    f.write("## Recommended Approach\n\n")
    f.write(f"**Primary**: {recommendation['primary_approach']}\n\n")

    if recommendation['secondary_approaches']:
        f.write(f"**Secondary**: {', '.join(recommendation['secondary_approaches'])}\n\n")

    f.write(f"**Reasoning**: {recommendation['reasoning']}\n\n")

    if 'warnings' in recommendation:
        f.write("### ⚠️  Warnings\n\n")
        for warning in recommendation['warnings']:
            f.write(f"- {warning}\n")
        f.write("\n")

    f.write("## Immediate Next Actions\n\n")
    for i, action in enumerate(recommendation['immediate_actions'], 1):
        f.write(f"{i}. {action}\n")

    f.write("\n## Implementation Roadmap\n\n")
    for phase in roadmap['phases']:
        f.write(f"### Phase {phase['phase']}: {phase['name']}\n\n")
        f.write(f"**Duration**: {phase['duration']}\n\n")
        if 'estimated_impact' in phase:
            f.write(f"**Estimated Impact**: {phase['estimated_impact']}\n\n")
        f.write("**Tasks**:\n")
        for task in phase['tasks']:
            f.write(f"- {task}\n")
        f.write(f"\n**Success Criteria**: {phase['success_criteria']}\n\n")

    f.write("## Expected Outcome\n\n")
    f.write(f"- Current: {current_acc}%\n")
    f.write(f"- Estimated after improvements: ~{current_acc + total_improvement:.0f}%\n")
    f.write(f"- Goal: 95%\n")
    f.write(f"- Status: {'✅ Achievable' if current_acc + total_improvement >= 95 else '⚠️ May need additional work'}\n\n")

    f.write("## Approaches Evaluated\n\n")
    for i, approach in enumerate(approaches, 1):
        f.write(f"### {i}. {approach['name']}\n\n")
        f.write(f"- **Feasibility**: {approach['feasibility']}\n")
        f.write(f"- **Estimated Improvement**: {approach['estimated_improvement']}\n")
        f.write(f"- **Cost**: {approach['cost']}\n")
        f.write(f"- **Timeline**: {approach['time']}\n")
        f.write(f"- **Notes**: {approach['notes']}\n\n")
        f.write("**Steps**:\n")
        for step in approach['steps']:
            f.write(f"- {step}\n")
        f.write("\n")

print(f"\n✅ Saved action plan to:")
print(f"   - {output_file}")
print(f"   - {md_file}")
