#!/usr/bin/env python3
"""
MLA 9 Holdout Validation - Final check before shipping

Tests the MLA v1.1 prompt against the holdout set to ensure
we haven't overfit to the training data.
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

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, "backend/.env"))

# Production config
MODEL_NAME = "gemini-3-flash-preview"
BATCH_SIZE = 5
TEMPERATURE = 0.0
THINKING_BUDGET = 1024
MAX_OUTPUT_TOKENS = 65536
MAX_RETRIES = 5
BASE_DELAY = 2
RATE_LIMIT_PAUSE = 30

# Paths - using HOLDOUT set
DATASET_PATH = os.path.join(PROJECT_ROOT, "Checker_Prompt_Optimization/mla9_holdout_set.jsonl")
PROMPT_PATH = os.path.join(PROJECT_ROOT, "backend/prompts/validator_prompt_mla9_v1.1.txt")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "Checker_Prompt_Optimization/mla9_holdout_validation_results.json")


def load_data(path: str) -> List[Dict[str, Any]]:
    print(f"📂 Loading HOLDOUT data from {path}", flush=True)
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
    formatted = []
    for i, citation in enumerate(citations, start_idx):
        formatted.append(f"CITATION TO VALIDATE {i}: {citation}")
    return "\n\n".join(formatted)


def parse_response(response_text: str) -> List[Dict[str, Any]]:
    results = []
    citation_pattern = r'(?:═+\s+)?CITATION #(\d+)\s*\n\s*═+(.+?)(?=(?:═+\s+)?CITATION #\d+|$)'
    matches = re.finditer(citation_pattern, response_text, re.DOTALL)

    for match in matches:
        citation_num = int(match.group(1))
        block_content = match.group(2)

        is_valid = False
        if '✓ No MLA 9 formatting errors detected' in block_content or 'No MLA 9 formatting errors' in block_content:
            is_valid = True

        corrected = None
        corrected_match = re.search(r'CORRECTED CITATION:\s*\n?(.*?)(?:\n─|$)', block_content, re.DOTALL)
        if corrected_match:
            corrected = corrected_match.group(1).strip()

        has_placeholder = bool(re.search(r'\[MISSING:[^\]]+\]', corrected or ""))
        
        results.append({
            "citation_number": citation_num,
            "is_valid": is_valid,
            "corrected": corrected,
            "has_placeholder": has_placeholder
        })
    return results


async def call_api_with_retry(client, full_prompt: str, batch_num: int) -> str:
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


async def main():
    print("🧪 MLA 9 HOLDOUT VALIDATION - Final Check", flush=True)
    print(f"Model: {MODEL_NAME}", flush=True)
    print(f"Prompt: validator_prompt_mla9_v1.1.txt", flush=True)
    print("="*60, flush=True)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found", flush=True)
        return
    
    client = new_genai.Client(api_key=api_key)
    data = load_data(DATASET_PATH)
    prompt_template = load_prompt(PROMPT_PATH)
    
    citations = [d['citation'] for d in data]
    ground_truth = {i+1: d['ground_truth'] for i, d in enumerate(data)}
    
    all_results = []
    total_batches = (len(citations) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_num, i in enumerate(range(0, len(citations), BATCH_SIZE), 1):
        batch_citations = citations[i:i+BATCH_SIZE]
        start_idx = i + 1
        
        print(f"🚀 Batch {batch_num}/{total_batches} (Citations {start_idx}-{start_idx + len(batch_citations) - 1})", flush=True)
        
        formatted = format_citations_for_batch(batch_citations, start_idx)
        full_prompt = prompt_template + "\n\n" + formatted
        
        response_text = await call_api_with_retry(client, full_prompt, batch_num)
        parsed = parse_response(response_text)
        
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
        print(f"   Accuracy: {batch_acc:.0f}% ({batch_correct}/{len(parsed)})", flush=True)
        
        await asyncio.sleep(2)
    
    # Calculate metrics
    correct_count = sum(1 for r in all_results if r.get("correct"))
    total = len(all_results)
    accuracy = (correct_count / total) * 100 if total else 0
    
    tp = sum(1 for r in all_results if r.get("ground_truth") == True and r.get("is_valid") == True)
    tn = sum(1 for r in all_results if r.get("ground_truth") == False and r.get("is_valid") == False)
    fp = sum(1 for r in all_results if r.get("ground_truth") == False and r.get("is_valid") == True)
    fn = sum(1 for r in all_results if r.get("ground_truth") == True and r.get("is_valid") == False)
    
    placeholder_count = sum(1 for r in all_results if r.get("has_placeholder"))
    
    # Results
    print("\n" + "="*60, flush=True)
    print("📊 HOLDOUT VALIDATION RESULTS", flush=True)
    print("="*60, flush=True)
    print(f"\n📌 Accuracy: {accuracy:.2f}% ({correct_count}/{total})", flush=True)
    print(f"   TP={tp}, TN={tn}, FP={fp}, FN={fn}", flush=True)
    print(f"   Placeholders: {placeholder_count}", flush=True)
    
    # Compare to training set performance
    print(f"\n📈 Training Set: 83.93% (94/112)", flush=True)
    print(f"📈 Holdout Set:  {accuracy:.2f}% ({correct_count}/{total})", flush=True)
    
    diff = accuracy - 83.93
    if abs(diff) <= 5:
        print(f"\n✅ PASS: Holdout within 5% of training ({diff:+.2f}%) - No overfitting detected", flush=True)
    elif diff < -5:
        print(f"\n⚠️ WARNING: Holdout {abs(diff):.1f}% lower than training - Possible overfitting", flush=True)
    else:
        print(f"\n✅ PASS: Holdout actually higher than training! ({diff:+.2f}%)", flush=True)
    
    # Final recommendation
    print("\n" + "="*60, flush=True)
    if accuracy >= 80:
        print(f"✅ SHIP: Holdout accuracy {accuracy:.1f}% ≥ 80% threshold", flush=True)
    else:
        print(f"❌ FAIL: Holdout accuracy {accuracy:.1f}% < 80% threshold", flush=True)
    print("="*60, flush=True)
    
    # Save results
    output = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": MODEL_NAME,
            "prompt": "validator_prompt_mla9_v1.1.txt",
            "dataset": "mla9_holdout_set.jsonl",
            "total_citations": len(citations)
        },
        "metrics": {
            "accuracy": accuracy,
            "correct": correct_count,
            "total": total,
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "placeholder_count": placeholder_count
        },
        "comparison": {
            "training_accuracy": 83.93,
            "holdout_accuracy": accuracy,
            "difference": diff
        },
        "detailed_results": all_results
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Results saved to {OUTPUT_FILE}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
