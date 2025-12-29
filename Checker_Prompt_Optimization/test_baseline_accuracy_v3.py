#!/usr/bin/env python3
"""
Test 1: Baseline Accuracy Test

Run the full 121 citation test set with the new v3 prompt to ensure 
baseline accuracy is not negatively affected.

Target: Accuracy should remain >= 95%
"""

import os
import json
import asyncio
import re
import sys
from google import genai as new_genai
from google.genai import types
from dotenv import load_dotenv

sys.stdout.reconfigure(line_buffering=True)

# Get project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, "backend/.env"))

# Configuration
MODEL_NAME = "gemini-2.5-flash"
PROMPT_V2_PATH = os.path.join(PROJECT_ROOT, "backend/prompts/validator_prompt_v2_corrected.txt")
PROMPT_V3_PATH = os.path.join(PROJECT_ROOT, "backend/prompts/validator_prompt_v3_no_hallucination.txt")
TEST_SET_PATH = os.path.join(PROJECT_ROOT, "Checker_Prompt_Optimization/test_set_121_corrected.jsonl")
TEMPERATURE = 0.0
THINKING_BUDGET = 1024
MAX_OUTPUT_TOKENS = 10000


def load_prompt(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


def load_test_set(path: str) -> list:
    data = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def extract_validation_result(response_text: str) -> bool:
    """Determine if LLM validated the citation as correct (no errors)"""
    # Check for "No APA 7 formatting errors detected"
    if "No APA 7 formatting errors detected" in response_text:
        return True
    if "✓" in response_text and "❌" not in response_text:
        return True
    # If any ❌ markers are present, it's invalid
    if "❌" in response_text:
        return False
    return True  # Default to valid if unclear


async def validate_citation(client, prompt_template, citation: str, ground_truth: bool, idx: int):
    """Send citation and check if LLM's verdict matches ground truth"""
    full_prompt = prompt_template + f"\n\nCITATION TO VALIDATE 1: {citation}"
    
    config = types.GenerateContentConfig(
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET)
    )
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt,
            config=config
        )
        
        predicted_valid = extract_validation_result(response.text)
        correct = predicted_valid == ground_truth
        
        return {
            "idx": idx,
            "citation": citation,
            "ground_truth": ground_truth,
            "predicted": predicted_valid,
            "correct": correct,
            "raw_response": response.text[:500] if response.text else None
        }
    except Exception as e:
        return {
            "idx": idx,
            "citation": citation,
            "ground_truth": ground_truth,
            "predicted": None,
            "correct": False,
            "error": str(e)
        }


async def run_test(client, prompt_path: str, test_set: list, label: str):
    """Run test with a specific prompt"""
    prompt_template = load_prompt(prompt_path)
    
    print(f"\n{'='*60}")
    print(f"Testing: {label}")
    print(f"Prompt: {prompt_path}")
    print(f"{'='*60}")
    
    results = []
    for i, item in enumerate(test_set):
        result = await validate_citation(
            client, prompt_template,
            item["citation"],
            item["ground_truth"],
            i + 1
        )
        results.append(result)
        
        status = "✅" if result.get("correct") else "❌"
        print(f"{status} [{i+1:3d}] GT={item['ground_truth']}, Pred={result.get('predicted')}")
        
        if result.get("error"):
            print(f"   Error: {result['error']}")
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    return results


def calculate_metrics(results: list) -> dict:
    """Calculate accuracy and breakdown metrics"""
    total = len(results)
    correct = sum(1 for r in results if r.get("correct"))
    
    # Breakdown by ground truth
    true_valid = [r for r in results if r["ground_truth"] == True]
    true_invalid = [r for r in results if r["ground_truth"] == False]
    
    tp = sum(1 for r in true_valid if r.get("predicted") == True)
    fn = sum(1 for r in true_valid if r.get("predicted") == False)
    tn = sum(1 for r in true_invalid if r.get("predicted") == False)
    fp = sum(1 for r in true_invalid if r.get("predicted") == True)
    
    return {
        "accuracy": correct / total if total > 0 else 0,
        "correct": correct,
        "total": total,
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn
    }


async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return
    
    client = new_genai.Client(api_key=api_key)
    test_set = load_test_set(TEST_SET_PATH)
    
    print(f"🧪 Baseline Accuracy Test - {len(test_set)} citations")
    print(f"🔧 Config: model={MODEL_NAME}, temp={TEMPERATURE}, thinking={THINKING_BUDGET}")
    print("="*60)
    
    # Test both prompts
    v2_results = await run_test(client, PROMPT_V2_PATH, test_set, "V2 (Current Production)")
    v3_results = await run_test(client, PROMPT_V3_PATH, test_set, "V3 (No Hallucination Fix)")
    
    # Calculate metrics
    v2_metrics = calculate_metrics(v2_results)
    v3_metrics = calculate_metrics(v3_results)
    
    # Summary
    print("\n" + "="*60)
    print("📊 RESULTS SUMMARY")
    print("="*60)
    
    print(f"\n📌 V2 (Production):")
    print(f"   Accuracy: {v2_metrics['accuracy']:.1%} ({v2_metrics['correct']}/{v2_metrics['total']})")
    print(f"   TP={v2_metrics['true_positives']}, TN={v2_metrics['true_negatives']}, FP={v2_metrics['false_positives']}, FN={v2_metrics['false_negatives']}")
    
    print(f"\n📌 V3 (No Hallucination):")
    print(f"   Accuracy: {v3_metrics['accuracy']:.1%} ({v3_metrics['correct']}/{v3_metrics['total']})")
    print(f"   TP={v3_metrics['true_positives']}, TN={v3_metrics['true_negatives']}, FP={v3_metrics['false_positives']}, FN={v3_metrics['false_negatives']}")
    
    # Comparison
    diff = v3_metrics['accuracy'] - v2_metrics['accuracy']
    print(f"\n📈 Change: {diff:+.1%}")
    
    # Pass/Fail criteria
    print("\n" + "="*60)
    if v3_metrics['accuracy'] >= 0.95:
        print("✅ PASS: V3 accuracy >= 95%")
    else:
        print(f"❌ FAIL: V3 accuracy {v3_metrics['accuracy']:.1%} < 95%")
    
    if v3_metrics['accuracy'] >= v2_metrics['accuracy'] - 0.02:
        print("✅ PASS: V3 accuracy within 2% of V2")
    else:
        print(f"⚠️ WARNING: V3 accuracy dropped by {-diff:.1%}")
    print("="*60)
    
    # Save results
    output = {
        "v2_metrics": v2_metrics,
        "v3_metrics": v3_metrics,
        "v2_results": v2_results,
        "v3_results": v3_results
    }
    output_path = os.path.join(PROJECT_ROOT, "Checker_Prompt_Optimization/baseline_accuracy_v3_test.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Results saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
