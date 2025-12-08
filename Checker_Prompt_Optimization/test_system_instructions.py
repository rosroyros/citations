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

def test_system_instructions_with_usage():
    """Test using system instructions and examine usage metadata"""

    print("🧠 Testing System Instructions + Usage Metadata")
    print("=" * 55)

    client = new_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Load our optimized prompt as system instruction
    with open("backend/prompts/validator_prompt_optimized.txt", 'r') as f:
        system_instruction = f.read()

    # Use a shorter, clearer version for system instruction
    system_instruction = "You are an APA 7th edition citation validator. For each citation, identify errors and provide corrections in the specified format."

    # Load test data
    data = load_data("Checker_Prompt_Optimization/test_set_121_corrected.jsonl", limit=10)
    citations = [d['citation'] for d in data[:5]]  # Test with 5 citations

    print(f"📝 System instruction length: {len(system_instruction)} characters")
    print(f"📋 Testing {len(citations)} citations with gemini-2.5-flash")

    configs = [
        ("No thinking", types.ThinkingConfig(thinking_budget=0)),
        ("Dynamic thinking", types.ThinkingConfig(thinking_budget=-1)),
    ]

    results = {}

    for desc, thinking_config in configs:
        print(f"\n{'='*20} {desc} {'='*20}")

        try:
            start_time = time.time()

            config = types.GenerateContentConfig(
                temperature=1.0,
                max_output_tokens=2000,
                thinking_config=thinking_config,
                system_instruction=system_instruction
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

            print(f"✅ Response received in {elapsed_time:.2f}s")
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

                        # Look for thinking-specific fields
                        thinking_fields = [k for k in metadata_dict.keys() if 'think' in k.lower()]
                        if thinking_fields:
                            print(f"🧠 Thinking-related fields: {thinking_fields}")
                        else:
                            print(f"🧠 No explicit thinking fields found in metadata")
                    else:
                        print(f"   Content: {metadata_dict}")

                except Exception as e:
                    print(f"   Error parsing metadata: {e}")
            else:
                print(f"❌ No usage_metadata found")

            # Check for any thinking-related attributes
            thinking_attrs = [attr for attr in dir(response) if 'think' in attr.lower()]
            if thinking_attrs:
                print(f"🧠 Other thinking attributes: {thinking_attrs}")

            # Sample response
            if response.text:
                print(f"\n📝 Response preview (first 500 chars):")
                sample = response.text[:500]
                if len(response.text) > 500:
                    sample += "..."
                print(f"   {sample}")

            results[desc] = {
                'success': True,
                'response_length': len(response.text) if response.text else 0,
                'elapsed_time': elapsed_time,
                'usage_metadata': response.usage_metadata.model_dump() if (hasattr(response, 'usage_metadata') and response.usage_metadata and hasattr(response.usage_metadata, 'model_dump')) else None
            }

        except Exception as e:
            print(f"❌ Error: {e}")
            results[desc] = {'success': False, 'error': str(e)}

    # Summary comparison
    print(f"\n{'='*60}")
    print("📊 COMPARISON SUMMARY")
    print(f"{'='*60}")

    for desc, result in results.items():
        if result['success']:
            print(f"\n{desc}:")
            print(f"  ✅ Success")
            print(f"  📄 Response: {result['response_length']} chars")
            print(f"  ⏱️  Time: {result['elapsed_time']:.2f}s")

            if result['usage_metadata']:
                print(f"  📊 Usage metadata available: ✅")
                # Look for any fields that might indicate thinking usage
                metadata = result['usage_metadata']
                if 'prompt_token_count' in metadata and 'candidates_token_count' in metadata:
                    total_tokens = metadata.get('prompt_token_count', 0) + metadata.get('candidates_token_count', 0)
                    print(f"  🪙 Total tokens: {total_tokens}")

                # Check for any fields that might relate to thinking
                potential_thinking_fields = [k for k in metadata.keys() if any(word in k.lower() for word in ['think', 'reason', 'process'])]
                if potential_thinking_fields:
                    print(f"  🧠 Potential thinking fields: {potential_thinking_fields}")
            else:
                print(f"  📊 Usage metadata: ❌")
        else:
            print(f"\n{desc}: ❌ Failed - {result['error']}")

    print(f"\n🏁 Test completed")

if __name__ == "__main__":
    test_system_instructions_with_usage()