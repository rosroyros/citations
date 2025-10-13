"""
Tests for ContentAssembler

Integration tests for the content assembly system that combines
templates, LLM generation, and structured knowledge base data.
"""
import pytest
import json
from pathlib import Path
from backend.pseo.generator.content_assembler import ContentAssembler


@pytest.fixture
def assembler():
    """Create ContentAssembler instance with real paths"""
    knowledge_base_dir = "backend/pseo/knowledge_base"
    templates_dir = "backend/pseo/templates"
    return ContentAssembler(knowledge_base_dir, templates_dir)


def test_assembler_initialization(assembler):
    """Test ContentAssembler initializes correctly"""
    assert assembler.knowledge_base_dir.exists()
    assert assembler.templates_dir.exists()
    assert assembler.template_engine is not None
    assert assembler.llm_writer is not None


def test_assemble_mega_guide(assembler):
    """Test assembling a complete mega guide"""
    config = {
        "title": "Test Guide: Checking APA Citations",
        "description": "Learn how to validate APA citations",
        "keywords": ["check APA citations", "APA validation"],
        "pain_points": ["90.9% of papers have citation errors"]
    }

    result = assembler.assemble_mega_guide("checking APA citations", config)

    # Check result structure
    assert "content" in result
    assert "metadata" in result
    assert "template_data" in result

    # Check content quality
    content = result["content"]
    assert len(content) > 0
    assert "# Test Guide: Checking APA Citations" in content or "Test Guide: Checking APA Citations" in content

    # Check metadata
    metadata = result["metadata"]
    assert "word_count" in metadata
    assert "reading_time" in metadata
    assert "last_updated" in metadata
    assert metadata["word_count"] >= 5000  # Mega guide minimum


def test_assemble_source_type_page(assembler):
    """Test assembling a source type page"""
    config = {
        "title": "How to Cite a Journal Article in APA",
        "description": "Complete guide to APA journal citations",
        "keywords": ["cite journal article", "APA journal citation"]
    }

    result = assembler.assemble_source_type_page("journal article", config)

    # Check result structure
    assert "content" in result
    assert "metadata" in result
    assert "template_data" in result

    # Check content quality
    content = result["content"]
    assert len(content) > 0

    # Check metadata
    metadata = result["metadata"]
    assert metadata["word_count"] >= 2000  # Source type minimum


def test_load_relevant_rules(assembler):
    """Test loading and filtering rules by topic"""
    rules = assembler._load_relevant_rules("author formatting")

    assert isinstance(rules, list)
    assert len(rules) > 0
    # Should contain rules related to authors
    assert any("author" in str(rule).lower() for rule in rules)


def test_load_examples(assembler):
    """Test loading citation examples"""
    examples = assembler._load_examples("journal article")

    assert isinstance(examples, list)
    assert len(examples) > 0
    assert len(examples) <= 10  # Should limit to 10


def test_load_errors(assembler):
    """Test loading common errors"""
    errors = assembler._load_errors("capitalization")

    assert isinstance(errors, list)
    assert len(errors) >= 0  # May be empty for some topics


def test_generate_metadata(assembler):
    """Test metadata generation"""
    test_content = " ".join(["word"] * 5000)  # 5000 words
    config = {
        "title": "Test Title",
        "description": "Test description"
    }

    metadata = assembler._generate_metadata(test_content, config)

    assert metadata["meta_title"] == "Test Title"
    assert metadata["meta_description"] == "Test description"
    assert metadata["word_count"] == 5000
    assert "25 minute" in metadata["reading_time"]  # 5000 words / 200 wpm = 25 min
    assert "last_updated" in metadata


def test_generate_checklist(assembler):
    """Test validation checklist generation"""
    rules = [
        {"rule_id": "test1", "description": "Test rule 1"},
        {"rule_id": "test2", "description": "Test rule 2"}
    ]

    checklist = assembler._generate_checklist(rules)

    assert isinstance(checklist, list)
    assert len(checklist) >= len(rules)


def test_mega_guide_word_count_validation(assembler):
    """Test that mega guide validates minimum word count"""
    # This will generate real content and check if it meets minimum
    config = {
        "title": "Test Guide",
        "description": "Test description",
        "keywords": ["test"],
        "pain_points": ["testing"]
    }

    result = assembler.assemble_mega_guide("APA citations", config)

    # Should have at least 5000 words
    assert result["metadata"]["word_count"] >= 5000


def test_source_type_word_count_validation(assembler):
    """Test that source type page validates minimum word count"""
    config = {
        "title": "Test Source Type",
        "description": "Test description",
        "keywords": ["test"]
    }

    result = assembler.assemble_source_type_page("journal article", config)

    # Should have at least 2000 words
    assert result["metadata"]["word_count"] >= 2000


def test_reading_time_calculation(assembler):
    """Test reading time is calculated correctly"""
    # 200 words = 1 minute
    # 400 words = 2 minutes
    # 5000 words = 25 minutes

    test_cases = [
        (" ".join(["word"] * 200), "1 minute"),
        (" ".join(["word"] * 400), "2 minutes"),
        (" ".join(["word"] * 5000), "25 minutes")
    ]

    config = {"title": "Test", "description": "Test"}

    for content, expected in test_cases:
        metadata = assembler._generate_metadata(content, config)
        assert expected in metadata["reading_time"]


def test_assemble_with_missing_config_keys(assembler):
    """Test assembler handles missing config keys gracefully"""
    minimal_config = {
        "title": "Minimal Test"
        # Missing description, keywords, etc.
    }

    # Should not crash, should use defaults
    result = assembler.assemble_mega_guide("test topic", minimal_config)

    assert "content" in result
    assert "metadata" in result


def test_load_source_type_data(assembler):
    """Test loading source type specific data"""
    data = assembler._load_source_type_data("journal article")

    assert isinstance(data, dict)
    assert "rules" in data or len(data) > 0


def test_load_examples_for_source_type(assembler):
    """Test loading examples filtered by source type"""
    examples = assembler._load_examples_for_source_type("journal article")

    assert isinstance(examples, list)
    # Should contain journal article examples
    if len(examples) > 0:
        assert any("journal" in str(ex).lower() for ex in examples[:5])
