"""
Manual test of DSPy predictor in isolation.
"""
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.providers.dspy_provider import DSPyProvider


def test_predictor_sync():
    """Test DSPy predictor in synchronous context."""
    print("Initializing DSPy provider...")
    provider = DSPyProvider()

    print(f"Provider initialized: {provider}")
    print(f"Predictor: {provider.predictor}")

    # Test citation
    citation = "Smith, J., & Jones, M. (2023). Understanding research methods. _Journal of Academic Studies_, _45_(2), 123-145. https://doi.org/10.1234/example"

    print(f"\nTesting citation: {citation[:80]}...")

    try:
        # Call predictor directly (synchronous)
        print("Calling predictor...")
        prediction = provider.predictor(citation=citation)

        print(f"\nPrediction successful!")
        print(f"Reasoning: {prediction.reasoning[:200]}...")
        print(f"Is Valid: {prediction.is_valid}")
        print(f"Explanation: {prediction.explanation[:200]}...")

        return True

    except Exception as e:
        print(f"\n❌ Error calling predictor: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_validation():
    """Test full validation flow (async)."""
    import asyncio

    print("\n" + "="*70)
    print("Testing full validation flow (async)")
    print("="*70)

    provider = DSPyProvider()
    citation = "Smith, J., & Jones, M. (2023). Understanding research methods. _Journal of Academic Studies_, _45_(2), 123-145. https://doi.org/10.1234/example"

    async def run_validation():
        try:
            print("Calling validate_citations (async)...")
            result = await provider.validate_citations(citation, style="apa7")

            print(f"\nValidation successful!")
            print(f"Results: {result}")
            return True

        except Exception as e:
            print(f"\n❌ Error in validation: {e}")
            import traceback
            traceback.print_exc()
            return False

    return asyncio.run(run_validation())


if __name__ == "__main__":
    print("="*70)
    print("DSPy Predictor Manual Test")
    print("="*70)

    # Test 1: Synchronous predictor call
    success1 = test_predictor_sync()

    # Test 2: Full async validation
    if success1:
        success2 = test_full_validation()

        if success2:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Async validation failed")
    else:
        print("\n❌ Predictor test failed - skipping async test")
