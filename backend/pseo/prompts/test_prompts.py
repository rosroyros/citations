#!/usr/bin/env python3
"""Test prompt templates with LLMWriter."""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.llm_writer import LLMWriter
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_prompt(prompt_file: str) -> str:
    """Load prompt template from file."""
    prompt_path = Path(__file__).parent / prompt_file
    return prompt_path.read_text()


def test_introduction_prompt():
    """Test introduction prompt with sample topic."""
    logger.info("\n=== Testing Introduction Prompt ===")

    writer = LLMWriter()

    # Test topic: checking APA citations
    result = writer.generate_introduction(
        topic="checking APA citations",
        keywords=["check APA citations", "APA validation", "citation checker"],
        rules={"description": "APA 7 citation format rules"},
        pain_points=["90.9% of papers have citation errors", "Students spend hours checking citations manually"]
    )

    word_count = len(result.split())
    logger.info(f"Generated introduction: {word_count} words")
    logger.info(f"Content preview:\n{result[:300]}...")

    # Validate
    assert 150 <= word_count <= 300, f"Word count {word_count} outside range 150-300"
    assert "you" in result.lower(), "Should use second person"
    assert "APA" in result or "citation" in result.lower(), "Should mention topic"

    logger.info("✓ Introduction prompt test PASSED")
    return result


def test_explanation_prompt():
    """Test explanation prompt with sample concept."""
    logger.info("\n=== Testing Explanation Prompt ===")

    writer = LLMWriter()

    # Test concept: author name formatting
    result = writer.generate_explanation(
        concept="author name formatting in APA citations",
        rules={"description": "Last name, First initial. Middle initial. Format for authors in reference list"},
        examples=["Smith, J. K. (2020). Title.", "Jones, A. B., & Williams, C. D. (2021). Title."]
    )

    word_count = len(result.split())
    logger.info(f"Generated explanation: {word_count} words")
    logger.info(f"Content preview:\n{result[:300]}...")

    # Validate
    assert 300 <= word_count <= 700, f"Word count {word_count} outside range 300-700"
    assert "##" in result or "###" in result, "Should have headings"

    logger.info("✓ Explanation prompt test PASSED")
    return result


def test_faq_prompt():
    """Test FAQ prompt with sample topic."""
    logger.info("\n=== Testing FAQ Prompt ===")

    writer = LLMWriter()

    # Test topic: journal article citations
    result = writer.generate_faq(
        topic="citing journal articles in APA format",
        num_questions=5
    )

    logger.info(f"Generated {len(result)} FAQ items")
    for i, item in enumerate(result[:2], 1):
        logger.info(f"\nFAQ {i}:")
        logger.info(f"Q: {item['question']}")
        logger.info(f"A: {item['answer'][:100]}...")

    # Validate
    assert len(result) >= 4, f"Should generate at least 4 questions, got {len(result)}"
    assert all('question' in item and 'answer' in item for item in result), "Each item should have question and answer"

    logger.info("✓ FAQ prompt test PASSED")
    return result


def main():
    """Run all prompt tests."""
    logger.info("Starting prompt template tests...")
    logger.info("=" * 60)

    try:
        # Test introduction
        intro = test_introduction_prompt()

        # Test explanation
        explanation = test_explanation_prompt()

        # Test FAQ
        faq = test_faq_prompt()

        logger.info("\n" + "=" * 60)
        logger.info("✅ All prompt tests PASSED!")
        logger.info("\nPrompts are ready for use in content generation.")

        return 0

    except Exception as e:
        logger.error(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
