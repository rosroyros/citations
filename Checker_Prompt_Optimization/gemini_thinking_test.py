import os
import json
import asyncio
import re
import time
import sys
from typing import List, Dict, Any
import google.generativeai as genai
try:
    from google import genai as new_genai
    from google.genai import types
    NEW_API_AVAILABLE = True
except ImportError:
    NEW_API_AVAILABLE = False
from pathlib import Path
from dotenv import load_dotenv

# Force unbuffered output for background process
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load environment variables
load_dotenv("backend/.env")

# Configuration - Only test 2.5-flash and 2.5-pro with thinking disabled
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro"
]
DATASET_PATH = "Checker_Prompt_Optimization/test_set_121_corrected.jsonl"
PROMPT_PATH = "backend/prompts/validator_prompt_optimized.txt"
OUTPUT_FILE = "Checker_Prompt_Optimization/gemini_no_thinking_results.json"

# Test configuration
BATCH_SIZE = 5
MAX_RETRIES = 3
RETRY_DELAY = 2
TEST_LIMIT = 121  # Full test

async def load_data(path: str, limit: int = None) -> List[Dict[str, Any]]:
    print(f"📂 Loading data from {path}", flush=True)
    data = []
    with open(path, 'r') as f:
        for i, line in enumerate(f, 1):
            if line.strip():
                try:
                    data.append(json.loads(line))
                    if limit and len(data) >= limit:
                        break
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing line {i}: {e}", flush=True)
                    continue

    print(f"✅ Loaded {len(data)} citations", flush=True)
    return data

def load_prompt(path: str) -> str:
    print(f"📄 Loading prompt from {path}", flush=True)
    with open(path, 'r') as f:
        return f.read()

def format_citations(citations: List[str], start_index: int = 1) -> str:
    """Format citations with continuous numbering across batches"""
    formatted = []
    for i, citation in enumerate(citations, start_index):
        formatted.append(f"{i}. {citation}")
    return "\n\n".join(formatted)

def parse_response(response_text: str) -> List[Dict[str, Any]]:
    """Enhanced parser based on OpenAIProvider logic."""
    results = []
    citation_pattern = r'(?:═+\s+)?CITATION #(\d+)\s*\n\s*═+(.+?)(?=(?:═+\s+)?CITATION #\d+|$)'
    matches = re.finditer(citation_pattern, response_text, re.DOTALL)

    for match in matches:
        citation_num = int(match.group(1))
        block_content = match.group(2)

        is_valid = False
        if '✓ No APA 7 formatting errors detected' in block_content or 'No APA 7 formatting errors' in block_content:
            is_valid = True

        results.append({
            "citation_number": citation_num,
            "is_valid": is_valid,
            "raw_block": block_content[:200] + "..." if len(block_content) > 200 else block_content
        })
    return results

async def retry_gemini_call(api_call, *args, **kwargs):
    """Retry logic with exponential backoff for Gemini API (async)"""
    for attempt in range(MAX_RETRIES):
        try:
            return await api_call(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            # Check for retryable errors
            if any(keyword in error_str for keyword in ['rate limit', 'timeout', 'overloaded', 'try again']):
                if attempt == MAX_RETRIES - 1:
                    print(f"❌ Final attempt failed: {type(e).__name__}: {str(e)[:100]}...", flush=True)
                    raise
                wait_time = RETRY_DELAY * (2 ** attempt)
                print(f"⚠️  Attempt {attempt + 1} failed ({type(e).__name__}), retrying in {wait_time}s...", flush=True)
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ Non-retryable error: {type(e).__name__}: {str(e)[:100]}...", flush=True)
                raise

def retry_gemini_call_sync(api_call, *args, **kwargs):
    """Retry logic with exponential backoff for Gemini API (sync)"""
    for attempt in range(MAX_RETRIES):
        try:
            return api_call(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            # Check for retryable errors
            if any(keyword in error_str for keyword in ['rate limit', 'timeout', 'overloaded', 'try again']):
                if attempt == MAX_RETRIES - 1:
                    print(f"❌ Final attempt failed: {type(e).__name__}: {str(e)[:100]}...", flush=True)
                    raise
                wait_time = RETRY_DELAY * (2 ** attempt)
                print(f"⚠️  Attempt {attempt + 1} failed ({type(e).__name__}), retrying in {wait_time}s...", flush=True)
                time.sleep(wait_time)
            else:
                print(f"❌ Non-retryable error: {type(e).__name__}: {str(e)[:100]}...", flush=True)
                raise

def test_gemini_model_no_thinking(model_name: str, prompt_template: str, citations: List[str], start_idx: int):
    """Test Gemini model with thinking disabled using new API when available"""
    print(f"🚀 Testing {model_name} (NO THINKING) - Citations {start_idx}-{start_idx + len(citations) - 1}", flush=True)

    full_prompt = prompt_template + "\n\n" + format_citations(citations, start_idx)

    try:
        if NEW_API_AVAILABLE and "2.5" in model_name:
            # Use new API with thinking disabled
            client = new_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            # Special handling for 2.5-pro (thinking-only model)
            if model_name == "gemini-2.5-pro":
                # 2.5-pro only works in thinking mode, minimum is 128
                config = types.GenerateContentConfig(
                    temperature=1.0,
                    max_output_tokens=10000,
                    thinking_config=types.ThinkingConfig(thinking_budget=128)  # Minimum valid thinking
                )
                print(f"🧠 {model_name}: Using minimum thinking budget=128 (required for this model)", flush=True)
            else:
                # 2.5-flash can work without thinking
                config = types.GenerateContentConfig(
                    temperature=1.0,
                    max_output_tokens=10000,
                    thinking_config=types.ThinkingConfig(thinking_budget=0)  # Disable thinking
                )
                print(f"🧠 {model_name}: Thinking disabled", flush=True)

            response = retry_gemini_call_sync(
                client.models.generate_content,
                model=model_name,
                contents=full_prompt,
                config=config
            )
            return response.text
        else:
            # Fallback to old API (for non-2.5 models or if new API not available)
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel(model_name)

            generation_config = {
                "temperature": 1.0,
                "max_output_tokens": 10000,
            }

            response = retry_gemini_call_sync(
                model.generate_content,
                full_prompt,
                generation_config=generation_config
            )
            return response.text
    except Exception as e:
        print(f"❌ {model_name} failed: {e}", flush=True)
        return ""

async def process_single_batch(prompt_template: str, batch_citations: List[str], start_idx: int, batch_num: int, total_batches: int):
    """Process a single batch across 2 Gemini models (no thinking)"""
    print(f"\n🚀 Processing Batch {batch_num}/{total_batches} (Citations {start_idx}-{start_idx + len(batch_citations) - 1}) - NO THINKING", flush=True)

    # Run 2 models sequentially (new API is sync, not async)
    start_time = time.time()

    results = []
    for model_name in MODELS:
        result = test_gemini_model_no_thinking(model_name, prompt_template, batch_citations, start_idx)
        results.append(result)

    batch_time = time.time() - start_time

    # Process results
    batch_outputs = {}

    for i, (model_name, result) in enumerate(zip(MODELS, results)):
        if isinstance(result, Exception):
            print(f"❌ {model_name} failed with exception: {result}", flush=True)
            batch_outputs[model_name] = ""
        else:
            batch_outputs[model_name] = result or ""
            if result:
                parsed_count = len(parse_response(result))
                print(f"✅ {model_name}: {parsed_count} citations parsed in {batch_time:.1f}s", flush=True)
            else:
                print(f"⚠️  {model_name}: No response", flush=True)

    return batch_outputs

async def run_test(limit: int = TEST_LIMIT):
    """Main test function - compare with vs without thinking"""
    print("🎯 Gemini Models Test - NO THINKING (thinkingBudget: -1)", flush=True)
    print("=" * 60, flush=True)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found.", flush=True)
        return

    print(f"✅ Gemini API key found", flush=True)
    print(f"🤖 Testing {len(MODELS)} models with NO THINKING: {', '.join(MODELS)}", flush=True)

    data = await load_data(DATASET_PATH, limit)
    prompt_template = load_prompt(PROMPT_PATH)

    citations = [d['citation'] for d in data]
    ground_truth = {i+1: d['ground_truth'] for i, d in enumerate(data)}

    print(f"📊 Testing {len(citations)} citations with thinking disabled", flush=True)
    print(f"📦 Batch size: {BATCH_SIZE} | Total batches: {(len(citations) + BATCH_SIZE - 1) // BATCH_SIZE}", flush=True)
    print(f"🔄 Retries: {MAX_RETRIES} with exponential backoff", flush=True)
    print(f"🧠 THINKING: DISABLED (thinkingBudget: -1)", flush=True)

    results = {
        "metadata": {
            "total_citations": len(citations),
            "batch_size": BATCH_SIZE,
            "max_retries": MAX_RETRIES,
            "models_tested": MODELS,
            "test_type": "gemini_no_thinking",
            "thinking_budget": -1,
            "real_time_tracking": True
        },
    }

    # Initialize results for each model
    for model_name in MODELS:
        results[model_name] = {"parsed": [], "response_text": "", "batch_times": []}

    # Process all batches
    total_batches = (len(citations) + BATCH_SIZE - 1) // BATCH_SIZE
    start_time = time.time()

    for batch_num, i in enumerate(range(0, len(citations), BATCH_SIZE), 1):
        batch_citations = citations[i:i+BATCH_SIZE]
        start_idx = i + 1  # Citation numbers are 1-based

        print(f"\n📍 Starting batch {batch_num}/{total_batches} at {time.strftime('%H:%M:%S')}", flush=True)

        batch_outputs = await process_single_batch(
            prompt_template, batch_citations, start_idx, batch_num, total_batches
        )

        # Parse and aggregate results
        for model_name in MODELS:
            response_text = batch_outputs[model_name]
            results[model_name]["response_text"] += response_text + "\n\n"

            if response_text:
                parsed = parse_response(response_text)
                results[model_name]["parsed"].extend(parsed)

                # Log progress for this batch
                correct_count = sum(1 for p in parsed
                                  if p['citation_number'] in ground_truth
                                  and p['is_valid'] == ground_truth[p['citation_number']])

                batch_accuracy = (correct_count / len(parsed)) * 100 if parsed else 0
                total_correct = sum(1 for p in results[model_name]["parsed"]
                                  if p['citation_number'] in ground_truth
                                  and p['is_valid'] == ground_truth[p['citation_number']])
                total_accuracy = (total_correct / len(results[model_name]["parsed"])) * 100 if results[model_name]["parsed"] else 0

                print(f"📈 {model_name}: {correct_count}/{len(parsed)} correct this batch ({batch_accuracy:.1f}%) | {total_correct}/{len(results[model_name]['parsed'])} total ({total_accuracy:.1f}%)", flush=True)

        # Overall progress
        elapsed = time.time() - start_time
        citations_processed = (batch_num * BATCH_SIZE)
        avg_time_per_citation = elapsed / citations_processed if citations_processed > 0 else 0
        estimated_total = avg_time_per_citation * len(citations)
        eta = estimated_total - elapsed

        print(f"⏱️  Progress: {batch_num}/{total_batches} batches | {citations_processed}/{len(citations)} citations ({(citations_processed/len(citations)*100):.1f}%) | ETA: {eta/60:.1f}min", flush=True)

    total_time = time.time() - start_time
    print(f"\n⏱️  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)", flush=True)

    # Calculate final metrics
    print(f"\n📊 FINAL RESULTS (NO THINKING)", flush=True)
    print("=" * 60, flush=True)

    for model_name in MODELS:
        parsed = results[model_name]["parsed"]
        response_text = results[model_name]["response_text"]

        correct_count = 0
        parsed_count = len(parsed)
        details = []

        for p in parsed:
            num = p['citation_number']
            if num in ground_truth:
                is_correct = p['is_valid'] == ground_truth[num]
                if is_correct:
                    correct_count += 1
                details.append({
                    "citation_number": num,
                    "predicted": p['is_valid'],
                    "ground_truth": ground_truth[num],
                    "correct": is_correct
                })

        accuracy = (correct_count / len(data)) * 100 if data else 0
        parsing_success = (parsed_count / len(data)) * 100 if data else 0

        results[model_name].update({
            "parsed_count": parsed_count,
            "accuracy": accuracy,
            "parsing_success": parsing_success,
            "details": details,
            "response_length": len(response_text)
        })

        print(f"{model_name.upper()} (NO THINKING):", flush=True)
        print(f"  📋 Parsed: {parsed_count}/{len(data)} ({parsing_success:.1f}%)", flush=True)
        print(f"  🎯 Accuracy: {accuracy:.2f}% ({correct_count}/{len(data)})", flush=True)
        print(f"  📄 Response length: {len(response_text):,} characters", flush=True)
        print(f"  ⚡ Avg time per citation: {total_time/len(citations):.2f}s", flush=True)
        print(flush=True)

    # Add summary to results
    results["summary"] = {
        "total_time_seconds": total_time,
        "total_time_minutes": total_time / 60,
        "avg_time_per_citation": total_time / len(citations),
        "citations_per_hour": len(citations) / (total_time / 3600) if total_time > 0 else 0,
        "best_accuracy": max(results[model]["accuracy"] for model in MODELS),
        "best_parsing": max(results[model]["parsing_success"] for model in MODELS),
        "winner_accuracy": max(MODELS, key=lambda x: results[x]["accuracy"]),
        "winner_parsing": max(MODELS, key=lambda x: results[x]["parsing_success"])
    }

    print("🏆 WINNER (NO THINKING):", flush=True)
    print(f"  Accuracy: {results['summary']['winner_accuracy'].upper()} ({results['summary']['best_accuracy']:.2f}%)", flush=True)
    print(f"  Parsing: {results['summary']['winner_parsing'].upper()} ({results['summary']['best_parsing']:.1f}%)", flush=True)
    print(f"  Performance: {results['summary']['citations_per_hour']:.1f} citations/hour", flush=True)

    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to {OUTPUT_FILE}", flush=True)
    print("🎉 No-thinking test completed successfully!", flush=True)

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else TEST_LIMIT
    asyncio.run(run_test(limit))