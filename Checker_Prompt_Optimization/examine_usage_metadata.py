#!/usr/bin/env python3
import os
import json
from google import genai as new_genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv("backend/.env")

def examine_usage_metadata():
    """Examine usage_metadata to see if it contains thinking information"""

    print("🔍 Examining Usage Metadata for Thinking Information")
    print("=" * 60)

    client = new_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Use a citation validation prompt similar to our tests
    prompt = """
You are an APA 7th edition citation validator. Validate this citation:

_King James Bible_ (2017) King James Bible Online. https://www.kingjamesbibleonline.org/ (Original work published: 1769)

Provide validation results in APA format.
"""

    configs = [
        ("2.5-flash no thinking", "gemini-2.5-flash", types.ThinkingConfig(thinking_budget=0)),
        ("2.5-flash dynamic thinking", "gemini-2.5-flash", types.ThinkingConfig(thinking_budget=-1)),
        ("2.5-pro min thinking", "gemini-2.5-pro", types.ThinkingConfig(thinking_budget=128)),
    ]

    for desc, model, thinking_config in configs:
        print(f"\n🧠 {desc}")
        print("=" * 40)

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

            print(f"✅ Response received")
            print(f"📄 Response text length: {len(response.text) if response.text else 'None'} characters")

            # Examine usage_metadata
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                print(f"📊 Usage metadata type: {type(response.usage_metadata)}")
                print(f"📊 Usage metadata attributes: {[attr for attr in dir(response.usage_metadata) if not attr.startswith('_')]}")

                # Convert to dict for easier examination
                try:
                    metadata_dict = response.usage_metadata.model_dump() if hasattr(response.usage_metadata, 'model_dump') else str(response.usage_metadata)
                    print(f"📊 Usage metadata content:")
                    if isinstance(metadata_dict, dict):
                        for key, value in metadata_dict.items():
                            print(f"  {key}: {value}")
                    else:
                        print(f"  {metadata_dict}")
                except Exception as e:
                    print(f"  Error converting metadata: {e}")
            else:
                print(f"❌ No usage_metadata found or it's empty")

            # Check for any other thinking-related info
            thinking_attrs = [attr for attr in dir(response) if 'think' in attr.lower()]
            if thinking_attrs:
                print(f"🧠 Thinking-related attributes: {thinking_attrs}")
                for attr in thinking_attrs:
                    try:
                        value = getattr(response, attr)
                        print(f"  {attr}: {value}")
                    except Exception as e:
                        print(f"  {attr}: Error accessing - {e}")
            else:
                print(f"🧠 No thinking-related attributes found")

            # Sample of response content
            if response.text:
                print(f"📝 Response preview (first 300 chars):")
                print(f"  {response.text[:300]}...")

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🏁 Metadata examination completed")

if __name__ == "__main__":
    examine_usage_metadata()