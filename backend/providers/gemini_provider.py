import os
import re
import time
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from providers.base import CitationValidator
from prompt_manager import PromptManager
from logger import setup_logger

# Try to import the new Google genai API first, fallback to legacy
try:
    from google import genai as new_genai
    from google.genai import types
    NEW_API_AVAILABLE = True
except ImportError:
    NEW_API_AVAILABLE = False
    import google.generativeai as genai

# Always import legacy genai for fallback compatibility
try:
    import google.generativeai as legacy_genai
except ImportError:
    legacy_genai = None

logger = setup_logger("gemini_provider")


class GeminiProvider(CitationValidator):
    """
    Gemini-based citation validator using Google's Gemini models.
    Uses the "User Content" strategy for better accuracy.
    """

    def __init__(self, api_key: str = None, model: str = "gemini-3-flash-preview", temperature: float = 0.0, prompt_path: str = None):
        """
        Initialize Gemini provider.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model name to use (default: gemini-3-flash-preview)
            temperature: Temperature for generation (default: 0.0)
            prompt_path: Optional path to specific prompt file
        """
        # Load environment variables
        load_dotenv()

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.temperature = temperature

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        self.prompt_manager = PromptManager(prompt_path=prompt_path)

        # Initialize client based on API availability
        if NEW_API_AVAILABLE and ("2.5" in model or "3" in model):
            self.client = new_genai.Client(api_key=self.api_key)
            self.use_new_api = True
            logger.info(f"Gemini provider initialized with new API and model: {model}")
        else:
            # Legacy API fallback
            if legacy_genai:
                legacy_genai.configure(api_key=self.api_key)
            else:
                raise ImportError("Legacy Google GenerativeAI not available")
            self.use_new_api = False
            logger.info(f"Gemini provider initialized with legacy API and model: {model}")

    async def validate_citations(self, citations: str, style: str = "apa7") -> Dict[str, Any]:
        """
        Validate citations using Gemini API.

        Args:
            citations: Raw citation text
            style: Citation style (default: "apa7")

        Returns:
            Validation results dictionary with structured errors
        """
        logger.info(f"Starting validation for {len(citations)} characters of citation text")
        logger.debug(f"Citations to validate: {citations[:2000]}...")

        start_time = time.time()

        # Build prompt components
        prompt_template = self.prompt_manager.load_prompt()
        formatted_citations = self.prompt_manager.format_citations(citations)

        # Build the full prompt using User Content strategy
        # According to issue notes, this gives ~79% accuracy vs ~20% for system_instruction
        full_prompt = f"{prompt_template}\n\n{formatted_citations}"

        logger.debug(f"Prepared prompt ({len(full_prompt)} chars) in {time.time() - start_time:.3f}s")

        # Call Gemini API
        logger.info(f"Calling Gemini API with model: {self.model}")
        api_start = time.time()

        try:
            if self.use_new_api:
                response = await self._call_new_api_with_response(full_prompt)
                response_text = response.text
                # Log token usage from usage_metadata
                if (hasattr(response, 'usage_metadata') and
                    response.usage_metadata):
                    metadata = response.usage_metadata
                    # Use actual field names from Gemini API response
                    prompt_tokens = getattr(metadata, 'prompt_token_count', 0)
                    api_total_tokens = getattr(metadata, 'total_token_count', 0)
                    # candidates_token_count is the actual output tokens
                    output_tokens = getattr(metadata, 'candidates_token_count', 0)

                    # Calculate total as prompt + completion for user-facing display
                    # This ensures transparency since users expect total = prompt + completion
                    calculated_total = prompt_tokens + output_tokens

                    # Log both the API total and calculated total for debugging
                    if api_total_tokens != calculated_total:
                        logger.info(f"Token usage: {prompt_tokens} prompt + {output_tokens} completion = {calculated_total} total (API reports {api_total_tokens}, difference: {api_total_tokens - calculated_total} overhead tokens)")
                    else:
                        logger.info(f"Token usage: {prompt_tokens} prompt + {output_tokens} completion = {calculated_total} total")
            else:
                response_text = await self._call_legacy_api(full_prompt)
                # Legacy API doesn't provide reliable token usage
                logger.info(f"Token usage: N/A (legacy API)")

            api_duration = time.time() - api_start
            logger.info(f"Gemini API call completed in {api_duration:.3f}s")

        except Exception as e:
            api_duration = time.time() - api_start
            logger.error(f"Gemini API call failed after {api_duration:.3f}s: {str(e)}", exc_info=True)
            raise

        # Parse the response
        parse_start = time.time()
        try:
            parsed_results = self._parse_response(response_text)
            parse_duration = time.time() - parse_start
            logger.debug(f"Parsed response in {parse_duration:.3f}s")
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {str(e)}", exc_info=True)
            logger.debug(f"Raw response: {response_text[:1000]}...")
            # Return empty results on parse error
            parsed_results = []

        total_time = time.time() - start_time
        logger.info(f"Total validation completed in {total_time:.3f}s for {len(parsed_results)} citations")

        # Convert to expected format
        results = {
            "results": parsed_results
        }

        return results

    async def _call_new_api_with_response(self, prompt: str):
        """Call the new Google genai API and return the full response object."""
        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                # Default config
                config = types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=10000,
                )

                # Gemini 3 Flash: Use low thinking budget for consistency
                # Testing showed 100% consistency and ~81% accuracy with thinking_budget=1024
                if "gemini-3-flash" in self.model:
                    config = types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=10000,
                        thinking_config=types.ThinkingConfig(thinking_budget=1024)
                    )
                # Gemini 2.5 Pro: Use minimum thinking budget
                elif self.model == "gemini-2.5-pro":
                    # 2.5-pro requires thinking mode, but we avoid it per requirements
                    # If we must use it, set minimum thinking budget of 128 tokens
                    # This is the smallest allowed value that still enables thinking mode
                    config = types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=10000,
                        thinking_config=types.ThinkingConfig(thinking_budget=128)
                    )
                    logger.warning(f"Using minimum thinking budget for {self.model}")

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config
                )

                return response

            except Exception as e:
                error_str = str(e).lower()

                # Check for retryable errors
                if any(keyword in error_str for keyword in ['rate limit', 'timeout', 'overloaded', 'try again', 'resource exhausted']):
                    if attempt == max_retries - 1:
                        logger.error(f"Final attempt failed for Gemini API: {str(e)}")
                        raise

                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Gemini API attempt {attempt + 1} failed, retrying in {delay}s: {str(e)[:100]}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Non-retryable Gemini API error: {str(e)}")
                    raise

    async def _call_new_api(self, prompt: str) -> str:
        """Call the new Google genai API."""
        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                # Default config
                config = types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=10000,
                )

                # Gemini 3 Flash: Use low thinking budget for consistency
                # Testing showed 100% consistency and ~81% accuracy with thinking_budget=1024
                if "gemini-3-flash" in self.model:
                    config = types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=10000,
                        thinking_config=types.ThinkingConfig(thinking_budget=1024)
                    )
                # Gemini 2.5 Pro: Use minimum thinking budget
                elif self.model == "gemini-2.5-pro":
                    # 2.5-pro requires thinking mode, but we avoid it per requirements
                    # If we must use it, set minimum thinking budget of 128 tokens
                    # This is the smallest allowed value that still enables thinking mode
                    config = types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=10000,
                        thinking_config=types.ThinkingConfig(thinking_budget=128)
                    )
                    logger.warning(f"Using minimum thinking budget for {self.model}")

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config
                )

                return response.text

            except Exception as e:
                error_str = str(e).lower()

                # Check for retryable errors
                if any(keyword in error_str for keyword in ['rate limit', 'timeout', 'overloaded', 'try again', 'resource exhausted']):
                    if attempt == max_retries - 1:
                        logger.error(f"Final attempt failed for Gemini API: {str(e)}")
                        raise

                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Gemini API attempt {attempt + 1} failed, retrying in {delay}s: {str(e)[:100]}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Non-retryable Gemini API error: {str(e)}")
                    raise

    async def _call_legacy_api(self, prompt: str) -> str:
        """Call the legacy Google generativeai API."""
        max_retries = 3
        base_delay = 2

        # Initialize model
        if legacy_genai:
            model = legacy_genai.GenerativeModel(self.model)
        else:
            raise ImportError("Legacy Google GenerativeAI not available")

        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": 10000,
        }

        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                return response.text

            except Exception as e:
                error_str = str(e).lower()

                # Check for retryable errors
                if any(keyword in error_str for keyword in ['rate limit', 'timeout', 'overloaded', 'try again', 'resource exhausted']):
                    if attempt == max_retries - 1:
                        logger.error(f"Final attempt failed for Gemini legacy API: {str(e)}")
                        raise

                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Gemini legacy API attempt {attempt + 1} failed, retrying in {delay}s: {str(e)[:100]}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Non-retryable Gemini legacy API error: {str(e)}")
                    raise
    

    def _parse_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse Gemini response text into structured validation results.
        Uses the same parsing logic as OpenAI provider for consistency.

        Args:
            response_text: Raw text from Gemini

        Returns:
            List of validation results, one per citation
        """
        logger.debug("Parsing Gemini response into structured format")

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
        Parse a single citation block from Gemini response.
        Mirrors the OpenAI provider's parsing logic.

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
            elif line_stripped.startswith('VALIDATION RESULTS:'):
                current_section = 'validation'
            # Parse content based on section
            elif current_section == 'original' and line_stripped and not line_stripped.startswith('SOURCE TYPE:'):
                original_lines.append(line_stripped)
            elif current_section == 'corrected_citation' and line_stripped:
                # Handle separator at end of corrected citation
                if line_stripped.startswith('─'):
                    current_section = None
                    continue
                    
                # Append line to corrected citation (handles multi-line wrap)
                if result.get("corrected_citation") is None:
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
            
            # Check for CORRECTED CITATION section start (checked last to avoid consuming current line if it's the header)
            if line_stripped.startswith('CORRECTED CITATION:'):
                current_section = 'corrected_citation'
                # Extract content from the same line if present
                content = line_stripped.replace('CORRECTED CITATION:', '').strip()
                if content:
                    result["corrected_citation"] = content
                
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

    def generate_completion(self, prompt: str) -> Optional[str]:
        """
        Simple method for testing direct API access.
        Used by the debug test script.

        Args:
            prompt: Simple text prompt

        Returns:
            Generated text or None on error
        """
        try:
            if self.use_new_api:
                config = types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=100,
                )
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config
                )
                return response.text
            else:
                if legacy_genai:
                    model = legacy_genai.GenerativeModel(self.model)
                    response = model.generate_content(prompt)
                    return response.text
                else:
                    raise ImportError("Legacy Google GenerativeAI not available")
        except Exception as e:
            logger.error(f"Failed to generate completion: {str(e)}")
            return None