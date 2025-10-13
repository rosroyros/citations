"""
Content Assembler for PSEO Pages

Orchestrates the assembly of complete PSEO pages by combining:
- Jinja2 templates (structure)
- LLM-generated content (unique sections)
- Structured knowledge base data (rules, examples, errors)
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from .template_engine import TemplateEngine
from .llm_writer import LLMWriter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentAssembler:
    """
    Assembles complete PSEO page content by combining templates,
    LLM generation, and structured knowledge base data.
    """

    def __init__(self, knowledge_base_dir: str, templates_dir: str):
        """
        Initialize ContentAssembler

        Args:
            knowledge_base_dir: Path to knowledge base JSON files
            templates_dir: Path to Jinja2 templates
        """
        logger.info(f"Initializing ContentAssembler")
        logger.info(f"  Knowledge base: {knowledge_base_dir}")
        logger.info(f"  Templates: {templates_dir}")

        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.templates_dir = Path(templates_dir)

        # Validate directories exist
        if not self.knowledge_base_dir.exists():
            raise ValueError(f"Knowledge base directory does not exist: {knowledge_base_dir}")
        if not self.templates_dir.exists():
            raise ValueError(f"Templates directory does not exist: {templates_dir}")

        # Initialize components
        self.template_engine = TemplateEngine(templates_dir)
        self.llm_writer = LLMWriter()

        logger.info("ContentAssembler initialized successfully")

    def assemble_mega_guide(self, topic: str, config: dict) -> dict:
        """
        Assemble complete mega guide content

        Args:
            topic: Main topic for the guide (e.g., "checking APA citations")
            config: Configuration dict with title, description, keywords, pain_points

        Returns:
            Dict with 'content' (markdown), 'metadata', 'template_data', 'token_usage'
        """
        logger.info(f"=== Assembling Mega Guide: {topic} ===")

        # 1. Load template
        logger.info("Step 1: Loading mega guide template")
        template = self.template_engine.load_template("mega_guide_template.md")

        # 2. Load structured data from knowledge base
        logger.info("Step 2: Loading structured data from knowledge base")
        relevant_rules = self._load_relevant_rules(topic)
        examples = self._load_examples(topic)
        errors = self._load_errors(topic)

        logger.info(f"  Loaded {len(relevant_rules)} rules, {len(examples)} examples, {len(errors)} errors")

        # 3. Generate LLM sections
        logger.info("Step 3: Generating LLM content sections")
        llm_content = self._generate_mega_guide_sections(topic, config, relevant_rules)

        # 4. Combine all content
        logger.info("Step 4: Combining all content into template")
        template_data = {
            "guide_title": config.get("title", ""),
            "guide_description": config.get("description", ""),
            "target_keywords": config.get("keywords", []),
            "pain_points": config.get("pain_points", []),
            **llm_content,
            "examples": examples,
            "common_errors": errors,
            "validation_checklist": self._generate_checklist(relevant_rules),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "reading_time": "25 minutes"  # Will recalculate after rendering
        }

        # 5. Render template
        logger.info("Step 5: Rendering template with data")
        content = self.template_engine.inject_variables(template, template_data)

        # 6. Validate output
        logger.info("Step 6: Validating generated content")
        if not self.template_engine.validate_output(content, min_words=5000):
            raise ValueError(f"Generated mega guide too short for topic: {topic}")

        # 7. Generate metadata
        logger.info("Step 7: Generating metadata")
        metadata = self._generate_metadata(content, config)

        # 8. Get token usage from LLM writer
        token_usage = self.llm_writer.get_usage_summary()
        logger.info(f"=== Mega Guide Complete: {metadata['word_count']} words ===")
        logger.info(f"Token usage: {token_usage['total_input_tokens']} input, "
                   f"{token_usage['total_output_tokens']} output, "
                   f"${token_usage['total_cost_usd']:.6f}")

        return {
            "content": content,
            "metadata": metadata,
            "template_data": template_data,
            "token_usage": token_usage
        }

    def assemble_source_type_page(self, source_type: str, config: dict) -> dict:
        """
        Assemble source type guide content

        Args:
            source_type: Type of source (e.g., "journal article", "book", "website")
            config: Configuration dict with title, description, keywords

        Returns:
            Dict with 'content' (markdown), 'metadata', 'template_data', 'token_usage'
        """
        logger.info(f"=== Assembling Source Type Page: {source_type} ===")

        # 1. Load template
        logger.info("Step 1: Loading source type template")
        template = self.template_engine.load_template("source_type_template.md")

        # 2. Load specific data for this source type
        logger.info("Step 2: Loading source type specific data")
        source_type_data = self._load_source_type_data(source_type)
        examples = self._load_examples_for_source_type(source_type)
        errors = self._load_errors_for_source_type(source_type)

        logger.info(f"  Loaded {len(examples)} examples, {len(errors)} errors")

        # 3. Generate LLM sections
        logger.info("Step 3: Generating LLM content sections")
        llm_content = self._generate_source_type_sections(source_type, config, source_type_data)

        # 4. Combine content
        logger.info("Step 4: Combining all content into template")
        template_data = {
            **config,
            **llm_content,
            "source_type_name": source_type.title(),
            "examples": examples,
            "common_errors": errors,
            "validation_checklist": self._generate_checklist(source_type_data.get('rules', [])),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "reading_time": "10 minutes"  # Will recalculate
        }

        # 5. Render template
        logger.info("Step 5: Rendering template with data")
        content = self.template_engine.inject_variables(template, template_data)

        # 6. Validate output
        logger.info("Step 6: Validating generated content")
        if not self.template_engine.validate_output(content, min_words=2000):
            raise ValueError(f"Generated source type page too short: {source_type}")

        # 7. Generate metadata
        logger.info("Step 7: Generating metadata")
        metadata = self._generate_metadata(content, config)

        # 8. Get token usage from LLM writer
        token_usage = self.llm_writer.get_usage_summary()
        logger.info(f"=== Source Type Page Complete: {metadata['word_count']} words ===")
        logger.info(f"Token usage: {token_usage['total_input_tokens']} input, "
                   f"{token_usage['total_output_tokens']} output, "
                   f"${token_usage['total_cost_usd']:.6f}")

        return {
            "content": content,
            "metadata": metadata,
            "template_data": template_data,
            "token_usage": token_usage
        }

    def _generate_mega_guide_sections(self, topic: str, config: dict, rules: list) -> dict:
        """
        Generate all LLM content sections for mega guide

        Args:
            topic: Guide topic
            config: Configuration dict
            rules: List of relevant rules

        Returns:
            Dict with LLM-generated content sections
        """
        logger.info("Generating LLM sections for mega guide")

        sections = {}

        # Introduction
        logger.info("  Generating introduction...")
        sections["introduction"] = self.llm_writer.generate_introduction(
            topic=topic,
            keywords=config.get('keywords', []),
            rules={"rules": rules[:5]},  # Pass top 5 rules
            pain_points=config.get('pain_points', [])
        )

        # Main sections (simplified for now - in full version would generate multiple)
        logger.info("  Generating main content sections...")
        sections["main_sections"] = self._generate_main_sections(topic, rules)

        # FAQ
        logger.info("  Generating FAQ section...")
        sections["faq_questions"] = self.llm_writer.generate_faq(topic, num_questions=12)

        # Related resources (auto-generated based on topic)
        logger.info("  Generating related resources...")
        sections["related_resources"] = self._generate_related_resources(topic)

        logger.info("All LLM sections generated successfully")
        return sections

    def _generate_source_type_sections(self, source_type: str, config: dict, data: dict) -> dict:
        """
        Generate LLM content for source type page

        Args:
            source_type: Type of source
            config: Configuration dict
            data: Source type specific data

        Returns:
            Dict with LLM-generated content
        """
        logger.info("Generating LLM sections for source type page")

        sections = {}

        # Basic format explanation
        logger.info("  Generating format explanation...")
        example_strs = self._examples_to_strings(data.get('examples', [])[:2])
        sections["basic_format_explanation"] = self.llm_writer.generate_explanation(
            concept=f"{source_type} citation format",
            rules=data.get('rules', {}),
            examples=example_strs
        )

        # Step-by-step instructions
        logger.info("  Generating step-by-step instructions...")
        sections["step_by_step_instructions"] = self.llm_writer.generate_step_by_step(
            task=f"Create {source_type} citation",
            rules=data.get('rules', {})
        )

        # Special cases
        logger.info("  Generating special cases...")
        sections["special_cases"] = self._generate_special_cases(source_type, data)

        # FAQ
        logger.info("  Generating FAQ...")
        sections["faq"] = self.llm_writer.generate_faq(f"citing {source_type}", num_questions=6)

        logger.info("All source type sections generated successfully")
        return sections

    def _load_relevant_rules(self, topic: str) -> list:
        """
        Load rules relevant to topic from knowledge base

        Args:
            topic: Topic to filter rules by

        Returns:
            List of relevant rule dicts
        """
        logger.debug(f"Loading relevant rules for topic: {topic}")

        rules_file = self.knowledge_base_dir / "citation_rules.json"

        if not rules_file.exists():
            logger.warning(f"Rules file not found: {rules_file}")
            return []

        with open(rules_file, 'r', encoding='utf-8') as f:
            all_rules = json.load(f)

        # Filter rules based on topic keywords
        topic_lower = topic.lower()
        topic_keywords = set(topic_lower.split())

        relevant_rules = []

        for rule in all_rules:
            # Check if any topic keyword appears in rule description or category
            rule_text = (
                rule.get('description', '') + ' ' +
                rule.get('category', '') + ' ' +
                rule.get('rule_id', '')
            ).lower()

            if any(keyword in rule_text for keyword in topic_keywords):
                relevant_rules.append(rule)

        # If no specific matches, return all rules (user wants broad guide)
        if not relevant_rules:
            logger.info(f"No specific rules matched topic '{topic}', returning all rules")
            relevant_rules = all_rules

        logger.debug(f"Found {len(relevant_rules)} relevant rules")
        return relevant_rules

    def _load_examples(self, topic: str) -> list:
        """
        Load examples relevant to topic

        Args:
            topic: Topic to filter examples by

        Returns:
            List of example dicts (max 10)
        """
        logger.debug(f"Loading examples for topic: {topic}")

        examples_file = self.knowledge_base_dir / "examples.json"

        if not examples_file.exists():
            logger.warning(f"Examples file not found: {examples_file}")
            return []

        with open(examples_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both dict with "examples" key and direct list
        if isinstance(data, dict) and "examples" in data:
            all_examples = data["examples"]
        elif isinstance(data, list):
            all_examples = data
        else:
            logger.warning(f"Unexpected examples.json structure: {type(data)}")
            return []

        # Return first 10 examples (filtering can be added later)
        examples = all_examples[:10]

        logger.debug(f"Loaded {len(examples)} examples")
        return examples

    def _load_errors(self, topic: str) -> list:
        """
        Load common errors relevant to topic

        Args:
            topic: Topic to filter errors by

        Returns:
            List of error dicts
        """
        logger.debug(f"Loading errors for topic: {topic}")

        errors_file = self.knowledge_base_dir / "common_errors.json"

        if not errors_file.exists():
            logger.warning(f"Errors file not found: {errors_file}")
            return []

        with open(errors_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both dict with "errors" key and direct list
        if isinstance(data, dict) and "errors" in data:
            all_errors = data["errors"]
        elif isinstance(data, list):
            all_errors = data
        else:
            logger.warning(f"Unexpected errors.json structure: {type(data)}")
            return []

        # Return first 10 errors (filtering can be added later)
        errors = all_errors[:10]

        logger.debug(f"Loaded {len(errors)} errors")
        return errors

    def _load_source_type_data(self, source_type: str) -> dict:
        """
        Load source type specific data

        Args:
            source_type: Type of source

        Returns:
            Dict with rules and other source-specific data
        """
        logger.debug(f"Loading source type data for: {source_type}")

        # Load all rules and filter by source type
        rules = self._load_relevant_rules(source_type)

        # Get examples for this source type
        examples = self._load_examples_for_source_type(source_type)

        return {
            "rules": rules,
            "examples": examples[:5]  # Top 5 for explanation
        }

    def _load_examples_for_source_type(self, source_type: str) -> list:
        """
        Load examples filtered by source type

        Args:
            source_type: Type of source (e.g., "journal article")

        Returns:
            List of examples for this source type
        """
        logger.debug(f"Loading examples for source type: {source_type}")

        examples_file = self.knowledge_base_dir / "examples.json"

        if not examples_file.exists():
            logger.warning(f"Examples file not found: {examples_file}")
            return []

        with open(examples_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both dict with "examples" key and direct list
        if isinstance(data, dict) and "examples" in data:
            all_examples = data["examples"]
        elif isinstance(data, list):
            all_examples = data
        else:
            logger.warning(f"Unexpected examples.json structure: {type(data)}")
            return []

        # Filter by source type
        source_type_lower = source_type.lower().replace(" ", "_")

        filtered_examples = [
            ex for ex in all_examples
            if source_type_lower in ex.get('source_type', '').lower()
        ]

        # If no matches, return general examples
        if not filtered_examples:
            logger.info(f"No examples matched '{source_type}', returning general examples")
            filtered_examples = all_examples[:10]

        logger.debug(f"Found {len(filtered_examples)} examples for source type")
        return filtered_examples[:10]

    def _load_errors_for_source_type(self, source_type: str) -> list:
        """
        Load errors relevant to source type

        Args:
            source_type: Type of source

        Returns:
            List of error dicts
        """
        logger.debug(f"Loading errors for source type: {source_type}")

        # For now, just load general errors
        # In future, could filter by source type
        return self._load_errors(source_type)

    def _generate_metadata(self, content: str, config: dict) -> dict:
        """
        Generate SEO metadata for page

        Args:
            content: Full page content (markdown)
            config: Configuration dict

        Returns:
            Dict with metadata fields
        """
        logger.debug("Generating page metadata")

        word_count = len(content.split())
        reading_time_minutes = max(1, word_count // 200)  # 200 words per minute

        metadata = {
            "meta_title": config.get('title', ''),
            "meta_description": config.get('description', ''),
            "word_count": word_count,
            "reading_time": f"{reading_time_minutes} minute{'s' if reading_time_minutes > 1 else ''}",
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }

        logger.debug(f"Metadata: {word_count} words, {reading_time_minutes} min read")
        return metadata

    def _generate_checklist(self, rules: list) -> list:
        """
        Generate validation checklist from rules

        Args:
            rules: List of rule dicts

        Returns:
            List of checklist items
        """
        logger.debug(f"Generating checklist from {len(rules)} rules")

        checklist = []

        for rule in rules[:10]:  # Top 10 rules
            checklist.append({
                "item": rule.get('description', rule.get('rule_id', 'Unknown rule')),
                "rule_id": rule.get('rule_id', '')
            })

        logger.debug(f"Generated {len(checklist)} checklist items")
        return checklist

    def _generate_main_sections(self, topic: str, rules: list) -> str:
        """
        Generate main content sections (simplified version)

        Args:
            topic: Guide topic
            rules: Relevant rules

        Returns:
            Markdown content for main sections
        """
        logger.debug("Generating main sections")

        # For now, generate one comprehensive explanation
        # In full version, would generate multiple H2 sections

        main_content = self.llm_writer.generate_explanation(
            concept=f"comprehensive guide to {topic}",
            rules={"rules": rules[:10]},
            examples=[]
        )

        return main_content

    def _generate_special_cases(self, source_type: str, data: dict) -> str:
        """
        Generate special cases section for source type

        Args:
            source_type: Type of source
            data: Source type data

        Returns:
            Markdown content for special cases
        """
        logger.debug(f"Generating special cases for {source_type}")

        # Generate explanation of special cases for this source type
        special_cases = self.llm_writer.generate_explanation(
            concept=f"special cases and edge cases when citing {source_type}",
            rules=data.get('rules', {}),
            examples=[]
        )

        return special_cases

    def _generate_related_resources(self, topic: str) -> list:
        """
        Generate list of related resources

        Args:
            topic: Guide topic

        Returns:
            List of related resource dicts
        """
        logger.debug(f"Generating related resources for {topic}")

        # Simplified version - just return common related pages
        # In full version, would be smarter about relationships

        related = [
            {"title": "APA Citation Checker", "url": "/checker/"},
            {"title": "Common APA Errors", "url": "/guides/common-errors/"},
            {"title": "APA Style Guide", "url": "/guides/apa-style/"}
        ]

        return related

    def _examples_to_strings(self, examples: list) -> list:
        """
        Convert example dicts to strings for LLM prompts

        Args:
            examples: List of example dicts

        Returns:
            List of example citation strings
        """
        strings = []
        for ex in examples:
            if isinstance(ex, dict):
                # Extract reference_citation from example dict
                citation = ex.get('reference_citation', str(ex))
                strings.append(citation)
            else:
                strings.append(str(ex))

        return strings
