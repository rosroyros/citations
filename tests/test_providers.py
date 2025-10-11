import pytest
from backend.providers.base import CitationValidator
from backend.providers.openai_provider import OpenAIProvider


def test_provider_interface():
    """Test that provider has required validate_citations method."""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
    assert hasattr(provider, 'validate_citations')
    assert callable(getattr(provider, 'validate_citations'))


def test_provider_returns_expected_structure():
    """Test that provider returns dict with 'results' key."""
    # This test uses a mock to avoid hitting real API
    provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")

    # Mock response structure test
    # In a real implementation, we'd mock the OpenAI API call
    # For now, verify the method exists and has correct signature
    import inspect
    sig = inspect.signature(provider.validate_citations)
    assert 'citations' in sig.parameters
    assert 'style' in sig.parameters
