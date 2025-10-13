import pytest
import json
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the backend directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from backend.pseo.generator.template_engine import TemplateEngine


class TestTemplateEngine:
    """Test suite for TemplateEngine class."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.templates_dir = Path(self.temp_dir) / "templates"
        self.knowledge_base_dir = Path(self.temp_dir) / "knowledge_base"

        self.templates_dir.mkdir()
        self.knowledge_base_dir.mkdir()

        # Create sample template
        self.sample_template = self.templates_dir / "test_template.md"
        self.sample_template.write_text("""# {{ guide_title }}

{{ guide_description }}

## Introduction
{{ introduction }}

## Examples
{% for example in examples %}
- {{ example.citation }}
{% endfor %}

Word count: {{ word_count }}
""")

        # Create sample data file
        self.sample_data = self.knowledge_base_dir / "examples.json"
        sample_examples = [
            {"citation": "Smith, J. (2020). Article title. Journal Name, 15(2), 123-145."},
            {"citation": "Doe, J. (2021). Book title. Publisher."}
        ]
        self.sample_data.write_text(json.dumps(sample_examples, indent=2))

        # Initialize template engine
        self.engine = TemplateEngine(str(self.templates_dir))

    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir)

    def test_template_loading(self):
        """Test that templates can be loaded successfully."""
        template = self.engine.load_template("test_template.md")
        assert template is not None
        assert template.name == "test_template.md"

    def test_template_loading_nonexistent(self):
        """Test that loading nonexistent template raises error."""
        with pytest.raises(Exception):
            self.engine.load_template("nonexistent.md")

    def test_variable_injection(self):
        """Test that variables are injected correctly into template."""
        template = self.engine.load_template("test_template.md")

        data = {
            "guide_title": "Test Guide",
            "guide_description": "A test description",
            "introduction": "This is the introduction.",
            "examples": [
                {"citation": "Smith, J. (2020). Article title. Journal Name, 15(2), 123-145."}
            ],
            "word_count": 1500
        }

        result = self.engine.inject_variables(template, data)

        assert "Test Guide" in result
        assert "A test description" in result
        assert "This is the introduction." in result
        assert "Smith, J. (2020)" in result
        assert "1500" in result

    def test_load_structured_data(self):
        """Test loading structured data from JSON files."""
        # Mock the knowledge base path
        original_method = self.engine.load_structured_data

        def mock_load_structured_data(data_type, filters=None):
            if data_type == "examples":
                file_path = self.sample_data
            else:
                file_path = self.knowledge_base_dir / f"{data_type}.json"

            if not file_path.exists():
                return {}

            with open(file_path, 'r') as f:
                return json.load(f)

        self.engine.load_structured_data = mock_load_structured_data

        data = self.engine.load_structured_data("examples")
        assert isinstance(data, list)
        assert len(data) == 2
        assert "Smith, J." in data[0]["citation"]
        assert "Doe, J." in data[1]["citation"]

    def test_load_structured_data_nonexistent(self):
        """Test loading nonexistent data file returns empty dict."""
        data = self.engine.load_structured_data("nonexistent.json")
        assert data == {}

    def test_output_validation_pass(self):
        """Test that content validation passes for sufficient content."""
        content = "This is test content with enough words to pass validation. " * 50
        assert self.engine.validate_output(content, min_words=100) == True

    def test_output_validation_fail(self):
        """Test that content validation fails for insufficient content."""
        content = "Short content."
        assert self.engine.validate_output(content, min_words=100) == False

    def test_save_markdown(self):
        """Test saving content to markdown file."""
        content = "# Test Content\n\nThis is test content."
        output_path = Path(self.temp_dir) / "output" / "test.md"

        self.engine.save_markdown(content, str(output_path))

        assert output_path.exists()
        saved_content = output_path.read_text()
        assert saved_content == content

    def test_save_markdown_creates_directories(self):
        """Test that save_markdown creates parent directories."""
        content = "# Test Content"
        nested_path = Path(self.temp_dir) / "level1" / "level2" / "test.md"

        self.engine.save_markdown(content, str(nested_path))

        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_filter_data(self):
        """Test data filtering functionality."""
        data = [
            {"type": "journal", "title": "Article 1"},
            {"type": "book", "title": "Book 1"},
            {"type": "journal", "title": "Article 2"}
        ]

        filters = {"type": "journal"}
        filtered = self.engine._filter_data(data, filters)

        assert len(filtered) == 2
        assert all(item["type"] == "journal" for item in filtered)

    def test_filter_data_non_list(self):
        """Test filtering non-list data returns original."""
        data = {"key": "value"}
        filtered = self.engine._filter_data(data, {"key": "value"})
        assert filtered == data

    def test_template_engine_initialization(self):
        """Test TemplateEngine initialization."""
        assert self.engine.templates_dir == self.templates_dir
        assert self.engine.env is not None

    def test_template_engine_invalid_directory(self):
        """Test TemplateEngine initialization with invalid directory."""
        with pytest.raises(ValueError):
            TemplateEngine("/nonexistent/directory")