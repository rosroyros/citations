"""
Prompt management for citation validation.
Loads validation prompts and formats citations for LLM input.
"""
import os
from pathlib import Path
from logger import setup_logger

logger = setup_logger("prompt_manager")


class PromptManager:
    """Manages loading and formatting of validation prompts."""

    def __init__(self, prompt_path: str = None):
        """
        Initialize prompt manager.

        Args:
            prompt_path: Optional custom path to prompt file.
                        Defaults to backend/prompts/validator_prompt.txt
        """
        if prompt_path is None:
            # Default to GEPA-optimized prompt in backend/prompts/
            backend_dir = Path(__file__).parent
            prompt_path = backend_dir / "prompts" / "validator_prompt_optimized.txt"

        self.prompt_path = Path(prompt_path)
        logger.debug(f"PromptManager initialized with path: {self.prompt_path}")

    def load_prompt(self) -> str:
        """
        Load the validation prompt from file.

        Returns:
            str: The prompt template text

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        logger.debug(f"Loading prompt from: {self.prompt_path}")

        if not self.prompt_path.exists():
            logger.error(f"Prompt file not found: {self.prompt_path}")
            raise FileNotFoundError(f"Prompt file not found: {self.prompt_path}")

        with open(self.prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()

        logger.info(f"Loaded validation prompt: {self.prompt_path.name} ({len(prompt)} characters)")
        return prompt

    def format_citations(self, citations_text: str) -> str:
        """
        Format citations text for LLM input.
        Handles various separators (single/double newlines).

        Args:
            citations_text: Raw citation text from user

        Returns:
            str: Formatted citations ready to append to prompt

        Raises:
            ValueError: If citations_text is empty
        """
        if not citations_text or not citations_text.strip():
            logger.error("Empty citations provided")
            raise ValueError("Citations cannot be empty")

        # Clean up the input - normalize whitespace
        citations_text = citations_text.strip()

        logger.debug(f"Formatting {len(citations_text)} characters of citation text")

        # Split citations by double newline OR single newline
        # We'll number them for clarity
        lines = citations_text.split('\n')

        # Group into citations (either by blank lines or assume each line is a citation)
        citations = []
        current_citation = []

        for line in lines:
            line = line.strip()
            if not line:
                # Blank line - end current citation if any
                if current_citation:
                    citations.append(' '.join(current_citation))
                    current_citation = []
            else:
                current_citation.append(line)

        # Don't forget the last citation
        if current_citation:
            citations.append(' '.join(current_citation))

        if not citations:
            logger.error("No citations found after parsing")
            raise ValueError("Citations cannot be empty")

        # Format with numbering
        formatted = []
        for i, citation in enumerate(citations, 1):
            formatted.append(f"{i}. {citation}")

        result = '\n\n'.join(formatted)
        logger.info(f"Formatted {len(citations)} citation(s)")

        return result

    def build_prompt(self, citations_text: str) -> str:
        """
        Build complete prompt with validation rules + citations.

        Args:
            citations_text: Raw citation text from user

        Returns:
            str: Complete prompt ready for LLM

        Raises:
            ValueError: If citations_text is empty
            FileNotFoundError: If prompt template not found
        """
        logger.debug("Building full prompt")

        prompt_template = self.load_prompt()
        formatted_citations = self.format_citations(citations_text)

        # Combine prompt + citations
        full_prompt = f"{prompt_template}\n\n{formatted_citations}"

        logger.info(f"Built complete prompt: {len(full_prompt)} characters")
        logger.debug(f"Prompt preview: {full_prompt[:200]}...")

        return full_prompt
