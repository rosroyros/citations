#!/usr/bin/env python3
"""
V3 Prompt Comparison Test - Production Configuration

Tests the V3 no-hallucination prompt against V2 corrected prompt using:
- Exact production config: gemini-3-flash-preview, temp=0.0, thinking_budget=1024
- Batch size: 5 citations per call
- Dataset: test_set_121_corrected.jsonl (121 citations)

This follows the r652.13 methodology exactly.
"""

import os
import json
import asyncio
import re
import time
import sys
from typing import List, Dict, Any
from google import genai as new_genai
from google.genai import types
from dotenv import load_dotenv

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Get project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, "backend/.env"))

# === PRODUCTION CONFIGURATION - MUST MATCH r652.13 ===
MODEL_NAME = "gemini-3-flash-preview"
BATCH_SIZE = 5
TEMPERATURE = 0.0
THINKING_BUDGET = 1024
MAX_OUTPUT_TOKENS = 65536
MAX_RETRIES = 5
BASE_DELAY = 2
RATE_LIMIT_PAUSE = 30

# Paths
DATASET_PATH = os.path.join(PROJECT_ROOT, "Checker_Prompt_Optimization/test_set_121_corrected.jsonl")
PROMPT_V2_PATH = os.path.join(PROJECT_ROOT, "backend/prompts/validator_prompt_v2_corrected.txt")
PROMPT_V3_PATH = os.path.join(PROJECT_ROOT, "backend/prompts/validator_prompt_v3_no_hallucination.txt")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "Checker_Prompt_Optimization/v3_prompt_comparison_results.json")


def load_data(path: str) -> List[Dict[str, Any]]:
    print(f"📂 Loading data from {path}", flush=True)
    data = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    print(f"✅ Loaded {len(data)} citations", flush=True)
    return data


def load_prompt(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


def format_citations_for_batch(citations: List[str], start_idx: int) -> str:
    """Format citations for batch (numbered for clarity)"""
    formatted = []
    for i, citation in enumerate(citations, start_idx):
        formatted.append(f"CITATION TO VALIDATE {i}: {citation}")
    return "\n\n".join(formatted)


def parse_response(response_text: str) -> List[Dict[str, Any]]:
    """Parse response and extract citations"""
    results = []
    citation_pattern = r'(?:═+\s+)?CITATION #(\d+)\s*\n\s*═+(.+?)(?=(?:═+\s+)?CITATION #\d+|$)'
    matches = re.finditer(citation_pattern, response_text, re.DOTALL)

    for match in matches:
        citation_num = int(match.group(1))
        block_content = match.group(2)

        is_valid = False
        if '✓ No APA 7 formatting errors detected' in block_content or 'No APA 7 formatting errors' in block_content:
            is_valid = True

        # Extract corrected citation for placeholder analysis
        corrected = None
        corrected_match = re.search(r'CORRECTED CITATION:\s*\n?(.*?)(?:\n─|$)', block_content, re.DOTALL)
        if corrected_match:
            corrected = corrected_match.group(1).strip()

        # Check for placeholders
        has_placeholder = bool(re.search(r'\[MISSING:[^\]]+\]', corrected or ""))
        
        results.append({
            "citation_number": citation_num,
            "is_valid": is_valid,
            "corrected": corrected,
            "has_placeholder": has_placeholder
        })
    return results


async def call_api_with_retry(client, full_prompt: str, batch_num: int) -> str:
    """Call API with retry logic matching production"""
    for attempt in range(MAX_RETRIES):
        try:
            config = types.GenerateContentConfig(
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True,
                    thinking_budget=THINKING_BUDGET
                )
            )
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=full_prompt,
                config=config
            )
            return response.text
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "429" in error_str or ("resource" in error_str and "exhausted" in error_str):
                print(f"🛑 Batch {batch_num}: Rate limit! Pausing {RATE_LIMIT_PAUSE}s...", flush=True)
                await asyncio.sleep(RATE_LIMIT_PAUSE)
                continue

            if attempt < MAX_RETRIES - 1:
                wait_time = BASE_DELAY * (2 ** attempt)
                print(f"⚠️ Batch {batch_num}: Attempt {attempt+1} failed, retrying in {wait_time}s...", flush=True)
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ Batch {batch_num}: Failed after {MAX_RETRIES} attempts: {e}", flush=True)
                return ""
    return ""


async def test_prompt(client, prompt_path: str, prompt_label: str, citations: List[str], ground_truth: Dict[int, bool]) -> Dict:
    """Test a single prompt against all citations"""
    print(f"\n{'='*60}", flush=True)
    print(f"Testing: {prompt_label}", flush=True)
    print(f"Prompt: {os.path.basename(prompt_path)}", flush=True)
    print(f"{'='*60}", flush=True)
    
    prompt_template = load_prompt(prompt_path)
    all_results = []
    total_batches = (len(citations) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_num, i in enumerate(range(0, len(citations), BATCH_SIZE), 1):
        batch_citations = citations[i:i+BATCH_SIZE]
        start_idx = i + 1
        
        print(f"\n🚀 Batch {batch_num}/{total_batches} (Citations {start_idx}-{start_idx + len(batch_citations) - 1})", flush=True)
        
        # Format and send
        formatted = format_citations_for_batch(batch_citations, start_idx)
        full_prompt = prompt_template + "\n\nCITATIONS TO VALIDATE:\n\n" + formatted
        
        response_text = await call_api_with_retry(client, full_prompt, batch_num)
        parsed = parse_response(response_text)
        
        print(f"   Parsed {len(parsed)} citations", flush=True)
        
        # Calculate batch accuracy
        batch_correct = 0
        for p in parsed:
            c_num = p["citation_number"]
            expected = ground_truth.get(c_num)
            actual = p["is_valid"]
            correct = actual == expected
            if correct:
                batch_correct += 1
            p["ground_truth"] = expected
            p["correct"] = correct
            all_results.append(p)
        
        batch_acc = (batch_correct / len(parsed)) * 100 if parsed else 0
        print(f"   Batch accuracy: {batch_acc:.1f}% ({batch_correct}/{len(parsed)})", flush=True)
        
        await asyncio.sleep(2)  # Rate limit pause
    
    # Calculate overall metrics
    correct_count = sum(1 for r in all_results if r.get("correct"))
    total = len(all_results)
    accuracy = (correct_count / total) * 100 if total else 0
    
    # Breakdown
    tp = sum(1 for r in all_results if r.get("ground_truth") == True and r.get("is_valid") == True)
    tn = sum(1 for r in all_results if r.get("ground_truth") == False and r.get("is_valid") == False)
    fp = sum(1 for r in all_results if r.get("ground_truth") == False and r.get("is_valid") == True)
    fn = sum(1 for r in all_results if r.get("ground_truth") == True and r.get("is_valid") == False)
    
    # Placeholder stats (for V3)
    placeholder_count = sum(1 for r in all_results if r.get("has_placeholder"))
    
    return {
        "prompt_label": prompt_label,
        "prompt_path": prompt_path,
        "accuracy": accuracy,
        "correct": correct_count,
        "total": total,
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "placeholder_count": placeholder_count,
        "results": all_results
    }


async def main():
    print("🧪 V3 Prompt Comparison Test - Production Config", flush=True)
    print(f"Model: {MODEL_NAME}", flush=True)
    print(f"Config: temp={TEMPERATURE}, thinking_budget={THINKING_BUDGET}, batch_size={BATCH_SIZE}", flush=True)
    print("="*60, flush=True)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found", flush=True)
        return
    
    client = new_genai.Client(api_key=api_key)
    data = load_data(DATASET_PATH)
    
    citations = [d['citation'] for d in data]
    ground_truth = {i+1: d['ground_truth'] for i, d in enumerate(data)}
    
    # Test both prompts
    v2_results = await test_prompt(client, PROMPT_V2_PATH, "V2 (Corrected)", citations, ground_truth)
    v3_results = await test_prompt(client, PROMPT_V3_PATH, "V3 (No Hallucination)", citations, ground_truth)
    
    # Summary
    print("\n" + "="*60, flush=True)
    print("📊 RESULTS SUMMARY", flush=True)
    print("="*60, flush=True)
    
    print(f"\n📌 V2 (Corrected):", flush=True)
    print(f"   Accuracy: {v2_results['accuracy']:.2f}% ({v2_results['correct']}/{v2_results['total']})", flush=True)
    print(f"   TP={v2_results['true_positives']}, TN={v2_results['true_negatives']}, FP={v2_results['false_positives']}, FN={v2_results['false_negatives']}", flush=True)
    print(f"   Placeholders: {v2_results['placeholder_count']}", flush=True)
    
    print(f"\n📌 V3 (No Hallucination):", flush=True)
    print(f"   Accuracy: {v3_results['accuracy']:.2f}% ({v3_results['correct']}/{v3_results['total']})", flush=True)
    print(f"   TP={v3_results['true_positives']}, TN={v3_results['true_negatives']}, FP={v3_results['false_positives']}, FN={v3_results['false_negatives']}", flush=True)
    print(f"   Placeholders: {v3_results['placeholder_count']}", flush=True)
    
    # Comparison
    diff = v3_results['accuracy'] - v2_results['accuracy']
    print(f"\n📈 Accuracy Change: {diff:+.2f}%", flush=True)
    
    fp_diff = v3_results['false_positives'] - v2_results['false_positives']
    print(f"📉 False Positive Change: {fp_diff:+d}", flush=True)
    
    # Pass/Fail
    print("\n" + "="*60, flush=True)
    if v3_results['accuracy'] >= v2_results['accuracy'] - 2:
        print("✅ PASS: V3 accuracy within 2% of V2", flush=True)
    else:
        print(f"❌ FAIL: V3 accuracy dropped by more than 2%", flush=True)
    
    if v3_results['placeholder_count'] > v2_results['placeholder_count']:
        print(f"✅ PASS: V3 uses more placeholders ({v3_results['placeholder_count']} vs {v2_results['placeholder_count']})", flush=True)
    else:
        print(f"⚠️ INFO: V3 placeholders: {v3_results['placeholder_count']}, V2: {v2_results['placeholder_count']}", flush=True)
    print("="*60, flush=True)
    
    # Save results
    output = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": MODEL_NAME,
            "config": f"temp={TEMPERATURE}, thinking_budget={THINKING_BUDGET}, batch_size={BATCH_SIZE}",
            "dataset": DATASET_PATH,
            "total_citations": len(citations)
        },
        "v2_metrics": {k: v for k, v in v2_results.items() if k != "results"},
        "v3_metrics": {k: v for k, v in v3_results.items() if k != "results"},
        "comparison": {
            "accuracy_diff": diff,
            "false_positive_diff": fp_diff,
            "placeholder_diff": v3_results['placeholder_count'] - v2_results['placeholder_count']
        },
        "v2_detailed": v2_results["results"],
        "v3_detailed": v3_results["results"]
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Results saved to {OUTPUT_FILE}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
