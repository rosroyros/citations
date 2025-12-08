#!/usr/bin/env python3
import os
import json
import time
from google import genai as new_genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv("backend/.env")

def load_data(path: str, limit: int = None):
    """Load test data"""
    data = []
    with open(path, 'r') as f:
        for i, line in enumerate(f, 1):
            if line.strip():
                try:
                    data.append(json.loads(line))
                    if limit and len(data) >= limit:
                        break
                except json.JSONDecodeError:
                    continue
    return data

def format_citations(citations: list, start_index: int = 1):
    """Format citations with continuous numbering"""
    formatted = []
    for i, citation in enumerate(citations, start_index):
        formatted.append(f"{i}. {citation}")
    return "\n\n".join(formatted)

def test_combined_prompt():
    """Test with combined system instruction + content in single prompt"""

    print("🧠 Testing Combined Prompt (No System Instructions)")
    print("=" * 55)

    client = new_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Load our optimized prompt
    with open("backend/prompts/validator_prompt_optimized.txt", 'r') as f:
        system_prompt = f.read()

    # Load test data
    data = load_data("Checker_Prompt_Optimization/test_set_121_corrected.jsonl", limit=10)
    citations = [d['citation'] for d in data[:5]]  # Test with 5 citations

    print(f"📝 Using optimized prompt ({len(system_prompt)} chars)")
    print(f"📋 Testing {len(citations)} citations with gemini-2.5-flash (default thinking)")

    # Create combined prompt
    formatted_citations = format_citations(citations)
    combined_prompt = system_prompt + "\n\n" + formatted_citations

    print(f"📄 Total prompt length: {len(combined_prompt)} characters")

    try:
        start_time = time.time()

        # Config without thinking_config and without system_instruction
        config = types.GenerateContentConfig(
            temperature=1.0,
            max_output_tokens=2000
            # NO thinking_config - uses default
            # NO system_instruction - all in content
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=combined_prompt,
            config=config
        )

        elapsed_time = time.time() - start_time

        print(f"\n✅ Response received in {elapsed_time:.2f}s")
        print(f"📄 Response text length: {len(response.text) if response.text else 'None'} characters")

        # Examine usage metadata
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            print(f"\n📊 USAGE METADATA:")

            metadata_dict = response.usage_metadata.model_dump()

            # Key metrics
            thoughts_tokens = metadata_dict.get('thoughts_token_count', 0) or 0
            prompt_tokens = metadata_dict.get('prompt_token_count', 0) or 0
            candidates_tokens = metadata_dict.get('candidates_token_count', 0) or 0
            total_tokens = metadata_dict.get('total_token_count', 0) or 0

            print(f"   Thoughts tokens: {thoughts_tokens}")
            print(f"   Prompt tokens: {prompt_tokens}")
            print(f"   Response tokens: {candidates_tokens}")
            print(f"   Total tokens: {total_tokens}")

            print(f"\n🧠 THINKING ANALYSIS:")
            if thoughts_tokens > 0:
                print(f"   🎯 Dynamic thinking was used!")
                print(f"   📊 Thinking cost: {thoughts_tokens:,} tokens")
                print(f"   💰 Thinking overhead: {((thoughts_tokens / (prompt_tokens + candidates_tokens)) * 100):.1f}% of response cost")
            else:
                print(f"   🚀 No thinking tokens detected")

            print(f"\n📈 PERFORMANCE:")
            print(f"   Time: {elapsed_time:.2f}s")
            print(f"   Tokens/second: {total_tokens/elapsed_time:.1f}")

        else:
            print(f"❌ No usage_metadata found")

        # Sample response
        if response.text:
            print(f"\n📝 Response preview (first 600 chars):")
            sample = response.text[:600]
            if len(response.text) > 600:
                sample += "..."
            print(f"   {sample}")

            # Count citations in response
            citation_count = response.text.count("CITATION #")
            if citation_count > 0:
                print(f"\n📋 Citations processed: {citation_count}")
            else:
                # Look for other patterns that might indicate successful processing
                if "ORIGINAL:" in response.text and "VALIDATION RESULTS:" in response.text:
                    print(f"\n📋 Response structure looks good (contains ORIGINAL and VALIDATION sections)")
                else:
                    print(f"\n⚠️  Response structure unclear")

    except Exception as e:
        print(f"❌ Error: {e}")

    print(f"\n🏁 Combined prompt test completed")

if __name__ == "__main__":
    test_combined_prompt()