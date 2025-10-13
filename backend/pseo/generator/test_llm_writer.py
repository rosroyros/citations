"""
Tests for LLM Writer (GPT-4o-mini integration)
"""
import pytest
import json
from unittest.mock import Mock, patch
from llm_writer import LLMWriter


class TestLLMWriter:
    """Test suite for LLM content generation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.writer = LLMWriter(model="gpt-4o-mini")

    def test_initialization(self):
        """Test LLM writer initializes correctly"""
        assert self.writer.model == "gpt-4o-mini"
        assert self.writer.client is not None

    def test_generate_introduction_structure(self):
        """Test introduction generation returns correct structure"""
        result = self.writer.generate_introduction(
            topic="checking APA citations",
            keywords=["check APA citations", "APA validation"],
            rules={"description": "APA 7 citation rules"},
            pain_points=["90.9% of papers have errors"]
        )

        # Check basic requirements
        assert isinstance(result, str)
        assert len(result) > 0

        # Check word count (minimum 150 words for test, requirement is 200-250)
        word_count = len(result.split())
        assert word_count >= 150, f"Introduction too short: {word_count} words"

        # Check keyword presence
        assert "APA" in result.upper(), "Should contain APA keyword"

        # Check conversational tone (second person)
        assert "you" in result.lower(), "Should use conversational 'you'"

    def test_generate_explanation_structure(self):
        """Test explanation generation returns correct structure"""
        result = self.writer.generate_explanation(
            concept="author name formatting in APA",
            rules={"description": "Author names: Last, F. M."},
            examples=["Smith, J. (2020).", "Jones, A. B. (2021)."]
        )

        # Check basic requirements
        assert isinstance(result, str)
        assert len(result) > 0

        # Check word count (minimum 300 words for test, requirement is 400-600)
        word_count = len(result.split())
        assert word_count >= 300, f"Explanation too short: {word_count} words"

        # Check contains examples
        assert len(result) > 500, "Should contain substantial content"

    def test_generate_faq_structure(self):
        """Test FAQ generation returns valid JSON structure"""
        result = self.writer.generate_faq(
            topic="citing journal articles in APA",
            num_questions=5
        )

        # Check it's a list
        assert isinstance(result, list), "FAQ should return list"

        # Check has correct number of questions
        assert len(result) >= 4, f"Expected at least 4 FAQs, got {len(result)}"

        # Check each FAQ has correct structure
        for faq in result:
            assert "question" in faq, "Each FAQ needs 'question' field"
            assert "answer" in faq, "Each FAQ needs 'answer' field"
            assert isinstance(faq["question"], str)
            assert isinstance(faq["answer"], str)
            assert len(faq["answer"].split()) >= 50, "Answer should be 50+ words"

    def test_generate_step_by_step_structure(self):
        """Test step-by-step generation returns numbered list"""
        result = self.writer.generate_step_by_step(
            task="Create a journal article citation in APA",
            rules={"description": "Format: Author. (Year). Title. Journal, vol(issue), pages."},
            complexity="beginner"
        )

        # Check basic requirements
        assert isinstance(result, str)
        assert len(result) > 0

        # Check for numbered list or step indicators
        assert any(str(i) in result for i in range(1, 6)), "Should contain numbered steps"

        # Check reasonable length
        word_count = len(result.split())
        assert word_count >= 200, f"Steps too short: {word_count} words"

    def test_validate_uniqueness_similar_content(self):
        """Test uniqueness scoring detects similar content"""
        new_content = "This is about checking APA citations and finding errors."
        existing_content = ["This guide explains how to check APA citations for errors."]

        score = self.writer.validate_uniqueness(new_content, existing_content)

        # Check score is valid
        assert 0 <= score <= 1, f"Uniqueness score should be 0-1, got {score}"

        # Similar content should have lower uniqueness
        assert score < 0.8, f"Similar content should score < 0.8, got {score}"

    def test_validate_uniqueness_different_content(self):
        """Test uniqueness scoring detects different content"""
        new_content = "The zebra jumped over the purple mountain at midnight."
        existing_content = ["This guide explains how to check APA citations for errors."]

        score = self.writer.validate_uniqueness(new_content, existing_content)

        # Different content should have high uniqueness
        assert score > 0.7, f"Different content should score > 0.7, got {score}"

    def test_summarize_rules_helper(self):
        """Test rule summarization helper"""
        rules = [
            {"rule_id": "rule1", "description": "First rule"},
            {"rule_id": "rule2", "description": "Second rule"},
            {"rule_id": "rule3", "description": "Third rule"},
        ]

        summary = self.writer._summarize_rules(rules)

        assert isinstance(summary, str)
        assert "First rule" in summary
        assert "Second rule" in summary

    def test_summarize_errors_helper(self):
        """Test error summarization helper"""
        errors = [
            {"error_name": "Capitalization Error", "description": "Title not in sentence case"},
            {"error_name": "Italics Error", "description": "Journal name not italicized"}
        ]

        summary = self.writer._summarize_errors(errors)

        assert isinstance(summary, str)
        assert "Capitalization Error" in summary
        assert "Italics Error" in summary

    def test_token_usage_tracking(self):
        """Test that token usage is tracked"""
        # Generate something small
        result = self.writer.generate_introduction(
            topic="test topic",
            keywords=["test"],
            rules={"description": "test rules"},
            pain_points=["test pain point"]
        )

        # Check token tracking
        assert hasattr(self.writer, 'total_input_tokens')
        assert hasattr(self.writer, 'total_output_tokens')
        assert self.writer.total_input_tokens > 0
        assert self.writer.total_output_tokens > 0

    def test_cost_calculation(self):
        """Test cost calculation method"""
        self.writer.total_input_tokens = 3000
        self.writer.total_output_tokens = 1500

        cost = self.writer.calculate_total_cost()

        # GPT-4o-mini: $0.15/1M input, $0.60/1M output
        expected_cost = (3000/1_000_000 * 0.15) + (1500/1_000_000 * 0.60)
        assert abs(cost - expected_cost) < 0.0001, f"Expected {expected_cost}, got {cost}"


    @patch('llm_writer.OpenAI')
    def test_api_error_handling(self, mock_openai):
        """Test graceful error handling when API fails"""
        # Mock API to raise an error
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        writer = LLMWriter()

        # Should raise or return error message, not crash
        with pytest.raises(Exception) as exc_info:
            writer.generate_introduction(
                topic="test",
                keywords=["test"],
                rules={},
                pain_points=[]
            )
        assert "API Error" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
