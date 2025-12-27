import pytest
from unittest.mock import Mock
from providers.openai_provider import OpenAIProvider

class TestOpenAIParsing:
    """Unit tests for OpenAIProvider parsing logic."""

    @pytest.fixture
    def provider(self):
        """Create OpenAIProvider instance."""
        return OpenAIProvider(api_key="test-key")

    def test_parse_response_success(self, provider):
        """Test successful response parsing with expected format."""
        response = """
═══════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════
ORIGINAL: Smith, J. (2020). The book title. Publisher.
SOURCE TYPE: Book
VALIDATION RESULTS:
✓ No APA 7 formatting errors detected

═══════════════════════════════════════════════════════════════
CITATION #2
═══════════════════════════════════════════════════════════════
ORIGINAL: Doe, J. (2021). Article title. *Journal Name*, 15(3), 123-145.
SOURCE TYPE: Journal Article
VALIDATION RESULTS:
❌ Title: Article titles should be in sentence case
Should be: Article title
❌ Volume: Volume number should be italicized
Should be: *Journal Name*, *15*(3), 123-145

───────────────────────────────────────────────────────────────
CORRECTED CITATION:
Doe, J. (2021). Article title. *Journal Name*, *15*(3), 123-145.
───────────────────────────────────────────────────────────────
        """.strip()

        results = provider._parse_response(response)

        assert len(results) == 2

        # Check first citation (no errors)
        assert results[0]["citation_number"] == 1
        assert results[0]["original"] == "Smith, J. (2020). The book title. Publisher."
        assert len(results[0]["errors"]) == 0
        assert results[0].get("corrected_citation") is None

        # Check second citation (has errors and correction)
        assert results[1]["citation_number"] == 2
        assert len(results[1]["errors"]) == 2
        
        # Verify markdown to HTML conversion
        assert "<em>Journal Name</em>" in results[1]["corrected_citation"]
        assert "<em>15</em>" in results[1]["corrected_citation"]

    def test_corrected_citation_discarded_when_no_errors(self, provider):
        """Test that corrected citation is discarded if no errors found."""
        response = """
CITATION #1
═══════════════════════════════════════════════════════════════
ORIGINAL: Smith, J. (2020). Title. Publisher.
SOURCE TYPE: Book
VALIDATION RESULTS:
✓ No APA 7 formatting errors detected

───────────────────────────────────────────────────────────────
CORRECTED CITATION:
Different Text
───────────────────────────────────────────────────────────────
        """.strip()
        
        results = provider._parse_response(response)
        assert len(results) == 1
        assert results[0].get("corrected_citation") is None

    def test_corrected_citation_discarded_when_identical(self, provider):
       """Test that corrected citation is discarded if identical to original."""
       response = """
CITATION #1
═══════════════════════════════════════════════════════════════
ORIGINAL: Smith, J. (2020). _Title_. Publisher.
SOURCE TYPE: Book
VALIDATION RESULTS:
❌ Random: Error
Should be: fix

───────────────────────────────────────────────────────────────
CORRECTED CITATION:
Smith, J. (2020). _Title_. Publisher.
───────────────────────────────────────────────────────────────
       """.strip()
       
       results = provider._parse_response(response)
       assert len(results) == 1
       assert results[0].get("corrected_citation") is None

    def test_parse_response_corrected_citation_multiline(self, provider):
        """Test parsing of multi-line corrected citation."""
        response = """
CITATION #1
═══════════════════════════════════════════════════════════════
ORIGINAL: Smith, J. (2020). WRONG Title. Publisher.
SOURCE TYPE: Book
VALIDATION RESULTS:
❌ Title: Error found
Should be: Correct Title

───────────────────────────────────────────────────────────────
CORRECTED CITATION:
Smith, J. (2020).
Correct Title.
Publisher.
───────────────────────────────────────────────────────────────
        """.strip()
        
        results = provider._parse_response(response)
        assert len(results) == 1
        assert results[0].get("corrected_citation") == "Smith, J. (2020). Correct Title. Publisher."

    def test_markdown_formatting_helper(self, provider):
        """Test inherited markdown formatting helper."""
        input_text = "**Bold** and _Italic_ and *Other*"
        expected = "<strong>Bold</strong> and <em>Italic</em> and <em>Other</em>"
        assert provider._format_markdown_to_html(input_text) == expected
