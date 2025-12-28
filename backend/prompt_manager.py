"""
Prompt management for citation validation.
Loads validation prompts and formats citations for LLM input.
"""
import os
from pathlib import Path
from typing import Optional
from logger import setup_logger
from styles import StyleType, DEFAULT_STYLE, get_style_config

logger = setup_logger("prompt_manager")


class PromptManager:
    """Manages loading and formatting of validation prompts."""

    def __init__(self, prompt_path: str = None):
        """
        Initialize prompt manager.

        Args:
            prompt_path: Optional custom path to prompt file.
                        If not provided, prompts are loaded dynamically based on style.
        """
        self._custom_prompt_path = Path(prompt_path) if prompt_path else None
        self._prompts_dir = Path(__file__).parent / "prompts"
        logger.debug(f"PromptManager initialized with prompts dir: {self._prompts_dir}")

    def load_prompt(self, style: StyleType = DEFAULT_STYLE) -> str:
        """
        Load the validation prompt for a given citation style.

        Args:
            style: Citation style to load prompt for (default: apa7)

        Returns:
            str: The prompt template text

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        # Use custom path if provided (for backward compatibility)
        if self._custom_prompt_path:
            prompt_path = self._custom_prompt_path
        else:
            # Load from styles config
            config = get_style_config(style)
            prompt_path = self._prompts_dir / config["prompt_file"]

        logger.debug(f"Loading prompt from: {prompt_path}")

        if not prompt_path.exists():
            logger.error(f"Prompt file not found: {prompt_path}")
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()

        logger.info(f"Loaded validation prompt: {prompt_path.name} ({len(prompt)} characters)")
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

    def build_prompt(self, citations_text: str, style: StyleType = DEFAULT_STYLE) -> str:
        """
        Build complete prompt with validation rules + citations.

        Args:
            citations_text: Raw citation text from user
            style: Citation style to use (default: apa7)

        Returns:
            str: Complete prompt ready for LLM

        Raises:
            ValueError: If citations_text is empty
            FileNotFoundError: If prompt template not found
        """
        logger.debug(f"Building full prompt for style: {style}")

        prompt_template = self.load_prompt(style)
        formatted_citations = self.format_citations(citations_text)

        # Combine prompt + citations
        full_prompt = f"{prompt_template}\n\n{formatted_citations}"

        logger.info(f"Built complete prompt: {len(full_prompt)} characters")
        logger.debug(f"Prompt preview: {full_prompt[:200]}...")

        return full_prompt
