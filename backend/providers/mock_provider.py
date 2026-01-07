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

            # Convert markdown formatting to HTML for frontend display
            # Use shared method from base class
            original_with_formatting = self._format_markdown_to_html(citation_text)

            # Alternate between valid and citations with errors
            if i % 3 == 0:
                # Valid citation (no errors)
                results.append({
                    "citation_number": i + 1,
                    "original": original_with_formatting,
                    "source_type": "journal",
                    "errors": [],
                    "corrected_citation": None
                })
            else:
                # Citation with typical APA 7 errors
                # Create a simple "corrected" version by lowercasing to simulate the sentence case fix
                corrected_text = original_with_formatting.lower()
                
                results.append({
                    "citation_number": i + 1,
                    "original": original_with_formatting,
                    "source_type": "journal" if i % 2 == 0 else "book",
                    "errors": [
                        {
                            "component": "Title",
                            "problem": "Journal article title should use sentence case (only first word and proper nouns capitalized)",
                            "correction": corrected_text
                        }
                    ],
                    "corrected_citation": corrected_text
                })

        return {
            "results": results
        }

    def generate_completion(self, prompt: str) -> str:
        """
        Generate a mock completion for inline citation validation.

        Returns JSON that matches inline citations to references.

        Args:
            prompt: The LLM prompt for inline validation

        Returns:
            JSON string with mock inline validation results
        """
        import json
        import re

        # Extract citation IDs and text from prompt (format: "c1: (Smith, 2019)")
        citation_pattern = r'(c\d+):\s*(.+?)(?=\nc\d+:|$)'
        citation_matches = re.findall(citation_pattern, prompt, re.DOTALL)

        if not citation_matches:
            # Fallback: try JSON pattern
            json_pattern = r'"id":\s*"(c\d+)"'
            citation_ids = re.findall(json_pattern, prompt)
            citation_matches = [(cid, f"(Mock Citation {i})") for i, cid in enumerate(citation_ids)]

        if not citation_matches:
            # Last fallback
            citation_matches = [(f"c{i}", f"(Mock {i})") for i in range(1, 6)]

        results = []
        for i, (cid, text) in enumerate(citation_matches):
            text = text.strip()
            # Alternate between matched and orphaned for testing
            if i % 4 == 0:
                # Orphan (no match)
                results.append({
                    "id": cid,
                    "citation_text": text,
                    "match_status": "orphan",
                    "matched_ref_index": None,
                    "notes": "No matching reference found"
                })
            elif i % 4 == 1:
                # Matched
                results.append({
                    "id": cid,
                    "citation_text": text,
                    "match_status": "matched",
                    "matched_ref_index": (i % 5) + 1,
                    "notes": None
                })
            elif i % 4 == 2:
                # Mismatch (wrong format)
                results.append({
                    "id": cid,
                    "citation_text": text,
                    "match_status": "mismatch",
                    "matched_ref_index": (i % 5) + 1,
                    "notes": "Year format incorrect"
                })
            else:
                # Ambiguous
                results.append({
                    "id": cid,
                    "citation_text": text,
                    "match_status": "ambiguous",
                    "matched_ref_index": (i % 5) + 1,
                    "notes": "Multiple possible matches"
                })

        return json.dumps({"results": results})
