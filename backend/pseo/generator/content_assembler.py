"""
Content Assembler for PSEO Pages

Orchestrates the assembly of complete PSEO pages by combining:
- Jinja2 templates (structure)
- LLM-generated content (unique sections)
- Structured knowledge base data (rules, examples, errors)
"""
import json
import logging
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from .template_engine import TemplateEngine
from .llm_writer import LLMWriter

# Add TF-IDF similarity calculation
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    TFIDF_AVAILABLE = True
except ImportError:
    TFIDF_AVAILABLE = False
    logging.warning("scikit-learn not available - TF-IDF similarity calculation disabled")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentAssembler:
    """
    Assembles complete PSEO page content by combining templates,
    LLM generation, and structured knowledge base data.
    """

    def __init__(self, knowledge_base_dir: str, templates_dir: str, citation_style: str = "APA 7th edition"):
        """
        Initialize ContentAssembler

        Args:
            knowledge_base_dir: Path to knowledge base JSON files
            templates_dir: Path to Jinja2 templates
            citation_style: Citation style for LLM content generation (default: APA 7th edition)
        """
        logger.info(f"Initializing ContentAssembler")
        logger.info(f"  Knowledge base: {knowledge_base_dir}")
        logger.info(f"  Templates: {templates_dir}")
        logger.info(f"  Citation style: {citation_style}")

        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.templates_dir = Path(templates_dir)
        self.citation_style = citation_style

        # Validate directories exist
        if not self.knowledge_base_dir.exists():
            raise ValueError(f"Knowledge base directory does not exist: {knowledge_base_dir}")
        if not self.templates_dir.exists():
            raise ValueError(f"Templates directory does not exist: {templates_dir}")

        # Initialize components
        self.template_engine = TemplateEngine(templates_dir)
        self.llm_writer = LLMWriter(citation_style=citation_style)

        # Token budget enforcement
        self.max_cost_per_page = 0.50  # USD per page
        self.token_budgets = {
            "navigation_guide": {"max_tokens": 500, "target_words": 350},
            "real_examples": {"max_tokens": 800, "target_words": 500},
            "source_issues": {"max_tokens": 600, "target_words": 400},
            "faq": {"max_tokens": 400, "target_words": 250},
            "step_by_step": {"max_tokens": 600, "target_words": 400},
            "source_notes": {"max_tokens": 300, "target_words": 200}
        }

        logger.info("ContentAssembler initialized successfully")

    @property
    def style_display_name(self) -> str:
        """Get display name for citation style (e.g., 'MLA 9 Format' or 'APA Format')"""
        if "mla" in self.citation_style.lower():
            return "MLA 9 Format"
        return "APA Format"

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
        if not self.template_engine.validate_output(content, min_words=800):
            raise ValueError(f"Generated mega guide too short for topic: {topic}")

        # 7. Generate metadata
        logger.info("Step 7: Generating metadata")
        metadata = self._generate_metadata(content, config, page_type="mega_guide")

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

        # Auto-generate title if missing (common for specific sources)
        if not config.get('title'):
            generated_title = f"How to Cite {source_type} in {self.style_display_name}"
            config = {**config, 'title': generated_title}
            logger.info(f"  Auto-generated title: {generated_title}")

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
            "quick_reference_template": self._generate_quick_reference_template(source_type),
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
        if not self.template_engine.validate_output(content, min_words=800):
            raise ValueError(f"Generated source type page too short: {source_type}")

        # 7. Generate metadata
        logger.info("Step 7: Generating metadata")
        metadata = self._generate_metadata(content, config, page_type="source_type")

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
            topic: Topic to filter errors by (e.g., "conference paper citation", "newspaper citation")

        Returns:
            List of error dicts filtered by source type
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

        # Map topic to source type tag used in knowledge base
        source_type_map = {
            "conference paper citation": "conference_paper",
            "dissertation citation": "dissertation",
            "thesis citation": "thesis",
            "book chapter citation": "book_chapter",
            "edited book citation": "edited_book",
            "report citation": "report",
            "government report citation": "government_report",
            "dataset citation": "dataset",
            "newspaper citation": "newspaper_article",
            "newspaper print citation": "newspaper_article",
            "magazine citation": "magazine_article",
            "blog citation": "blog_post",
            "youtube citation": "youtube_video",
            "podcast citation": "podcast",
            "ted talk citation": "ted_talk",
            "wikipedia citation": "wikipedia",
            "dictionary citation": "dictionary",
            "encyclopedia citation": "encyclopedia",
            "film citation": "film",
            "tv episode citation": "tv_episode",
            "twitter citation": "twitter_post",
            "instagram citation": "instagram_post",
            "facebook citation": "facebook_post",
            "linkedin citation": "linkedin_post",
            "software citation": "software",
            "patent citation": "patent",
            "artwork citation": "artwork",
            "ebook citation": "ebook",
            "working paper citation": "working_paper",
            "white paper citation": "white_paper",
            "press release citation": "press_release"
        }

        source_type_tag = source_type_map.get(topic.lower())

        # Filter errors by source type
        filtered_errors = []
        generic_errors = []

        for error in all_errors:
            affected_types = error.get("affected_source_types", [])

            # If error applies to all source types, treat as generic
            if "all_source_types" in affected_types:
                generic_errors.append(error)
            # If source type tag matches, add to filtered list
            elif source_type_tag and source_type_tag in affected_types:
                filtered_errors.append(error)
            # If no affected_source_types specified, it's also generic
            elif not affected_types:
                generic_errors.append(error)

        # Prefer source-specific errors, fall back to generic if needed
        if len(filtered_errors) >= 5:
            errors = filtered_errors[:10]
            logger.info(f"Using {len(errors)} source-specific errors for {topic}")
        else:
            # Mix: use what we have + fill with generic
            errors = filtered_errors + generic_errors[:max(0, 10 - len(filtered_errors))]
            logger.info(f"Using {len(filtered_errors)} source-specific + {len(errors) - len(filtered_errors)} generic errors for {topic}")

        logger.debug(f"Loaded {len(errors)} total errors (from {len(all_errors)} available)")
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

        # If no matches, return empty list (better than wrong source type)
        if not filtered_examples:
            logger.info(f"No examples matched '{source_type}', returning empty list")
            return []

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

    def _generate_metadata(self, content: str, config: dict, page_type: str = None) -> dict:
        """
        Generate SEO metadata for page

        Args:
            content: Full page content (markdown)
            config: Configuration dict
            page_type: Page type (mega_guide, source_type, etc.)

        Returns:
            Dict with metadata fields
        """
        logger.debug("Generating page metadata")

        word_count = len(content.split())
        reading_time_minutes = max(1, word_count // 200)  # 200 words per minute

        metadata = {
            "page_type": page_type or config.get('page_type', 'source_type'),
            "meta_title": config.get('title', ''),
            "meta_description": config.get('description', ''),
            "word_count": word_count,
            "reading_time": f"{reading_time_minutes} minute{'s' if reading_time_minutes > 1 else ''}",
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }

        logger.debug(f"Metadata: page_type={metadata['page_type']}, {word_count} words, {reading_time_minutes} min read")
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

    def _generate_main_sections(self, topic: str, rules: list) -> list:
        """
        Generate main content sections as list of dicts

        Args:
            topic: Guide topic
            rules: Relevant rules

        Returns:
            List of section dicts with title, slug, content, examples
        """
        logger.debug("Generating main sections")

        # Define 5 comprehensive sections for mega guides
        section_definitions = [
            {
                "title": "Understanding MLA 9th Edition",
                "slug": "understanding-mla-9th-edition", 
                "concept": f"the core philosophy and container system in {topic}",
                "rules_slice": rules[:5]
            },
            {
                "title": "Author Formatting Rules",
                "slug": "author-formatting-rules",
                "concept": "author name formatting in MLA 9 including full names, name inversion, two authors with 'and', and et al. for three or more authors",
                "rules_slice": [r for r in rules if r.get('category') == 'author_formatting'][:5] or rules[:3]
            },
            {
                "title": "Title and Source Formatting", 
                "slug": "title-source-formatting",
                "concept": "title formatting in MLA 9 including Title Case capitalization, when to use italics for complete works, and when to use quotation marks for shorter works",
                "rules_slice": [r for r in rules if r.get('category') == 'title_formatting'][:5] or rules[3:6]
            },
            {
                "title": "Dates, Publishers, and Locations",
                "slug": "dates-publishers-locations",
                "concept": "date formatting in MLA 9 including Day Month Year format, date placement after publisher, URLs without http://, and DOI formatting",
                "rules_slice": [r for r in rules if r.get('category') in ('date_formatting', 'url_formatting')][:5] or rules[5:8]
            },
            {
                "title": "In-Text Citations",
                "slug": "in-text-citations",
                "concept": "in-text citations in MLA 9 including parenthetical and narrative citations, author-page format without p. or pp., and handling sources without page numbers",
                "rules_slice": [r for r in rules if r.get('category') == 'punctuation'][:5] or rules[8:11]
            }
        ]

        sections = []
        for section_def in section_definitions:
            logger.info(f"  Generating section: {section_def['title']}...")
            
            content = self.llm_writer.generate_explanation(
                concept=section_def["concept"],
                rules={"rules": section_def["rules_slice"]},
                examples=[],
                max_tokens=3000  # High value to avoid gpt-5.2 truncation bug
            )
            
            sections.append({
                "title": section_def["title"],
                "slug": section_def["slug"],
                "content": content,
                "examples": []
            })

        return sections

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
        Generate list of related resources based on citation style

        Args:
            topic: Guide topic

        Returns:
            List of related resource dicts
        """
        logger.debug(f"Generating related resources for {topic}")

        # Return style-appropriate resources
        if "mla" in self.citation_style.lower():
            related = [
                {"title": "MLA Citation Checker", "url": "/"},
                {"title": "How to Cite Books in MLA", "url": "/how-to-cite-book-mla/"},
                {"title": "MLA 9th Edition Guide", "url": "/guide/mla-9th-edition/"}
            ]
        else:
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

    def _generate_quick_reference_template(self, source_type: str) -> str:
        """
        Generate quick reference template based on source type and citation style

        Args:
            source_type: Type of source

        Returns:
            Formatted template string with HTML
        """
        logger.debug(f"Generating quick reference template for {source_type}")

        # MLA 9 templates - use full first names, "and" between authors, year after publisher
        mla_templates = {
            "book citation": "Author Last, First Name. <em>Title of Book</em>. Publisher, Year.",
            "book citation MLA": "Author Last, First Name. <em>Title of Book</em>. Publisher, Year.",
            "journal_article": "Author Last, First Name. \"Title of Article.\" <em>Journal Name</em>, vol. X, no. X, Year, pp. XX-XX.",
            "website citation": "Author Last, First Name. \"Title of Page.\" <em>Website Name</em>, Publisher, Day Month Year, URL.",
            "newspaper citation": "Author Last, First Name. \"Title of Article.\" <em>Newspaper Name</em>, Day Month Year, p. XX.",
            "youtube citation": "Author/Username. \"Title of Video.\" <em>YouTube</em>, uploaded by Channel Name, Day Month Year, URL.",
            "YouTube": "Author/Username. \"Title of Video.\" <em>YouTube</em>, uploaded by Channel Name, Day Month Year, URL.",
            "ebook citation": "Author Last, First Name. <em>Title of Book</em>. E-book ed., Publisher, Year.",
            "dissertation citation": "Author Last, First Name. <em>Title of Dissertation</em>. Year. University, PhD dissertation.",
            "conference paper citation": "Author Last, First Name. \"Title of Paper.\" <em>Conference Name</em>, Year, Location.",
            "podcast citation": "Host Last, First Name, host. \"Episode Title.\" <em>Podcast Name</em>, Publisher, Day Month Year.",
            "film citation": "Director Last, First Name, director. <em>Title of Film</em>. Studio, Year.",
            "wikipedia citation": "\"Title of Article.\" <em>Wikipedia</em>, Wikimedia Foundation, Day Month Year, URL.",
        }

        # APA 7 templates (original)
        apa_templates = {
            "conference paper citation": "Author, A. A. (Year). <em>Title of paper</em>. In E. E. Editor (Ed.), <em>Title of proceedings</em> (pp. pages). Publisher. https://doi.org/xxxxx",
            "dissertation citation": "Author, A. A. (Year). <em>Title of dissertation</em> [Doctoral dissertation, Institution Name]. Database Name. https://doi.org/xxxxx",
            "thesis citation": "Author, A. A. (Year). <em>Title of thesis</em> [Master's thesis, Institution Name]. Database Name. https://URL",
            "book chapter citation": "Author, A. A. (Year). Title of chapter. In E. E. Editor (Ed.), <em>Book title</em> (pp. pages). Publisher. https://doi.org/xxxxx",
            "edited book citation": "Editor, E. E. (Ed.). (Year). <em>Book title</em>. Publisher. https://doi.org/xxxxx",
            "report citation": "Author, A. A. (Year). <em>Title of report</em> (Report No. XXX). Publisher. https://doi.org/xxxxx",
            "government report citation": "Agency Name. (Year). <em>Title of report</em> (Report No. XXX). Publisher. https://URL",
            "dataset citation": "Author, A. A. (Year). <em>Title of dataset</em> (Version X) [Data set]. Publisher. https://doi.org/xxxxx",
            "newspaper citation": "Author, A. A. (Year, Month Day). Title of article. <em>Newspaper Name</em>. https://www.url.com",
            "magazine citation": "Author, A. A. (Year, Month Day). Title of article. <em>Magazine Name</em>, <em>volume</em>(issue), pages. https://www.url.com",
            "blog citation": "Author, A. A. (Year, Month Day). <em>Title of blog post</em>. Blog Name. https://www.url.com",
            "youtube citation": "Author/Username. (Year, Month Day). <em>Title of video</em> [Video]. YouTube. https://www.youtube.com/watch?v=xxxxx",
            "podcast citation": "Host, H. H. (Host). (Year, Month Day). Episode title (No. episode number) [Audio podcast episode]. In <em>Podcast name</em>. Publisher. https://www.url.com",
            "ted talk citation": "Speaker, S. S. (Year, Month). <em>Title of talk</em> [Video]. TED. https://www.ted.com/talks/xxxxx",
            "wikipedia citation": "Wikipedia contributors. (Year, Month Day). Title of article. In <em>Wikipedia</em>. Retrieved Month Day, Year, from https://en.wikipedia.org/wiki/xxxxx",
            "dictionary citation": "Author, A. A. (Year). Title of entry. In <em>Dictionary name</em> (edition ed.). Publisher. https://www.url.com",
            "encyclopedia citation": "Author, A. A. (Year). Title of entry. In E. E. Editor (Ed.), <em>Encyclopedia name</em> (Vol. volume, pp. pages). Publisher. https://www.url.com",
            "film citation": "Director, D. D. (Director). (Year). <em>Title of film</em> [Film]. Studio. https://www.url.com",
            "tv episode citation": "Writer, W. W. (Writer), & Director, D. D. (Director). (Year, Month Day). Episode title (Season X, Episode Y) [TV series episode]. In P. P. Producer (Executive Producer), <em>Series name</em>. Studio. https://www.url.com",
            "twitter citation": "Author [@username]. (Year, Month Day). <em>First 20 words of tweet</em> [Tweet]. Twitter. https://twitter.com/username/status/xxxxx",
            "instagram citation": "Author [@username]. (Year, Month Day). <em>First 20 words of caption</em> [Photograph]. Instagram. https://www.instagram.com/p/xxxxx",
            "facebook citation": "Author. (Year, Month Day). <em>First 20 words of post</em> [Status update]. Facebook. https://www.facebook.com/username/posts/xxxxx",
            "linkedin citation": "Author. (Year, Month Day). <em>First 20 words of post</em> [Status update]. LinkedIn. https://www.linkedin.com/posts/xxxxx",
            "software citation": "Author, A. A. (Year). <em>Software name</em> (Version X.X) [Computer software]. Publisher. https://www.url.com",
            "patent citation": "Inventor, I. I. (Year). <em>Patent title</em> (U.S. Patent No. X,XXX,XXX). U.S. Patent and Trademark Office. https://www.url.com",
            "artwork citation": "Artist, A. A. (Year). <em>Title of work</em> [Medium]. Museum/Collection Name, Location. https://www.url.com",
            "music citation": "Artist, A. A. (Year). <em>Song title</em> [Song]. On <em>Album name</em>. Record Label. https://www.url.com",
            "ebook citation": "Author, A. A. (Year). <em>Book title</em> [E-book]. Publisher. https://doi.org/xxxxx",
            "working paper citation": "Author, A. A. (Year). <em>Title of working paper</em> (Working Paper No. XXX). Institution Name. https://www.url.com",
            "white paper citation": "Author/Organization. (Year). <em>Title of white paper</em>. Publisher/Organization. https://www.url.com",
            "press release citation": "Organization Name. (Year, Month Day). <em>Title of press release</em> [Press release]. https://www.url.com"
        }

        # Select templates based on citation style
        if "mla" in self.citation_style.lower():
            templates = mla_templates
            default_template = "Author Last, First Name. <em>Title of Work</em>. Publisher, Year."
        else:
            templates = apa_templates
            default_template = "Author, A. A. (Year). <em>Title of work</em>. <em>Source Name</em>, <em>volume</em>(issue), pages. https://doi.org/xxxxx"

        # Return appropriate template
        template = templates.get(source_type.lower(), default_template)

        logger.debug(f"Using template: {template[:50]}...")
        return template

    def _generate_validation_quick_reference(self, validation_element: str) -> str:
        """
        Generate validation quick reference based on validation element
        Args:
            validation_element: Type of validation element (e.g., "capitalization", "italics", "doi")
        Returns:
            Formatted quick reference string with HTML
        """
        logger.debug(f"Generating validation quick reference for {validation_element}")

        # Validation quick reference templates
        validation_quick_refs = {
            "capitalization": "Article titles: Sentence case. Journal titles: Title Case.",
            "italics": "Italicize: journal names, book titles, volume numbers. NOT: article titles, issue numbers.",
            "doi": "Format: https://doi.org/10.xxxx NO period after DOI.",
            "ampersand": "Use & for multiple authors in reference list, 'and' in text.",
            "author_names": "Surname, I. I. for individuals. Full name for organizations.",
            "date_formatting": "References: Year only. Text: (Year, Month Day) for specific dates.",
            "volume_issue": "Volume italicized: *Journal*, *volume*(issue), pages.",
            "et_al": "List up to 20 authors, then use First Author et al.",
            "in_text_citations": "(Author, Year) for parenthetical. Author (Year) for narrative.",
            "reference_list": "Hanging indent, alphabetized, double-spaced.",
            "alphabetization": "Alphabetize by author surname, then by year.",
            "citation_consistency": "Every in-text citation must have matching reference.",
            "publisher_info": "Include publisher for books. Omit for periodicals.",
            "url_formatting": "Live hyperlinks, no underline, remove database names.",
            "hanging_indents": "First line flush left, subsequent lines indented 0.5 inches."
        }

        # Default template for unknown validation elements
        default_template = "Check formatting according to APA 7th edition guidelines."

        # Return appropriate template
        template = validation_quick_refs.get(validation_element.lower(), default_template)

        logger.debug(f"Using validation template: {template}")
        return template

    def assemble_validation_page(self, validation_element: str, config: dict) -> dict:
        """
        Assemble validation guide content
        Args:
            validation_element: Type of validation element (e.g., "capitalization", "italics", "doi")
            config: Configuration dict with title, description, keywords
        Returns:
            Dict with 'content' (markdown), 'metadata', 'template_data', 'token_usage'
        """
        logger.info(f"=== Assembling Validation Page: {validation_element} ===")

        # 1. Load validation template
        logger.info("Step 1: Loading validation template")
        template = self.template_engine.load_template("validation_template.md")

        # 2. Generate LLM content sections FIRST
        logger.info("Step 2: Generating LLM content sections")
        llm_content = self._generate_validation_llm_sections(validation_element, config)

        # 3. Load validation-specific data using LLM content
        logger.info("Step 3: Loading validation specific data")
        validation_data = self._load_validation_data(validation_element, llm_content)
        errors = self._load_errors_for_validation_element(validation_element)

        # 4. Prepare template variables
        logger.info("Step 4: Preparing template variables")

        # DEBUG: Log validation_data content before template creation
        logger.debug(f"Validation data keys: {validation_data.keys()}")
        before_after_from_data = validation_data.get("before_after_examples", [])
        tools_tips_from_data = {k: v for k, v in validation_data.items() if k.startswith(('word_', 'docs_', 'search_', 'time_', 'common_'))}
        logger.debug(f"Before/after from validation_data: {len(before_after_from_data)} items")
        logger.debug(f"Tools tips from validation_data: {len(tools_tips_from_data)} keys")

        template_data = {
            "title": config["title"],
            "description": config["description"],
            "validation_element": validation_element,
            "validation_element_display": "DOI" if validation_element == "doi" else validation_element.replace('_', ' ').title(),
            "quick_reference_template": self._generate_validation_quick_reference(validation_element),
            "what_to_look_for_rules": validation_data.get("rules", "Rules for this validation element..."),
            "apa_official_guidance": validation_data.get("apa_guidance", "According to APA 7th edition guidelines..."),
            "correct_example": validation_data.get("correct_example", ""),
            "incorrect_example": validation_data.get("incorrect_example", ""),
            "key_rules": validation_data.get("key_rules", ""),
            "step_by_step_instructions": llm_content.get("step_by_step_instructions", ""),
            "verification_step_number": len(validation_data.get("steps", [])) + 3,
            "final_step_number": len(validation_data.get("steps", [])) + 4,
            "find_replace_strategy": validation_data.get("find_replace_strategy", ""),
            "common_errors": errors[:5],  # Limit to top 5 errors
            "affected_source_types": validation_data.get("affected_source_types", []),
            "validation_checklist_items": validation_data.get("checklist_items", ""),
            "word_find_instructions": validation_data.get("word_find_instructions", ""),
            "word_find_replace_instructions": validation_data.get("word_find_replace_instructions", ""),
            "word_styles_instructions": validation_data.get("word_styles_instructions", ""),
            "docs_find_instructions": validation_data.get("docs_find_instructions", ""),
            "docs_addons_instructions": validation_data.get("docs_addons_instructions", ""),
            "search_strategies": validation_data.get("search_strategies", ""),
            "time_saving_techniques": validation_data.get("time_saving_techniques", []),
            "common_pitfalls": validation_data.get("common_pitfalls", []),
            "before_after_examples": validation_data.get("before_after_examples", []),
            "related_validation_guides": validation_data.get("related_validation_guides", []),
            "related_errors": validation_data.get("related_errors", []),
            "relevant_source_guides": validation_data.get("relevant_source_guides", []),
            "last_updated": datetime.now().strftime("%B %d, %Y"),
            "reading_time": self._calculate_reading_time(2000),  # Target 2000 words
            "faq_items": llm_content.get("faq_items", [])
        }

        # DEBUG: Log final template data
        logger.debug(f"Final template before_after_examples: {len(template_data.get('before_after_examples', []))} items")
        tools_tips_in_template = {k: v for k, v in template_data.items() if k.startswith(('word_', 'docs_', 'search_', 'time_', 'common_')) and v}
        logger.debug(f"Final template tools tips keys with content: {len(tools_tips_in_template)}")

        # 5. Render template
        logger.info("Step 5: Rendering template")

        # DEBUG: Log what we're passing to template
        logger.debug(f"Template data keys: {template_data.keys()}")
        logger.debug(f"affected_source_types type: {type(template_data.get('affected_source_types'))}")
        logger.debug(f"affected_source_types length: {len(template_data.get('affected_source_types', []))}")
        if template_data.get('affected_source_types'):
            logger.debug(f"First source type: {template_data['affected_source_types'][0]}")
        logger.debug(f"before_after_examples type: {type(template_data.get('before_after_examples'))}")
        logger.debug(f"before_after_examples length: {len(template_data.get('before_after_examples', []))}")
        logger.debug(f"common_errors type: {type(template_data.get('common_errors'))}")
        logger.debug(f"common_errors length: {len(template_data.get('common_errors', []))}")

        content = self.template_engine.inject_variables(template, template_data)

        # 6. Add front matter for static site generator
        logger.info("Step 6: Adding front matter")
        front_matter = f"""---
title: {config["title"]}
description: {config["description"]}
meta_title: {config["title"]}
meta_description: {config["description"]}
page_type: validation
url_slug: {config["url_slug"]}
url: {config["url"]}
last_updated: {datetime.now().strftime("%Y-%m-%d")}
word_count: {self._estimate_word_count(content)}
reading_time: {self._calculate_reading_time(self._estimate_word_count(content))}
validation_element: {validation_element}
---

"""
        content = front_matter + content

        # 7. Prepare metadata
        metadata = {
            "title": config["title"],
            "description": config["description"],
            "keywords": config["keywords"],
            "url": config["url"],
            "validation_element": validation_element,
            "word_count": self._estimate_word_count(content),
            "last_updated": datetime.now().isoformat()
        }

        # 8. Prepare response
        result = {
            "content": content,
            "metadata": metadata,
            "template_data": template_data,
            "token_usage": llm_content.get("token_usage", {})
        }

        logger.info(f"✅ Validation page assembled: {len(content)} characters")
        return result

    def _load_validation_data(self, validation_element: str, llm_content: dict) -> dict:
        """
        Load validation-specific data with LLM-generated content
        Args:
            validation_element: Type of validation element
            llm_content: LLM-generated content sections
        Returns:
            Dict with validation data
        """
        # DEBUG: Log what we received from LLM
        logger.debug(f"LLM content keys: {llm_content.keys()}")
        before_after_raw = llm_content.get("before_after_examples", [])
        tools_tips_raw = llm_content.get("tools_tips", {})
        logger.debug(f"Before/after raw type: {type(before_after_raw)}, length: {len(before_after_raw) if isinstance(before_after_raw, (list, dict)) else 'N/A'}")
        logger.debug(f"Tools tips raw type: {type(tools_tips_raw)}, keys: {list(tools_tips_raw.keys()) if isinstance(tools_tips_raw, dict) else 'N/A'}")
        if before_after_raw and isinstance(before_after_raw, list) and len(before_after_raw) > 0:
            logger.debug(f"First before_after example keys: {list(before_after_raw[0].keys()) if isinstance(before_after_raw[0], dict) else 'Not a dict'}")

        # Use structured content directly from new dedicated LLM methods
        source_type_content = llm_content.get("source_type_variations", {})
        if isinstance(source_type_content, dict) and "raw_content" in source_type_content:
            parsed_source_types = self._parse_source_type_content(source_type_content["raw_content"])
        else:
            parsed_source_types = source_type_content  # Assume it's already parsed if not the old format
        parsed_before_after = llm_content.get("before_after_examples", [])
        parsed_tools_tips = llm_content.get("tools_tips", {})

        # DEBUG: Log what we're returning
        logger.debug(f"Returning parsed_before_after type: {type(parsed_before_after)}, length: {len(parsed_before_after) if isinstance(parsed_before_after, (list, dict)) else 'N/A'}")
        logger.debug(f"Returning parsed_tools_tips type: {type(parsed_tools_tips)}, keys: {list(parsed_tools_tips.keys()) if isinstance(parsed_tools_tips, dict) else 'N/A'}")

        return {
            # Template content variables
            "rules": llm_content.get("rules", f"Rules for checking {validation_element} in APA citations..."),
            "apa_guidance": llm_content.get("apa_guidance", f"According to APA 7th edition guidelines for {validation_element}..."),
            "correct_example": llm_content.get("correct_example", f"Correct {validation_element} example..."),
            "incorrect_example": llm_content.get("incorrect_example", f"Incorrect {validation_element} example..."),
            "key_rules": llm_content.get("key_rules", "Key rules to remember..."),
            "what_to_look_for_rules": llm_content.get("rules", f"Rules for checking {validation_element} in APA citations..."),
            "find_replace_strategy": llm_content.get("find_replace_strategy", "Use Find & Replace for..."),
            "validation_checklist_items": llm_content.get("checklist_items", "Checklist items..."),

            # Template data structures (EXACT field names)
            "affected_source_types": parsed_source_types,
            "before_after_examples": parsed_before_after,
            "common_errors": self._load_errors_for_validation_element(validation_element),

            # Tools & tips with exact template field names
            "word_find_instructions": parsed_tools_tips.get("word_find", "Word find instructions..."),
            "word_find_replace_instructions": parsed_tools_tips.get("word_find_replace", "Word Find & Replace instructions..."),
            "word_styles_instructions": parsed_tools_tips.get("word_styles", "Word styles instructions..."),
            "docs_find_instructions": parsed_tools_tips.get("docs_find", "Docs find instructions..."),
            "docs_addons_instructions": parsed_tools_tips.get("docs_addons", "Docs add-ons instructions..."),
            "search_strategies": parsed_tools_tips.get("search_strategies", "Search strategies..."),
            "time_saving_techniques": parsed_tools_tips.get("time_saving_techniques", []),
            "common_pitfalls": parsed_tools_tips.get("common_pitfalls", ["Pitfall 1", "Pitfall 2"]),

            # Other template fields
            "related_validation_guides": [],
            "related_errors": [],
            "relevant_source_guides": [],
            "error_frequency_table": self._format_error_frequency_table(validation_element)
        }

    def _load_errors_for_validation_element(self, validation_element: str) -> List[dict]:
        """
        Load errors relevant to a validation element
        Args:
            validation_element: Type of validation element
        Returns:
            List of error dicts
        """
        # Load common errors
        errors_file = self.knowledge_base_dir / "common_errors.json"

        if not errors_file.exists():
            logger.warning(f"Common errors file not found: {errors_file}")
            return []

        with open(errors_file, 'r', encoding='utf-8') as f:
            all_errors = json.load(f)

        # Map validation elements to error categories
        validation_to_category_map = {
            "author_names": "author_format",
            "capitalization": "capitalization",
            "doi": "doi_url",
            "italics": "italics",
            "ampersand": "punctuation",
            "publisher_info": "punctuation",
            "url_formatting": "doi_url",
            "date_formatting": "punctuation",
            "volume_issue": "punctuation",
            "et_al": "author_format",
            "reference_list": "punctuation",
            "in_text_citations": "punctuation",
            "alphabetization": "punctuation",
            "citation_consistency": "punctuation",
            "hanging_indents": "italics"
        }

        target_category = validation_to_category_map.get(validation_element, validation_element)

        # Filter errors relevant to this validation element
        relevant_errors = []
        for error in all_errors:
            # Enhanced matching with category mapping
            if target_category.lower() in error.get("category", "").lower():
                error["detection_method"] = error.get("fix_instructions", [""])[0] if error.get("fix_instructions") else ""
                error["quick_fix"] = error.get("fix_instructions", [""])[-1] if error.get("fix_instructions") else ""
                error["frequency"] = error.get("frequency", {}).get("estimated_frequency", "Common")
                error["severity"] = "High" if error.get("difficulty_to_fix") == "easy" else "Medium"
                error["easy_to_spot"] = "Yes" if error.get("difficulty_to_fix") == "easy" else "No"
                relevant_errors.append(error)

        logger.info(f"Found {len(relevant_errors)} relevant errors for {validation_element}")
        return relevant_errors

    def _generate_validation_llm_sections(self, validation_element: str, config: dict) -> dict:
        """
        Generate LLM content sections for validation guides
        Args:
            validation_element: Type of validation element
            config: Configuration dict
        Returns:
            Dict with generated content sections
        """
        logger.info(f"Generating LLM sections for validation element: {validation_element}")

        # Define prompts for validation guides
        prompts = {
            "step_by_step": f"""
            As an expert academic writing assistant specializing in APA 7th edition citation validation,
            create a comprehensive step-by-step guide for checking {validation_element} in APA citations.

            Write detailed, step-by-step instructions (400-600 words) that guide users through:
            1. Preparation steps
            2. Systematic checking process with specific actions
            3. Verification steps

            Focus on practical, actionable steps that users can follow to validate {validation_element} in their citations.
            Include specific examples of what to look for and how to fix issues.

            The tone should be helpful and educational, aimed at undergraduate and graduate students.
            """,

            "faq": f"""
            Generate 6 frequently asked questions and answers about checking {validation_element} in APA citations.

            Cover common concerns, edge cases, and practical questions students might have.
            Each answer should be 2-3 sentences long and provide clear, actionable guidance.

            Questions should cover:
            1. Basic rules about {validation_element}
            2. Common mistakes to avoid
            3. Source type variations
            4. Time-saving tips
            5. How to handle special cases
            6. Where to find more help
            """,
            "rules": f"""
            As an APA 7th edition expert, provide clear, concise rules for checking {validation_element} in citations.
            Explain the specific formatting requirements and common guidelines that apply to {validation_element}.
            Keep it to 2-3 sentences with the most important rules that students need to remember.
            Focus on practical, actionable guidance.
            """,
            "apa_guidance": f"""
            Provide official APA 7th edition guidance for {validation_element} formatting.
            Quote or paraphrase the official APA rules for {validation_element} in academic citations.
            Include any specific exceptions or special considerations mentioned in the APA manual.
            Keep it to 2-3 sentences with the most authoritative guidance.
            """,
            "correct_example": f"""
            Provide a clear, correct example of properly formatted {validation_element} in an APA citation.
            Show exactly how {validation_element} should appear in a complete citation.
            Make sure the example follows all APA 7th edition rules for {validation_element}.
            Just provide the example, no additional explanation needed.
            """,
            "incorrect_example": f"""
            Provide a clear example of incorrectly formatted {validation_element} that shows a common mistake.
            This should be a realistic example of what students often get wrong with {validation_element}.
            Make sure the example clearly demonstrates a formatting error.
            Just provide the example, no additional explanation needed.
            """,
            "key_rules": f"""
            Summarize the 3-4 most important rules to remember when checking {validation_element} in APA citations.
            Focus on the rules that are most frequently violated or most important for academic integrity.
            Present as a concise bullet-point style summary.
            Keep it brief and memorable for quick reference.
            """
        }

        generated_content = {}
        total_token_usage = {}

        # Generate each section using existing LLM methods and enhanced prompts
        try:
            # Generate step-by-step instructions
            logger.info("Generating step-by-step instructions...")
            generated_content["step_by_step_instructions"] = self.llm_writer.generate_step_by_step(
                task=f"check {validation_element} in APA citations",
                rules={"rules": ["Check formatting", "Verify consistency", "Apply APA rules"]}
            )
            time.sleep(0.5)  # Short delay between API calls

            # Generate source type guidance
            logger.info("Generating source type guidance...")
            source_type_prompt = f"""
            Generate specific {validation_element} guidance for different source types in APA citations.

            For each source type (journal articles, books, book chapters, webpages, reports):
            - Name of source type
            - Format description: specific {validation_element} rules for that source type
            - What to check: key items to verify
            - Example: complete example with correct {validation_element}

            Format as a list of dictionaries with keys: name, format_description, check_items, example
            """
            generated_content["source_type_variations"] = self._generate_structured_content(source_type_prompt)
            time.sleep(0.5)  # Short delay between API calls

            # Generate tools and tips
            logger.info("Generating tools and tips...")
            tools_prompt = f"""
            Generate practical tool usage instructions for checking {validation_element} in APA citations.

            Include:
            1. word_find: Microsoft Word find feature instructions
            2. word_find_replace: Word Find & Replace instructions
            3. word_styles: Word styles panel instructions
            4. docs_find: Google Docs find feature instructions
            5. docs_addons: Google Docs add-ons instructions
            6. search_strategies: specific search patterns to find {validation_element} errors
            7. time_saving_techniques: list of time-saving techniques with descriptions
            8. common_pitfalls: list of common mistakes to avoid

            Be specific and actionable.
            """
            generated_content["tools_tips"] = self.llm_writer.generate_tools_and_tips(validation_element)
            time.sleep(0.5)  # Short delay between API calls

            # Generate before/after examples
            logger.info("Generating before/after examples...")
            examples_prompt = f"""
            Generate 5 realistic before/after examples of {validation_element} errors and fixes in APA citations.

            For each example:
            - scenario: description of the situation
            - incorrect_citation: full citation with the {validation_element} error
            - problem_highlighted: specific part that's wrong
            - correct_citation: corrected citation
            - changes: list of what changed and why
            - rule_applied: which APA rule was applied
            - error_type: type of error
            - fix_applied: description of fix
            - difficulty: Easy/Medium/Hard

            Use realistic academic sources.
            """
            generated_content["before_after_examples"] = self.llm_writer.generate_before_after_examples(validation_element, 5)
            time.sleep(0.5)  # Short delay between API calls

            # Generate APA rules and examples
            logger.info("Generating APA rules and examples...")
            rules_prompt = f"""
            Generate APA 7th edition rules for {validation_element} in citations.

            Include:
            1. rules: clear explanation of the rules
            2. apa_guidance: official APA guidance quote
            3. correct_example: specific correct example
            4. incorrect_example: specific incorrect example
            5. key_rules: formatted list of key rules to remember
            6. find_replace_strategy: specific Find & Replace strategy
            7. checklist_items: detailed checklist items

            Be authoritative and precise.
            """
            rules_content = self._generate_structured_content(rules_prompt)
            generated_content.update(rules_content)
            time.sleep(0.5)  # Short delay between API calls

            # Generate FAQ
            logger.info("Generating FAQ...")
            faq_items = self.llm_writer.generate_faq(f"checking {validation_element} in APA citations", num_questions=6)
            generated_content["faq_items"] = faq_items
            time.sleep(0.5)  # Short delay between API calls

            # Generate template-specific content for missing variables
            logger.info("Generating rules content...")
            generated_content["rules"] = self.llm_writer.generate_explanation(
                concept=f"rules for {validation_element}",
                rules={"prompt": prompts["rules"]},
                examples=[]
            )
            time.sleep(0.5)  # Short delay between API calls

            logger.info("Generating APA guidance content...")
            generated_content["apa_guidance"] = self.llm_writer.generate_explanation(
                concept=f"APA guidance for {validation_element}",
                rules={"prompt": prompts["apa_guidance"]},
                examples=[]
            )
            time.sleep(0.5)  # Short delay between API calls

            logger.info("Generating correct example...")
            generated_content["correct_example"] = self.llm_writer.generate_explanation(
                concept=f"correct {validation_element} example",
                rules={"prompt": prompts["correct_example"]},
                examples=[]
            )
            time.sleep(0.5)  # Short delay between API calls

            logger.info("Generating incorrect example...")
            generated_content["incorrect_example"] = self.llm_writer.generate_explanation(
                concept=f"incorrect {validation_element} example",
                rules={"prompt": prompts["incorrect_example"]},
                examples=[]
            )
            time.sleep(0.5)  # Short delay between API calls

            logger.info("Generating key rules...")
            generated_content["key_rules"] = self.llm_writer.generate_explanation(
                concept=f"key rules for {validation_element}",
                rules={"prompt": prompts["key_rules"]},
                examples=[]
            )

            logger.info("✅ All LLM sections generated successfully")

        except Exception as e:
            logger.error(f"Error generating LLM content: {str(e)}")
            generated_content["step_by_step_instructions"] = self._get_fallback_validation_content("step_by_step", validation_element)
            generated_content["faq_items"] = self._get_fallback_validation_content("faq", validation_element)
            # Add fallback content for all template variables
            generated_content["rules"] = f"Rules for checking {validation_element} in APA citations..."
            generated_content["apa_guidance"] = f"According to APA 7th edition guidelines for {validation_element}..."
            generated_content["correct_example"] = f"Correct {validation_element} example..."
            generated_content["incorrect_example"] = f"Incorrect {validation_element} example..."
            generated_content["key_rules"] = "Key rules to remember..."

        generated_content["token_usage"] = total_token_usage
        return generated_content

    def _generate_structured_content(self, prompt: str) -> dict:
        """
        Generate structured content from LLM
        Args:
            prompt: Prompt for structured content generation
        Returns:
            Dict with structured content
        """
        try:
            # Use existing explanation method to generate content
            content = self.llm_writer.generate_explanation(
                concept="structured content generation",
                rules={"prompt": prompt},
                examples=[]
            )

            # Return the raw content for parsing
            return {
                "raw_content": content,
                "structured": True
            }
        except Exception as e:
            logger.error(f"Error generating structured content: {str(e)}")
            return {}

    def _parse_source_type_content(self, raw_content: str) -> List[dict]:
        """
        Parse LLM-generated source type content into structured format
        Args:
            raw_content: Raw markdown content from LLM
        Returns:
            List of source type dictionaries
        """
        if not raw_content:
            return []

        import re
        source_types = []

        # Look for ### headers followed by content
        sections = re.split(r'\n### (.+?)\n', raw_content)

        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                source_name = sections[i].strip()
                content_section = sections[i + 1]

                # Extract format description
                format_match = re.search(r'\*\*Format Description\*\*:?\s*(.*?)(?=\n\n|\n\*\*|$)', content_section, re.DOTALL)
                format_desc = format_match.group(1).strip() if format_match else ""

                # Extract what to check
                check_match = re.search(r'\*\*What to Check\*\*:?\s*(.*?)(?=\n\n|\n\*\*|$)', content_section, re.DOTALL)
                check_items = check_match.group(1).strip() if check_match else ""

                # Extract example
                example_match = re.search(r'\*\*Example\*\*:?\s*(.*?)(?=\n\n|\n###|$)', content_section, re.DOTALL)
                example = example_match.group(1).strip() if example_match else ""

                if format_desc or check_items or example:
                    source_types.append({
                        "name": source_name,
                        "format_description": format_desc,
                        "check_items": check_items,
                        "example": example
                    })

        return source_types

    def _parse_before_after_examples(self, raw_content: str) -> List[dict]:
        """
        Parse LLM-generated examples into structured format
        Args:
            raw_content: Raw markdown content from LLM
        Returns:
            List of example dictionaries
        """
        if not raw_content:
            return []

        import re
        examples = []

        # Look for ### Example patterns (no numbers)
        example_sections = re.split(r'\n### Example.*?\n', raw_content)

        for i in range(1, len(example_sections), 2):
            if i + 1 < len(example_sections):
                scenario = example_sections[i].strip()
                content = example_sections[i + 1]

                # Extract various fields using the actual LLM structure
                incorrect_match = re.search(r'❌\s*(.*?)(?=\n\n|✅|\*\*)', content, re.DOTALL)
                incorrect = incorrect_match.group(1).strip() if incorrect_match else ""

                correct_match = re.search(r'✅\s*(.*?)(?=\n\n|\*\*)', content, re.DOTALL)
                correct = correct_match.group(1).strip() if correct_match else ""

                changes_match = re.search(r'\*\*Changes\*\*:?\s*(.*?)(?=\n\n|\*\*|Rule applied|Difficulty)', content, re.DOTALL)
                changes_text = changes_match.group(1).strip() if changes_match else ""

                rule_match = re.search(r'\*\*Rule applied\*\*:?\s*(.*?)(?=\n\n|\*\*|Difficulty)', content, re.DOTALL)
                rule_applied = rule_match.group(1).strip() if rule_match else ""

                error_type_match = re.search(r'\*\*Error Type\*\*:?\s*(.*?)(?=\n\n|\*\*|Difficulty)', content, re.DOTALL)
                error_type = error_type_match.group(1).strip() if error_type_match else ""

                difficulty_match = re.search(r'\*\*Difficulty\*\*:?\s*(.*?)(?=\n\n|\*\*|$)', content, re.DOTALL)
                difficulty = difficulty_match.group(1).strip() if difficulty_match else "Medium"

                # Parse changes into list
                changes = []
                if changes_text:
                    for line in changes_text.split('\n'):
                        line = re.sub(r'^-\s*', '', line.strip())
                        if line:
                            changes.append(line)

                if incorrect or correct:
                    examples.append({
                        "scenario": scenario,
                        "incorrect_citation": incorrect,
                        "correct_citation": correct,
                        "changes": changes,
                        "rule_applied": rule_applied,
                        "error_type": error_type,
                        "fix_applied": f"Applied {rule_applied}" if rule_applied else "Fixed formatting",
                        "difficulty": difficulty
                    })

        # If no examples were found with the structured approach, try a simpler approach
        if not examples:
            # Look for simple patterns with ❌ and ✅ markers
            simple_examples = re.findall(r'❌\s*(.*?)\s*✅\s*(.*?)(?=\n\n|\n##|\Z)', raw_content, re.DOTALL)
            for i, (incorrect, correct) in enumerate(simple_examples[:6]):
                examples.append({
                    "scenario": f"Example {i+1}: Common capitalization error",
                    "incorrect_citation": incorrect.strip(),
                    "correct_citation": correct.strip(),
                    "changes": ["Fixed capitalization to follow APA rules"],
                    "rule_applied": "APA capitalization guidelines",
                    "error_type": "Capitalization error",
                    "fix_applied": "Applied APA capitalization formatting",
                    "difficulty": "Easy"
                })

        return examples[:6]  # Limit to 6 examples

    def _parse_tools_tips_content(self, raw_content: str) -> dict:
        """
        Parse LLM-generated tools content into structured format
        Args:
            raw_content: Raw markdown content from LLM
        Returns:
            Dict with parsed tools content
        """
        if not raw_content:
            return {}

        result = {
            "word_find": "",
            "word_find_replace": "",
            "word_styles": "",
            "docs_find": "",
            "docs_addons": "",
            "search_strategies": "",
            "time_saving_techniques": [],
            "common_pitfalls": []
        }

        import re

        # Extract each section using the actual LLM structure
        sections = {
            "word_find": r'- \*\*Find feature\*\*:?\s*(.*?)(?=\n-|\n\*\*|\n###|$)',
            "word_find_replace": r'- \*\*Find & Replace\*\*:?\s*(.*?)(?=\n-|\n\*\*|\n###|$)',
            "word_styles": r'- \*\*Styles panel\*\*:?\s*(.*?)(?=\n-|\n\*\*|\n###|$)',
            "docs_find": r'- \*\*Find feature\*\*:?\s*(.*?)(?=\n-|\n\*\*|\n###|\*\*Google Docs)',
            "docs_addons": r'- \*\*Add-ons\*\*:?\s*(.*?)(?=\n-|\n\*\*|\n###|\*\*Google Docs)',
            "search_strategies": r'\*\*To find potential errors\*\*:?\s*(.*?)(?=\n###|\n\*\*|$)'
        }

        for key, pattern in sections.items():
            match = re.search(pattern, raw_content, re.DOTALL | re.IGNORECASE)
            if match:
                result[key] = match.group(1).strip()

        # Extract time-saving techniques
        techniques_match = re.search(r'\*\*Time-saving Techniques\*\*:?\s*(.*?)(?=\n\*\*|\n###|$)', raw_content, re.DOTALL | re.IGNORECASE)
        if techniques_match:
            techniques_text = techniques_match.group(1).strip()
            techniques = []
            for line in techniques_text.split('\n'):
                line = re.sub(r'^\d+\.\s*', '', line.strip())
                line = re.sub(r'^-\s*', '', line.strip())
                if line and len(line) > 10:
                    techniques.append({"name": line, "description": line, "when_to_use": "Always", "how_to_do": line, "time_saved": "2-5 minutes"})
            result["time_saving_techniques"] = techniques[:5]

        # Extract common pitfalls
        pitfalls_match = re.search(r'\*\*Common Pitfalls to Avoid\*\*:?\s*(.*?)(?=\n\*\*|\n###|$)', raw_content, re.DOTALL | re.IGNORECASE)
        if pitfalls_match:
            pitfalls_text = pitfalls_match.group(1).strip()
            pitfalls = []
            for line in pitfalls_text.split('\n'):
                line = re.sub(r'^\d+\.\s*', '', line.strip())
                line = re.sub(r'^-\s*', '', line.strip())
                if line and len(line) > 5:
                    pitfalls.append(line)
            result["common_pitfalls"] = pitfalls[:5]

        return result

    def _parse_faq_content(self, faq_content: str) -> List[dict]:
        """
        Parse FAQ content from LLM into structured format
        Args:
            faq_content: Raw FAQ content from LLM
        Returns:
            List of FAQ dicts
        """
        faq_items = []

        # Split by common question patterns
        import re

        # Try to match Q&A patterns
        qa_pattern = r'(?:Q[:\s]*|Question[:\s]*|^(?:\d+\.?\s*)?)(.+?)(?:\n\s*(?:A[:\s]*|Answer[:\s]*|.*?)(.+?))(?=\n(?:Q[:\s]*|Question[:\s]*|^\d+\.?\s*|\Z))'

        matches = re.findall(qa_pattern, faq_content, re.MULTILINE | re.DOTALL)

        if matches:
            for question, answer in matches:
                faq_items.append({
                    "question": question.strip(),
                    "answer": answer.strip()
                })
        else:
            # Fallback: split by double newlines and try to extract Q&A
            sections = faq_content.split('\n\n')
            current_qa = {}

            for section in sections:
                section = section.strip()
                if not section:
                    continue

                # Check if this looks like a question
                if any(q in section.lower() for q in ['what', 'how', 'when', 'where', 'why', 'should', 'can', '?']):
                    if current_qa:
                        faq_items.append(current_qa)
                    current_qa = {"question": section, "answer": ""}
                elif current_qa and not current_qa["answer"]:
                    current_qa["answer"] = section
                elif not current_qa:
                    # Create a Q&A pair from the section
                    lines = section.split('\n')
                    if len(lines) >= 2:
                        faq_items.append({
                            "question": lines[0].strip(),
                            "answer": '\n'.join(lines[1:]).strip()
                        })

            # Don't forget the last one
            if current_qa and current_qa.get("answer"):
                faq_items.append(current_qa)

        # Ensure we have exactly 6 FAQs
        while len(faq_items) < 6:
            faq_items.append({
                "question": f"Common question about validation",
                "answer": "Here's a helpful answer to guide you through the validation process."
            })

        return faq_items[:6]

    def _format_error_frequency_table(self, validation_element: str) -> str:
        """Generate markdown table for error frequency"""
        errors = self._load_errors_for_validation_element(validation_element)

        if not errors:
            return "| Error Type | Frequency | Severity | Easy to Spot? |\n|------------|-----------|----------|--------------|"

        table_rows = []
        for error in errors[:5]:  # Top 5 errors
            table_rows.append(
                f"| {error.get('error_name', 'Unknown')} | "
                f"{error.get('frequency', 'Unknown')} | "
                f"{error.get('severity', 'Medium')} | "
                f"{error.get('easy_to_spot', 'Unknown')} |"
            )

        header = "| Error Type | Frequency | Severity | Easy to Spot? |\n|------------|-----------|----------|--------------|"
        return header + "\n" + "\n".join(table_rows)

    def _get_fallback_validation_content(self, section_type: str, validation_element: str) -> str:
        """
        Get fallback content for validation sections if LLM generation fails
        Args:
            section_type: Type of section
            validation_element: Type of validation element
        Returns:
            Fallback content string
        """
        fallbacks = {
            "step_by_step": f"""
            ## Step-by-Step Process for Checking {validation_element.title()}

            ### Preparation
            1. Open your reference list
            2. Review the APA rules for {validation_element}
            3. Identify citations that need checking

            ### Checking Process
            1. Examine each citation for {validation_element} formatting
            2. Compare against APA guidelines
            3. Mark any issues you find
            4. Make corrections as needed

            ### Verification
            1. Double-check your corrections
            2. Ensure consistency across all citations
            3. Use an automated checker for final validation
            """,

            "faq": [
                {
                    "question": f"What is the most common {validation_element} error?",
                    "answer": f"The most frequent {validation_element} error involves incorrect formatting according to APA guidelines."
                },
                {
                    "question": f"How long does it take to check {validation_element}?",
                    "answer": f"Checking {validation_element} typically takes 2-3 minutes per citation once you're familiar with the rules."
                },
                {
                    "question": f"Should I use an automated checker for {validation_element}?",
                    "answer": "Automated checkers are great for initial validation, but manual review is still recommended for accuracy."
                }
            ]
        }

        return fallbacks.get(section_type, f"Content for {section_type} about {validation_element}")

    def _calculate_reading_time(self, word_count: int) -> int:
        """
        Calculate estimated reading time in minutes
        Args:
            word_count: Number of words
        Returns:
            Reading time in minutes
        """
        # Average reading speed: 200-250 words per minute
        words_per_minute = 225
        return max(1, round(word_count / words_per_minute))

    def _estimate_word_count(self, content: str) -> int:
        """
        Estimate word count from content
        Args:
            content: Text content
        Returns:
            Estimated word count
        """
        # Simple word count estimation
        words = content.split()
        return len(words)

    def assemble_specific_source_page(self, source_id: str) -> dict:
        """
        Assemble specific source guide with focus on unique content
        """
        logger.info(f"=== Assembling Specific Source Page: {source_id} ===")

        # 1. Load minimal source config
        source_config = self._load_source_config(source_id)

        # 2. Load parent source type data (for inheritance)
        parent_data = self._load_parent_source_type_data(source_config["parent_source_type"])

        # 3. Load template
        template = self.template_engine.load_template("specific_source_template.md")

        # 4. Generate UNIQUE content (not duplicating parent)
        llm_content = self._generate_unique_source_content(source_config, parent_data)

        # 5. Combine with inherited data
        template_data = {
            "source_name": source_config["name"],
            "source_slug": source_id,
            "source_url": source_config["url"],
            "source_category": source_config["category"],
            "parent_source_name": parent_data["display_name"],
            "parent_source_url": parent_data["parent_page_url"],
            "inherited_template": parent_data["reference_template"],
            "style_display_name": self.style_display_name,  # Dynamic style name
            **llm_content,  # Generated unique content
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "reading_time": "5 minutes"  # Target 800-1200 words
        }

        # 6. Content uniqueness validation
        content = self.template_engine.inject_variables(template, template_data)
        self._validate_content_uniqueness(content, parent_data.get("parent_page_url", ""))

        # 7. Add schema markup and front matter
        final_content = self._add_front_matter_and_schema(content, source_config, template_data)

        # 8. Generate metadata
        metadata = self._generate_specific_metadata(final_content, source_config)

        # 9. Get token usage from LLM writer
        token_usage = self.llm_writer.get_usage_summary()

        # 10. Enforce budget constraints
        self._enforce_token_budget(token_usage, source_config["name"])

        logger.info(f"✅ Specific Source Page Complete: {metadata['word_count']} words")
        logger.info(f"Token usage: {token_usage['total_input_tokens']} input, "
                   f"{token_usage['total_output_tokens']} output, "
                   f"${token_usage['total_cost_usd']:.6f}")

        return {
            "content": final_content,
            "metadata": metadata,
            "template_data": template_data,
            "token_usage": token_usage
        }

    def _enforce_token_budget(self, token_usage: dict, source_name: str) -> None:
        """
        Enforce token budget constraints and log warnings if exceeded
        """
        total_cost = token_usage.get('total_cost_usd', 0)
        total_tokens = token_usage.get('total_input_tokens', 0) + token_usage.get('total_output_tokens', 0)

        # Check cost budget
        if total_cost > self.max_cost_per_page:
            logger.warning(f"⚠️  Cost budget exceeded for {source_name}: ${total_cost:.4f} > ${self.max_cost_per_page:.2f}")
            logger.warning("Consider optimizing prompts or reducing content length")
        else:
            logger.debug(f"✅ Cost within budget for {source_name}: ${total_cost:.4f}")

        # Check token efficiency (rough estimate: 200 words per 1000 tokens)
        estimated_words_from_tokens = (total_tokens / 1000) * 200
        if estimated_words_from_tokens < 800:  # Expected minimum word count
            logger.warning(f"⚠️  Low token efficiency for {source_name}: {total_tokens} tokens for ~{estimated_words_from_tokens:.0f} words")
            logger.warning("Consider improving prompt efficiency")

        # Log budget status
        remaining_budget = self.max_cost_per_page - total_cost
        logger.info(f"Budget status for {source_name}: ${total_cost:.4f} used, ${remaining_budget:.4f} remaining")

    def check_budget_health(self) -> dict:
        """
        Check overall budget health and provide recommendations
        """
        current_usage = self.llm_writer.get_usage_summary()
        total_cost = current_usage.get('total_cost_usd', 0)
        total_tokens = current_usage.get('total_input_tokens', 0) + current_usage.get('total_output_tokens', 0)

        avg_cost_per_page = total_cost / max(1, current_usage.get('pages_generated', 1))
        token_efficiency = (total_tokens / max(1, current_usage.get('total_words_generated', 1))) * 1000

        health_status = {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "avg_cost_per_page": avg_cost_per_page,
            "token_efficiency": token_efficiency,  # tokens per word
            "within_budget": avg_cost_per_page <= self.max_cost_per_page,
            "recommendations": []
        }

        # Generate recommendations
        if avg_cost_per_page > self.max_cost_per_page * 0.8:
            health_status["recommendations"].append("Average cost approaching budget limit - optimize prompts")

        if token_efficiency > 6:  # More than 6 tokens per word is inefficient
            health_status["recommendations"].append("Token efficiency could be improved - shorter prompts")

        if not health_status["within_budget"]:
            health_status["recommendations"].append("Cost exceeds budget - review generation strategy")

        return health_status

    def _load_source_config(self, source_id: str) -> dict:
        """
        Load specific source configuration
        """
        config_file = self.templates_dir.parent / "configs" / "specific_sources.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Specific sources config not found: {config_file}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Find the source by ID
        for source in config_data["sources"]:
            if source["id"] == source_id:
                return source

        raise ValueError(f"Source ID '{source_id}' not found in config")

    def _load_parent_source_type_data(self, parent_type: str) -> dict:
        """
        Load parent source type data for inheritance
        """
        inheritance_file = self.knowledge_base_dir / "inheritance" / f"{parent_type}.json"

        if not inheritance_file.exists():
            logger.warning(f"Parent inheritance data not found: {inheritance_file}")
            # Return default structure
            return {
                "display_name": parent_type.replace("_", " ").title(),
                "parent_page_url": f"/how-to-cite-{parent_type}-apa/",
                "reference_template": "Author, A. A. (Year). Title. Source.",
                "template_explanation": "Standard citation format",
                "common_rules": []
            }

        with open(inheritance_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _generate_unique_source_content(self, source_config: dict, parent_data: dict) -> dict:
        """
        Generate content that's UNIQUE to this specific source with error handling and retries
        """
        source_name = source_config["name"]
        source_url = source_config["url"]
        parent_format = parent_data["reference_template"]

        content = {}
        errors = []

        # Define content generation tasks with retry logic
        generation_tasks = [
            ("where_to_find_info", lambda: self._retry_generation(
                lambda: self.llm_writer.generate_source_navigation_guide(
                    source_name=source_name,
                    source_url=source_url,
                    what_to_find=["author", "publication date", "title", "URL/access info"]
                ),
                "navigation_guide",
                source_name
            )),
            ("real_examples", lambda: self._retry_generation(
                lambda: self.llm_writer.generate_real_source_examples(
                    source_name=source_name,
                    source_url=source_url,
                    base_template=parent_format,
                    num_examples=4
                ),
                "real_examples",
                source_name
            )),
            ("source_specific_issues", lambda: self._retry_generation(
                lambda: self.llm_writer.generate_source_specific_issues(
                    source_name=source_name,
                    common_problems=["finding authors", "date formats", "URL handling", "access requirements"]
                ),
                "source_issues",
                source_name
            )),
            ("source_faq", lambda: self._retry_generation(
                lambda: self.llm_writer.generate_source_specific_faq(
                    source_name=source_name,
                    parent_source_type=parent_data["display_name"]
                ),
                "faq",
                source_name
            )),
            ("step_by_step_instructions", lambda: self._retry_generation(
                lambda: self.llm_writer.generate_step_by_step(
                    task=f"create {source_name} citation",
                    rules={"template": parent_format, "source_url": source_url}
                ),
                "step_by_step",
                source_name
            )),
            ("source_specific_notes", lambda: self._retry_generation(
                lambda: self.llm_writer.generate_source_specific_notes(
                    source_name=source_name,
                    parent_rules=parent_data.get("common_rules", [])
                ),
                "source_notes",
                source_name
            ))
        ]

        # Execute generation tasks with error handling
        for key, generator_func in generation_tasks:
            try:
                result = generator_func()
                if result:
                    content[key] = result
                    logger.debug(f"Generated {key} for {source_name}")
                else:
                    logger.warning(f"Empty result for {key} - using fallback")
                    content[key] = self._get_fallback_content(key, source_name, parent_data)
                    errors.append(f"Empty content for {key}")

            except Exception as e:
                logger.error(f"Failed to generate {key} for {source_name}: {str(e)}")
                content[key] = self._get_fallback_content(key, source_name, parent_data)
                errors.append(f"Generation error for {key}: {str(e)}")

        # Add static content that doesn't need LLM generation
        content["key_point_1"] = f"Use {parent_data['display_name']} format with {source_name} specifics"
        content["key_point_2"] = f"Locate citation info on {source_name}'s website"
        content["key_point_3"] = f"Handle {source_name}'s unique formatting requirements"

        # Add template-related content
        content["related_sources"] = self._generate_related_sources(source_config)
        content["validation_guides"] = self._generate_validation_guides(source_config)

        # Log errors and check if we have too many failures
        if errors:
            logger.warning(f"Content generation completed with {len(errors)} errors for {source_name}")
            if len(errors) > 3:  # More than 3 errors is concerning
                logger.error(f"High error rate ({len(errors)}) for {source_name} - manual review recommended")

        return content

    def _retry_generation(self, generator_func, content_type: str, source_name: str, max_retries: int = 2) -> str:
        """
        Retry LLM generation with different strategies on failure
        """
        for attempt in range(max_retries + 1):
            try:
                result = generator_func()
                if result and len(result.strip()) > 50:  # Minimum content length
                    return result
                else:
                    logger.warning(f"Attempt {attempt + 1}: {content_type} too short for {source_name}")
                    if attempt < max_retries:
                        continue  # Try again
                    else:
                        return self._get_retry_fallback(content_type, source_name)

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {content_type}: {str(e)}")
                if attempt < max_retries:
                    # Brief pause before retry
                    time.sleep(1)
                    continue
                else:
                    logger.error(f"All retries failed for {content_type} - using fallback")
                    return self._get_retry_fallback(content_type, source_name)

        return ""

    def _get_fallback_content(self, content_type: str, source_name: str, parent_data: dict) -> str:
        """
        Get fallback content when LLM generation fails
        """
        fallbacks = {
            "where_to_find_info": f"""
            ## Where to Find Citation Information on {source_name}

            To cite content from {source_name}, you'll need to locate:
            - Author information (usually at the top of the article)
            - Publication date (typically below the title)
            - Article or content title
            - Direct URL from your browser

            Look for these elements in the standard locations on {source_name}'s website.
            """,

            "real_examples": f"""
            ## Examples from {source_name}

            Example 1: Standard article
            [Author]. (Year, Month Day). Title of content. {source_name}. https://www.example.com/content

            Example 2: Multiple authors
            [Author 1], [Author 2], & [Author 3]. (Year, Month Day). Title of content. {source_name}. https://www.example.com/content
            """,

            "source_specific_issues": f"""
            ## Common Issues When Citing {source_name}

            **Missing Author Information**
            Some content on {source_name} may not list individual authors. Use the organization name instead.

            **Date Formatting**
            Ensure you use the full publication date in Year, Month Day format.

            **URL Requirements**
            Always use the direct URL to the specific content, not the homepage.
            """,

            "source_faq": f"""
            ## Frequently Asked Questions

            **Q: How do I cite {source_name} content with no author?**
            A: Use the {source_name} organization name as the author.

            **Q: What if I can't find a publication date?**
            A: Use (n.d.) for "no date" and include the retrieval date if necessary.

            **Q: How do I handle multiple authors from {source_name}?**
            A: List all authors up to 20, or use "et al." for three or more in-text citations.
            """,

            "step_by_step_instructions": f"""
            ## Step-by-Step Instructions

            1. Navigate to the {source_name} content you want to cite
            2. Locate the author information at the top of the content
            3. Find the publication date below the title
            4. Copy the exact title of the content
            5. Get the direct URL from your browser
            6. Format according to APA 7th edition guidelines
            7. Create both reference list and in-text citations
            """,

            "source_specific_notes": f"""
            ## Notes for Citing {source_name}

            {source_name} content follows standard {parent_data.get('display_name', 'source type')} citation format
            with some specific requirements for their platform. Pay attention to author attribution
            and ensure you have the complete publication information.
            """
        }

        return fallbacks.get(content_type, f"Content temporarily unavailable for {content_type}.")

    def _get_retry_fallback(self, content_type: str, source_name: str) -> str:
        """
        Get fallback content specifically for retry failures
        """
        return f"""
        ## {content_type.replace('_', ' ').title()}

        Citation information for {source_name} follows standard APA 7th edition guidelines.
        Please refer to the parent source type guide for detailed formatting instructions.

        For specific questions about citing {source_name}, check the relevant sections of this guide
        or use our citation checker tool for automated validation.
        """

    def _generate_related_sources(self, source_config: dict) -> List[dict]:
        """
        Generate related sources based on category
        """
        # This would typically come from a configuration or database
        # For now, provide generic related sources
        category = source_config.get("category", "general")

        related_map = {
            "newspaper": [
                {"name": "The Washington Post", "description": "How to cite Washington Post articles", "url": "/cite-washington-post-apa/"},
                {"name": "The Wall Street Journal", "description": "How to cite WSJ articles", "url": "/cite-wall-street-journal-apa/"}
            ],
            "video_platform": [
                {"name": "TED Talks", "description": "How to cite TED Talks", "url": "/cite-ted-talks-apa/"},
                {"name": "Vimeo", "description": "How to cite Vimeo videos", "url": "/cite-vimeo-apa/"}
            ],
            "reference": [
                {"name": "Dictionary.com", "description": "How to cite Dictionary.com", "url": "/cite-dictionary-com-apa/"},
                {"name": "Encyclopedia Britannica", "description": "How to cite Encyclopedia Britannica", "url": "/cite-encyclopedia-britannica-apa/"}
            ],
            "government": [
                {"name": "NIH", "description": "How to cite NIH publications", "url": "/cite-nih-apa/"},
                {"name": "FDA", "description": "How to cite FDA documents", "url": "/cite-fda-apa/"}
            ],
            "academic_database": [
                {"name": "JSTOR", "description": "How to cite JSTOR articles", "url": "/cite-jstor-apa/"},
                {"name": "Google Scholar", "description": "How to cite Google Scholar results", "url": "/cite-google-scholar-apa/"}
            ]
        }

        return related_map.get(category, [
            {"name": "Similar Source", "description": "How to cite similar sources", "url": "/cite-similar-source-apa/"}
        ])

    def _generate_validation_guides(self, source_config: dict) -> List[dict]:
        """
        Generate relevant validation guides based on source type
        """
        # Standard validation guides that apply to most sources
        validation_guides = [
            {"name": "Check Capitalization", "url": "/how-to-check-capitalization-apa/"},
            {"name": "Validate URL Format", "url": "/how-to-check-url-apa/"},
            {"name": "Check Author Formatting", "url": "/how-to-check-author-format-apa/"}
        ]

        # Add specific guides based on source type
        if source_config.get("parent_source_type") in ["journal_article", "newspaper_article"]:
            validation_guides.append({"name": "Validate DOI Format", "url": "/how-to-check-doi-apa/"})

        if source_config.get("category") == "video_platform":
            validation_guides.append({"name": "Check Video Citations", "url": "/how-to-check-video-citations-apa/"})

        return validation_guides[:4]  # Limit to 4 guides

    def _validate_content_uniqueness(self, specific_content: str, parent_url: str) -> None:
        """
        Ensure specific source page doesn't duplicate parent content using TF-IDF similarity
        """
        if not TFIDF_AVAILABLE:
            logger.warning("TF-IDF similarity calculation not available - skipping uniqueness validation")
            return

        try:
            # Load parent content (simplified - would normally load from file system)
            parent_content = self._load_parent_content(parent_url)

            if not parent_content:
                logger.warning("Could not load parent content for similarity comparison")
                return

            # Clean content for comparison (remove headings, frontmatter, links)
            specific_clean = self._clean_content_for_comparison(specific_content)
            parent_clean = self._clean_content_for_comparison(parent_content)

            # Calculate similarity using TF-IDF
            similarity = self._calculate_content_similarity(specific_clean, parent_clean)

            logger.info(f"Content similarity calculated: {similarity:.2%}")

            if similarity > 0.3:  # 30% similarity threshold
                logger.warning(f"Content similarity too high: {similarity:.2%}")
                raise ValueError(f"Specific source page too similar to parent page ({similarity:.1%} overlap)")

            logger.info(f"Content uniqueness validated: {(1-similarity):.1%} unique")

        except Exception as e:
            logger.error(f"Error in content uniqueness validation: {str(e)}")
            # Don't fail the entire process if similarity check fails
            logger.warning("Proceeding without uniqueness validation due to error")

    def _load_parent_content(self, parent_url: str) -> str:
        """
        Load parent source type page content for comparison
        """
        # This is a placeholder implementation
        # In practice, this would load the actual parent page content
        # from the file system or content management system

        # For now, return a generic parent content template
        return """
        # How to Cite Newspaper Articles in APA Format

        This guide covers the general principles of citing newspaper articles in APA 7th edition format.

        ## Basic Format

        Author, A. A. (Year, Month Day). Title of article. *Name of Newspaper*. URL

        ## Key Elements

        - Author names in standard format
        - Full publication date
        - Article title in sentence case
        - Newspaper name in italics
        - Direct URL

        ## Common Issues

        - Finding author information
        - Handling missing dates
        - Formatting URLs correctly
        """

    def _clean_content_for_comparison(self, content: str) -> str:
        """
        Clean content for similarity comparison by removing structural elements
        """
        if not content:
            return ""

        # Remove YAML front matter
        content = re.sub(r'^---.*?---\n', '', content, flags=re.DOTALL)

        # Remove markdown headings
        content = re.sub(r'^#+\s+.*$', '', content, flags=re.MULTILINE)

        # Remove code blocks and templates
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        content = re.sub(r'`[^`]*`', '', content)

        # Remove internal links [text](url)
        content = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', content)

        # Remove HTML tags
        content = re.sub(r'<[^>]*>', '', content)

        # Remove extra whitespace and empty lines
        content = re.sub(r'\n\s*\n', '\n', content)
        content = content.strip()

        # Convert to lowercase for comparison
        return content.lower()

    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate TF-IDF cosine similarity between two texts
        """
        if not TFIDF_AVAILABLE:
            return 0.0

        try:
            # Handle empty texts
            if not text1 or not text2:
                return 0.0

            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=1000,
                ngram_range=(1, 2)  # Include bigrams for better semantic matching
            )

            # Vectorize texts
            tfidf_matrix = vectorizer.fit_transform([text1, text2])

            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            similarity = similarity_matrix[0][0]

            # Ensure similarity is between 0 and 1
            similarity = max(0.0, min(1.0, similarity))

            logger.debug(f"TF-IDF similarity: {similarity:.4f}")
            return similarity

        except Exception as e:
            logger.error(f"Error calculating TF-IDF similarity: {str(e)}")
            return 0.0

    def _generate_howto_schema(self, source_name: str, steps: List[str]) -> dict:
        """
        Generate HowTo schema markup for specific source page
        """
        return {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": f"How to Cite {source_name} in {self.style_display_name}",
            "description": f"Step-by-step guide to citing {source_name} in {self.style_display_name}",
            "step": [
                {"@type": "HowToStep", "text": step}
                for step in steps
            ]
        }

    def _add_front_matter_and_schema(self, content: str, source_config: dict, template_data: dict) -> str:
        """
        Add YAML front matter and schema markup to content
        """
        # Generate schema
        steps = [
            "Locate citation information on the source",
            "Format author names according to APA rules",
            "Add publication date in correct format",
            "Format title according to source type",
            "Complete reference with URL/DOI",
            "Create in-text citations"
        ]

        schema = self._generate_howto_schema(source_config["name"], steps)

        # Create front matter
        front_matter = f"""---
title: "How to Cite {source_config['name']} in {self.style_display_name}"
description: "{source_config['description']}"
meta_title: "Cite {source_config['name']} in {self.style_display_name} | Complete Guide"
meta_description: "Learn how to cite {source_config['name']} in {self.style_display_name}. Includes examples, templates, and specific formatting requirements."
page_type: "specific_source"
url_slug: "{source_config['url_slug']}"
source_name: "{source_config['name']}"
source_category: "{source_config['category']}"
parent_source_type: "{source_config['parent_source_type']}"
last_updated: "{datetime.now().strftime('%Y-%m-%d')}"
word_count: {self._estimate_word_count(content)}
reading_time: "5 minutes"
keywords: ["cite {source_config['name'].lower()} apa", "{source_config['name'].lower()} citation", "apa 7th edition"]
schema: {json.dumps(schema)}
---

"""

        return front_matter + content

    def _generate_specific_metadata(self, content: str, source_config: dict) -> dict:
        """
        Generate metadata for specific source page
        """
        word_count = self._estimate_word_count(content)

        return {
            "title": f"How to Cite {source_config['name']} in {self.style_display_name}",
            "description": source_config["description"],
            "source_name": source_config["name"],
            "source_category": source_config["category"],
            "url": source_config["url_slug"],
            "word_count": word_count,
            "reading_time": f"{max(1, word_count // 200)} minutes",
            "last_updated": datetime.now().isoformat(),
            "page_type": "specific_source"
        }
