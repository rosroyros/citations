"""
Unit tests for DSPy provider.
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.providers.dspy_provider import DSPyProvider


@pytest.mark.asyncio
async def test_dspy_provider_init():
    """Test DSPy provider initialization."""
    provider = DSPyProvider()
    assert provider is not None
    assert provider.predictor is not None


@pytest.mark.asyncio
async def test_dspy_provider_valid_citation():
    """Test DSPy provider with a valid citation."""
    provider = DSPyProvider()

    # Valid journal article citation
    citation = "Smith, J., & Jones, M. (2023). Understanding research methods. _Journal of Academic Studies_, _45_(2), 123-145. https://doi.org/10.1234/example"

    result = await provider.validate_citations(citation, style="apa7")

    assert result is not None
    assert "results" in result
    assert len(result["results"]) > 0

    # Check structure
    first_result = result["results"][0]
    assert "citation_number" in first_result
    assert "original" in first_result
    assert "source_type" in first_result
    assert "errors" in first_result

    # Check that markdown italics were converted to HTML
    assert "<em>" in first_result["original"]
    assert "_" not in first_result["original"] or r"\_" in first_result["original"]


@pytest.mark.asyncio
async def test_dspy_provider_invalid_citation():
    """Test DSPy provider with an invalid citation."""
    provider = DSPyProvider()

    # Invalid citation (missing italics, wrong punctuation)
    citation = "Smith J. (2023) Understanding research methods Journal of Academic Studies 45(2) 123-145"

    result = await provider.validate_citations(citation, style="apa7")

    assert result is not None
    assert "results" in result
    assert len(result["results"]) > 0

    # Should detect errors
    first_result = result["results"][0]
    # Note: DSPy may or may not detect errors depending on the model
    # Just verify structure is correct
    assert isinstance(first_result["errors"], list)


@pytest.mark.asyncio
async def test_dspy_provider_multiple_citations():
    """Test DSPy provider with multiple citations."""
    provider = DSPyProvider()

    citations = """Smith, J., & Jones, M. (2023). Understanding research methods. _Journal of Academic Studies_, _45_(2), 123-145. https://doi.org/10.1234/example

Brown, A. (2022). _Writing in APA style_. Academic Press."""

    result = await provider.validate_citations(citations, style="apa7")

    assert result is not None
    assert "results" in result
    assert len(result["results"]) >= 2  # Should split into at least 2 citations


def test_markdown_to_html_conversion():
    """Test markdown to HTML conversion."""
    provider = DSPyProvider()

    # Test basic italics
    text = "This is _italic text_ in markdown"
    html = provider._markdown_to_html(text)
    assert "<em>italic text</em>" in html
    assert "This is <em>italic text</em> in markdown" == html

    # Test multiple italics
    text = "_Journal Title_, _45_(2), pages"
    html = provider._markdown_to_html(text)
    assert "<em>Journal Title</em>" in html
    assert "<em>45</em>" in html


def test_html_to_text():
    """Test HTML to text conversion."""
    provider = DSPyProvider()

    html = "<p>Smith, J. (2023). <em>Book title</em>. Publisher.</p>"
    text = provider._html_to_text(html)

    assert "Smith, J. (2023)." in text
    assert "Book title" in text
    assert "Publisher" in text
    assert "<p>" not in text
    assert "<em>" not in text


def test_split_citations():
    """Test citation splitting."""
    provider = DSPyProvider()

    text = """Citation 1 here with some content.

Citation 2 here with different content.

Citation 3 here with more content."""

    citations = provider._split_citations(text)

    assert len(citations) == 3
    assert "Citation 1" in citations[0]
    assert "Citation 2" in citations[1]
    assert "Citation 3" in citations[2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
