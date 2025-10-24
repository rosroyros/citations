"""
DSPy configuration for citation validator.
"""
import os
import dspy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global flag to track if DSPy is already configured
_dspy_configured = False
_dspy_lm = None


def setup_dspy(model: str = "gpt-4o-mini"):
    """
    Configure DSPy with OpenAI API.

    Args:
        model: Model name (default: gpt-4o-mini)

    Returns:
        dspy.LM: Configured language model instance
    """
    global _dspy_configured, _dspy_lm

    # Return existing LM if already configured
    if _dspy_configured and _dspy_lm is not None:
        return _dspy_lm

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    # Configure DSPy with OpenAI
    lm = dspy.LM(
        model=f"openai/{model}",
        api_key=api_key,
        max_tokens=2000,
        temperature=0.0  # Deterministic for validation tasks
    )

    # Set as default LM for DSPy only if not configured yet
    if not _dspy_configured:
        dspy.configure(lm=lm)
        _dspy_configured = True
        _dspy_lm = lm

    return lm


def test_dspy_connection():
    """Test DSPy connection with a simple query."""
    lm = setup_dspy()

    # Simple test
    response = lm("Say 'DSPy configured successfully!'")
    print(f"✓ DSPy configured successfully")
    print(f"✓ Model: {lm.model}")
    print(f"✓ Test response: {response}")

    return True


if __name__ == "__main__":
    test_dspy_connection()
