import os
import json
import asyncio
import re
import time
import sys
from typing import List, Dict, Any
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError, AuthenticationError
from pathlib import Path
from dotenv import load_dotenv

# Force unbuffered output for background process
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load environment variables
load_dotenv("backend/.env")

# Configuration
MODEL = "gpt-5-mini"
DATASET_PATH = "Checker_Prompt_Optimization/test_set_121_corrected.jsonl"
PROMPT_PATH = "backend/prompts/validator_prompt_optimized.txt"
OUTPUT_FILE = "Checker_Prompt_Optimization/responses_api_parallel_results.json"

# Updated configuration
BATCH_SIZE = 5  # Smaller batches for reliability
MAX_RETRIES = 3
RETRY_DELAY = 2  # Initial delay in seconds
CLIENT_TIMEOUT = 85.0  # Same as production

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
    print(f"📄 Loading prompt from {path}")
    with open(path, 'r') as f:
        return f.read()

def format_citations(citations: List[str], start_index: int = 1) -> str:
    """Format citations with continuous numbering across batches"""
    formatted = []
    for i, citation in enumerate(citations, start_index):
        formatted.append(f"{i}. {citation}")
    return "\n\n".join(formatted)

def parse_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Enhanced parser based on OpenAIProvider logic.
    Returns list of dicts with 'citation_number', 'is_valid', 'raw_block'.
    """
    results = []
    citation_pattern = r'(?:═+\s+)?CITATION #(\d+)\s*\n\s*═+(.+?)(?=(?:═+\s+)?CITATION #\d+|$)'
    matches = re.finditer(citation_pattern, response_text, re.DOTALL)

    for match in matches:
        citation_num = int(match.group(1))
        block_content = match.group(2)

        is_valid = False
        # Multiple ways the model might say the citation is valid
        valid_indicators = [
            '✓ No APA 7 formatting errors detected',
            'No APA 7 formatting errors detected',
            '✓ No APA 7 formatting errors',
            'No APA 7 formatting errors',
            'No major APA 7 formatting errors detected',
            '✓ No major APA 7 formatting errors detected'
        ]

        if any(indicator in block_content for indicator in valid_indicators):
            is_valid = True

        results.append({
            "citation_number": citation_num,
            "is_valid": is_valid,
            "raw_block": block_content[:200] + "..." if len(block_content) > 200 else block_content
        })
    return results

async def retry_api_call(api_call, *args, **kwargs):
    """Retry logic with exponential backoff"""
    for attempt in range(MAX_RETRIES):
        try:
            return await api_call(*args, **kwargs)
        except (APITimeoutError, RateLimitError) as e:
            if attempt == MAX_RETRIES - 1:
                print(f"❌ Final attempt failed: {type(e).__name__}: {str(e)[:100]}...")
                raise
            wait_time = RETRY_DELAY * (2 ** attempt)
            print(f"⚠️  Attempt {attempt + 1} failed ({type(e).__name__}), retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
        except Exception as e:
            print(f"❌ Non-retryable error: {type(e).__name__}: {str(e)[:100]}...")
            raise

async def test_old_approach(client: AsyncOpenAI, prompt_template: str, citations: List[str], start_idx: int):
    """Old Chat Completions API with retry logic"""
    print(f"🔵 Testing Old Approach (Chat) - Citations {start_idx}-{start_idx + len(citations) - 1}")

    full_prompt = prompt_template + "\n\n" + format_citations(citations, start_idx)

    try:
        response = await retry_api_call(
            client.chat.completions.create,
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert APA 7th edition citation validator."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=1,
            max_completion_tokens=10000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Old Approach failed: {e}")
        return ""

async def test_new_v1(client: AsyncOpenAI, prompt_template: str, citations: List[str], start_idx: int):
    """New Responses API V1 - Simple instructions with retry logic"""
    print(f"🟢 Testing New V1 (Simple Instructions) - Citations {start_idx}-{start_idx + len(citations) - 1}")

    full_prompt = prompt_template + "\n\n" + format_citations(citations, start_idx)

    try:
        response = await retry_api_call(
            client.responses.create,
            model=MODEL,
            instructions="You are an expert APA 7th edition citation validator.",
            input=full_prompt,
            temperature=1,
            max_output_tokens=10000,
            reasoning={"effort": "medium"} if MODEL.startswith("gpt-5") else None
        )
        return response.output_text
    except Exception as e:
        print(f"❌ New V1 failed: {e}")
        return ""

async def test_new_v2(client: AsyncOpenAI, prompt_template: str, citations: List[str], start_idx: int):
    """New Responses API V2 - Full prompt as instructions with retry logic"""
    print(f"🔴 Testing New V2 (Full Instructions) - Citations {start_idx}-{start_idx + len(citations) - 1}")

    citation_input = format_citations(citations, start_idx)

    try:
        response = await retry_api_call(
            client.responses.create,
            model=MODEL,
            instructions=prompt_template,
            input=citation_input,
            temperature=1,
            max_output_tokens=10000,
            reasoning={"effort": "medium"} if MODEL.startswith("gpt-5") else None
        )
        return response.output_text
    except Exception as e:
        print(f"❌ New V2 failed: {e}")
        return ""

async def process_single_batch(client: AsyncOpenAI, prompt_template: str, batch_citations: List[str],
                              start_idx: int, batch_num: int, total_batches: int):
    """Process a single batch across all 3 approaches in parallel"""
    print(f"\n🚀 Processing Batch {batch_num}/{total_batches} (Citations {start_idx}-{start_idx + len(batch_citations) - 1})")

    # Run all 3 approaches in parallel
    start_time = time.time()

    tasks = [
        test_old_approach(client, prompt_template, batch_citations, start_idx),
        test_new_v1(client, prompt_template, batch_citations, start_idx),
        test_new_v2(client, prompt_template, batch_citations, start_idx)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    batch_time = time.time() - start_time

    # Process results
    batch_outputs = {}
    approach_names = ["old", "new_v1", "new_v2"]

    for i, (approach_name, result) in enumerate(zip(approach_names, results)):
        if isinstance(result, Exception):
            print(f"❌ {approach_name} failed with exception: {result}")
            batch_outputs[approach_name] = ""
        else:
            batch_outputs[approach_name] = result or ""
            if result:
                parsed_count = len(parse_response(result))
                print(f"✅ {approach_name}: {parsed_count} citations parsed in {batch_time:.1f}s")
            else:
                print(f"⚠️  {approach_name}: No response")

    return batch_outputs

async def run_test(limit: int = None):
    """Main test function with improved logging and parallel processing"""
    print("🎯 OpenAI Responses API Migration Test - Parallel Edition")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found.")
        return

    client = AsyncOpenAI(api_key=api_key, timeout=CLIENT_TIMEOUT)
    print(f"✅ OpenAI client initialized (timeout: {CLIENT_TIMEOUT}s)")

    data = await load_data(DATASET_PATH, limit)
    prompt_template = load_prompt(PROMPT_PATH)

    citations = [d['citation'] for d in data]
    ground_truth = {i+1: d['ground_truth'] for i, d in enumerate(data)}

    print(f"📊 Testing {len(citations)} citations across 3 API approaches")
    print(f"📦 Batch size: {BATCH_SIZE} | Total batches: {(len(citations) + BATCH_SIZE - 1) // BATCH_SIZE}")
    print(f"🔄 Retries: {MAX_RETRIES} with exponential backoff")

    results = {
        "metadata": {
            "total_citations": len(citations),
            "batch_size": BATCH_SIZE,
            "max_retries": MAX_RETRIES,
            "client_timeout": CLIENT_TIMEOUT,
            "model": MODEL
        },
        "old": {"parsed": [], "response_text": "", "batch_times": []},
        "new_v1": {"parsed": [], "response_text": "", "batch_times": []},
        "new_v2": {"parsed": [], "response_text": "", "batch_times": []}
    }

    approaches = ["old", "new_v1", "new_v2"]

    # Process all batches
    total_batches = (len(citations) + BATCH_SIZE - 1) // BATCH_SIZE
    start_time = time.time()

    for batch_num, i in enumerate(range(0, len(citations), BATCH_SIZE), 1):
        batch_citations = citations[i:i+BATCH_SIZE]
        start_idx = i + 1  # Citation numbers are 1-based

        batch_outputs = await process_single_batch(
            client, prompt_template, batch_citations, start_idx, batch_num, total_batches
        )

        # Parse and aggregate results
        for approach_name in approaches:
            response_text = batch_outputs[approach_name]
            results[approach_name]["response_text"] += response_text + "\n\n"

            if response_text:
                parsed = parse_response(response_text)
                results[approach_name]["parsed"].extend(parsed)

                # Log progress for this batch
                correct_count = sum(1 for p in parsed
                                  if p['citation_number'] in ground_truth
                                  and p['is_valid'] == ground_truth[p['citation_number']])

                print(f"📈 {approach_name}: {correct_count}/{len(parsed)} correct in this batch")

    total_time = time.time() - start_time
    print(f"\n⏱️  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")

    # Calculate final metrics
    print(f"\n📊 FINAL RESULTS")
    print("=" * 60)

    for approach_name in approaches:
        parsed = results[approach_name]["parsed"]
        response_text = results[approach_name]["response_text"]

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

        results[approach_name].update({
            "parsed_count": parsed_count,
            "accuracy": accuracy,
            "parsing_success": parsing_success,
            "details": details,
            "response_length": len(response_text)
        })

        print(f"{approach_name.upper()}:")
        print(f"  📋 Parsed: {parsed_count}/{len(data)} ({parsing_success:.1f}%)")
        print(f"  🎯 Accuracy: {accuracy:.2f}% ({correct_count}/{len(data)})")
        print(f"  📄 Response length: {len(response_text):,} characters")
        print()

    # Add summary to results
    results["summary"] = {
        "total_time_seconds": total_time,
        "total_time_minutes": total_time / 60,
        "best_accuracy": max(results[app]["accuracy"] for app in approaches),
        "best_parsing": max(results[app]["parsing_success"] for app in approaches),
        "winner_accuracy": max(approaches, key=lambda x: results[x]["accuracy"]),
        "winner_parsing": max(approaches, key=lambda x: results[x]["parsing_success"])
    }

    print("🏆 WINNER:")
    print(f"  Accuracy: {results['summary']['winner_accuracy'].upper()} ({results['summary']['best_accuracy']:.2f}%)")
    print(f"  Parsing: {results['summary']['winner_parsing'].upper()} ({results['summary']['best_parsing']:.1f}%)")

    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(run_test(limit))