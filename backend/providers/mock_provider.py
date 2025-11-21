"""Mock LLM provider for fast E2E testing without API calls."""
from typing import Dict, Any
from providers.base import CitationValidator


class MockProvider(CitationValidator):
    """
    Mock citation validator that returns instant responses without API calls.
    Used for E2E testing to avoid slow/expensive OpenAI calls.
    """

    async def validate_citations(self, citations: str, style: str = "apa7") -> Dict[str, Any]:
        """
        Return mock validation results instantly.

        Returns realistic validation data for common test cases:
        - Citations with typical APA 7 errors (capitalization, formatting)
        - Mix of valid and invalid citations
        - Fast response (<100ms)

        Args:
            citations: Raw citation text
            style: Citation style (ignored in mock)

        Returns:
            Mock validation results matching OpenAI format
        """
        # Parse citation count (split by newlines)
        citation_lines = [line.strip() for line in citations.strip().split('\n') if line.strip()]
        num_citations = len(citation_lines)

        # Generate mock results
        results = []
        for i in range(num_citations):
            citation_text = citation_lines[i] if i < len(citation_lines) else f"Citation {i+1}"

            # Alternate between valid and citations with errors
            if i % 3 == 0:
                # Valid citation (no errors)
                results.append({
                    "citation_number": i + 1,
                    "original": citation_text,
                    "source_type": "journal",
                    "errors": []
                })
            else:
                # Citation with typical APA 7 errors
                results.append({
                    "citation_number": i + 1,
                    "original": citation_text,
                    "source_type": "journal" if i % 2 == 0 else "book",
                    "errors": [
                        {
                            "component": "Title",
                            "problem": "Journal article title should use sentence case (only first word and proper nouns capitalized)",
                            "correction": citation_text.lower()
                        }
                    ]
                })

        return {
            "results": results
        }
