#!/usr/bin/env python3
"""Analyze specific problem citations: compare current vs v2 prompt"""

import json
from pathlib import Path

# Load test set to get citation indices
test_file = Path("../Checker_Prompt_Optimization/test_set_121_corrected.jsonl")
citations = []
with open(test_file, 'r') as f:
    for i, line in enumerate(f):
        citations.append((i, json.loads(line)))

def load_results(file_path):
    """Load JSONL results - indexed by line order (0-based)"""
    results = []
    with open(file_path, 'r') as f:
        for line in f:
            results.append(json.loads(line))
    return results

def get_errors_by_index(results_file):
    """Get which citation indices (0-based) had errors"""
    results = load_results(results_file)
    errors = []
    for idx, result in enumerate(results):
        if not result['correct']:
            errors.append(idx)
    return errors

# Get current baseline errors
print("Loading current baseline (5mini-high)...")
current_file = Path("GPT-5-mini_optimized_high_detailed_121.jsonl")
if current_file.exists():
    current_errors = get_errors_by_index(current_file)
    print(f"Current prompt errors: {len(current_errors)} citations")
    print(f"Error indices: {current_errors[:20]}...")
else:
    print("❌ Current baseline not found")
    current_errors = None

# Get v2 errors for each config
print("\nLoading v2 results...")
v2_files = {
    "4o-mini": "GPT-4o-mini_v2_default_round1_detailed_121.jsonl",
    "5mini-low": "GPT-5-mini_v2_low_round1_detailed_121.jsonl",
    "5mini-med": "GPT-5-mini_v2_medium_round1_detailed_121.jsonl"
}

v2_errors = {}
for config, filepath in v2_files.items():
    if Path(filepath).exists():
        errors = get_errors_by_index(filepath)
        v2_errors[config] = errors
        print(f"V2 {config} errors: {len(errors)} citations")

# If we have current errors, analyze which ones v2 fixed
if current_errors:
    print("\n" + "="*70)
    print("WHICH ERRORS DID V2 FIX?")
    print("="*70)
    
    for config, v2_errs in v2_errors.items():
        fixed = set(current_errors) - set(v2_errs)
        new_errors = set(v2_errs) - set(current_errors)
        
        print(f"\n{config}:")
        print(f"  Fixed from current: {len(fixed)} citations")
        print(f"  New errors in v2: {len(new_errors)} citations")
        print(f"  Net improvement: {len(fixed) - len(new_errors):+d}")
        
        if fixed:
            print(f"  Fixed indices: {sorted(list(fixed))[:10]}...")
        if new_errors:
            print(f"  New error indices: {sorted(list(new_errors))[:10]}...")

