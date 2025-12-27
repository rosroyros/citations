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
        logger.debug(f"Citations to validate: {citations[:2000]}...")

        # Build prompt components
        start_time = time.time()
        prompt_template = self.prompt_manager.load_prompt()
        formatted_citations = self.prompt_manager.format_citations(citations)
        logger.debug(f"Prepared prompt components in {time.time() - start_time:.3f}s")

        # Call OpenAI API with retry logic
        logger.info(f"Calling OpenAI API with model: {self.model}")
        api_start = time.time()

        # Build completion kwargs
        completion_kwargs = {
            "model": self.model,
            "instructions": prompt_template,
            "input": formatted_citations,
            "temperature": 1 if self.model.startswith("gpt-5") else 0.1,  # GPT-5 requires temperature=1
            "timeout": 85.0,  # 85 second timeout (stays under nginx 90s and Cloudflare 100s limits)
            "service_tier": "priority"  # Enable Priority Processing for lower latency
        }

        # Use appropriate parameter based on model family
        if self.model.startswith("gpt-5"):
            completion_kwargs["max_output_tokens"] = 10000  # Increased to handle large batches without truncation
            completion_kwargs["reasoning"] = {"effort": "medium"}  # 75.2% accuracy, only -2.5% vs baseline for better latency
        else:
            completion_kwargs["max_output_tokens"] = 10000

        # Retry logic with exponential backoff
        max_retries = 3
        retry_delay = 2  # Initial delay in seconds

        # Estimate request size for debugging
        request_size_chars = len(prompt_template) + len(formatted_citations)

        for attempt in range(max_retries):
            attempt_start = time.time()
            configured_timeout = completion_kwargs.get("timeout")

            logger.info(f"Attempt {attempt + 1}/{max_retries}: Calling OpenAI (timeout={configured_timeout}s, model={self.model}, size={request_size_chars} chars)")

            try:
                response = await self.client.responses.create(**completion_kwargs)
                attempt_duration = time.time() - attempt_start
                logger.info(f"Attempt {attempt + 1}/{max_retries}: Success in {attempt_duration:.3f}s")
                break  # Success, exit retry loop

            except AuthenticationError as e:
                logger.error(f"OpenAI authentication failed: {str(e)}", exc_info=True)
                raise ValueError("Invalid OpenAI API key. Please check your configuration.") from e

            except (APITimeoutError, RateLimitError) as e:
                attempt_duration = time.time() - attempt_start
                error_type = "timeout" if isinstance(e, APITimeoutError) else "rate_limit"
                
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries}: Failed with {error_type} after {attempt_duration:.3f}s "
                    f"(Configured timeout: {configured_timeout}s)"
                )
                
                if await self._handle_retry_error(e, attempt, max_retries, retry_delay):
                    continue  # Retry attempted
                else:
                    # Max retries exceeded
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

        # Log usage (Response object structure differs in Responses API)
        # Assuming response.usage has prompt_tokens/completion_tokens or similar
        # Based on previous tests, it might be input_tokens/output_tokens
        if hasattr(response, 'usage'):
             # Handle potential differences in usage object keys
             input_tokens = getattr(response.usage, 'input_tokens', getattr(response.usage, 'prompt_tokens', 0))
             output_tokens = getattr(response.usage, 'output_tokens', getattr(response.usage, 'completion_tokens', 0))
             total_tokens = getattr(response.usage, 'total_tokens', input_tokens + output_tokens)
             logger.info(f"Token usage: {input_tokens} input + {output_tokens} output = {total_tokens} total")

        # Extract response text
        response_text = response.output_text
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
            "errors": [],
            "corrected_citation": None
        }

        current_section = None
        original_lines = []

        for line in lines:
            line_stripped = line.strip()

            # Track sections
            if line_stripped.startswith('ORIGINAL:'):
                current_section = 'original'
                # Extract content from the same line if present
                content = line_stripped.replace('ORIGINAL:', '').strip()
                if content:
                    original_lines.append(content)
            elif line_stripped.startswith('SOURCE TYPE:'):
                current_section = 'source_type'
                source_type = line_stripped.replace('SOURCE TYPE:', '').strip()
                result["source_type"] = source_type
            elif line_stripped.startswith('VALIDATION RESULTS:'):
                current_section = 'validation'
            elif line_stripped.startswith('CORRECTED CITATION:'):
                current_section = 'corrected_citation'
                # Extract content from the same line if present
                content = line_stripped.replace('CORRECTED CITATION:', '').strip()
                if content:
                    result["corrected_citation"] = content

            # Parse content based on section
            elif current_section == 'original' and line_stripped and not line_stripped.startswith('SOURCE TYPE:'):
                original_lines.append(line_stripped)
            elif current_section == 'corrected_citation' and line_stripped:
                # Handle separator at end of corrected citation
                if line_stripped.startswith('─'):
                    current_section = None
                    continue
                    
                # Append line to corrected citation (handles multi-line wrap)
                if result["corrected_citation"] is None:
                    result["corrected_citation"] = line_stripped
                else:
                    result["corrected_citation"] += " " + line_stripped
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
            result["original"] = self._format_markdown_to_html(result["original"])

        # Process corrected citation
        if "corrected_citation" in result and result["corrected_citation"]:
            # Defensive Logic 1: If no errors, discard corrected citation
            if not result.get("errors"):
                result["corrected_citation"] = None
            else:
                # normalize strings for comparison
                cleaned_original = re.sub(r'\s+', ' ', result.get("original", "")).strip()
                cleaned_corrected = re.sub(r'\s+', ' ', result["corrected_citation"]).strip()
                
                # Apply HTML formatting to corrected
                formatted_corrected = self._format_markdown_to_html(cleaned_corrected)
                
                # Defensive Logic 2: If identical to original (comparing HTML vs HTML), discard
                if cleaned_original == formatted_corrected:
                     result["corrected_citation"] = None
                else:
                     result["corrected_citation"] = formatted_corrected
                     logger.info(f"Parsed corrected citation for #{citation_num}")

        # Apply same markdown→HTML conversion to error corrections
        for error in result["errors"]:
            if error.get("correction"):
                error["correction"] = self._format_markdown_to_html(error["correction"])

        return result
