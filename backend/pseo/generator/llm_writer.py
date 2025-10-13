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
                     temperature: float = 0.7) -> str:
        """
        Make API call to OpenAI

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)

        Returns:
            Generated text
        """
        logger.debug(f"Making OpenAI API call - max_tokens: {max_tokens}, temp: {temperature}")
        logger.debug(f"Prompt preview: {prompt[:200]}...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert academic writing assistant specializing in APA citation guides."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
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
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise

    def generate_introduction(self, topic: str, keywords: List[str],
                             rules: Dict, pain_points: List[str]) -> str:
        """
        Generate 200-250 word introduction for a guide

        Args:
            topic: Main topic of the guide
            keywords: Target keywords to include
            rules: Relevant APA rules (dict or list)
            pain_points: Common user frustrations

        Returns:
            Introduction text (200-250 words)
        """
        logger.info(f"Generating introduction for topic: {topic}")

        prompt = f"""Write an introduction for an APA citation guide about {topic}.

KEYWORDS: {', '.join(keywords)}
PAIN POINTS: {', '.join(pain_points)}
RELEVANT RULES: {self._summarize_rules(rules)}

Requirements:
- 200-250 words
- Conversational, empathetic tone
- Use second person ("you")
- Acknowledge user frustrations
- Preview guide content
- Natural keyword integration
- Make this unique from generic guides

Output only the introduction text."""

        return self._call_openai(prompt, max_tokens=400, temperature=0.7)

    def generate_explanation(self, concept: str, rules: Dict,
                            examples: List[str]) -> str:
        """
        Generate 400-600 word explanation section

        Args:
            concept: Concept to explain
            rules: Relevant rules
            examples: Citation examples

        Returns:
            Explanation text (400-600 words, markdown formatted)
        """
        logger.info(f"Generating explanation for concept: {concept}")

        prompt = f"""Explain {concept} for an APA citation guide.

RULES: {self._summarize_rules(rules)}
EXAMPLES: {chr(10).join(examples[:3])}

Requirements:
- 400-600 words
- Clear, simple language
- Use headings and lists
- Include 2-3 examples
- Show correct formatting
- Explain why rules matter
- Avoid jargon

Use Markdown formatting for structure."""

        return self._call_openai(prompt, max_tokens=800, temperature=0.7)

    def generate_why_errors_happen(self, errors: List[Dict]) -> str:
        """
        Generate section explaining why common errors occur

        Args:
            errors: List of common error dictionaries

        Returns:
            Explanation text (300-500 words)
        """
        logger.info(f"Generating 'why errors happen' section for {len(errors)} errors")

        prompt = f"""Write a "Why These Errors Happen" section for an APA citation guide.

COMMON ERRORS: {self._summarize_errors(errors)}

Requirements:
- 300-500 words
- Psychological explanations
- Acknowledge confusion points
- Empathetic tone
- Explain database/technology factors
- Note learning curve

Be specific about what makes these rules confusing for students."""

        return self._call_openai(prompt, max_tokens=600, temperature=0.7)

    def generate_step_by_step(self, task: str, rules: Dict,
                              complexity: str = "beginner") -> str:
        """
        Generate step-by-step instructions

        Args:
            task: Task to explain
            rules: Relevant rules
            complexity: Target audience level (beginner/intermediate/advanced)

        Returns:
            Step-by-step instructions (markdown formatted)
        """
        logger.info(f"Generating step-by-step instructions for: {task}")

        prompt = f"""Write step-by-step instructions for: {task}

RULES: {self._summarize_rules(rules)}
COMPLEXITY LEVEL: {complexity}

Requirements:
- 5-8 clear steps
- Each step has action + verification
- Include time estimates
- Add tips for efficiency
- Use numbered list
- Bold key actions
- Include "What you need" section

Assume beginner user with no prior citation knowledge."""

        return self._call_openai(prompt, max_tokens=600, temperature=0.7)

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
- Answers 50-150 words each
- Cover common confusion points
- Include practical scenarios
- Link to detailed resources where helpful

Format as JSON array:
[
  {{
    "question": "Question text",
    "answer": "Answer text"
  }}
]

Output only valid JSON, no markdown code blocks."""

        response = self._call_openai(prompt, max_tokens=1200, temperature=0.7)

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
