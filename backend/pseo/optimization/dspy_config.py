"""
DSPy configuration for citation validator optimization.
"""
import os
import dspy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_dspy():
    """
    Configure DSPy with OpenAI API.

    Returns:
        dspy.LM: Configured language model instance
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    # Configure DSPy with OpenAI
    # Using gpt-4o-mini for cost-effective optimization
    lm = dspy.LM(
        model="openai/gpt-4o-mini",
        api_key=api_key,
        max_tokens=2000,
        temperature=0.0  # Deterministic for validation tasks
    )

    # Set as default LM for DSPy
    dspy.configure(lm=lm)

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
