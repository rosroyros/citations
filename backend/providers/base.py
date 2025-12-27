from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import re


class CitationValidator(ABC):
    """
    Abstract base class for citation validation providers.

    All provider implementations must inherit from this class and
    implement the validate_citations method.
    """

    @abstractmethod
    async def validate_citations(self, citations: str, style: str = "apa7") -> Dict[str, Any]:
        """
        Validate citations against a style guide.

        Args:
            citations: Raw citation text (one or more citations)
            style: Citation style to validate against (default: "apa7")

        Returns:
        return {
            "results": [
                {
                    "citation": "original citation text",
                    "errors": ["error 1", "error 2"],
                    "is_valid": bool
                },
                ...
            ]
        }
        """
        pass

    def _format_markdown_to_html(self, text: str) -> str:
        """
        Convert markdown formatting (bold/italics) to HTML tags.
        
        Args:
            text: Text with markdown formatting (**bold**, _italic_)
            
        Returns:
            Text with HTML tags (<strong>bold</strong>, <em>italic</em>)
        """
        if not text:
            return text
            
        # Convert bold (**text**) to HTML <strong>
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        # Convert italics (_text_) to HTML <em>
        text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
        # Convert italics (*text*) to HTML <em> (handle only single asterisks)
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
        
        return text
