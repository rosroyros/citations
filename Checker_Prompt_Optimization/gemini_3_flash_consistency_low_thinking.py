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
MODEL_NAME = "gemini-3-flash-preview"
RUNS = 3
DATASET_PATH = "Checker_Prompt_Optimization/test_set_121_corrected.jsonl"
PROMPT_PATH = "backend/prompts/validator_prompt_optimized.txt"
OUTPUT_FILE = "Checker_Prompt_Optimization/gemini_3_flash_low_thinking_consistency_results.json"

# Load Sensitivity Configuration
BATCH_SIZE = 5     # Process citations in small batches
MAX_RETRIES = 5    # Increased retries for stability
BASE_DELAY = 2     # Start with 2s delay
RATE_LIMIT_PAUSE = 30 # Sleep 30s if we hit a 429

async def load_data(path: str) -> List[Dict[str, Any]]:
    print(f"📂 Loading data from {path}", flush=True)
    data = []
    with open(path, 'r') as f:
        for i, line in enumerate(f, 1):
            if line.strip():
                try:
                    data.append(json.loads(line))
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

async def call_gemini_safe(client, full_prompt, run_id):
    """
    Wraps the API call with robust retry logic and rate limit handling.
    """
    for attempt in range(MAX_RETRIES):
        try:
            # Low Thinking Configuration
            # Temp 0.0 for determinism
            # Thinking Budget limited to 1024 tokens to force "Low Thinking"
            config = types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=65536,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True,
                    thinking_budget=1024 
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
            
            # Explicit Rate Limit Handling
            if "429" in error_str or "resource" in error_str and "exhausted" in error_str:
                print(f"🛑 Run {run_id}: Rate limit hit! Pausing for {RATE_LIMIT_PAUSE}s...", flush=True)
                await asyncio.sleep(RATE_LIMIT_PAUSE)
                continue # Retry after long pause

            # Standard Backoff for other errors
            if attempt < MAX_RETRIES - 1:
                wait_time = BASE_DELAY * (2 ** attempt)
                print(f"⚠️  Run {run_id}: Attempt {attempt + 1} failed ({type(e).__name__}), retrying in {wait_time}s...", flush=True)
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ Run {run_id}: Failed after {MAX_RETRIES} attempts. Error: {e}", flush=True)
                return ""
    return ""

async def process_batch(client, prompt_template, batch_citations, start_idx, batch_num, total_batches):
    """
    Process a single batch for all RUNS in parallel.
    """
    print(f"\n🚀 Processing Batch {batch_num}/{total_batches} (Citations {start_idx}-{start_idx + len(batch_citations) - 1})", flush=True)
    
    # Construct the user message (Prompt + Citations)
    formatted_citations = format_citations_for_content(batch_citations, start_idx)
    full_prompt = prompt_template + "\n\nCITATIONS TO VALIDATE:\n\n" + formatted_citations

    tasks = []
    for i in range(RUNS):
        run_id = i + 1
        tasks.append(call_gemini_safe(client, full_prompt, run_id))

    # Execute all 3 runs for this batch concurrently
    results = await asyncio.gather(*tasks)
    
    parsed_results = {}
    for i, response_text in enumerate(results):
        run_id = i + 1
        parsed = parse_response(response_text)
        parsed_results[f"run_{run_id}"] = {
            "response_text": response_text,
            "parsed": parsed
        }
        print(f"   Run {run_id}: Parsed {len(parsed)} citations", flush=True)

    return parsed_results

async def run_consistency_test():
    print(f"🧪 Starting Gemini Consistency Test (Low Thinking, Temp 0)", flush=True)
    print(f"Target: {MODEL_NAME} | Runs: {RUNS}", flush=True)
    print("=" * 60, flush=True)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found.", flush=True)
        return

    client = new_genai.Client(api_key=api_key)

    data = await load_data(DATASET_PATH)
    prompt_template = load_prompt(PROMPT_PATH)
    
    citations = [d['citation'] for d in data]
    ground_truth = {i+1: d['ground_truth'] for i, d in enumerate(data)}

    # Initialize results container
    final_stats = {}
    
    # Initialize full output structure or load existing
    if os.path.exists(OUTPUT_FILE):
        print(f"🔄 Resuming from {OUTPUT_FILE}...", flush=True)
        with open(OUTPUT_FILE, 'r') as f:
            output_data = json.load(f)
            
        # Re-populate final_stats from loaded data
        for run_key, responses in output_data["raw_responses"].items():
            for response_text in responses:
                parsed = parse_response(response_text)
                for p in parsed:
                    c_num = p["citation_number"]
                    if c_num not in final_stats:
                        final_stats[c_num] = {"ground_truth": ground_truth.get(c_num)}
                    final_stats[c_num][run_key] = p["is_valid"]
    else:
        output_data = {
            "metadata": {
                "model": MODEL_NAME,
                "runs": RUNS,
                "total_citations": len(citations),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prompt_version": "optimized",
                "config": "temp=0.0, thinking_budget=1024"
            },
            "raw_responses": {f"run_{i+1}": [] for i in range(RUNS)},
            "citation_analysis": []
        }

    total_batches = (len(citations) + BATCH_SIZE - 1) // BATCH_SIZE

    # Process Batches
    for batch_num, i in enumerate(range(0, len(citations), BATCH_SIZE), 1):
        # Check if this batch is already processed
        if len(output_data["raw_responses"]["run_1"]) >= batch_num:
            print(f"⏩ Skipping Batch {batch_num} (already processed)", flush=True)
            continue

        batch_citations = citations[i:i+BATCH_SIZE]
        start_idx = i + 1
        
        batch_results = await process_batch(
            client, prompt_template, batch_citations, start_idx, batch_num, total_batches
        )

        # Organize results
        for run_key, data in batch_results.items():
            output_data["raw_responses"][run_key].append(data["response_text"])
            
            # Map parsed results to global stats
            for p in data["parsed"]:
                c_num = p["citation_number"]
                if c_num not in final_stats:
                    final_stats[c_num] = {"ground_truth": ground_truth.get(c_num)}
                
                final_stats[c_num][run_key] = p["is_valid"]

        # Save progress
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(output_data, f, indent=2)

        # Small pause between batches
        await asyncio.sleep(2)

    # Analyze Consistency
    print("\n📊 Analyzing Consistency...", flush=True)
    consistent_count = 0
    flipper_count = 0
    
    for c_num in sorted(final_stats.keys()):
        stats = final_stats[c_num]
        results = [stats.get(f"run_{r+1}") for r in range(RUNS)]
        
        if any(r is None for r in results):
            stats["status"] = "parsing_error"
            continue

        is_consistent = all(r == results[0] for r in results)
        stats["consistent"] = is_consistent
        
        output_data["citation_analysis"].append({
            "citation_number": c_num,
            "ground_truth": stats["ground_truth"],
            "runs": {f"run_{r+1}": results[r] for r in range(RUNS)},
            "consistent": is_consistent
        })

        if is_consistent:
            consistent_count += 1
        else:
            flipper_count += 1
            print(f"⚠️  Citation #{c_num} FLIPPED: {results}", flush=True)

    # Calculate Metrics
    consistency_rate = (consistent_count / len(citations)) * 100
    
    accuracies = []
    for r in range(RUNS):
        key = f"run_{r+1}"
        correct = sum(1 for c in final_stats.values() if c.get(key) == c.get("ground_truth"))
        acc = (correct / len(citations)) * 100
        accuracies.append(acc)
        print(f"Run {r+1} Accuracy: {acc:.2f}%", flush=True)

    output_data["metrics"] = {
        "consistency_rate": consistency_rate,
        "flipper_count": flipper_count,
        "run_accuracies": accuracies,
        "avg_accuracy": sum(accuracies) / len(accuracies)
    }

    print("=" * 60, flush=True)
    print(f"🏆 CONSISTENCY SCORE: {consistency_rate:.2f}%", flush=True)
    print(f"📉 FLIPPERS: {flipper_count} citations changed verdict between runs", flush=True)
    print("=" * 60, flush=True)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)
    print(f"💾 Results saved to {OUTPUT_FILE}", flush=True)

if __name__ == "__main__":
    asyncio.run(run_consistency_test())
