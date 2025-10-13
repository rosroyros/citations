from jinja2 import Environment, FileSystemLoader, Template
import json
from pathlib import Path
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemplateEngine:
    """Template engine for generating PSEO content using Jinja2 templates."""

    def __init__(self, templates_dir: str):
        """Initialize template engine with templates directory."""
        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            raise ValueError(f"Templates directory does not exist: {templates_dir}")

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        logger.info(f"Template engine initialized with templates dir: {templates_dir}")

    def load_template(self, template_name: str) -> Template:
        """Load a Jinja2 template by name."""
        try:
            template = self.env.get_template(template_name)
            logger.info(f"Loaded template: {template_name}")
            return template
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            raise

    def load_structured_data(self, data_type: str, filters: Dict = None) -> Dict:
        """Load data from knowledge base JSON files."""
        file_path = Path(f"backend/pseo/knowledge_base/{data_type}.json")

        if not file_path.exists():
            logger.warning(f"Data file does not exist: {file_path}")
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if filters:
                data = self._filter_data(data, filters)

            logger.info(f"Loaded {data_type} data: {len(data) if isinstance(data, list) else 'dict'} items")
            return data

        except Exception as e:
            logger.error(f"Failed to load data from {file_path}: {e}")
            raise

    def inject_variables(self, template: Template, data: Dict) -> str:
        """Inject variables into template and render."""
        try:
            rendered = template.render(**data)
            logger.info(f"Template rendered successfully, length: {len(rendered)} chars")
            return rendered
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise

    def validate_output(self, content: str, min_words: int = 800) -> bool:
        """Basic validation of generated content."""
        word_count = len(content.split())
        is_valid = word_count >= min_words

        if not is_valid:
            logger.warning(f"Content validation failed: {word_count} words < {min_words} minimum")
        else:
            logger.info(f"Content validation passed: {word_count} words")

        return is_valid

    def save_markdown(self, content: str, filepath: str) -> None:
        """Save content to markdown file."""
        try:
            output_path = Path(filepath)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Content saved to: {filepath}")

        except Exception as e:
            logger.error(f"Failed to save content to {filepath}: {e}")
            raise

    def _filter_data(self, data: Any, filters: Dict) -> Any:
        """Apply filters to data based on filter criteria."""
        if not isinstance(data, list):
            return data

        filtered = data
        for key, value in filters.items():
            if isinstance(filtered, list) and filtered and isinstance(filtered[0], dict):
                filtered = [item for item in filtered if item.get(key) == value]

        return filtered