import pytest
from backend.prompt_manager import PromptManager


def test_load_prompt():
    """Test that prompt manager loads validation prompt from file."""
    pm = PromptManager()
    prompt = pm.load_prompt()

    assert prompt is not None
    assert len(prompt) > 0
    assert isinstance(prompt, str)
    # Should contain APA 7 validation rules
    assert "APA 7" in prompt or "APA 7th" in prompt


def test_format_single_citation():
    """Test formatting a single citation."""
    pm = PromptManager()
    citations_text = "Smith, J. (2023). Sample article. Journal Name, 10(2), 123-145."

    formatted = pm.format_citations(citations_text)

    assert isinstance(formatted, str)
    assert citations_text in formatted


def test_format_multiple_citations_double_newline():
    """Test formatting multiple citations separated by double newlines."""
    pm = PromptManager()
    citations_text = """Smith, J. (2023). First article. Journal, 10(2), 123-145.

Doe, A. (2022). Second article. Another Journal, 5(1), 45-67."""

    formatted = pm.format_citations(citations_text)

    assert "Smith, J." in formatted
    assert "Doe, A." in formatted


def test_format_multiple_citations_single_newline():
    """Test formatting multiple citations separated by single newlines."""
    pm = PromptManager()
    citations_text = """Smith, J. (2023). First article. Journal, 10(2), 123-145.
Doe, A. (2022). Second article. Another Journal, 5(1), 45-67."""

    formatted = pm.format_citations(citations_text)

    assert "Smith, J." in formatted
    assert "Doe, A." in formatted


def test_format_empty_citations():
    """Test that empty citations are handled."""
    pm = PromptManager()

    with pytest.raises(ValueError, match="Citations cannot be empty"):
        pm.format_citations("")

    with pytest.raises(ValueError, match="Citations cannot be empty"):
        pm.format_citations("   ")


def test_build_full_prompt():
    """Test building complete prompt with citations."""
    pm = PromptManager()
    citations_text = "Smith, J. (2023). Sample article. Journal Name, 10(2), 123-145."

    full_prompt = pm.build_prompt(citations_text)

    # Should contain both the validation rules and the citations
    assert "APA 7" in full_prompt or "APA 7th" in full_prompt
    assert citations_text in full_prompt
    assert len(full_prompt) > len(citations_text)  # Prompt + citations
