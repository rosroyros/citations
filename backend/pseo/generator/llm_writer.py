"""
LLM Writer for content generation using GPT-4o-mini

This module handles all LLM-based content generation for PSEO pages including:
- Introductions
- Explanations
- Step-by-step instructions
- FAQs
- Content uniqueness validation
"""
import json
import logging
import time
from typing import List, Dict, Optional
from openai import OpenAI

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LLMWriter:
    """
    Handles LLM content generation using GPT-4o-mini

    Pricing: $0.15/1M input tokens, $0.60/1M output tokens
    """

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        """
        Initialize LLM writer

        Args:
            model: OpenAI model to use (default: gpt-4o-mini)
            api_key: OpenAI API key (optional, uses env var if not provided)
        """
        logger.info(f"Initializing LLMWriter with model: {model}")
        self.model = model
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()

        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # Pricing (per 1M tokens)
        self.input_price_per_million = 0.15
        self.output_price_per_million = 0.60

        logger.info(f"LLMWriter initialized successfully")

    def _call_openai(self, prompt: str, max_tokens: int = 1000,
                     temperature: float = 0.7, max_retries: int = 3) -> str:
        """
        Make API call to OpenAI with timeout and retry logic

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            max_retries: Maximum number of retry attempts

        Returns:
            Generated text
        """
        logger.debug(f"Making OpenAI API call - max_tokens: {max_tokens}, temp: {temperature}")
        logger.debug(f"Prompt preview: {prompt[:200]}...")

        for attempt in range(max_retries):
            try:
                logger.debug(f"API attempt {attempt + 1}/{max_retries}")

                # Add small delay to avoid rate limiting
                if attempt > 0:
                    time.sleep(1)  # 1 second delay between retries

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert academic writing assistant specializing in APA citation guides. NEVER use em dashes (—) in your writing. Use commas, periods, or split into separate sentences instead."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=60.0  # 60 second timeout
                )

                # Track token usage
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens

                logger.info(f"API call successful - Input tokens: {response.usage.prompt_tokens}, "
                           f"Output tokens: {response.usage.completion_tokens}")
                logger.debug(f"Running totals - Input: {self.total_input_tokens}, "
                            f"Output: {self.total_output_tokens}")

                result = response.choices[0].message.content
                logger.debug(f"Generated text preview: {result[:200]}...")

                return result

            except Exception as e:
                logger.error(f"OpenAI API call failed on attempt {attempt + 1}/{max_retries}: {str(e)}")

                if attempt < max_retries - 1:
                    # Exponential backoff: 2^attempt seconds, max 30 seconds
                    backoff_time = min(2 ** attempt, 30)
                    logger.info(f"Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)
                else:
                    logger.error(f"All {max_retries} attempts failed")
                    raise

    def generate_introduction(self, topic: str, keywords: List[str],
                             rules: Dict, pain_points: List[str]) -> str:
        """
        Generate 300-400 word introduction for a guide

        Args:
            topic: Main topic of the guide
            keywords: Target keywords to include
            rules: Relevant APA rules (dict or list)
            pain_points: Common user frustrations

        Returns:
            Introduction text (300-400 words)
        """
        logger.info(f"Generating introduction for topic: {topic}")

        prompt = f"""Write an introduction for an APA citation guide about {topic}.

KEYWORDS: {', '.join(keywords)}
PAIN POINTS: {', '.join(pain_points)}
RELEVANT RULES: {self._summarize_rules(rules)}

Requirements:
- 300-400 words (longer, more comprehensive)
- Conversational, empathetic tone
- Use second person ("you")
- Acknowledge user frustrations
- Preview guide content
- Natural keyword integration
- Make this unique from generic guides
- DO NOT use H1 headings (#), only plain text or H3+ headings (###) if needed
- NEVER use em dashes (—). Use commas, periods, or split into separate sentences instead.

Output only the introduction text."""

        return self._call_openai(prompt, max_tokens=600, temperature=0.7)

    def generate_explanation(self, concept: str, rules: Dict,
                            examples: List[str]) -> str:
        """
        Generate 800-1200 word explanation section

        Args:
            concept: Concept to explain
            rules: Relevant rules
            examples: Citation examples

        Returns:
            Explanation text (800-1200 words, markdown formatted)
        """
        logger.info(f"Generating explanation for concept: {concept}")

        prompt = f"""Explain {concept} for an APA citation guide.

RULES: {self._summarize_rules(rules)}
EXAMPLES: {chr(10).join(examples[:3])}

Requirements:
- 800-1200 words (comprehensive, detailed explanation)
- Clear, simple language
- Use H2 (##) or H3 (###) headings for subsections - NEVER use H1 (#)
- Include 2-3 examples with detailed explanations
- Show correct formatting
- Explain why rules matter
- Avoid jargon
- Add practical tips and common pitfalls
- NEVER use em dashes (—). Use commas, periods, or split into separate sentences instead.

Use Markdown formatting for structure. Remember: NO H1 headings, only H2 (##) and below."""

        return self._call_openai(prompt, max_tokens=1800, temperature=0.7)

    def generate_why_errors_happen(self, errors: List[Dict]) -> str:
        """
        Generate section explaining why common errors occur

        Args:
            errors: List of common error dictionaries

        Returns:
            Explanation text (400-600 words)
        """
        logger.info(f"Generating 'why errors happen' section for {len(errors)} errors")

        prompt = f"""Write a "Why These Errors Happen" section for an APA citation guide.

COMMON ERRORS: {self._summarize_errors(errors)}

Requirements:
- 400-600 words (detailed explanations)
- Psychological explanations
- Acknowledge confusion points
- Empathetic tone
- Explain database/technology factors
- Note learning curve
- DO NOT use H1 headings (#), only H2 (##) or H3 (###) if needed
- NEVER use em dashes (—). Use commas, periods, or split into separate sentences instead.

Be specific about what makes these rules confusing for students."""

        return self._call_openai(prompt, max_tokens=900, temperature=0.7)

    def generate_step_by_step(self, task: str, rules: Dict,
                              complexity: str = "beginner") -> str:
        """
        Generate step-by-step instructions

        Args:
            task: Task to explain
            rules: Relevant rules
            complexity: Target audience level (beginner/intermediate/advanced)

        Returns:
            Step-by-step instructions (markdown formatted, 500-700 words)
        """
        logger.info(f"Generating step-by-step instructions for: {task}")

        prompt = f"""Write step-by-step instructions for: {task}

RULES: {self._summarize_rules(rules)}
COMPLEXITY LEVEL: {complexity}

Requirements:
- 500-700 words with detailed steps
- 5-8 clear steps, each with detailed explanation
- Each step has action + verification
- Include time estimates
- Add tips for efficiency
- Use numbered list
- Bold key actions
- Include "What you need" section
- DO NOT use H1 headings (#), only H2 (##) or H3 (###) if needed
- NEVER use em dashes (—). Use commas, periods, or split into separate sentences instead.

Assume beginner user with no prior citation knowledge."""

        return self._call_openai(prompt, max_tokens=1000, temperature=0.7)

    def generate_faq(self, topic: str, num_questions: int = 8) -> List[Dict]:
        """
        Generate FAQ questions and answers

        Args:
            topic: Topic for FAQs
            num_questions: Number of Q&A pairs to generate

        Returns:
            List of dicts with 'question' and 'answer' keys
        """
        logger.info(f"Generating {num_questions} FAQ items for topic: {topic}")

        prompt = f"""Generate {num_questions} FAQ questions and answers for {topic}.

Requirements:
- Questions in natural language (how people search)
- Answers 100-200 words each (more detailed, comprehensive)
- Cover common confusion points
- Include practical scenarios
- Link to detailed resources where helpful
- DO NOT use H1 headings in answers
- NEVER use em dashes (—). Use commas, periods, or split into separate sentences instead.

Format as JSON array:
[
  {{
    "question": "Question text",
    "answer": "Answer text"
  }}
]

Output only valid JSON, no markdown code blocks."""

        response = self._call_openai(prompt, max_tokens=2000, temperature=0.7)

        try:
            # Clean up response if it contains markdown code blocks
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # Remove markdown code blocks
                lines = cleaned_response.split('\n')
                cleaned_response = '\n'.join(lines[1:-1])

            faqs = json.loads(cleaned_response)
            logger.info(f"Successfully parsed {len(faqs)} FAQ items")
            return faqs

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse FAQ JSON: {e}")
            logger.error(f"Response was: {response}")
            # Return empty list if parsing fails
            return []

    def validate_uniqueness(self, new_content: str,
                           existing_content: List[str]) -> float:
        """
        Check uniqueness score against existing content using Jaccard similarity

        Args:
            new_content: New content to check
            existing_content: List of existing content to compare against

        Returns:
            Uniqueness score (0.0 = duplicate, 1.0 = completely unique)
        """
        logger.debug(f"Validating uniqueness against {len(existing_content)} existing pieces")

        # Simple word-based Jaccard similarity
        new_words = set(new_content.lower().split())
        max_similarity = 0.0

        for existing in existing_content:
            existing_words = set(existing.lower().split())
            intersection = new_words.intersection(existing_words)
            union = new_words.union(existing_words)

            if len(union) == 0:
                similarity = 0.0
            else:
                similarity = len(intersection) / len(union)

            max_similarity = max(max_similarity, similarity)

        uniqueness = 1.0 - max_similarity
        logger.debug(f"Uniqueness score: {uniqueness:.3f}")
        return uniqueness

    def _summarize_rules(self, rules) -> str:
        """
        Summarize rules for prompt context

        Args:
            rules: Rules dict or list

        Returns:
            Formatted rule summary
        """
        if isinstance(rules, list):
            summary = "\n".join([f"- {r.get('description', r.get('rule_id', ''))}"
                               for r in rules[:5]])
        elif isinstance(rules, dict):
            summary = rules.get('description', str(rules))
        else:
            summary = str(rules)

        logger.debug(f"Summarized {len(summary)} chars of rules")
        return summary

    def _summarize_errors(self, errors: List[Dict]) -> str:
        """
        Summarize errors for prompt context

        Args:
            errors: List of error dicts

        Returns:
            Formatted error summary
        """
        summary = "\n".join([f"- {e.get('error_name', '')}: {e.get('description', '')}"
                            for e in errors[:5]])
        logger.debug(f"Summarized {len(errors)} errors into {len(summary)} chars")
        return summary

    def calculate_total_cost(self) -> float:
        """
        Calculate total API cost based on token usage

        Returns:
            Total cost in USD
        """
        input_cost = (self.total_input_tokens / 1_000_000) * self.input_price_per_million
        output_cost = (self.total_output_tokens / 1_000_000) * self.output_price_per_million
        total_cost = input_cost + output_cost

        logger.info(f"Total cost calculation:")
        logger.info(f"  Input tokens: {self.total_input_tokens:,} = ${input_cost:.6f}")
        logger.info(f"  Output tokens: {self.total_output_tokens:,} = ${output_cost:.6f}")
        logger.info(f"  TOTAL: ${total_cost:.6f}")

        return total_cost

    def get_usage_summary(self) -> Dict:
        """
        Get summary of token usage and costs

        Returns:
            Dict with usage statistics
        """
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": self.calculate_total_cost(),
            "model": self.model
        }

    def generate_tools_and_tips(self, validation_element: str) -> Dict:
        """
        Generate structured tools and tips content for validation guides

        Args:
            validation_element: Type of validation element (e.g., "capitalization", "italics", "doi")

        Returns:
            Dict with structured tools and tips content
        """
        logger.info(f"Generating tools and tips for: {validation_element}")

        prompt = f"""Generate comprehensive tools and tips for checking {validation_element} in APA citations.

Focus on Microsoft Word and Google Docs features with specific, actionable instructions:

Microsoft Word Features:
- How to use Find feature (Ctrl+F/Cmd+F) to locate {validation_element} errors
- How to use Find & Replace (Ctrl+H/Cmd+Shift+H) for bulk corrections
- How to use Styles panel for formatting
- Advanced search techniques for finding {validation_element} issues

Google Docs Features:
- How to use Find and Replace for checking {validation_element}
- How to use Add-ons for citation checking
- How to use keyboard shortcuts efficiently

Search Strategies:
- Specific search patterns to find {validation_element} errors
- How to search for common mistake patterns
- How to systematically check all citations

Time-Saving Techniques:
- Batch processing methods
- Keyboard shortcuts for efficiency
- Checklists for systematic review
- Automation tools and recommendations

Common Pitfalls:
- Mistakes users commonly make when checking {validation_element}
- How to avoid these common errors
- Warning signs to watch for

Provide practical, step-by-step instructions that students can immediately apply. Use clear, simple language and focus on actionable advice.

Format the response as a JSON object with these exact keys:
{{
  "word_find": "Microsoft Word Find feature instructions",
  "word_find_replace": "Microsoft Word Find & Replace instructions",
  "word_styles": "Microsoft Word Styles panel instructions",
  "docs_find": "Google Docs Find feature instructions",
  "docs_addons": "Google Docs Add-ons instructions",
  "search_strategies": "Specific search patterns and techniques",
  "time_saving_techniques": ["Technique 1: Description", "Technique 2: Description", "Technique 3: Description"],
  "common_pitfalls": ["Pitfall 1", "Pitfall 2", "Pitfall 3"]
}}"""

        try:
            response = self._call_openai(prompt, max_tokens=1500)

            # Parse JSON response
            try:
                content = response.strip()
                # Try to extract JSON from the response
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    tools_data = json.loads(json_str)

                    logger.info(f"✅ Generated tools and tips for {validation_element}")
                    return tools_data
                else:
                    logger.warning("No JSON found in response, using fallback")
                    return self._get_tools_fallback(validation_element)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return self._get_tools_fallback(validation_element)

        except Exception as e:
            logger.error(f"Error generating tools and tips: {e}")
            return self._get_tools_fallback(validation_element)

    def generate_before_after_examples(self, validation_element: str, num_examples: int = 5) -> List[Dict]:
        """
        Generate structured before/after examples for validation guides

        Args:
            validation_element: Type of validation element (e.g., "capitalization", "italics", "doi")
            num_examples: Number of examples to generate (default: 5)

        Returns:
            List of example dictionaries
        """
        logger.info(f"Generating {num_examples} before/after examples for: {validation_element}")

        examples_list = []
        for i in range(num_examples):
            prompt = f"""Generate one realistic before/after example for {validation_element} in APA citations.

Example {i+1}:
Create a realistic academic citation scenario with {validation_element} errors and corrections.

Include:
- scenario: Brief description of the situation
- incorrect_citation: Full citation with the {validation_element} error
- correct_citation: Corrected citation
- changes: List of specific changes made
- rule_applied: Which APA rule was applied
- error_type: Type of error (e.g., "Capitalization error", "Formatting error")
- fix_applied: Description of what was fixed
- difficulty: Easy/Medium/Hard

Use realistic academic sources (journal articles, books, webpages, etc.). Make the examples educational and clearly demonstrate the difference between incorrect and correct {validation_element} formatting.

Format the response as a JSON object with these exact keys:
{{
  "scenario": "Brief description",
  "incorrect_citation": "Full incorrect citation",
  "correct_citation": "Full correct citation",
  "changes": ["Change 1", "Change 2", "Change 3"],
  "rule_applied": "APA rule applied",
  "error_type": "Type of error",
  "fix_applied": "Description of fix",
  "difficulty": "Easy/Medium/Hard"
}}"""

            try:
                response = self._call_openai(prompt, max_tokens=800)

                # Parse JSON response
                try:
                    content = response.strip()
                    if '{' in content and '}' in content:
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        json_str = content[start:end]
                        example_data = json.loads(json_str)

                        examples_list.append(example_data)
                        logger.info(f"✅ Generated example {i+1} for {validation_element}")
                    else:
                        logger.warning(f"No JSON found in example {i+1} response")
                        examples_list.append(self._get_example_fallback(validation_element, i+1))

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON for example {i+1}: {e}")
                    examples_list.append(self._get_example_fallback(validation_element, i+1))

            except Exception as e:
                logger.error(f"Error generating example {i+1}: {e}")
                examples_list.append(self._get_example_fallback(validation_element, i+1))

        return examples_list

    def _get_tools_fallback(self, validation_element: str) -> Dict:
        """Get fallback tools content when LLM generation fails"""
        return {
            "word_find": f"Use Ctrl+F (Windows) or Cmd+F (Mac) to find {validation_element} patterns",
            "word_find_replace": f"Use Ctrl+H (Windows) or Cmd+Shift+H (Mac) to fix {validation_element} errors",
            "word_styles": f"Use the Styles panel in Word to format {validation_element} correctly",
            "docs_find": f"Use Ctrl+F in Google Docs to find {validation_element} patterns",
            "docs_addons": "Use citation checker add-ons in Google Docs",
            "search_strategies": f"Search for common {validation_element} mistakes systematically",
            "time_saving_techniques": [
                "Create a checklist for systematic review",
                "Use keyboard shortcuts for efficiency",
                "Check citations in batches by source type"
            ],
            "common_pitfalls": [
                f"Forgetting to check all instances of {validation_element}",
                "Not verifying changes after corrections",
                "Rushing through the review process"
            ]
        }

    def _get_example_fallback(self, validation_element: str, example_num: int) -> Dict:
        """Get fallback example content when LLM generation fails"""
        return {
            "scenario": f"Example {example_num}: Common {validation_element} error in academic citation",
            "incorrect_citation": f"Incorrect {validation_element} formatting in citation",
            "correct_citation": f"Correct {validation_element} formatting in citation",
            "changes": [f"Fixed {validation_element} formatting according to APA rules"],
            "rule_applied": f"APA 7th edition {validation_element} guidelines",
            "error_type": f"{validation_element.title()} Error",
            "fix_applied": f"Applied proper {validation_element} formatting",
            "difficulty": "Easy"
        }

    def generate_source_navigation_guide(self, source_name: str, source_url: str, what_to_find: List[str]) -> str:
        """
        Generate guide on where to find citation information on a specific website
        """
        prompt = f"""
        As an expert in web navigation and academic research, create a detailed guide for finding citation information on {source_name} ({source_url}).

        Write 300-400 words explaining where students can locate:
        - {" - ".join(what_to_find)}

        Include specific guidance like:
        - "Look for the author byline at the top of the article"
        - "The publication date appears under the headline"
        - "URL is in the browser address bar"

        Be very specific about this website's layout and navigation. Use practical, actionable language.
        Focus on what makes {source_name} unique for finding citation information.
        """

        return self._generate_with_high_quality_model(prompt)

    def generate_real_source_examples(self, source_name: str, source_url: str, base_template: str, num_examples: int = 4) -> str:
        """
        Generate real citation examples from the specific source using web browsing
        """
        prompt = f"""
        Browse {source_url} and find {num_examples} recent articles/content pieces from 2023-2024.
        For each item found, create a complete APA 7th edition citation using this base template:
        {base_template}

        For each example, include:
        1. A brief scenario description (what type of content this is)
        2. Complete reference list citation in proper APA format
        3. In-text citation (parenthetical format)
        4. In-text citation (narrative format)
        5. Notes about what makes this example noteworthy or unique

        Examples should show variety when possible:
        - Standard individual author
        - Corporate author (if applicable)
        - Multiple authors
        - Special formatting cases specific to {source_name}

        Ensure all examples are authentic and properly formatted according to APA 7th edition.
        Focus on real, current content from {source_name}.
        """

        # Use web-enabled model for real examples
        return self._generate_with_web_browsing(prompt)

    def generate_source_specific_issues(self, source_name: str, common_problems: List[str]) -> str:
        """
        Generate content about common issues specific to this source
        """
        prompt = f"""
        Identify and explain common citation problems students encounter when citing {source_name}.

        Focus on practical issues like:
        - {" - ".join(common_problems)}

        For each problem:
        1. Describe the issue clearly
        2. Explain why it happens with this specific source
        3. Provide a step-by-step solution
        4. Show before/after examples if applicable

        Write 400-500 words. Use clear headings for each problem. Be specific to {source_name}'s format and interface.
        Focus on what makes {source_name} challenging or unique compared to other sources.
        """

        return self._generate_with_high_quality_model(prompt)

    def generate_source_specific_faq(self, source_name: str, parent_source_type: str) -> str:
        """
        Generate FAQ specific to this source
        """
        prompt = f"""
        Generate 5 frequently asked questions about citing {source_name} in APA format.

        Questions should be specific to this source and not generic citation questions. Include topics like:
        - Navigating {source_name}'s website to find citation info
        - Handling {source_name}'s unique author formats
        - Dealing with {source_name}'s publication date formats
        - URL and access requirements
        - How {source_name} differs from other {parent_source_type} sources

        Format each Q&A pair as:

        **Q: [Question]**

        A: [Concise, actionable answer 2-3 sentences]

        Make questions specific to {source_name} and answers practical for students.
        """

        return self._generate_with_high_quality_model(prompt)

    def generate_source_specific_notes(self, source_name: str, parent_rules: List[str]) -> str:
        """
        Generate notes about what makes this source unique for citation purposes
        """
        prompt = f"""
        Explain what makes citing {source_name} unique compared to general {parent_rules[0] if parent_rules else "source type"} citations.

        Write 2-3 paragraphs (150-200 words) covering:
        - Specific formatting requirements for {source_name}
        - Where {source_name} differs from standard citation rules
        - Common points of confusion for students
        - Best practices specific to this source

        Focus on actionable guidance that helps students avoid common mistakes with {source_name}.
        """

        return self._generate_with_high_quality_model(prompt)

    def _generate_with_high_quality_model(self, prompt: str) -> str:
        """
        Generate content using high-quality model (gpt-4o)
        """
        try:
            logger.debug(f"Generating content with high-quality model")

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in academic citation formats and APA 7th edition guidelines. Provide accurate, practical guidance for students."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            content = response.choices[0].message.content.strip()

            # Track token usage
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens

            logger.debug(f"Generated {len(content)} characters with high-quality model")
            return content

        except Exception as e:
            logger.error(f"Error generating content with high-quality model: {str(e)}")
            # Fallback to standard model
            return self._generate_with_standard_model(prompt)

    def _generate_with_web_browsing(self, prompt: str) -> str:
        """
        Generate content using web browsing model (gpt-4o with browsing)
        """
        try:
            logger.debug(f"Generating content with web browsing model")

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in academic citation formats with web browsing capability. Find real, current information and create accurate citations according to APA 7th edition guidelines."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.5,
                tools=[{"type": "web_search", "function": {"name": "search", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}}}]
            )

            content = response.choices[0].message.content.strip()

            # Track token usage
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens

            logger.debug(f"Generated {len(content)} characters with web browsing model")
            return content

        except Exception as e:
            logger.error(f"Error generating content with web browsing: {str(e)}")
            # Fallback to high-quality model without browsing
            fallback_prompt = prompt.replace("Browse", "Based on your knowledge of")
            return self._generate_with_high_quality_model(fallback_prompt)

    def _generate_with_standard_model(self, prompt: str) -> str:
        """
        Generate content using standard model (gpt-4o-mini)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in academic citation formats and APA 7th edition guidelines."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )

            content = response.choices[0].message.content.strip()

            # Track token usage
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens

            return content

        except Exception as e:
            logger.error(f"Error generating content with standard model: {str(e)}")
            return f"Content generation temporarily unavailable. Please try again later."
