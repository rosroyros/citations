#!/usr/bin/env python3
"""
Test correction quality using the golden set.

Methodology:
1. Take mutated citations from golden_set
2. Run through LLM with CORRECTED prompt
3. Verify CORRECTED output fixed the mutation we introduced
4. Also track exact match rate (may differ if LLM fixes other issues too)
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
load_dotenv("backend/.env")

# === PRODUCTION CONFIG - DO NOT CHANGE ===
MODEL_NAME = "gemini-3-flash-preview"
PROMPT_PATH = "backend/prompts/validator_prompt_v2_corrected.txt"
GOLDEN_SET_PATH = "Checker_Prompt_Optimization/correction_golden_set.jsonl"
TEMPERATURE = 0.0
THINKING_BUDGET = 1024
MAX_OUTPUT_TOKENS = 10000
# =========================================


def load_prompt(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


def load_golden_set(path: str) -> list:
    data = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def extract_corrected(response_text: str) -> str:
    """Extract CORRECTED CITATION: line from LLM response"""
    pattern = r'CORRECTED CITATION:\s*\n?(.*?)(?:\n─|$)'
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    pattern2 = r'CORRECTED CITATION:\s*(.+?)(?:\n\n|$)'
    match2 = re.search(pattern2, response_text, re.DOTALL)
    if match2:
        return match2.group(1).strip()
    
    return None


def normalize_citation(text: str) -> str:
    """Normalize for comparison"""
    if not text:
        return ""
    text = ' '.join(text.split())
    return text.strip()


def check_mutation_fixed(mutation_type: str, mutated: str, corrected: str) -> bool:
    """Check if the specific mutation was fixed (not exact match, just the mutation)"""
    if not corrected:
        return False
        
    if mutation_type == 'removed_italics':
        # Check if italics were restored (corrected has italics, mutated didn't)
        has_italics_mutated = bool(re.search(r'_[^_]+_', mutated))
        has_italics_corrected = bool(re.search(r'_[^_]+_', corrected))
        return has_italics_corrected and not has_italics_mutated
    
    elif mutation_type == 'ampersand_to_and':
        # Check if 'and' was replaced with '&'
        has_and_mutated = ', and' in mutated
        has_ampersand_corrected = ', &' in corrected
        return has_ampersand_corrected and has_and_mutated
    
    elif mutation_type == 'missing_oxford_comma':
        # Check if comma was added before &
        missing_comma_mutated = ' &' in mutated and ', &' not in mutated
        has_comma_corrected = ', &' in corrected
        return has_comma_corrected and missing_comma_mutated
    
    return False


async def validate_correction(client, prompt_template, mutated: str, original_valid: str, mutation_type: str, idx: int):
    """Send mutated citation, verify CORRECTED matches original"""
    full_prompt = prompt_template + f"\n\nCITATION TO VALIDATE 1: {mutated}"
    
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
        
        corrected = extract_corrected(response.text)
        normalized_corrected = normalize_citation(corrected)
        normalized_original = normalize_citation(original_valid)
        
        exact_match = normalized_corrected == normalized_original
        mutation_fixed = check_mutation_fixed(mutation_type, mutated, corrected)
        
        return {
            "idx": idx,
            "exact_match": exact_match,
            "mutation_fixed": mutation_fixed,
            "mutation_type": mutation_type,
            "original": original_valid,
            "mutated": mutated,
            "corrected": corrected,
            "normalized_corrected": normalized_corrected,
            "normalized_original": normalized_original,
            "raw_response": response.text[:1000] if response.text else None
        }
    except Exception as e:
        return {"idx": idx, "exact_match": False, "mutation_fixed": False, "mutation_type": mutation_type, "error": str(e)}


async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return
    
    client = new_genai.Client(api_key=api_key)
    prompt_template = load_prompt(PROMPT_PATH)
    golden_set = load_golden_set(GOLDEN_SET_PATH)
    
    print(f"🧪 Testing {len(golden_set)} golden citations")
    print(f"📄 Prompt: {PROMPT_PATH}")
    print(f"🔧 Config: model={MODEL_NAME}, temp={TEMPERATURE}, thinking={THINKING_BUDGET}")
    print("=" * 60)
    
    results = []
    for i, item in enumerate(golden_set):
        result = await validate_correction(
            client, prompt_template,
            item["mutated"],
            item["original_valid"],
            item["mutation_type"],
            i + 1
        )
        results.append(result)
        
        mutation_status = "✅" if result.get("mutation_fixed") else "❌"
        exact_status = "=" if result.get("exact_match") else "≠"
        print(f"{mutation_status} Citation {i+1} ({item['mutation_type']}): Fixed={result.get('mutation_fixed', False)}, Exact={result.get('exact_match', False)}")
        
        if not result.get("mutation_fixed") and not result.get("error"):
            print(f"   ⚠️ Mutation NOT fixed!")
            print(f"   Mutated:   {item['mutated'][:80]}...")
            corrected = result.get('corrected')
            print(f"   Corrected: {corrected[:80] if corrected else 'None'}...")
        
        if result.get("error"):
            print(f"   Error: {result['error']}")
        
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary
    mutations_fixed = sum(1 for r in results if r.get("mutation_fixed"))
    exact_matches = sum(1 for r in results if r.get("exact_match"))
    total = len(results)
    
    mutation_rate = (mutations_fixed / total) * 100 if total > 0 else 0
    exact_rate = (exact_matches / total) * 100 if total > 0 else 0
    
    print("=" * 60)
    print(f"🏆 MUTATION FIX RATE: {mutation_rate:.1f}% ({mutations_fixed}/{total})")
    print(f"📊 EXACT MATCH RATE: {exact_rate:.1f}% ({exact_matches}/{total})")
    print("=" * 60)
    
    # Breakdown by mutation type
    mutation_stats = {}
    for r in results:
        mt = r.get("mutation_type", "unknown")
        if mt not in mutation_stats:
            mutation_stats[mt] = {"total": 0, "fixed": 0, "exact": 0}
        mutation_stats[mt]["total"] += 1
        if r.get("mutation_fixed"):
            mutation_stats[mt]["fixed"] += 1
        if r.get("exact_match"):
            mutation_stats[mt]["exact"] += 1
    
    print("\n📊 Breakdown by mutation type:")
    for mt, stats in sorted(mutation_stats.items()):
        fix_pct = (stats["fixed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        exact_pct = (stats["exact"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        print(f"  {mt}: Fixed {fix_pct:.0f}%, Exact {exact_pct:.0f}% ({stats['fixed']}/{stats['total']} fixed, {stats['exact']}/{stats['total']} exact)")
    
    # Acceptance criteria check
    print("\n" + "=" * 60)
    if mutation_rate >= 90:
        print("✅ PASS: Mutation fix rate >= 90%")
    else:
        print(f"❌ FAIL: Mutation fix rate {mutation_rate:.1f}% < 90%")
    print("=" * 60)
    
    # Save results
    output_path = "Checker_Prompt_Optimization/correction_quality_results.json"
    with open(output_path, 'w') as f:
        json.dump({
            "mutation_fix_rate": mutation_rate,
            "exact_match_rate": exact_rate,
            "results": results
        }, f, indent=2)
    print(f"\n💾 Results saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
