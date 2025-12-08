#!/usr/bin/env python3
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

# Load environment variables
load_dotenv("backend/.env")

# Configuration
MODEL = "gemini-2.5-flash"
DATASET_PATH = "Checker_Prompt_Optimization/test_set_121_corrected.jsonl"
PROMPT_PATH = "backend/prompts/validator_prompt_optimized.txt"
OUTPUT_FILE = "Checker_Prompt_Optimization/gemini_2.5_flash_system_instructions_results.json"

# Test configuration
BATCH_SIZE = 5
MAX_RETRIES = 3
RETRY_DELAY = 2

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

def create_system_instruction():
    """Create clear system instruction for complete processing"""
    return """You are an APA 7th edition citation validator. For each citation provided in the content, you must provide a validation response.

CRITICAL REQUIREMENTS:
1. Process EVERY citation in the content - do not skip any
2. Process them in the exact order they appear
3. Number sequentially starting from #1 for the first citation in each batch
4. Use this exact format:

═══════════════════════════════════════════════════════════════════════════
CITATION #[number]
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
[exact citation text]

SOURCE TYPE: [journal article/book/webpage/etc]

VALIDATION RESULTS:

[Either:]
✓ No APA 7 formatting errors detected

[Or list each error as:]
❌ [Component]: [What's wrong]
   Should be: [Correct format]

───────────────────────────────────────────────────────────────────────────"""

def format_citations(citations: List[str], start_index: int = 1) -> str:
    """Format citations with continuous numbering across batches"""
    formatted = []
    for i, citation in enumerate(citations, start_index):
        formatted.append(f"{i}. {citation}")
    return "\n\n".join(formatted)

def parse_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Enhanced parser that handles both regular and system instruction responses.
    Returns list of dicts with 'citation_number', 'is_valid', 'raw_block'.
    """
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

def retry_gemini_call(api_call, *args, **kwargs):
    """Retry logic with exponential backoff for Gemini API"""
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

async def process_single_batch(system_instruction: str, batch_citations: List[str],
                              start_idx: int, batch_num: int, total_batches: int, client):
    """Process a single batch with system instructions and thinking tracking"""
    print(f"\n🚀 Processing Batch {batch_num}/{total_batches} (Citations {start_idx}-{start_idx + len(batch_citations) - 1})", flush=True)

    start_time = time.time()

    try:
        # Format citations as content
        content = format_citations(batch_citations, start_idx)
        print(f"📄 Content length: {len(content)} characters", flush=True)

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=1.0,
            max_output_tokens=8000
        )

        response = retry_gemini_call(
            client.models.generate_content,
            model=MODEL,
            contents=content,
            config=config
        )

        batch_time = time.time() - start_time

        if response.text:
            parsed = parse_response(response.text)
            print(f"✅ {MODEL}: {len(parsed)} citations parsed in {batch_time:.1f}s", flush=True)

            # Extract thinking metadata
            thinking_tokens = 0
            total_tokens = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                try:
                    metadata_dict = response.usage_metadata.model_dump()
                    thinking_tokens = metadata_dict.get('thoughts_token_count', 0) or 0
                    total_tokens = metadata_dict.get('total_token_count', 0) or 0
                    print(f"🧠 Thinking tokens: {thinking_tokens:,} | Total tokens: {total_tokens:,}", flush=True)
                except Exception as e:
                    print(f"⚠️  Could not extract metadata: {e}", flush=True)

            return {
                "response_text": response.text,
                "parsed": parsed,
                "batch_time": batch_time,
                "thinking_tokens": thinking_tokens,
                "total_tokens": total_tokens,
                "success": True
            }
        else:
            print(f"⚠️  {MODEL}: No response", flush=True)
            return {
                "response_text": "",
                "parsed": [],
                "batch_time": batch_time,
                "thinking_tokens": 0,
                "total_tokens": 0,
                "success": False
            }

    except Exception as e:
        batch_time = time.time() - start_time
        print(f"❌ {MODEL} failed with exception: {e}", flush=True)
        return {
            "response_text": "",
            "parsed": [],
            "batch_time": batch_time,
            "thinking_tokens": 0,
            "total_tokens": 0,
            "success": False,
            "error": str(e)
        }

async def run_test(test_limit: int = None):
    """Main test function with system instructions and thinking tracking"""
    print(f"🎯 Gemini 2.5-Flash Test: System Instructions ({'Sample' if test_limit else 'Full 121'})", flush=True)
    print("=" * 70, flush=True)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found.", flush=True)
        return

    client = new_genai.Client(api_key=api_key)
    print(f"✅ Gemini client initialized", flush=True)

    data = await load_data(DATASET_PATH, limit=test_limit)
    system_instruction = create_system_instruction()

    citations = [d['citation'] for d in data]
    ground_truth = {i+1: d['ground_truth'] for i, d in enumerate(data)}

    print(f"📊 Testing {len(citations)} citations with {MODEL}", flush=True)
    print(f"📦 Batch size: {BATCH_SIZE} | Total batches: {(len(citations) + BATCH_SIZE - 1) // BATCH_SIZE}", flush=True)
    print(f"🔄 Retries: {MAX_RETRIES} with exponential backoff", flush=True)
    print(f"🧠 Thinking: Default (dynamic, will track usage)", flush=True)

    results = {
        "metadata": {
            "total_citations": len(citations),
            "batch_size": BATCH_SIZE,
            "max_retries": MAX_RETRIES,
            "model": MODEL,
            "test_type": f"gemini_2.5_flash_system_instructions_{test_limit if test_limit else 'full'}",
            "system_instruction_length": len(system_instruction)
        },
        "results": {
            "parsed": [],
            "response_text": "",
            "batch_times": [],
            "thinking_tokens_per_batch": [],
            "total_tokens_per_batch": []
        }
    }

    # Process all batches
    total_batches = (len(citations) + BATCH_SIZE - 1) // BATCH_SIZE
    start_time = time.time()

    for batch_num, i in enumerate(range(0, len(citations), BATCH_SIZE), 1):
        batch_citations = citations[i:i+BATCH_SIZE]
        start_idx = i + 1  # Citation numbers are 1-based

        print(f"\n📍 Starting batch {batch_num}/{total_batches} at {time.strftime('%H:%M:%S')}", flush=True)

        batch_result = await process_single_batch(
            system_instruction, batch_citations, start_idx, batch_num, total_batches, client
        )

        # Store batch results
        if batch_result["response_text"]:
            results["results"]["response_text"] += batch_result["response_text"] + "\n\n"
        results["results"]["parsed"].extend(batch_result["parsed"])
        results["results"]["batch_times"].append(batch_result["batch_time"])
        results["results"]["thinking_tokens_per_batch"].append(batch_result["thinking_tokens"])
        results["results"]["total_tokens_per_batch"].append(batch_result["total_tokens"])

        if batch_result["success"] and batch_result["parsed"]:
            # Log progress for this batch
            correct_count = sum(1 for p in batch_result["parsed"]
                              if p['citation_number'] in ground_truth
                              and p['is_valid'] == ground_truth[p['citation_number']])

            batch_accuracy = (correct_count / len(batch_result["parsed"])) * 100
            total_correct = sum(1 for p in results["results"]["parsed"]
                              if p['citation_number'] in ground_truth
                              and p['is_valid'] == ground_truth[p['citation_number']])
            total_accuracy = (total_correct / len(results["results"]["parsed"])) * 100

            print(f"📈 {MODEL}: {correct_count}/{len(batch_result['parsed'])} correct this batch ({batch_accuracy:.1f}%) | {total_correct}/{len(results['results']['parsed'])} total ({total_accuracy:.1f}%)", flush=True)

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
    print(f"\n📊 FINAL RESULTS", flush=True)
    print("=" * 50, flush=True)

    parsed = results["results"]["parsed"]
    response_text = results["results"]["response_text"]
    batch_times = results["results"]["batch_times"]
    thinking_tokens_per_batch = results["results"]["thinking_tokens_per_batch"]
    total_tokens_per_batch = results["results"]["total_tokens_per_batch"]

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

    # Thinking statistics
    total_thinking_tokens = sum(thinking_tokens_per_batch)
    total_response_tokens = sum(total_tokens_per_batch)
    avg_thinking_per_batch = total_thinking_tokens / len(thinking_tokens_per_batch) if thinking_tokens_per_batch else 0
    thinking_overhead = (total_thinking_tokens / (total_response_tokens - total_thinking_tokens) * 100) if (total_response_tokens > total_thinking_tokens) else 0

    results["results"].update({
        "parsed_count": parsed_count,
        "accuracy": accuracy,
        "parsing_success": parsing_success,
        "details": details,
        "response_length": len(response_text),
        "total_time_seconds": total_time,
        "total_time_minutes": total_time / 60,
        "avg_time_per_citation": total_time / len(citations),
        "citations_per_hour": len(citations) / (total_time / 3600) if total_time > 0 else 0,
        "thinking_stats": {
            "total_thinking_tokens": total_thinking_tokens,
            "total_response_tokens": total_response_tokens,
            "avg_thinking_per_batch": avg_thinking_per_batch,
            "thinking_overhead_percentage": thinking_overhead,
            "batches_with_thinking": sum(1 for t in thinking_tokens_per_batch if t > 0)
        }
    })

    print(f"{MODEL.upper()} (System Instructions):", flush=True)
    print(f"  📋 Parsed: {parsed_count}/{len(data)} ({parsing_success:.1f}%)", flush=True)
    print(f"  🎯 Accuracy: {accuracy:.2f}% ({correct_count}/{len(data)})", flush=True)
    print(f"  📄 Response length: {len(response_text):,} characters", flush=True)
    print(f"  ⚡ Avg time per citation: {total_time/len(citations):.2f}s", flush=True)
    print(f"  🚀 Performance: {len(citations) / (total_time / 3600):.1f} citations/hour", flush=True)
    print(f"  🧠 Thinking stats:", flush=True)
    print(f"     Total thinking tokens: {total_thinking_tokens:,}", flush=True)
    print(f"     Avg thinking per batch: {avg_thinking_per_batch:.0f}", flush=True)
    print(f"     Thinking overhead: {thinking_overhead:.1f}% of response cost", flush=True)
    print(f"     Batches with thinking: {sum(1 for t in thinking_tokens_per_batch if t > 0)}/{len(thinking_tokens_per_batch)}", flush=True)

    # Save results
    suffix = "_sample" if test_limit else "_full"
    output_file = OUTPUT_FILE.replace(".json", f"{suffix}.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to {output_file}", flush=True)
    print("🎉 System instructions test completed successfully!", flush=True)

if __name__ == "__main__":
    test_limit = 5 if len(sys.argv) > 1 and sys.argv[1] == "5" else None
    asyncio.run(run_test(test_limit))