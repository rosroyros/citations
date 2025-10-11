from abc import ABC, abstractmethod
from typing import Dict, Any


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
            Dictionary with validation results:
            {
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
