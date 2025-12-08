#!/usr/bin/env python3
import os
import json
import time
from google import genai as new_genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv("backend/.env")

def test_valid_citation():
    """Test with a known valid citation to see response format"""

    print("🧠 Testing Known Valid Citation (Should Have No Errors)")
    print("=" * 55)

    client = new_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Use our original optimized prompt as system instruction
    system_instruction = """You are an APA 7th edition citation validator.

For each citation, provide validation results in this exact format:

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

    # Use citation #2 which should be valid
    valid_citation = "Malory, T. (2017). _Le morte d'Arthur_ (P. J. C. Field, Ed.). D. S. Brewer."

    print(f"📝 System instruction: Using original detailed format")
    print(f"📋 Testing 1 valid citation with gemini-2.5-flash (default thinking)")
    print(f"📄 Citation: {valid_citation}")

    try:
        start_time = time.time()

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
                # NO explicit thinking_config - uses default
            ),
            contents=valid_citation
        )

        elapsed_time = time.time() - start_time

        print(f"\n✅ Response received in {elapsed_time:.2f}s")
        print(f"📄 Response text length: {len(response.text) if response.text else 'None'} characters")

        # Examine usage metadata
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            metadata_dict = response.usage_metadata.model_dump()
            thoughts_tokens = metadata_dict.get('thoughts_token_count', 0) or 0
            total_tokens = metadata_dict.get('total_token_count', 0) or 0

            print(f"\n📊 USAGE METADATA:")
            print(f"   Thoughts tokens: {thoughts_tokens}")
            print(f"   Total tokens: {total_tokens}")
            print(f"   Time: {elapsed_time:.2f}s")

        # Full response
        if response.text:
            print(f"\n📝 FULL RESPONSE:")
            print("=" * 50)
            print(response.text)
            print("=" * 50)

            # Check if it says "No errors"
            if "✓ No APA 7 formatting errors detected" in response.text:
                print(f"\n✅ Correctly identified as valid (no errors)")
            elif "❌" in response.text:
                print(f"\n❌ Found errors (might be incorrect)")
            else:
                print(f"\n⚠️  Unclear response format")

    except Exception as e:
        print(f"❌ Error: {e}")

    print(f"\n🏁 Valid citation test completed")

if __name__ == "__main__":
    test_valid_citation()