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

# Configuration - ONLY gemini-2.5-flash
MODEL = "gemini-2.5-flash"
DATASET_PATH = "Checker_Prompt_Optimization/test_set_121_corrected.jsonl"
PROMPT_PATH = "backend/prompts/validator_prompt_optimized.txt"
OUTPUT_FILE = "Checker_Prompt_Optimization/gemini_2_5_flash_regular_run2_results.json"

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

def load_prompt(path: str) -> str:
    print(f"📄 Loading prompt from {path}", flush=True)
    with open(path, 'r') as f:
        return f.read()

def format_citations_for_content(citations: List[str], start_idx: int) -> str:
    """Format citations for content (numbered for clarity)"""
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

        results.append({
            "citation_number": citation_num,
            "is_valid": is_valid,
            "raw_block": block_content[:200] + "..." if len(block_content) > 200 else block_content
        })
    return results

def retry_gemini_call(api_call, *args, **kwargs):
    """Retry logic with exponential backoff"""
    for attempt in range(MAX_RETRIES):
        try:
            return api_call(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
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

async def test_regular_approach(citations: List[str], start_idx: int):
    """Test regular approach (combined prompt)"""
    print(f"🔵 Testing Regular Approach - Citations {start_idx}-{start_idx + len(citations) - 1}", flush=True)

    try:
        client = new_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # Combine prompt and citations
        prompt_template = load_prompt(PROMPT_PATH)
        formatted_citations = format_citations_for_content(citations, start_idx)
        full_prompt = prompt_template + "\n\nCITATIONS TO VALIDATE:\n\n" + formatted_citations

        config = types.GenerateContentConfig(
            temperature=1.0,
            max_output_tokens=8000
        )

        response = retry_gemini_call(
            client.models.generate_content,
            model=MODEL,
            contents=full_prompt,
            config=config
        )

        # Extract thinking metadata
        thinking_tokens = 0
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            try:
                metadata_dict = response.usage_metadata.model_dump()
                thinking_tokens = metadata_dict.get('thoughts_token_count', 0) or 0
            except:
                pass

        return response.text, thinking_tokens

    except Exception as e:
        print(f"❌ Regular approach failed: {e}", flush=True)
        return "", None

async def process_regular_batch(citations: List[str], start_idx: int, batch_num: int, total_batches: int):
    """Process a single batch with regular approach"""
    print(f"\n🚀 Processing Batch {batch_num}/{total_batches} (Citations {start_idx}-{start_idx + len(citations) - 1})", flush=True)

    start_time = time.time()

    # Test regular approach
    regular_response, regular_thinking = await test_regular_approach(citations, start_idx)

    batch_time = time.time() - start_time

    # Parse responses
    regular_parsed = parse_response(regular_response) if regular_response else []

    print(f"📊 Regular: {len(regular_parsed)} parsed | Time: {batch_time:.1f}s", flush=True)
    if regular_thinking and regular_thinking > 0:
        print(f"🧠 Regular thinking: {regular_thinking:,} tokens", flush=True)

    return {
        "regular": {
            "response_text": regular_response,
            "parsed": regular_parsed,
            "thinking_tokens": regular_thinking
        },
        "batch_time": batch_time
    }

async def run_regular_test():
    """Main regular approach test"""
    print(f"🎯 Gemini 2.5-Flash Regular Approach Test - Run 2", flush=True)
    print("=" * 60, flush=True)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found.", flush=True)
        return

    print(f"✅ Gemini API key found", flush=True)
    print(f"🤖 Testing regular approach with {MODEL}", flush=True)

    data = await load_data(DATASET_PATH)
    citations = [d['citation'] for d in data]
    ground_truth = {i+1: d['ground_truth'] for i, d in enumerate(data)}

    print(f"📊 Testing {len(citations)} citations with regular approach", flush=True)
    print(f"📦 Batch size: {BATCH_SIZE} | Total batches: {(len(citations) + BATCH_SIZE - 1) // BATCH_SIZE}", flush=True)

    results = {
        "metadata": {
            "total_citations": len(citations),
            "batch_size": BATCH_SIZE,
            "model": MODEL,
            "test_type": "gemini_2_5_flash_regular_run2",
            "approach": "regular_combined_prompt"
        },
        "regular": {"parsed": [], "response_text": "", "thinking_tokens": [], "times": []}
    }

    # Process batches
    total_batches = (len(citations) + BATCH_SIZE - 1) // BATCH_SIZE
    start_time = time.time()

    for batch_num, i in enumerate(range(0, len(citations), BATCH_SIZE), 1):
        batch_citations = citations[i:i+BATCH_SIZE]
        start_idx = i + 1

        batch_results = await process_regular_batch(
            batch_citations, start_idx, batch_num, total_batches
        )

        # Store results
        results["regular"]["parsed"].extend(batch_results["regular"]["parsed"])
        if batch_results["regular"]["response_text"]:
            results["regular"]["response_text"] += batch_results["regular"]["response_text"] + "\n\n"
        results["regular"]["thinking_tokens"].append(batch_results["regular"]["thinking_tokens"])
        results["regular"]["times"].append(batch_results["batch_time"])

        # Progress
        elapsed = time.time() - start_time
        citations_processed = (batch_num * BATCH_SIZE)
        avg_time_per_citation = elapsed / citations_processed if citations_processed > 0 else 0
        eta = avg_time_per_citation * len(citations) - elapsed

        print(f"⏱️  Progress: {batch_num}/{total_batches} batches | {citations_processed}/{len(citations)} ({(citations_processed/len(citations)*100):.1f}%) | ETA: {eta/60:.1f}min", flush=True)

    total_time = time.time() - start_time
    print(f"\n⏱️  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)", flush=True)

    # Calculate final metrics
    print(f"\n📊 FINAL REGULAR APPROACH RESULTS", flush=True)
    print("=" * 50, flush=True)

    parsed = results["regular"]["parsed"]
    thinking_tokens = results["regular"]["thinking_tokens"]

    correct_count = 0
    for p in parsed:
        if p['citation_number'] in ground_truth:
            if p['is_valid'] == ground_truth[p['citation_number']]:
                correct_count += 1

    accuracy = (correct_count / len(data)) * 100 if data else 0
    parsing_success = (len(parsed) / len(data)) * 100 if data else 0
    total_thinking = sum(t for t in thinking_tokens if t is not None)
    avg_thinking = total_thinking / len(thinking_tokens) if thinking_tokens else 0

    results["regular"].update({
        "accuracy": accuracy,
        "parsing_success": parsing_success,
        "correct_count": correct_count,
        "total_thinking_tokens": total_thinking,
        "avg_thinking_per_batch": avg_thinking,
        "avg_time_per_citation": total_time / len(citations)
    })

    print(f"\nREGULAR APPROACH:")
    print(f"  📋 Parsed: {len(parsed)}/{len(data)} ({parsing_success:.1f}%)")
    print(f"  🎯 Accuracy: {accuracy:.2f}% ({correct_count}/{len(data)})")
    print(f"  🧠 Total thinking: {total_thinking:,} tokens")
    print(f"  🧠 Avg thinking/batch: {avg_thinking:.0f}")
    print(f"  ⚡ Avg time/citation: {total_time/len(citations):.2f}s")

    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to {OUTPUT_FILE}", flush=True)
    print("🎉 Regular approach test completed successfully!", flush=True)

if __name__ == "__main__":
    asyncio.run(run_regular_test())