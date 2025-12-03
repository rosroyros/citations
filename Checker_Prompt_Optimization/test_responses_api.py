import os
import json
import asyncio
import re
from typing import List, Dict, Any
from openai import AsyncOpenAI
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

# Configuration
MODEL = "gpt-5-mini"
DATASET_PATH = "Checker_Prompt_Optimization/test_set_121_corrected.jsonl"
PROMPT_PATH = "backend/prompts/validator_prompt_optimized.txt"
OUTPUT_FILE = "Checker_Prompt_Optimization/responses_api_migration_results.json"

async def load_data(path: str, limit: int = None) -> List[Dict[str, Any]]:
    data = []
    with open(path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    if limit:
        return data[:limit]
    return data

def load_prompt(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()

def format_citations(citations: List[str]) -> str:
    formatted = []
    for i, citation in enumerate(citations, 1):
        formatted.append(f"{i}. {citation}")
    return "\n\n".join(formatted)

def parse_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Simplified parser based on OpenAIProvider logic.
    Returns list of dicts with 'citation_number', 'is_valid'.
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
            "raw_block": block_content[:100] + "..."
        })
    return results

async def test_old_approach(client: AsyncOpenAI, prompt_template: str, citations: List[str]):
    print("\n--- Testing Old Approach (Chat Completions) ---")
    full_prompt = prompt_template + "\n\n" + format_citations(citations)
    
    try:
        response = await client.chat.completions.create(
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
        print(f"Error in Old Approach: {e}")
        return ""

async def test_new_v1(client: AsyncOpenAI, prompt_template: str, citations: List[str]):
    print("\n--- Testing New Approach V1 (Responses API - Simple Instr) ---")
    full_prompt = prompt_template + "\n\n" + format_citations(citations)
    
    try:
        response = await client.responses.create(
            model=MODEL,
            instructions="You are an expert APA 7th edition citation validator.",
            input=full_prompt,
            temperature=1,
            max_output_tokens=10000,
            reasoning={"effort": "medium"} if MODEL.startswith("gpt-5") else None
        )
        return response.output_text
    except Exception as e:
        print(f"Error in New V1: {e}")
        return ""

async def test_new_v2(client: AsyncOpenAI, prompt_template: str, citations: List[str]):
    print("\n--- Testing New Approach V2 (Responses API - Full Prompt Instr) ---")
    citation_input = format_citations(citations)
    
    try:
        response = await client.responses.create(
            model=MODEL,
            instructions=prompt_template,
            input=citation_input,
            temperature=1,
            max_output_tokens=10000,
            reasoning={"effort": "medium"} if MODEL.startswith("gpt-5") else None
        )
        return response.output_text
    except Exception as e:
        print(f"Error in New V2: {e}")
        return ""

async def run_test(limit: int = None):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found.")
        return

    client = AsyncOpenAI(api_key=api_key, timeout=120.0)
    
    data = await load_data(DATASET_PATH, limit)
    prompt_template = load_prompt(PROMPT_PATH)
    
    citations = [d['citation'] for d in data]
    ground_truth = {i+1: d['ground_truth'] for i, d in enumerate(data)}
    
    results = {}
    
    # Run tests
    # Batching to avoid token limits (121 citations * ~150 tokens > 10k max)
    BATCH_SIZE = 20
    
    approaches = ["old", "new_v1", "new_v2"]
    aggregated_results = {key: {"parsed": [], "response_text": ""} for key in approaches}

    for i in range(0, len(citations), BATCH_SIZE):
        batch_citations = citations[i:i+BATCH_SIZE]
        print(f"\nProcessing batch {i+1}-{min(i+BATCH_SIZE, len(citations))}...")
        
        # We need to adjust citation numbers in the prompt/input to match global indices?
        # No, the parser extracts "CITATION #N".
        # If we format batch as 1..20, parser sees 1..20.
        # We need to map them back to global indices.
        # Or we can just pass global indices to format_citations if we modify it.
        # Let's modify format_citations to accept start_index.
        
        # Actually, let's keep it simple: The model sees 1..20. We map 1->i+1, 2->i+2...
        
        batch_responses = {
            "old": await test_old_approach(client, prompt_template, batch_citations),
            "new_v1": await test_new_v1(client, prompt_template, batch_citations),
            "new_v2": await test_new_v2(client, prompt_template, batch_citations)
        }
        
        for key in approaches:
            resp = batch_responses[key]
            aggregated_results[key]["response_text"] += resp + "\n\n"
            
            parsed = parse_response(resp)
            # Adjust citation numbers to global
            for p in parsed:
                p['citation_number'] += i
            
            aggregated_results[key]["parsed"].extend(parsed)

    # Evaluate
    for key in approaches:
        parsed = aggregated_results[key]["parsed"]
        response_text = aggregated_results[key]["response_text"]
        
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
        
        print(f"\nResults for {key}:")
        print(f"  Parsed: {parsed_count}/{len(data)}")
        print(f"  Accuracy: {accuracy:.2f}% ({correct_count}/{len(data)})")
        
        results[key] = {
            "parsed_count": parsed_count,
            "accuracy": accuracy,
            "details": details,
            "response_length": len(response_text),
            "response_text": response_text
        }

    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(run_test(limit))
