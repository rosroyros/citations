import os
import re
import time
from typing import Dict, Any, List
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError, AuthenticationError
from backend.providers.base import CitationValidator
from backend.prompt_manager import PromptManager
from backend.logger import setup_logger

logger = setup_logger("openai_provider")


class OpenAIProvider(CitationValidator):
    """
    OpenAI-based citation validator using GPT models.
    """

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name to use (default: gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.prompt_manager = PromptManager()
        logger.info(f"OpenAI provider initialized with model: {model}")

    async def validate_citations(self, citations: str, style: str = "apa7") -> Dict[str, Any]:
        """
        Validate citations using OpenAI API.

        Args:
            citations: Raw citation text
            style: Citation style (default: "apa7")

        Returns:
            Validation results dictionary with structured errors
        """
        logger.info(f"Starting validation for {len(citations)} characters of citation text")
        logger.debug(f"Citations to validate: {citations[:200]}...")

        # Build prompt with validation rules + citations
        start_time = time.time()
        prompt = self.prompt_manager.build_prompt(citations)
        logger.debug(f"Built prompt in {time.time() - start_time:.3f}s")

        # Call OpenAI API
        logger.info(f"Calling OpenAI API with model: {self.model}")
        api_start = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert APA 7th edition citation validator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
                timeout=30.0  # 30 second timeout
            )

            api_time = time.time() - api_start
            logger.info(f"OpenAI API call completed in {api_time:.3f}s")
            logger.info(f"Token usage: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion = {response.usage.total_tokens} total")

            # Extract response text
            response_text = response.choices[0].message.content
            logger.debug(f"Response text length: {len(response_text)} characters")
            logger.debug(f"Response preview: {response_text[:300]}...")

            # Parse response into structured format
            parse_start = time.time()
            results = self._parse_response(response_text)
            logger.info(f"Parsed response in {time.time() - parse_start:.3f}s")
            logger.info(f"Found {len(results)} citation result(s)")

            return {
                "results": results
            }

        except AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {str(e)}", exc_info=True)
            raise ValueError("Invalid OpenAI API key. Please check your configuration.") from e

        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {str(e)}", exc_info=True)
            raise ValueError("OpenAI rate limit exceeded. Please try again later.") from e

        except APITimeoutError as e:
            logger.error(f"OpenAI API timeout: {str(e)}", exc_info=True)
            raise ValueError("Request timed out. The citation text may be too long or the service is slow.") from e

        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            raise ValueError(f"OpenAI API error: {str(e)}") from e

        except Exception as e:
            logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
            raise

    def _parse_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response text into structured validation results.

        Args:
            response_text: Raw text from LLM

        Returns:
            List of validation results, one per citation
        """
        logger.debug("Parsing LLM response into structured format")

        results = []

        # Find all citation blocks by looking for CITATION # markers
        # Each block starts with ═══ CITATION #N ═══ and ends with either ─── or next ═══
        citation_pattern = r'═+\s*CITATION #(\d+)\s*═+(.+?)(?:─+|═+|$)'
        matches = re.finditer(citation_pattern, response_text, re.DOTALL)

        for match in matches:
            citation_num = int(match.group(1))
            block_content = match.group(2)

            try:
                result = self._parse_citation_block(citation_num, block_content)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to parse citation #{citation_num}: {str(e)}")
                logger.debug(f"Problematic block: {block_content[:200]}...")

        return results

    def _parse_citation_block(self, citation_num: int, block: str) -> Dict[str, Any]:
        """
        Parse a single citation block from LLM response.

        Args:
            citation_num: Citation number
            block: Text block content for one citation

        Returns:
            Structured validation result
        """
        lines = block.strip().split('\n')

        result = {
            "citation_number": citation_num,
            "original": "",
            "source_type": "",
            "errors": []
        }

        current_section = None
        original_lines = []

        for line in lines:
            line_stripped = line.strip()

            # Track sections
            if line_stripped.startswith('ORIGINAL:'):
                current_section = 'original'
            elif line_stripped.startswith('SOURCE TYPE:'):
                current_section = 'source_type'
                source_type = line_stripped.replace('SOURCE TYPE:', '').strip()
                result["source_type"] = source_type
            elif line_stripped.startswith('VALIDATION RESULTS:'):
                current_section = 'validation'
            elif line_stripped.startswith('─'):
                # End of block
                break
            # Parse content based on section
            elif current_section == 'original' and line_stripped and not line_stripped.startswith('SOURCE TYPE:'):
                original_lines.append(line_stripped)
            elif current_section == 'validation':
                # Check for no errors
                if '✓ No APA 7 formatting errors detected' in line_stripped or 'No APA 7 formatting errors' in line_stripped:
                    result["errors"] = []
                # Parse error lines
                elif line_stripped.startswith('❌'):
                    # Format: ❌ [Component]: [Problem]
                    error_match = re.match(r'❌\s*([^:]+):\s*(.+)', line_stripped)
                    if error_match:
                        error = {
                            "component": error_match.group(1).strip(),
                            "problem": error_match.group(2).strip(),
                            "correction": ""
                        }
                        result["errors"].append(error)
                # Parse correction lines (may be indented, so check in line not just at start)
                elif 'Should be:' in line_stripped and result["errors"]:
                    correction = line_stripped.split('Should be:')[1].strip()
                    result["errors"][-1]["correction"] = correction

        # Join original lines
        if original_lines:
            result["original"] = ' '.join(original_lines)
            # Convert markdown italics (_text_) back to HTML for frontend display
            import re
            result["original"] = re.sub(r'_([^_]+)_', r'<em>\1</em>', result["original"])

        return result
