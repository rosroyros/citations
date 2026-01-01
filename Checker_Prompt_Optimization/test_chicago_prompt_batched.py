#!/usr/bin/env python3
"""
Chicago 17 Prompt Baseline Test - Production Configuration

Tests the Chicago 17 v1 prompt against the training set to establish baseline accuracy.
Uses exact production config: gemini-3-flash-preview, temp=0.0, thinking_budget=1024

Metrics calculated:
- Overall Accuracy: % correctly classified as valid/invalid
- Error Detection: % of expected errors found
- False Positives: % flagged errors that don't exist
- Correction Quality: % corrected citations that look reasonable

Launch Criteria:
- Ship if: Overall Accuracy >=80%
- Iterate if: 65-79% (manual optimization needed)
- Block if: <65% (consider algorithmic optimization)
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

# === PRODUCTION CONFIGURATION ===
MODEL_NAME = "gemini-3-flash-preview"
BATCH_SIZE = 5
TEMPERATURE = 0.0
THINKING_BUDGET = 1024
MAX_OUTPUT_TOKENS = 65536
MAX_RETRIES = 5
BASE_DELAY = 2
RATE_LIMIT_PAUSE = 30

# Paths
DATASET_PATH = os.path.join(PROJECT_ROOT, "Checker_Prompt_Optimization/chicago_train_set.jsonl")
PROMPT_PATH = os.path.join(PROJECT_ROOT, "backend/prompts/validator_prompt_chicago17_v1.2.txt")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "Checker_Prompt_Optimization/chicago_baseline_results.json")


def load_data(path: str) -> List[Dict[str, Any]]:
    print(f"Loading data from {path}", flush=True)
    data = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    print(f"Loaded {len(data)} citations", flush=True)
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
    """Parse response and extract citations - adapted for Chicago 17 output format"""
    results = []
    citation_pattern = r'(?:═+\s+)?CITATION #(\d+)\s*\n\s*═+(.+?)(?=(?:═+\s+)?CITATION #\d+|$)'
    matches = re.finditer(citation_pattern, response_text, re.DOTALL)

    for match in matches:
        citation_num = int(match.group(1))
        block_content = match.group(2)

        # Check for Chicago 17 valid marker
        is_valid = False
        if '✓ No Chicago 17 formatting errors detected' in block_content or 'No Chicago 17 formatting errors' in block_content:
            is_valid = True

        # Extract corrected citation for analysis
        corrected = None
        corrected_match = re.search(r'CORRECTED CITATION:\s*\n?(.*?)(?:\n─|$)', block_content, re.DOTALL)
        if corrected_match:
            corrected = corrected_match.group(1).strip()

        # Check for placeholders (indicates proper handling of missing data)
        has_placeholder = bool(re.search(r'\[MISSING:[^\]]+\]', corrected or ""))

        # Extract source type
        source_type = None
        source_match = re.search(r'SOURCE TYPE:\s*(.+)', block_content)
        if source_match:
            source_type = source_match.group(1).strip().lower()

        # Count number of errors found
        error_count = len(re.findall(r'❌', block_content))

        results.append({
            "citation_number": citation_num,
            "is_valid": is_valid,
            "corrected": corrected,
            "has_placeholder": has_placeholder,
            "source_type": source_type,
            "error_count": error_count
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
                print(f"Rate limit! Batch {batch_num}: Pausing {RATE_LIMIT_PAUSE}s...", flush=True)
                await asyncio.sleep(RATE_LIMIT_PAUSE)
                continue

            if attempt < MAX_RETRIES - 1:
                wait_time = BASE_DELAY * (2 ** attempt)
                print(f"Batch {batch_num}: Attempt {attempt+1} failed, retrying in {wait_time}s...", flush=True)
                await asyncio.sleep(wait_time)
            else:
                print(f"Batch {batch_num}: Failed after {MAX_RETRIES} attempts: {e}", flush=True)
                return ""
    return ""


async def test_prompt(client, prompt_path: str, citations: List[str], ground_truth: Dict[int, bool], original_data: List[Dict]) -> Dict:
    """Test the Chicago 17 prompt against all citations"""
    print(f"\n{'='*60}", flush=True)
    print(f"Testing: Chicago 17 v1 Prompt", flush=True)
    print(f"Prompt: {os.path.basename(prompt_path)}", flush=True)
    print(f"Citations: {len(citations)}", flush=True)
    print(f"{'='*60}", flush=True)

    prompt_template = load_prompt(prompt_path)
    all_results = []
    total_batches = (len(citations) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_num, i in enumerate(range(0, len(citations), BATCH_SIZE), 1):
        batch_citations = citations[i:i+BATCH_SIZE]
        start_idx = i + 1

        print(f"\nBatch {batch_num}/{total_batches} (Citations {start_idx}-{start_idx + len(batch_citations) - 1})", flush=True)

        # Format and send - note: prompt already ends with "CITATIONS TO VALIDATE:"
        formatted = format_citations_for_batch(batch_citations, start_idx)
        full_prompt = prompt_template + "\n\n" + formatted

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
            # Add original citation text for reference
            if c_num <= len(original_data):
                p["citation_text"] = original_data[c_num - 1]["citation"]
            all_results.append(p)

        batch_acc = (batch_correct / len(parsed)) * 100 if parsed else 0
        print(f"   Batch accuracy: {batch_acc:.1f}% ({batch_correct}/{len(parsed)})", flush=True)

        # Show misclassifications
        for p in parsed:
            if not p.get("correct"):
                expected_str = "valid" if p.get("ground_truth") else "invalid"
                actual_str = "valid" if p.get("is_valid") else "invalid"
                print(f"   #{p['citation_number']}: expected {expected_str}, got {actual_str}", flush=True)

        await asyncio.sleep(2)  # Rate limit pause

    # Calculate overall metrics
    correct_count = sum(1 for r in all_results if r.get("correct"))
    total = len(all_results)
    accuracy = (correct_count / total) * 100 if total else 0

    # Confusion matrix
    tp = sum(1 for r in all_results if r.get("ground_truth") == True and r.get("is_valid") == True)
    tn = sum(1 for r in all_results if r.get("ground_truth") == False and r.get("is_valid") == False)
    fp = sum(1 for r in all_results if r.get("ground_truth") == False and r.get("is_valid") == True)  # Invalid marked valid
    fn = sum(1 for r in all_results if r.get("ground_truth") == True and r.get("is_valid") == False)  # Valid marked invalid

    # Precision, Recall, F1
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Placeholder stats
    placeholder_count = sum(1 for r in all_results if r.get("has_placeholder"))

    # Source type breakdown
    source_types = {}
    for r in all_results:
        st = r.get("source_type") or "unknown"
        if st not in source_types:
            source_types[st] = {"correct": 0, "total": 0}
        source_types[st]["total"] += 1
        if r.get("correct"):
            source_types[st]["correct"] += 1

    return {
        "prompt_path": prompt_path,
        "accuracy": accuracy,
        "correct": correct_count,
        "total": total,
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "placeholder_count": placeholder_count,
        "source_type_breakdown": source_types,
        "results": all_results
    }


def analyze_failures(results: List[Dict]) -> Dict:
    """Analyze failure patterns for insights"""
    failures = [r for r in results if not r.get("correct")]

    # Group by error type
    false_positives = [r for r in failures if r.get("ground_truth") == False and r.get("is_valid") == True]
    false_negatives = [r for r in failures if r.get("ground_truth") == True and r.get("is_valid") == False]

    return {
        "total_failures": len(failures),
        "false_positives": {
            "count": len(false_positives),
            "description": "Invalid citations marked as valid (missed errors)",
            "examples": [{"num": r["citation_number"], "citation": r.get("citation_text", "")[:100]}
                        for r in false_positives[:5]]
        },
        "false_negatives": {
            "count": len(false_negatives),
            "description": "Valid citations marked as invalid (phantom errors)",
            "examples": [{"num": r["citation_number"], "citation": r.get("citation_text", "")[:100]}
                        for r in false_negatives[:5]]
        }
    }


async def main():
    print("Chicago 17 Prompt Baseline Test - Production Config", flush=True)
    print(f"Model: {MODEL_NAME}", flush=True)
    print(f"Config: temp={TEMPERATURE}, thinking_budget={THINKING_BUDGET}, batch_size={BATCH_SIZE}", flush=True)
    print("="*60, flush=True)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found", flush=True)
        return

    client = new_genai.Client(api_key=api_key)
    data = load_data(DATASET_PATH)

    citations = [d['citation'] for d in data]
    ground_truth = {i+1: d['ground_truth'] for i, d in enumerate(data)}

    # Count expected valid/invalid
    expected_valid = sum(1 for d in data if d['ground_truth'])
    expected_invalid = sum(1 for d in data if not d['ground_truth'])
    print(f"Expected: {expected_valid} valid, {expected_invalid} invalid", flush=True)

    # Run test
    results = await test_prompt(client, PROMPT_PATH, citations, ground_truth, data)

    # Analyze failures
    failure_analysis = analyze_failures(results["results"])

    # Summary
    print("\n" + "="*60, flush=True)
    print("CHICAGO 17 BASELINE RESULTS", flush=True)
    print("="*60, flush=True)

    print(f"\nOverall Accuracy: {results['accuracy']:.2f}% ({results['correct']}/{results['total']})", flush=True)

    print(f"\nConfusion Matrix:", flush=True)
    print(f"   TP (Valid->Valid):     {results['true_positives']}", flush=True)
    print(f"   TN (Invalid->Invalid): {results['true_negatives']}", flush=True)
    print(f"   FP (Invalid->Valid):   {results['false_positives']} <- Missed errors", flush=True)
    print(f"   FN (Valid->Invalid):   {results['false_negatives']} <- Phantom errors", flush=True)

    print(f"\nAdditional Metrics:", flush=True)
    print(f"   Precision: {results['precision']:.2f}%", flush=True)
    print(f"   Recall: {results['recall']:.2f}%", flush=True)
    print(f"   F1 Score: {results['f1_score']:.2f}%", flush=True)
    print(f"   Placeholders used: {results['placeholder_count']}", flush=True)

    # Source type breakdown
    if results.get("source_type_breakdown"):
        print(f"\nAccuracy by Source Type:", flush=True)
        for st, stats in sorted(results["source_type_breakdown"].items()):
            st_acc = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   {st}: {st_acc:.1f}% ({stats['correct']}/{stats['total']})", flush=True)

    # Launch criteria evaluation
    print("\n" + "="*60, flush=True)
    print("LAUNCH CRITERIA EVALUATION", flush=True)
    print("="*60, flush=True)

    accuracy = results['accuracy']
    if accuracy >= 80:
        print(f"SHIP: Accuracy {accuracy:.1f}% >= 80% threshold", flush=True)
        recommendation = "ship"
    elif accuracy >= 65:
        print(f"ITERATE: Accuracy {accuracy:.1f}% in 65-79% range", flush=True)
        print("   Manual prompt optimization recommended", flush=True)
        recommendation = "iterate"
    else:
        print(f"BLOCK: Accuracy {accuracy:.1f}% < 65% threshold", flush=True)
        print("   Consider algorithmic optimization or training data review", flush=True)
        recommendation = "block"

    # Failure insights
    if failure_analysis["total_failures"] > 0:
        print(f"\nFailure Analysis ({failure_analysis['total_failures']} failures):", flush=True)

        if failure_analysis["false_positives"]["count"] > 0:
            print(f"\n   False Positives ({failure_analysis['false_positives']['count']}):", flush=True)
            print(f"   {failure_analysis['false_positives']['description']}", flush=True)
            for ex in failure_analysis["false_positives"]["examples"][:3]:
                print(f"      #{ex['num']}: {ex['citation'][:80]}...", flush=True)

        if failure_analysis["false_negatives"]["count"] > 0:
            print(f"\n   False Negatives ({failure_analysis['false_negatives']['count']}):", flush=True)
            print(f"   {failure_analysis['false_negatives']['description']}", flush=True)
            for ex in failure_analysis["false_negatives"]["examples"][:3]:
                print(f"      #{ex['num']}: {ex['citation'][:80]}...", flush=True)

    print("="*60, flush=True)

    # Save results
    output = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": MODEL_NAME,
            "config": f"temp={TEMPERATURE}, thinking_budget={THINKING_BUDGET}, batch_size={BATCH_SIZE}",
            "dataset": DATASET_PATH,
            "prompt": PROMPT_PATH,
            "total_citations": len(citations),
            "expected_valid": expected_valid,
            "expected_invalid": expected_invalid
        },
        "metrics": {k: v for k, v in results.items() if k != "results"},
        "launch_recommendation": recommendation,
        "failure_analysis": failure_analysis,
        "detailed_results": results["results"]
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {OUTPUT_FILE}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
