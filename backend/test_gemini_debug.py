#!/usr/bin/env python3
"""
Minimal test script to debug Gemini API connection issues
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

def test_imports():
    print("🔍 Testing imports...")

    try:
        import google.generativeai as genai
        print("✅ google.generativeai imported successfully")
        print(f"   Version: {getattr(genai, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"❌ Failed to import google.generativeai: {e}")
        return False

    try:
        from google import genai as new_genai
        from google.genai import types
        print("✅ New Google genai API imported successfully")
        return True
    except ImportError as e:
        print(f"⚠️  New Google genai API not available: {e}")
        return False

def test_api_key():
    print("\n🔑 Testing API key...")

    # Load from .env
    load_dotenv(".env")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env")
        return False

    if api_key.startswith("Your") or len(api_key) < 20:
        print(f"❌ API key appears invalid (starts with '{api_key[:10]}...', length: {len(api_key)})")
        return False

    print(f"✅ API key found (length: {len(api_key)})")
    print(f"   Prefix: {api_key[:10]}...")
    return True

def test_old_api():
    print("\n🔄 Testing legacy Gemini API...")

    try:
        import google.generativeai as genai

        load_dotenv(".env")
        api_key = os.getenv("GEMINI_API_KEY")

        genai.configure(api_key=api_key)

        # List available models
        models = genai.list_models()
        gemini_models = [m.name for m in models if "gemini" in m.name.lower()]

        print(f"✅ Found {len(gemini_models)} Gemini models:")
        for model in gemini_models[:5]:  # Show first 5
            print(f"   - {model}")

        # Test simple generation
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say 'API test successful'")

        if response and response.text:
            print(f"✅ Legacy API test successful: {response.text[:50]}...")
            return True
        else:
            print("❌ Legacy API: No response text")
            return False

    except Exception as e:
        print(f"❌ Legacy API failed: {type(e).__name__}: {str(e)[:200]}")
        return False

def test_new_api():
    print("\n🚀 Testing new Gemini API...")

    try:
        from google import genai as new_genai
        from google.genai import types

        load_dotenv(".env")
        api_key = os.getenv("GEMINI_API_KEY")

        client = new_genai.Client(api_key=api_key)

        # Test simple generation
        config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=100,
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Say 'New API test successful'",
            config=config
        )

        if response and response.text:
            print(f"✅ New API test successful: {response.text[:50]}...")
            return True
        else:
            print("❌ New API: No response text")
            return False

    except Exception as e:
        print(f"❌ New API failed: {type(e).__name__}: {str(e)[:200]}")
        return False

def test_from_app_context():
    print("\n🏗️  Testing from app context (using providers/gemini.py)...")

    try:
        from providers.gemini_provider import GeminiProvider

        provider = GeminiProvider()
        test_prompt = "Test prompt - just say 'Hello from Gemini'"

        response = provider.generate_completion(test_prompt)

        if response and response.strip():
            print(f"✅ GeminiProvider test successful: {response[:50]}...")
            return True
        else:
            print("❌ GeminiProvider: No response")
            return False

    except Exception as e:
        print(f"❌ GeminiProvider failed: {type(e).__name__}: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🐛 Gemini API Debug Test")
    print("=" * 50)

    success_count = 0
    total_tests = 0

    # Test 1: Imports
    total_tests += 1
    if test_imports():
        success_count += 1

    # Test 2: API Key
    total_tests += 1
    if test_api_key():
        success_count += 1

    # Test 3: Legacy API
    total_tests += 1
    if test_old_api():
        success_count += 1

    # Test 4: New API
    total_tests += 1
    if test_new_api():
        success_count += 1

    # Test 5: From app context
    total_tests += 1
    if test_from_app_context():
        success_count += 1

    print("\n" + "=" * 50)
    print(f"📊 Results: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("🎉 All tests passed! Gemini API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())