import os
import re
import json
import time
from typing import Dict, Any, List
from backend.providers.base import CitationValidator
from backend.logger import setup_logger

logger = setup_logger("dspy_provider")


class DSPyProvider(CitationValidator):
    """
    DSPy-based citation validator using optimized prompts.
    """

    def __init__(self, model: str = "gpt-4o-mini", optimized_prompt_path: str = None):
        """
        Initialize DSPy provider.

        Args:
            model: Model name to use (default: gpt-4o-mini)
            optimized_prompt_path: Path to optimized DSPy prompt JSON file
        """
        self.model = model
        self.optimized_prompt_path = optimized_prompt_path or os.path.join(
            "Checker_Prompt_Optimization",
            "optimized_output_v2",
            "optimized_validator_v2.json"
        )

        # Lazy import DSPy (only when this provider is used)
        import dspy
        self.dspy = dspy

        # Setup DSPy with OpenAI
        from backend.dspy_config import setup_dspy
        self.lm = setup_dspy(model=model)

        # Load optimized prompt and create predictor
        self.predictor = self._load_optimized_predictor()

        logger.info(f"DSPy provider initialized with model: {model}")
        logger.info(f"Loaded optimized prompt from: {self.optimized_prompt_path}")

    def _load_optimized_predictor(self):
        """Load the optimized DSPy predictor with custom signature."""
        logger.info(f"Loading optimized prompt from {self.optimized_prompt_path}")

        with open(self.optimized_prompt_path, 'r') as f:
            optimized_data = json.load(f)

        # Extract instructions from optimized prompt
        signature_data = optimized_data["predictor.predict"]["signature"]
        optimized_instructions = signature_data["instructions"]

        logger.info(f"Loaded optimized instructions ({len(optimized_instructions)} chars)")

        # Create signature with optimized instructions
        class OptimizedCitationValidation(self.dspy.Signature):
            citation = self.dspy.InputField(desc="Citation string with Markdown italics (_text_). Note: Markdown _text_ format indicates italics and is CORRECT.")
            reasoning = self.dspy.OutputField(desc="Step-by-step reasoning for validation")
            is_valid = self.dspy.OutputField(desc="true if citation follows APA 7th edition rules, false otherwise")
            explanation = self.dspy.OutputField(desc="Brief explanation of why the citation is valid or invalid")

        # Apply optimized instructions
        OptimizedCitationValidation.__doc__ = optimized_instructions

        # Create predictor with ChainOfThought
        predictor = self.dspy.ChainOfThought(OptimizedCitationValidation)

        logger.info("Optimized predictor created successfully")
        return predictor

    async def validate_citations(self, citations: str, style: str = "apa7") -> Dict[str, Any]:
        """
        Validate citations using DSPy optimized predictor.

        Args:
            citations: Raw citation text (can be HTML or plain text)
            style: Citation style (default: "apa7")

        Returns:
            Validation results dictionary with structured errors
        """
        logger.info(f"Starting DSPy validation for {len(citations)} characters")
        logger.debug(f"Citations preview: {citations[:200]}...")

        # Convert HTML to plain text if needed
        start_time = time.time()
        text_citations = self._html_to_text(citations)

        # Split into individual citations
        citation_list = self._split_citations(text_citations)
        logger.info(f"Split into {len(citation_list)} individual citation(s)")

        # Validate each citation
        results = []
        for idx, citation_text in enumerate(citation_list, 1):
            logger.info(f"Validating citation #{idx}")

            try:
                # Call DSPy predictor in thread pool (DSPy uses sync OpenAI client)
                import asyncio
                import functools
                loop = asyncio.get_event_loop()

                api_start = time.time()
                prediction = await loop.run_in_executor(
                    None,
                    functools.partial(self.predictor, citation=citation_text)
                )
                api_time = time.time() - api_start

                logger.info(f"DSPy prediction completed in {api_time:.3f}s")
                logger.debug(f"Reasoning: {prediction.reasoning[:100]}...")
                logger.debug(f"Is Valid: {prediction.is_valid}")
                logger.debug(f"Explanation: {prediction.explanation[:100]}...")

                # Parse prediction into structured format
                result = self._parse_prediction(idx, citation_text, prediction)
                results.append(result)

            except Exception as e:
                logger.error(f"Error validating citation #{idx}: {str(e)}", exc_info=True)
                # Add error result
                results.append({
                    "citation_number": idx,
                    "original": citation_text,
                    "source_type": "unknown",
                    "errors": [{
                        "component": "System",
                        "problem": f"Validation error: {str(e)}",
                        "correction": "Please try again or contact support"
                    }]
                })

        total_time = time.time() - start_time
        logger.info(f"Total validation time: {total_time:.3f}s for {len(results)} citation(s)")

        return {
            "results": results
        }

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text, preserving structure."""
        # Remove HTML tags but preserve line breaks
        text = re.sub(r'<br\s*/?>', '\n', html)
        text = re.sub(r'<p[^>]*>', '\n', text)
        text = re.sub(r'</p>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)

        # Decode HTML entities
        import html as html_lib
        text = html_lib.unescape(text)

        return text.strip()

    def _split_citations(self, text: str) -> List[str]:
        """Split text into individual citations."""
        # Split by double newlines or single newlines
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Filter out very short lines (likely not citations)
        citations = [line for line in lines if len(line) > 20]

        return citations if citations else [text]

    def _parse_prediction(self, citation_num: int, original: str, prediction) -> Dict[str, Any]:
        """
        Parse DSPy prediction into API response format.

        Converts markdown italics (_text_) to HTML (<em>text</em>).
        """
        # Parse is_valid
        is_valid_str = str(prediction.is_valid).lower()
        is_valid = is_valid_str in ['true', '1', 'yes']

        # Detect source type from explanation (simple heuristic)
        source_type = self._detect_source_type(original, prediction.explanation)

        # Parse errors from explanation
        errors = []
        if not is_valid:
            errors = self._parse_errors_from_explanation(prediction.explanation)

        # Convert markdown italics to HTML in original citation
        original_html = self._markdown_to_html(original)

        return {
            "citation_number": citation_num,
            "original": original_html,
            "source_type": source_type,
            "errors": errors
        }

    def _detect_source_type(self, citation: str, explanation: str) -> str:
        """Detect source type from citation and explanation."""
        citation_lower = citation.lower()
        explanation_lower = explanation.lower()

        # Check for common patterns
        if 'journal' in explanation_lower or 'article' in explanation_lower:
            return "Journal Article"
        elif 'book chapter' in explanation_lower:
            return "Book Chapter"
        elif 'book' in explanation_lower:
            return "Book"
        elif 'webpage' in explanation_lower or 'website' in explanation_lower or 'http' in citation_lower:
            return "Webpage"
        elif 'dissertation' in explanation_lower:
            return "Dissertation"
        else:
            return "Unknown"

    def _parse_errors_from_explanation(self, explanation: str) -> List[Dict[str, str]]:
        """
        Parse structured errors from the explanation text.

        The optimized prompt may output errors in various formats.
        We extract component, problem, and correction.
        """
        errors = []

        # Try to find structured error patterns
        # Pattern 1: "Component: Problem. Correction: Fix."
        pattern1 = r'(?:❌|-)?\s*([A-Za-z\s]+):\s*([^\.]+)\.\s*(?:Correction|Should be|Fix):\s*([^\.]+)'
        matches = re.finditer(pattern1, explanation, re.IGNORECASE)

        for match in matches:
            component = match.group(1).strip()
            problem = match.group(2).strip()
            correction = match.group(3).strip()

            errors.append({
                "component": component.title(),
                "problem": problem,
                "correction": correction
            })

        # If no structured errors found, create generic error
        if not errors and explanation:
            errors.append({
                "component": "Format",
                "problem": explanation[:200],
                "correction": "Please review APA 7th edition guidelines"
            })

        return errors

    def _markdown_to_html(self, text: str) -> str:
        r"""
        Convert markdown italics (_text_) to HTML (<em>text</em>).

        Simple conversion: _text_ -> <em>text</em>
        """
        # Convert markdown italics to HTML
        # Match underscores that wrap content (non-greedy)
        text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)

        return text
