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

def test_default_thinking_with_system():
    """Test default thinking behavior with system instructions"""

    print("🧠 Testing Default Thinking + System Instructions")
    print("=" * 55)
    print("(No explicit thinking_config specified)")

    client = new_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Use system instruction for citation validation
    system_instruction = "You are an APA 7th edition citation validator. For each citation, identify errors and provide corrections in the specified format."

    # Load test data
    data = load_data("Checker_Prompt_Optimization/test_set_121_corrected.jsonl", limit=10)
    citations = [d['citation'] for d in data[:5]]  # Test with 5 citations

    print(f"📝 System instruction: {system_instruction}")
    print(f"📋 Testing {len(citations)} citations with gemini-2.5-flash (default thinking)")

    try:
        start_time = time.time()

        # Config without thinking_config - uses default
        config = types.GenerateContentConfig(
            temperature=1.0,
            max_output_tokens=2000,
            system_instruction=system_instruction
            # Note: NO thinking_config specified - uses default
        )

        # Format citations as content
        content = format_citations(citations)
        print(f"📄 Content length: {len(content)} characters")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content,
            config=config
        )

        elapsed_time = time.time() - start_time

        print(f"\n✅ Response received in {elapsed_time:.2f}s")
        print(f"📄 Response text length: {len(response.text) if response.text else 'None'} characters")

        # Examine usage metadata
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            print(f"\n📊 USAGE METADATA:")
            print(f"   Type: {type(response.usage_metadata)}")

            try:
                metadata_dict = response.usage_metadata.model_dump() if hasattr(response.usage_metadata, 'model_dump') else str(response.usage_metadata)
                if isinstance(metadata_dict, dict):
                    for key, value in metadata_dict.items():
                        print(f"   {key}: {value}")

                    # Check for thinking tokens
                    thoughts_tokens = metadata_dict.get('thoughts_token_count', 0) or 0
                    prompt_tokens = metadata_dict.get('prompt_token_count', 0) or 0
                    candidates_tokens = metadata_dict.get('candidates_token_count', 0) or 0
                    total_tokens = metadata_dict.get('total_token_count', 0) or 0

                    print(f"\n🧠 THINKING ANALYSIS:")
                    print(f"   Thinking tokens: {thoughts_tokens}")
                    if thoughts_tokens > 0:
                        print(f"   🎯 Dynamic thinking was used!")
                        print(f"   📊 Thinking cost: {thoughts_tokens:,} tokens")
                        print(f"   💰 Thinking overhead: {((thoughts_tokens / (prompt_tokens + candidates_tokens)) * 100):.1f}% of response cost")
                    else:
                        print(f"   🚀 No thinking tokens detected")
                        print(f"   📊 Using faster response mode")

                    print(f"\n📈 PERFORMANCE:")
                    print(f"   Prompt tokens: {prompt_tokens:,}")
                    print(f"   Response tokens: {candidates_tokens:,}")
                    print(f"   Total tokens: {total_tokens:,}")
                    print(f"   Time: {elapsed_time:.2f}s")
                    print(f"   Tokens/second: {total_tokens/elapsed_time:.1f}")

                else:
                    print(f"   Content: {metadata_dict}")

            except Exception as e:
                print(f"   Error parsing metadata: {e}")
        else:
            print(f"❌ No usage_metadata found")

        # Sample response
        if response.text:
            print(f"\n📝 Response preview (first 800 chars):")
            sample = response.text[:800]
            if len(response.text) > 800:
                sample += "..."
            print(f"   {sample}")

            # Count citations in response
            citation_count = response.text.count("CITATION #")
            if citation_count > 0:
                print(f"\n📋 Citations processed: {citation_count}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print(f"\n🏁 Default thinking test completed")

if __name__ == "__main__":
    test_default_thinking_with_system()