import os
import re
import time
import asyncio
from typing import Dict, Any, List
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError, AuthenticationError
from providers.base import CitationValidator
from prompt_manager import PromptManager
from logger import setup_logger

logger = setup_logger("openai_provider")


class OpenAIProvider(CitationValidator):
    """
    OpenAI-based citation validator using GPT models.
    """

    def __init__(self, api_key: str = None, model: str = "gpt-5-mini"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name to use (default: gpt-5-mini)
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

        # Call OpenAI API with retry logic
        logger.info(f"Calling OpenAI API with model: {self.model}")
        api_start = time.time()

        # Build completion kwargs
        completion_kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert APA 7th edition citation validator."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 1 if self.model.startswith("gpt-5") else 0.1,  # GPT-5 requires temperature=1
            "timeout": 85.0  # 85 second timeout (stays under nginx 90s and Cloudflare 100s limits)
        }

        # Use appropriate parameter based on model family
        if self.model.startswith("gpt-5"):
            completion_kwargs["max_completion_tokens"] = 10000  # Increased to handle large batches without truncation
            completion_kwargs["reasoning_effort"] = "medium"  # 75.2% accuracy, only -2.5% vs baseline for better latency
        else:
            completion_kwargs["max_tokens"] = 10000

        # Retry logic with exponential backoff
        max_retries = 3
        retry_delay = 2  # Initial delay in seconds

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(**completion_kwargs)
                break  # Success, exit retry loop

            except AuthenticationError as e:
                logger.error(f"OpenAI authentication failed: {str(e)}", exc_info=True)
                raise ValueError("Invalid OpenAI API key. Please check your configuration.") from e

            except (APITimeoutError, RateLimitError) as e:
                if await self._handle_retry_error(e, attempt, max_retries, retry_delay):
                    continue  # Retry attempted
                else:
                    # Max retries exceeded
                    error_type = "timeout" if isinstance(e, APITimeoutError) else "rate limit"
                    raise ValueError(f"Request failed after multiple retries due to {error_type} errors. Please try again later.") from e

            except APIError as e:
                logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
                raise ValueError(f"OpenAI API error: {str(e)}") from e

        # API call successful - process response
        api_time = time.time() - api_start
        logger.info(f"OpenAI API call completed in {api_time:.3f}s")

        # Warn about slow requests (>30s)
        if api_time > 30:
            logger.warning(f"SLOW REQUEST: OpenAI API call took {api_time:.1f}s (>30s threshold)")
            logger.warning(f"Citation preview: {citations[:200]}...")

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

    async def _handle_retry_error(self, error: Exception, attempt: int, max_retries: int, retry_delay: int) -> bool:
        """
        Handle retryable errors with exponential backoff.

        Specifically handles APITimeoutError and RateLimitError from OpenAI API calls.
        Logs retry attempts with warning level and applies exponential backoff delays.

        Args:
            error: The exception that occurred (APITimeoutError or RateLimitError)
            attempt: Current attempt number (0-based)
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay in seconds (multiplied by 2^attempt for backoff)

        Returns:
            True if retry should be attempted, False if max retries exceeded
        """
        if attempt == max_retries - 1:  # Last attempt
            logger.error(f"OpenAI API error after {max_retries} attempts: {str(error)}", exc_info=True)
            return False

        # Log retry attempt with exponential backoff
        wait_time = retry_delay * (2 ** attempt)
        logger.warning(f"OpenAI API error (attempt {attempt + 1}/{max_retries}): {str(error)}. Retrying in {wait_time}s...")
        await asyncio.sleep(wait_time)
        return True

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
        # Handle both formats: "═══\nCITATION #N\n═══" and "CITATION #N\n═══"
        citation_pattern = r'(?:═+\s+)?CITATION #(\d+)\s*\n\s*═+(.+?)(?=(?:═+\s+)?CITATION #\d+|$)'
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
            # Convert markdown formatting back to HTML for frontend display
            # Convert bold (**text**) to HTML <strong>
            result["original"] = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', result["original"])
            # Convert italics (_text_) to HTML <em>
            result["original"] = re.sub(r'_([^_]+)_', r'<em>\1</em>', result["original"])

        return result
