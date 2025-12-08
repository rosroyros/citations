#!/usr/bin/env python3
import os
import json
from google import genai as new_genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv("backend/.env")

def test_thinking_metadata():
    """Test if thinking responses contain metadata about thinking time/tokens"""

    print("🧠 Testing Thinking Mode Metadata Extraction")
    print("=" * 50)

    client = new_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Test with a simple prompt to see response structure
    prompt = "What is 2+2? Show your work step by step."

    configs = [
        ("2.5-flash no thinking", "gemini-2.5-flash", types.ThinkingConfig(thinking_budget=0)),
        ("2.5-flash dynamic thinking", "gemini-2.5-flash", types.ThinkingConfig(thinking_budget=-1)),
        ("2.5-pro min thinking", "gemini-2.5-pro", types.ThinkingConfig(thinking_budget=128)),
        ("2.5-pro dynamic thinking", "gemini-2.5-pro", types.ThinkingConfig(thinking_budget=-1)),
    ]

    for desc, model, thinking_config in configs:
        print(f"\n🔍 Testing {desc}:")
        print("-" * 30)

        try:
            config = types.GenerateContentConfig(
                temperature=1.0,
                max_output_tokens=1000,
                thinking_config=thinking_config
            )

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )

            print(f"Response type: {type(response)}")
            print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")

            # Check for thinking-related attributes
            thinking_attrs = [attr for attr in dir(response) if 'think' in attr.lower()]
            if thinking_attrs:
                print(f"Thinking-related attributes: {thinking_attrs}")

            # Try to access potential thinking metadata
            if hasattr(response, 'thinking_metadata'):
                print(f"Thinking metadata: {response.thinking_metadata}")
            elif hasattr(response, 'metadata'):
                print(f"Metadata: {response.metadata}")

            # Check response text length
            print(f"Response text length: {len(response.text)} characters")
            print(f"First 200 chars: {response.text[:200]}...")

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🏁 Test completed")

if __name__ == "__main__":
    test_thinking_metadata()