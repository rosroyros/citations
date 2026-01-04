#!/usr/bin/env python3
"""
Test runner for inline citation validation prompts.

Usage:
    python3 test_inline_prompt.py --style apa --set train
    python3 test_inline_prompt.py --style mla --set holdout
    python3 test_inline_prompt.py --style apa --set train --verbose

Exit codes:
    0: Accuracy >= 80% threshold (PASS)
    1: Accuracy < 80% threshold (FAIL)
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from google import genai as new_genai
from google.genai import types

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Get project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, "backend/.env"))

# === PRODUCTION CONFIGURATION ===
MODEL_NAME = "gemini-3-flash-preview"
TEMPERATURE = 0.0
THINKING_BUDGET = 1024
MAX_OUTPUT_TOKENS = 65536
MAX_RETRIES = 5
BASE_DELAY = 2
RATE_LIMIT_PAUSE = 30
ACCURACY_THRESHOLD = 0.80


def load_golden_set(style: str, set_type: str) -> List[Dict]:
    """Load JSONL golden set file."""
    # Normalize style name: "apa7" -> "apa", "mla9" -> "mla"
    style_short = style.replace("7", "").replace("9", "")
    filename = f"inline_{style_short}_{set_type}.jsonl"
    path = Path(__file__).parent / filename

    if not path.exists():
        print(f"❌ Golden set file not found: {path}", flush=True)
        sys.exit(1)

    data = []
    with open(path) as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    print(f"📂 Loaded {len(data)} test cases from {filename}", flush=True)
    return data


def load_prompt(style: str) -> str:
    """Load inline validation prompt."""
    style_short = style.replace("7", "").replace("9", "")
    filename = f"validator_prompt_inline_{style_short}.txt"
    path = Path(PROJECT_ROOT) / "backend" / "prompts" / filename

    if not path.exists():
        print(f"❌ Prompt file not found: {path}", flush=True)
        sys.exit(1)

    with open(path) as f:
        return f.read()


def categorize_case(case: Dict) -> str:
    """Categorize test case by expected error type."""
    expected = case.get("expected", {})
    match_status = expected.get("match_status", "matched")
    errors = expected.get("errors", [])

    if match_status == "not_found":
        return "not_found"
    elif match_status == "mismatch":
        if errors:
            error_desc = errors[0].lower()
            if "year" in error_desc:
                return "year_mismatch"
            elif "author" in error_desc or "spelling" in error_desc:
                return "author_spelling"
            elif "et al" in error_desc:
                return "et_al_usage"
        return "mismatch_other"
    elif match_status == "matched":
        # Check for narrative citations
        if case.get("inline_citation", "") and not case["inline_citation"].startswith("("):
            return "narrative_citation"
        # Check for multi-citation
        if ";" in case.get("inline_citation", ""):
            return "multi_citation"
        return "perfect_match"
    else:
        return "other"


async def call_api_with_retry(client, full_prompt: str, case_num: int) -> Optional[str]:
    """Call API with retry logic."""
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
                print(f"  🛑 Case {case_num}: Rate limit! Pausing {RATE_LIMIT_PAUSE}s...", flush=True)
                await asyncio.sleep(RATE_LIMIT_PAUSE)
                continue

            if attempt < MAX_RETRIES - 1:
                wait_time = BASE_DELAY * (2 ** attempt)
                print(f"  ⚠️ Case {case_num}: Attempt {attempt+1} failed, retrying in {wait_time}s...", flush=True)
                await asyncio.sleep(wait_time)
            else:
                print(f"  ❌ Case {case_num}: Failed after {MAX_RETRIES} attempts: {e}", flush=True)
                return None
    return None


def parse_llm_response(response_text: str) -> Optional[Dict]:
    """Parse LLM JSON response."""
    if not response_text:
        return None

    # Try to extract JSON from response
    json_match = re.search(r'\{[^{}]*"results"[^{}]*\[[^\]]*\][^{}]*\}', response_text, re.DOTALL)
    if not json_match:
        # Fallback: look for any JSON object
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            # If we have a "results" key with array, get first result
            if "results" in parsed and isinstance(parsed["results"], list) and len(parsed["results"]) > 0:
                return parsed["results"][0]
            # Otherwise return the parsed object directly
            return parsed
        except json.JSONDecodeError:
            pass

    return None


def evaluate_result(expected: Dict, actual: Optional[Dict]) -> bool:
    """Check if actual matches expected."""
    if actual is None:
        return False

    # Primary check: match_status
    expected_status = expected.get("match_status")
    actual_status = actual.get("match_status")

    if expected_status != actual_status:
        return False

    # For matched/mismatch, check matched_ref_index
    if expected_status in ("matched", "mismatch"):
        expected_index = expected.get("matched_ref_index")
        actual_index = actual.get("matched_ref_index")

        if expected_index != actual_index:
            return False

    # For multi-citations, check matches array
    if expected.get("matches"):
        expected_matches = sorted([m.get("ref_index") for m in expected.get("matches", [])])
        actual_matches = sorted([m.get("ref_index") for m in actual.get("matches", [])])

        if expected_matches != actual_matches:
            return False

    return True


async def run_single_test(client, case: Dict, prompt_template: str, case_num: int) -> Dict:
    """Run prompt against a single test case."""
    inline_citation = case["inline_citation"]
    ref_list = case["ref_list"]
    expected = case["expected"]

    # Format prompt
    ref_list_formatted = "\n".join([f"{i+1}. {ref}" for i, ref in enumerate(ref_list)])
    inline_formatted = f'{{"id": "c1", "citation": "{inline_citation}"}}'

    full_prompt = prompt_template.replace("{reference_list}", ref_list_formatted)
    full_prompt = full_prompt.replace("{inline_citations}", inline_formatted)

    # Call API
    response_text = await call_api_with_retry(client, full_prompt, case_num)

    # Parse response
    actual = parse_llm_response(response_text)

    # Evaluate
    is_correct = evaluate_result(expected, actual)

    return {
        "case_num": case_num,
        "inline_citation": inline_citation,
        "expected": expected,
        "actual": actual,
        "is_correct": is_correct,
        "response_raw": response_text[:500] if response_text else None  # Truncate for storage
    }


async def run_prompt_test(
    test_cases: List[Dict],
    style: str,
    provider,
    verbose: bool = False
) -> Dict[str, Any]:
    """Run prompt against test cases and collect results."""
    print(f"\n{'='*60}", flush=True)
    print(f"Testing: Inline {style.upper()} Validation Prompt", flush=True)
    print(f"{'='*60}", flush=True)

    prompt_template = load_prompt(style)

    results = {
        "total": len(test_cases),
        "correct": 0,
        "by_category": {},
        "failures": []
    }

    for i, case in enumerate(test_cases, 1):
        result = await run_single_test(provider, case, prompt_template, i)

        if result["is_correct"]:
            results["correct"] += 1
            if verbose:
                print(f"  ✓ Case {i}: {result['inline_citation'][:40]}...", flush=True)
        else:
            results["failures"].append(result)
            print(f"  ✗ Case {i}: {result['inline_citation'][:40]}...", flush=True)
            if verbose and result["actual"]:
                print(f"    Expected: {result['expected'].get('match_status')}", flush=True)
                print(f"    Actual: {result['actual'].get('match_status')}", flush=True)

        # Track by category
        category = categorize_case(case)
        if category not in results["by_category"]:
            results["by_category"][category] = {"total": 0, "correct": 0}
        results["by_category"][category]["total"] += 1
        if result["is_correct"]:
            results["by_category"][category]["correct"] += 1

        # Rate limit pause
        await asyncio.sleep(1)

    return results


def calculate_metrics(results: Dict) -> Dict[str, Any]:
    """Calculate accuracy, precision, recall, F1."""
    accuracy = results["correct"] / results["total"] if results["total"] > 0 else 0

    # Calculate per-category metrics
    category_metrics = {}
    for cat, data in results["by_category"].items():
        acc = data["correct"] / data["total"] if data["total"] > 0 else 0
        category_metrics[cat] = {"accuracy": acc, "total": data["total"], "correct": data["correct"]}

    return {
        "overall_accuracy": accuracy,
        "correct": results["correct"],
        "total": results["total"],
        "by_category": category_metrics
    }


def print_report(results: Dict, metrics: Dict, verbose: bool = False):
    """Print formatted test report."""
    print(f"\n{'='*60}", flush=True)
    print(f"INLINE VALIDATION PROMPT TEST RESULTS", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"\nOverall Accuracy: {metrics['overall_accuracy']:.1%} ({metrics['correct']}/{metrics['total']})", flush=True)

    print(f"\nBy Category:", flush=True)
    for cat, data in sorted(metrics["by_category"].items(), key=lambda x: x[1]["accuracy"]):
        status = "✓" if data["accuracy"] >= 0.8 else "✗"
        print(f"  {status} {cat}: {data['accuracy']:.1%} ({data['correct']}/{data['total']} cases)", flush=True)

    if verbose and results["failures"]:
        print(f"\nFailures ({len(results['failures'])}):", flush=True)
        for f in results["failures"][:10]:  # Limit to first 10
            print(f"  - Case {f['case_num']}: {f['inline_citation'][:50]}...", flush=True)
            if f['expected']:
                print(f"    Expected: {f['expected'].get('match_status')}", flush=True)
            if f['actual']:
                print(f"    Actual: {f['actual'].get('match_status')}", flush=True)
            else:
                print(f"    Actual: [parse failed]", flush=True)


async def main():
    parser = argparse.ArgumentParser(
        description="Test inline citation validation prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_inline_prompt.py --style apa --set train
  python3 test_inline_prompt.py --style mla --set holdout --verbose
        """
    )
    parser.add_argument("--style", choices=["apa", "apa7", "mla", "mla9"], required=True,
                        help="Citation style (apa or mla)")
    parser.add_argument("--set", choices=["train", "holdout"], default="train",
                        help="Which golden set to use (default: train)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed output including failures")
    args = parser.parse_args()

    # Normalize style name
    style = args.style.lower()

    print(f"\n🧪 Inline Validation Prompt Test", flush=True)
    print(f"Style: {style.upper()}", flush=True)
    print(f"Set: {args.set}", flush=True)
    print(f"Model: {MODEL_NAME}", flush=True)
    print(f"Threshold: {ACCURACY_THRESHOLD:.0%}", flush=True)

    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment", flush=True)
        sys.exit(1)

    client = new_genai.Client(api_key=api_key)

    # Load test cases
    cases = load_golden_set(style, args.set)

    # Run tests
    results = await run_prompt_test(cases, style, client, args.verbose)
    metrics = calculate_metrics(results)

    # Print report
    print_report(results, metrics, args.verbose)

    # Exit with error if below threshold
    print("\n" + "="*60, flush=True)
    if metrics["overall_accuracy"] < ACCURACY_THRESHOLD:
        print(f"❌ FAIL: Accuracy {metrics['overall_accuracy']:.1%} < {ACCURACY_THRESHOLD:.0%} threshold", flush=True)
        sys.exit(1)
    else:
        print(f"✓ PASS: Accuracy {metrics['overall_accuracy']:.1%} >= {ACCURACY_THRESHOLD:.0%} threshold", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
