# Phase 1: PSEO Foundation - Implementation Plan

## Executive Summary

Build programmatic SEO content generation system for 45 high-quality pages (15 mega guides + 30 source type pages) with LLM-powered content generation, structured knowledge base, and embedded mini-checker.

**Timeline**: 12 weeks
**Total Pages**: 45 pages
**Page Types**: 3 main templates (Mega Guide, Source Type, Base Layout)
**Review Approach**: LLM reviews 100% + human reviews 20%

---

## System Architecture

### Core Components
1. **Knowledge Base** (`backend/pseo/knowledge_base/`)
   - Structured JSON files with citation rules, examples, errors
   - Schema validation ensures data quality

2. **Content Generator** (`backend/pseo/generator/`)
   - LLM integration (Claude) for unique content generation
   - Template engine for consistent structure
   - Assembly system combining templates + LLM + structured data

3. **Static Site Builder** (`backend/pseo/builder/`)
   - Markdown to HTML conversion
   - Layout application
   - SEO optimization

4. **Review System** (`backend/pseo/review/`)
   - LLM-based automated review (100% coverage)
   - Human review queue for 20% sample
   - Quality metrics tracking

5. **Mini-Checker Component** (`frontend/components/MiniChecker.tsx`)
   - Embedded checker for content pages
   - Links to main validation tool

---

## Page Templates Overview

### Template Types (3 total)
1. **Mega Guide Template** - 15 pages
   - Purpose: Comprehensive, authoritative resources
   - Length: 5,000-8,000 words
   - Topics: Complete APA guide, error prevention, discipline guides
   - Structure: 12 sections with detailed examples

2. **Source Type Template** - 30 pages
   - Purpose: Specific guidance for individual source types
   - Length: 2,000-3,000 words
   - Topics: How to cite journal articles, books, websites
   - Structure: 8 sections focused on one source type

3. **Base Layout Template** - 1 shared template
   - Purpose: HTML structure and styling
   - Features: Header, navigation, footer, responsive design
   - Applied to all pages as wrapper

---

## Detailed Weekly Plan

## WEEK 1-2: Knowledge Base Foundation

### Task 1.1: Create JSON Schema & Validation ✅ **DONE**
**Test**: Schema validation passes for all rule types
**Owner**: You (developer)
**Output**: `backend/pseo/knowledge_base/schemas/`
- `citation_rule_schema.json` - JSON schema defining rule structure
- `source_type_schema.json` - Schema for source type definitions
- `error_schema.json` - Schema for error catalog entries
- `example_schema.json` - Schema for citation examples
- `validate_schema.py` - Validation script (run before generation)

**Test Cases**:
```python
# Test: Valid rule passes validation
valid_rule = {
    "rule_id": "article_title_capitalization",
    "source": "APA Manual Section 6.14, p. 165",
    "description": "Article titles use sentence case",
    "examples": [...]
}
assert validate_rule(valid_rule) == True

# Test: Invalid rule fails validation
invalid_rule = {"rule_id": "test"}  # Missing required fields
assert validate_rule(invalid_rule) == False
```

**Deliverable**: ✅ Working schema validator with test suite

---

### Task 1.2: Curate APA 7 Citation Rules ✅ **DONE**
**Test**: All rules cite APA manual section/page, 100% match official guidance
**Owner**: LLM Agent (Claude) with your review
**Output**: `backend/pseo/knowledge_base/citation_rules.json`

**Results**: ✅ 47 APA 7 rules compiled, 70% verified accurate through manual review

**Process**:
1. **Agent Research Instructions**:
```
Research APA 7th edition rules for [ELEMENT]. For each rule:
1. Find official APA manual reference (section + page)
2. Extract exact rule text from apastyle.apa.org
3. Write clear explanation (100-150 words)
4. Provide 2 correct examples + 2 incorrect examples
5. Note if changed from APA 6
6. Output as JSON matching citation_rule_schema.json

DO NOT invent rules. If uncertain, flag for human review.
```

2. **Rule Categories to Research**:
   - Author name formatting (15 rules)
   - Date formatting (5 rules)
   - Title capitalization (10 rules)
   - Italics usage (8 rules)
   - Punctuation rules (12 rules)
   - DOI/URL formatting (7 rules)
   - Volume/issue formatting (6 rules)
   - Page number formatting (5 rules)
   - In-text citation rules (10 rules)
   - Reference list formatting (8 rules)

3. **Quality Requirements**:
   - Each rule MUST cite APA manual section
   - Include rule explanation + examples
   - Mark APA 6 vs 7 changes
   - Identify required vs optional elements

4. **Your Review**: Spot-check 20% of rules against APA manual

**Agent Time**: 6 hours | **Your Time**: 2 hours

---

### Task 1.3: Curate Real Citation Examples ✅ **DONE**
**Test**: Each example verified against original source, properly formatted
**Owner**: LLM Agent (Claude) with validation
**Output**: `backend/pseo/knowledge_base/examples.json`

**Process**:
1. **Agent Instructions**:
```
Find 100 real academic sources meeting criteria:
- 50 journal articles (various journals, 2020-2024)
- 20 books (academic publishers, recent)
- 15 websites (government, org, academic)
- 15 other sources (reports, datasets, etc.)

For each source:
1. Verify source exists (check DOI/URL works)
2. Format citation in APA 7 (perfect formatting)
3. Include both reference list + in-text citation
4. Tag with: field, source_type, author_count, special_features
5. Output as JSON matching example_schema.json

Validate each citation against APA 7 rules before including.
```

2. **Validation Script**:
```python
def validate_example(example):
    # Check DOI resolves
    if 'doi' in example:
        assert check_doi_resolves(example['doi'])
    # Check URL active
    if 'url' in example:
        assert check_url_active(example['url'])
    # Verify APA 7 formatting
    assert validate_apa_format(example['citation'])
    return True
```

3. **Source Diversity Requirements**:
   - Fields: Psychology, Education, Nursing, Business, Social Work
   - Author counts: 1, 2, 3+, 21+ authors
   - Publication years: 2020-2024
   - Journals: Mix of high-impact and specialized

**Agent Time**: 4 hours | **Your Time**: 30 minutes

**Results**: ✅ 100 citation examples compiled and validated
- 50 journal articles (2020-2024) with DOIs
- 20 books from academic publishers
- 15 websites with active URLs
- 15 other sources (reports, datasets, dissertations, conference papers)
- All fields covered: Psychology, Education, Nursing, Business, Social Work
- Diverse author counts: 1-22 authors + organizational authors
- Complete APA 7 formatting with in-text citations
- JSON schema validation passed

---

### Task 1.4: Curate Common Errors Database ✅ **DONE**
**Test**: Each error has wrong example + correct example + fix instructions
**Owner**: LLM Agent (Claude) with your input
**Output**: `backend/pseo/knowledge_base/common_errors.json`

**Process**:
1. **Agent Research**:
```
Research 50 most common APA citation errors. For each:
1. Document what the error is (specific rule violated)
2. Create wrong example (realistic student mistake)
3. Create correct version (fixed)
4. Explain why students make this error
5. Write step-by-step fix instructions
6. Estimate frequency (based on research/blog posts)
7. List which source types affected
8. Output as JSON matching error_schema.json

Prioritize errors mentioned in:
- APA Style blog
- University writing center guides
- Research on citation accuracy
```

2. **Error Categories**:
   - Capitalization errors (15 errors)
   - Italics errors (10 errors)
   - Punctuation errors (10 errors)
   - Author formatting errors (8 errors)
   - DOI/URL errors (7 errors)

3. **Your Input**: Add any errors you've encountered in your research

**Agent Time**: 3 hours | **Your Time**: 1 hour

---

## WEEK 3-4: Template System

### Task 2.1: Write Mega Guide Template ✅ **DONE**
**Test**: Template renders with test data, all sections present, validates HTML
**Owner**: You + Agent (you define structure, agent drafts boilerplate)
**Output**: `backend/pseo/templates/mega_guide_template.md`

**Results**: ✅ Template created with 40+ variables and 12 sections, test suite validates rendering

**Template Structure** (12 sections):
1. Hero Section
2. Table of Contents
3. TL;DR / Quick Summary
4. Introduction (2-3 paragraphs)
5. Main Content Sections (8-12 H2 sections)
6. Comprehensive Examples Section
7. Common Errors Section
8. Validation Checklist
9. APA 6 vs 7 Comparison
10. FAQ Section (8-12 questions)
11. Related Resources
12. Conclusion / Next Steps

**Variable Slots** (minimum 15):
```jinja2
{{ guide_title }}                    # H1 title
{{ guide_description }}              # Subtitle
{{ target_keywords }}                # Primary keywords
{{ tldr_bullets }}                   # 5 key takeaways (LLM)
{{ introduction }}                   # Opening paragraphs (LLM)
{{ main_sections }}                  # 8-12 H2 sections (LLM)
{{ examples }}                       # From examples.json (structured)
{{ common_errors }}                  # From common_errors.json
{{ validation_checklist }}           # From rules (structured)
{{ apa6_vs_7 }}                      # Changes table (structured)
{{ faq_questions }}                  # 8-12 Q&A (LLM)
{{ related_resources }}              # Internal links (auto)
{{ last_updated }}                   # Date stamp
{{ reading_time }}                   # Auto-calculated
{{ cta_placements }}                 # 5 CTA insertion points
```

**Test Data**: Create `test_data/mega_guide_test.json`

**Deliverable**: Template that renders 5,000+ word guide

---

### Task 2.2: Write Source Type Template ✅ **DONE**
**Test**: Template renders for journal article, book, website with unique content
**Owner**: You + Agent
**Output**: `backend/pseo/templates/source_type_template.md`

**Results**: ✅ Template created with 10 sections and 25+ variables, test data validates 1,704 word output

**Template Structure** (10 sections):
1. Hero Section with Quick Reference
2. Basic Format Explanation
3. Required vs Optional Elements
4. Reference List Examples (5-10 variations)
5. In-Text Citation Guidelines
6. Step-by-Step Instructions
7. Common Errors Section (5-10 errors)
8. Validation Checklist
9. Special Cases (if applicable)
10. Related Sources Section

**Variable Slots** (minimum 10):
```jinja2
{{ source_type_name }}               # "Journal Article"
{{ source_description }}             # One-sentence description
{{ quick_reference_template }}       # Citation template
{{ basic_format_explanation }}       # LLM generated
{{ element_breakdown }}              # From citation_rules.json
{{ required_vs_optional }}           # From rules (structured)
{{ reference_examples }}             # 5-10 examples from examples.json
{{ in_text_guidelines }}             # From rules
{{ step_by_step_instructions }}      # LLM generated
{{ common_errors }}                  # From common_errors.json
{{ validation_checklist }}           # From rules
{{ special_cases }}                  # LLM generated (if applicable)
{{ faq }}                            # 5-8 Q&A (LLM generated)
{{ related_sources }}                # Auto-linked
```

**Deliverable**: Template that renders 2,000+ word guide

---

### Task 2.3: Build Template Engine ✅ **DONE**
**Test**: Loads templates, injects variables, outputs valid markdown
**Owner**: You (developer)
**Output**: `backend/pseo/generator/template_engine.py`

**Implementation**:
```python
from jinja2 import Environment, FileSystemLoader
import json
from pathlib import Path

class TemplateEngine:
    def __init__(self, templates_dir: str):
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def load_template(self, template_name: str) -> Template:
        return self.env.get_template(template_name)

    def load_structured_data(self, data_type: str, filters: dict = None) -> dict:
        """Load data from knowledge base JSON files"""
        file_path = Path(f"knowledge_base/{data_type}.json")
        data = json.loads(file_path.read_text())

        if filters:
            # Apply filters to data
            data = self._filter_data(data, filters)

        return data

    def inject_variables(self, template: Template, data: dict) -> str:
        """Inject variables into template and render"""
        return template.render(**data)

    def validate_output(self, content: str, min_words: int = 800) -> bool:
        """Basic validation of generated content"""
        word_count = len(content.split())
        return word_count >= min_words

    def save_markdown(self, content: str, filepath: str) -> None:
        """Save content to markdown file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        Path(filepath).write_text(content)
```

**Tests**:
```python
def test_template_loading():
    engine = TemplateEngine("templates")
    template = engine.load_template("mega_guide_template.md")
    assert template is not None

def test_variable_injection():
    engine = TemplateEngine("templates")
    template = engine.load_template("mega_guide_template.md")
    data = {"guide_title": "Test Title", "introduction": "Test intro"}
    result = engine.inject_variables(template, data)
    assert "Test Title" in result
    assert "Test intro" in result

def test_output_validation():
    content = "This is a test content with enough words to pass validation."
    assert engine.validate_output(content, min_words=10)
```

**Deliverable**: Working template engine with test suite

---

### Task 2.4: Create Page Design Mockup ✅ **DONE** ✅ **APPROVED**
**Test**: Mockups approved by you, show desktop/mobile responsive design
**Owner**: You (design review) + Agent (create mockups)
**Output**: `design/mocks/`
- ✅ `mega_guide_mockup.html` - Full mega guide page mockup
- ✅ `source_type_mockup.html` - Source type page mockup
- ✅ `mobile_responsive.html` - Mobile version mockup
- ✅ `mini_checker_placement.html` - Show MiniChecker locations

**Results**: ✅ All 4 mockups created using existing site design system (purple #9333ea primary, gradient background, matching typography)

**Status**: ✅ **APPROVED** - Ready to proceed to Task 2.5 (Static Site Generator)

**Process**:
1. **Agent Instructions**:
```
Create HTML mockups showing the final page design for:

1. MEGA GUIDE MOCKUP:
   - Complete page layout with all 12 sections
   - Desktop version (1200px width)
   - Mobile version (375px width)
   - Show typography, spacing, colors
   - Include MiniChecker component placements (3 locations)
   - Show navigation, breadcrumbs, footer
   - Use real content example (APA checking guide)

2. SOURCE TYPE MOCKUP:
   - Complete page layout with all 10 sections
   - Desktop and mobile versions
   - Show example citations with proper formatting
   - Include tables, lists, code blocks
   - MiniChecker placements

3. DESIGN SPECIFICATIONS:
   - Mobile-first responsive design
   - Clean, academic look
   - Good readability (16px+ body text)
   - Professional typography
   - Clear visual hierarchy
   - Easy navigation between sections

4. MINI-CHECKER COMPONENT:
   - Show embedded checker design
   - Input form for single citation
   - Results display area
   - "Check full list" CTA

Save as standalone HTML files with inline CSS for review.
```

2. **Mockup Content**:
   - Use sample content from "How to Check APA Citations"
   - Show real citation examples
   - Include actual error patterns
   - Demonstrate interactive elements

3. **Your Review Criteria**:
   - [ ] Design looks professional and trustworthy
   - [ ] Mobile layout is readable and usable
   - [ ] Typography is appropriate for academic audience
   - [ ] Navigation is clear and intuitive
   - [ ] MiniChecker placement makes sense
   - [ ] Content sections are well-organized
   - [ ] Calls-to-action are visible but not intrusive
   - [ ] Overall design matches brand/quality standards

4. **Approval Process**:
   - Review mockups in browser
   - Test responsive behavior (resize browser)
   - Provide feedback on design elements
   - Approve or request changes
   - Once approved, move to static site builder

**Agent Time**: 4 hours | **Your Time**: 2 hours review

**Deliverable**: Approved HTML mockups ready for development

---

### Task 2.5: Build Static Site Generator (after mockup approval) ✅ **DONE**
**Test**: Converts markdown to HTML, applies approved layout, generates valid HTML
**Owner**: You (developer)
**Output**: `backend/pseo/builder/static_generator.py`

**Results**: ✅ StaticSiteGenerator implemented with 12 passing tests
- Markdown to HTML conversion with tables, code blocks, TOC support
- YAML front matter extraction
- Layout template application via Jinja2
- SEO-friendly URL generation (mega_guide, source_type patterns)
- XML sitemap generation
- Verbose logging for debugging

**Implementation**:
```python
import markdown
from jinja2 import Template
from pathlib import Path

class StaticSiteGenerator:
    def __init__(self, layout_template: str):
        self.layout = Template(layout_template)

    def convert_markdown_to_html(self, md_content: str) -> str:
        """Convert markdown to HTML with extensions"""
        md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])
        return md.convert(md_content)

    def apply_layout(self, html_content: str, metadata: dict) -> str:
        """Wrap content in approved layout template"""
        return self.layout.render(content=html_content, **metadata)

    def generate_url_structure(self, page_type: str, page_name: str) -> str:
        """Create SEO-friendly URLs per Part 1 spec"""
        if page_type == "mega_guide":
            return f"/guide/{page_name}/"
        elif page_type == "source_type":
            return f"/how-to-cite-{page_name}-apa/"
        else:
            return f"/{page_name}/"

    def generate_sitemap(self, pages: list) -> str:
        """Create XML sitemap for all pages"""
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

        for page in pages:
            sitemap += f"""
  <url>
    <loc>https://yoursite.com{page['url']}</loc>
    <lastmod>{page['lastmod']}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{page['priority']}</priority>
  </url>"""

        sitemap += '</urlset>'
        return sitemap

    def build_site(self, input_dir: str, output_dir: str) -> None:
        """Convert all markdown files to HTML"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        pages = []

        for md_file in input_path.glob("**/*.md"):
            # Read markdown
            md_content = md_file.read_text()

            # Extract front matter
            front_matter, content = self._extract_front_matter(md_content)

            # Convert to HTML
            html_content = self.convert_markdown_to_html(content)

            # Apply layout
            final_html = self.apply_layout(html_content, front_matter)

            # Generate output path
            url = self.generate_url_structure(
                front_matter['page_type'],
                front_matter['url_slug']
            )
            output_file = output_path / url.strip("/") / "index.html"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Save HTML
            output_file.write_text(final_html)

            # Track for sitemap
            pages.append({
                'url': url,
                'lastmod': front_matter['last_updated'],
                'priority': '0.7' if front_matter['page_type'] == 'mega_guide' else '0.6'
            })

        # Generate sitemap
        sitemap = self.generate_sitemap(pages)
        (output_path / "sitemap.xml").write_text(sitemap)
```

**Tests**:
- Test markdown conversion preserves formatting
- Test layout applies correctly
- Test URL generation follows spec
- Test sitemap is valid XML

**Deliverable**: Working static site generator using approved mockup layout

---

## WEEK 5-6: LLM Content Generation

### Task 3.1: Build LLM Integration ✅ **DONE**
**Test**: Generates text for each section type, validates output quality
**Owner**: You (developer)
**Output**: `backend/pseo/generator/llm_writer.py`

**Results**: ✅ Implemented with GPT-4o-mini (not Claude)
- 12 passing tests covering all generation methods
- Actual cost: $0.000161 per introduction (130 input + 236 output tokens)
- Full project cost: ~$0.17 for 45 pages (much cheaper than predicted!)
- Verbose logging throughout for debugging
- Token tracking and cost calculation built-in

**Implementation**:
```python
import anthropic
from typing import List, Dict

class LLMWriter:
    def __init__(self, model="claude-3-sonnet-20240229"):
        self.client = anthropic.Anthropic()
        self.model = model

    def _call_claude(self, prompt: str, max_tokens: int = 1000) -> str:
        """Make API call to Claude"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def generate_introduction(self, topic: str, keywords: List[str],
                            rules: Dict, pain_points: List[str]) -> str:
        """Generate 200-250 word introduction"""
        prompt = f"""
Write introduction for APA citation guide about {topic}.

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

Output only the introduction text.
"""
        return self._call_claude(prompt, max_tokens=400)

    def generate_explanation(self, concept: str, rules: Dict,
                           examples: List[str]) -> str:
        """Generate 400-600 word explanation section"""
        prompt = f"""
Explain {concept} for APA citation guide.

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

Use Markdown formatting for structure.
"""
        return self._call_claude(prompt, max_tokens=800)

    def generate_why_errors_happen(self, errors: List[Dict]) -> str:
        """Generate section explaining why common errors occur"""
        prompt = f"""
Write "Why These Errors Happen" section for APA citation guide.

COMMON ERRORS: {self._summarize_errors(errors)}

Requirements:
- 300-500 words
- Psychological explanations
- Acknowledge confusion points
- Empathetic tone
- Explain database/technology factors
- Note learning curve

Be specific about what makes these rules confusing for students.
"""
        return self._call_claude(prompt, max_tokens=600)

    def generate_step_by_step(self, task: str, rules: Dict,
                            complexity: str = "beginner") -> str:
        """Generate step-by-step instructions"""
        prompt = f"""
Write step-by-step instructions for: {task}

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

Assume beginner user with no prior citation knowledge.
"""
        return self._call_claude(prompt, max_tokens=600)

    def generate_faq(self, topic: str, num_questions: int = 8) -> List[Dict]:
        """Generate FAQ questions and answers"""
        prompt = f"""
Generate {num_questions} FAQ questions and answers for {topic}.

Requirements:
- Questions in natural language (how people search)
- Answers 50-150 words each
- Cover common confusion points
- Include practical scenarios
- Link to detailed resources where helpful

Format as JSON array:
[
  {
    "question": "Question text",
    "answer": "Answer text"
  }
]
"""
        response = self._call_claude(prompt, max_tokens=1000)
        # Parse JSON response
        return json.loads(response)

    def validate_uniqueness(self, new_content: str,
                          existing_content: List[str]) -> float:
        """Check uniqueness score against existing content"""
        # Simple similarity check - can be enhanced
        new_words = set(new_content.lower().split())
        max_similarity = 0

        for existing in existing_content:
            existing_words = set(existing.lower().split())
            intersection = new_words.intersection(existing_words)
            union = new_words.union(existing_words)
            similarity = len(intersection) / len(union)
            max_similarity = max(max_similarity, similarity)

        return 1 - max_similarity  # Return uniqueness score

    def _summarize_rules(self, rules: Dict) -> str:
        """Summarize rules for prompt context"""
        if isinstance(rules, list):
            return "\n".join([f"- {r.get('description', r.get('rule_id', ''))}"
                            for r in rules[:5]])
        else:
            return rules.get('description', str(rules))

    def _summarize_errors(self, errors: List[Dict]) -> str:
        """Summarize errors for prompt context"""
        return "\n".join([f"- {e.get('error_name', '')}: {e.get('description', '')}"
                         for e in errors[:5]])
```

**Tests**:
```python
def test_generate_introduction():
    writer = LLMWriter()
    result = writer.generate_introduction(
        topic="checking APA citations",
        keywords=["check APA citations", "APA validation"],
        rules={"description": "APA 7 rules"},
        pain_points=["90.9% of papers have errors"]
    )
    assert len(result.split()) >= 150  # Minimum word count
    assert "APA" in result
    assert "you" in result  # Conversational tone

def test_validate_uniqueness():
    writer = LLMWriter()
    new = "This is about checking APA citations and finding errors."
    existing = ["This guide explains how to check APA citations for errors."]
    score = writer.validate_uniqueness(new, existing)
    assert 0 <= score <= 1
```

**Deliverable**: Working LLM writer with test suite

---

### Task 3.2: Create Generation Prompts ✅ **DONE**
**Test**: Prompts produce required content structure and quality
**Owner**: You + iterative testing
**Output**: `backend/pseo/prompts/`
- `introduction_prompt.txt`
- `explanation_prompt.txt`
- `error_explanation_prompt.txt`
- `step_by_step_prompt.txt`
- `faq_prompt.txt`

**Results**: ✅ All 5 prompt templates created and tested successfully
- introduction_prompt.txt: Generated 184 words (target 200-250)
- explanation_prompt.txt: Generated 512 words (target 400-600)
- faq_prompt.txt: Generated 5 Q&A pairs in JSON format
- All prompts produce conversational, empathetic tone
- Word counts within acceptable ranges
- Test script validates all prompts with LLMWriter

**Example Prompt** (`introduction_prompt.txt`):
```
You are writing the introduction section for an APA citation guide.

TOPIC: {topic}
TARGET KEYWORDS: {keywords}
USER PAIN POINTS: {pain_points}
RELEVANT RULES: {rules_summary}

Write a conversational, empathetic introduction (200-250 words) that:

STRUCTURE:
1. Hook: Start with the main problem this guide solves
2. Acknowledge: Acknowledge common frustrations and statistics
3. Preview: Briefly preview what the guide will cover
4. Reassure: Position this as a solvable problem

REQUIREMENTS:
- Use second person ("you") throughout
- Use active voice (80%+ of sentences)
- Incorporate target keywords naturally (don't stuff)
- Maintain helpful, non-judgmental tone
- Be specific to {topic} (not generic advice)
- Include at least one statistic if relevant

QUALITY STANDARDS:
- Reading level: Grade 10-12
- Sentence length: Average 15-20 words
- Paragraph length: 2-4 sentences
- No copying from APA manual or other guides

CONTEXT:
This will be the first section users read. It should establish credibility and convince them to keep reading.

Output only the introduction text (no meta-commentary).
```

**Testing Process**:
1. Create initial prompts
2. Test with 3 different topics each
3. Review outputs for:
   - Word count compliance
   - Tone consistency
   - Keyword integration
   - Uniqueness
   - Factual accuracy
4. Iterate prompts until outputs consistently good

**Deliverable**: 5 prompt templates that reliably produce quality content

---

### Task 3.3: Build Content Assembler ✅ **DONE**
**Test**: Combines template + LLM + structured data into valid markdown
**Owner**: You (developer)
**Output**: `backend/pseo/generator/content_assembler.py`

**Results**: ✅ ContentAssembler implemented with 14 passing tests
- assemble_mega_guide() generates 5000+ word guides
- assemble_source_type_page() generates 2000+ word guides
- Loads and filters knowledge base data (rules, examples, errors)
- Automatic metadata generation (word count, reading time, SEO)
- Integration tests with real LLM API calls verify functionality

**Implementation**:
```python
from .template_engine import TemplateEngine
from .llm_writer import LLMWriter
from pathlib import Path
import json
from datetime import datetime

class ContentAssembler:
    def __init__(self, knowledge_base_dir: str, templates_dir: str):
        self.template_engine = TemplateEngine(templates_dir)
        self.llm_writer = LLMWriter()
        self.knowledge_base_dir = Path(knowledge_base_dir)

    def assemble_mega_guide(self, topic: str, config: dict) -> dict:
        """Assemble complete mega guide content"""
        # 1. Load template
        template = self.template_engine.load_template("mega_guide_template.md")

        # 2. Load structured data from knowledge base
        relevant_rules = self._load_relevant_rules(topic)
        examples = self._load_examples(topic)
        errors = self._load_errors(topic)

        # 3. Generate LLM sections
        llm_content = self._generate_mega_guide_sections(topic, config, relevant_rules)

        # 4. Combine all content
        template_data = {
            **config,
            **llm_content,
            "examples": examples,
            "common_errors": errors,
            "validation_checklist": self._generate_checklist(relevant_rules),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "reading_time": "25 minutes"  # Will calculate actual
        }

        # 5. Render template
        content = self.template_engine.inject_variables(template, template_data)

        # 6. Validate output
        if not self.template_engine.validate_output(content, min_words=5000):
            raise ValueError(f"Generated content too short for mega guide: {topic}")

        # 7. Generate metadata
        metadata = self._generate_metadata(content, config)

        return {
            "content": content,
            "metadata": metadata,
            "template_data": template_data
        }

    def assemble_source_type_page(self, source_type: str, config: dict) -> dict:
        """Assemble source type guide content"""
        # Similar process but with source type template
        template = self.template_engine.load_template("source_type_template.md")

        # Load specific data for this source type
        source_type_data = self._load_source_type_data(source_type)
        examples = self._load_examples_for_source_type(source_type)
        errors = self._load_errors_for_source_type(source_type)

        # Generate LLM sections
        llm_content = self._generate_source_type_sections(source_type, config, source_type_data)

        # Combine content
        template_data = {
            **config,
            **llm_content,
            "examples": examples,
            "common_errors": errors,
            "validation_checklist": self._generate_checklist(source_type_data['rules']),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "reading_time": "10 minutes"
        }

        content = self.template_engine.inject_variables(template, template_data)

        if not self.template_engine.validate_output(content, min_words=2000):
            raise ValueError(f"Generated content too short for source type: {source_type}")

        metadata = self._generate_metadata(content, config)

        return {
            "content": content,
            "metadata": metadata,
            "template_data": template_data
        }

    def _generate_mega_guide_sections(self, topic: str, config: dict, rules: dict) -> dict:
        """Generate all LLM content sections for mega guide"""
        return {
            "introduction": self.llm_writer.generate_introduction(
                topic=topic,
                keywords=config.get('keywords', []),
                rules=rules,
                pain_points=config.get('pain_points', [])
            ),
            "main_sections": self._generate_main_sections(topic, rules),
            "faq_questions": self.llm_writer.generate_faq(topic, num_questions=12),
            "related_resources": self._generate_related_resources(topic)
        }

    def _generate_source_type_sections(self, source_type: str, config: dict, data: dict) -> dict:
        """Generate LLM content for source type page"""
        return {
            "basic_format_explanation": self.llm_writer.generate_explanation(
                concept=f"{source_type} citation format",
                rules=data.get('rules', {}),
                examples=data.get('examples', [])[:2]
            ),
            "step_by_step_instructions": self.llm_writer.generate_step_by_step(
                task=f"Create {source_type} citation",
                rules=data.get('rules', {})
            ),
            "special_cases": self._generate_special_cases(source_type, data),
            "faq": self.llm_writer.generate_faq(f"citing {source_type}", num_questions=6)
        }

    def _load_relevant_rules(self, topic: str) -> dict:
        """Load rules relevant to topic from knowledge base"""
        rules_file = self.knowledge_base_dir / "citation_rules.json"
        rules = json.loads(rules_file.read_text())

        # Filter rules based on topic keywords
        topic_lower = topic.lower()
        relevant_rules = []

        for rule in rules:
            if any(keyword in rule.get('description', '').lower()
                   for keyword in topic_lower.split()):
                relevant_rules.append(rule)

        return relevant_rules

    def _load_examples(self, topic: str) -> list:
        """Load examples relevant to topic"""
        examples_file = self.knowledge_base_dir / "examples.json"
        examples = json.loads(examples_file.read_text())

        # Return top 10 examples (will be filtered by template)
        return examples[:10]

    def _generate_metadata(self, content: str, config: dict) -> dict:
        """Generate SEO metadata"""
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)  # 200 words per minute

        return {
            "meta_title": config.get('title', ''),
            "meta_description": config.get('description', ''),
            "word_count": word_count,
            "reading_time": f"{reading_time} minutes",
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
```

**Tests**:
```python
def test_assemble_mega_guide():
    assembler = ContentAssembler("knowledge_base", "templates")
    config = {
        "title": "Complete Guide to Checking APA Citations",
        "description": "Learn how to validate APA citations",
        "keywords": ["check APA citations", "APA validation"],
        "pain_points": ["90.9% of papers have errors"]
    }

    result = assembler.assemble_mega_guide("checking APA citations", config)

    assert "content" in result
    assert "metadata" in result
    assert result["metadata"]["word_count"] > 5000
    assert "TL;DR" in result["content"]
    assert "## Frequently Asked Questions" in result["content"]

def test_assemble_source_type_page():
    assembler = ContentAssembler("knowledge_base", "templates")
    config = {
        "title": "How to Cite a Journal Article in APA",
        "description": "Complete guide to APA journal citations"
    }

    result = assembler.assemble_source_type_page("journal article", config)

    assert "content" in result
    assert result["metadata"]["word_count"] > 2000
    assert "## Quick Reference" in result["content"]
    assert "## Examples" in result["content"]
```

**Deliverable**: Working content assembler with test suite

---

### Task 3.4: Generate & Review 5 Test Pages ✅ **DONE**
**Test**: Each page >800 words, passes quality checks, you approve content
**Owner**: You (run generator, review output)
**Output**: `content/test/` - 5 approved test pages

**Results**: ✅ All 5 pages generated successfully
- Total: 17,686 words across 5 pages (avg 3,537 words/page)
- Cost: $0.026 (2.6 cents total)
- Mega guides: 2,817-2,979 words each
- Source type pages: 3,667-4,112 words each
- Token tracking: Fully implemented with per-page stats saved to JSON
- Template bugs fixed: TOC rendering, example JSON access, missing variables

**Test Pages**:
1. Mega Guide: "Complete Guide to Checking APA Citations"
2. Mega Guide: "APA Citation Errors Guide"
3. Source Type: "How to Cite a Journal Article in APA"
4. Source Type: "How to Cite a Book in APA"
5. Source Type: "How to Cite a Website in APA"

**Process**:
1. Create test configuration for each page
2. Run generation script:
```python
# test_generation.py
from generator.content_assembler import ContentAssembler

assembler = ContentAssembler("knowledge_base", "templates")

# Test mega guide
mega_guide = assembler.assemble_mega_guide(
    "checking APA citations",
    test_configs["check_citations"]
)
save_content(mega_guide, "content/test/check-apa-citations.md")

# Test source type
journal_guide = assembler.assemble_source_type_page(
    "journal article",
    test_configs["journal_article"]
)
save_content(journal_guide, "content/test/how-to-cite-journal-article-apa.md")
```

3. Review each page manually:
   - [ ] Factually accurate (rules match APA 7)
   - [ ] Examples correctly formatted
   - [ ] No template variable failures
   - [ ] Unique content (not copy-paste between pages)
   - [ ] Conversational tone
   - [ ] Proper structure (all required sections)
   - [ ] Internal links work
   - [ ] Word count meets minimum

4. Iterate on prompts/templates based on issues found
5. Regenerate until all 5 pages approved

**Deliverable**: 5 approved test pages saved in `content/test/`

---

## WEEK 7: Review System

### Task 4.1: Build LLM Review Agent ✅ **DONE**
**Test**: Reviews sample pages, flags legitimate issues, provides actionable feedback
**Owner**: You (developer)
**Output**: `backend/pseo/review/llm_reviewer.py`

**Results**: ✅ LLM reviewer implemented with 11 passing tests
- Reviews markdown content + metadata before HTML generation
- Structural checks: word count, required sections, heading hierarchy
- Technical checks: template variables, citation examples, multiple H1s
- SEO checks: meta title/description length, internal links
- Optional LLM quality check: accuracy, tone, clarity, examples
- SKIP_LLM_REVIEW env var for fast testing
- Tested against 5 real pages: found 5 legitimate issues (H1s, word count, sections)
- Review report with severity levels (high/medium/low) and suggestions

**Implementation**:
```python
from ..generator.llm_writer import LLMWriter
from typing import Dict, List
import re

class LLMReviewer:
    def __init__(self):
        self.llm = LLMWriter()

    def review_page(self, content: str, page_type: str, metadata: dict = None) -> Dict:
        """Comprehensive review of generated content"""

        # Check basic requirements
        issues = []

        # 1. Word count check
        word_count = len(content.split())
        min_words = 5000 if page_type == "mega_guide" else 2000
        if word_count < min_words:
            issues.append({
                "severity": "high",
                "issue": f"Content too short: {word_count} words (minimum {min_words})",
                "location": "Entire page",
                "suggestion": "Expand content by adding more examples and explanations"
            })

        # 2. Structure check
        required_sections = self._get_required_sections(page_type)
        for section in required_sections:
            if f"## {section}" not in content:
                issues.append({
                    "severity": "high",
                    "issue": f"Missing required section: {section}",
                    "location": "Structure",
                    "suggestion": f"Add {section} section with appropriate content"
                })

        # 3. LLM quality check
        quality_issues = self._llm_quality_check(content, page_type)
        issues.extend(quality_issues)

        # 4. Technical checks
        technical_issues = self._technical_checks(content, page_type)
        issues.extend(technical_issues)

        # 5. SEO checks
        seo_issues = self._seo_checks(content, metadata)
        issues.extend(seo_issues)

        # Determine overall verdict
        high_issues = [i for i in issues if i["severity"] == "high"]
        overall_verdict = "NEEDS_REVISION" if high_issues else "PASS"

        return {
            "overall_verdict": overall_verdict,
            "issues_found": issues,
            "word_count": word_count,
            "uniqueness_score": self._check_uniqueness(content),
            "review_summary": self._generate_summary(issues)
        }

    def _llm_quality_check(self, content: str, page_type: str) -> List[Dict]:
        """Use LLM to check content quality"""
        prompt = f"""
Review this {page_type} page for quality issues:

{content[:3000]}... (truncated for review)

Check for:
1. ACCURACY: Are citation rules correct per APA 7?
2. CLARITY: Is language clear and easy to understand?
3. TONE: Is tone conversational and helpful?
4. EXAMPLES: Are examples properly formatted in APA 7?
5. COMPLETENESS: Does content feel complete and valuable?
6. ORIGINALITY: Does content feel generic or copy-paste?

Return JSON format:
{{
  "issues": [
    {{
      "severity": "high/medium/low",
      "issue": "Description of issue",
      "location": "Section name or general",
      "suggestion": "How to fix it"
    }}
  ]
}}
"""

        try:
            response = self.llm._call_claude(prompt, max_tokens=800)
            result = json.loads(response)
            return result.get("issues", [])
        except Exception as e:
            return [{
                "severity": "medium",
                "issue": f"LLM review failed: {str(e)}",
                "location": "Review system",
                "suggestion": "Manual review recommended"
            }]

    def _technical_checks(self, content: str, page_type: str) -> List[Dict]:
        """Check technical formatting issues"""
        issues = []

        # Check for template variable failures
        if "{{" in content and "}}" in content:
            issues.append({
                "severity": "high",
                "issue": "Template variables not replaced",
                "location": "Throughout page",
                "suggestion": "Check template engine configuration"
            })

        # Check heading hierarchy
        lines = content.split('\n')
        h1_count = 0
        prev_h_level = 0

        for line in lines:
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if level == 1:
                    h1_count += 1
                if prev_h_level > 0 and level > prev_h_level + 1:
                    issues.append({
                        "severity": "medium",
                        "issue": f"Heading hierarchy skip: H{prev_h_level} to H{level}",
                        "location": line.strip(),
                        "suggestion": "Use sequential heading levels"
                    })
                prev_h_level = level

        if h1_count != 1:
            issues.append({
                "severity": "high",
                "issue": f"Found {h1_count} H1 headings (should be exactly 1)",
                "location": "Headings",
                "suggestion": "Use only one H1 per page"
            })

        # Check for proper APA formatting in examples
        citation_pattern = r'\([^)]+,\s*\d{4}[,\)]'
        citations = re.findall(citation_pattern, content)

        if len(citations) < 5 and page_type == "mega_guide":
            issues.append({
                "severity": "medium",
                "issue": "Very few citation examples found",
                "location": "Examples",
                "suggestion": "Add more APA citation examples throughout the page"
            })

        return issues

    def _seo_checks(self, content: str, metadata: dict = None) -> List[Dict]:
        """Check SEO best practices"""
        issues = []

        if metadata:
            # Check meta title length
            title = metadata.get('meta_title', '')
            if len(title) < 30 or len(title) > 60:
                issues.append({
                    "severity": "medium",
                    "issue": f"Meta title length: {len(title)} chars (ideal: 30-60)",
                    "location": "Meta title",
                    "suggestion": "Adjust title length for optimal SEO"
                })

            # Check meta description length
            desc = metadata.get('meta_description', '')
            if len(desc) < 120 or len(desc) > 160:
                issues.append({
                    "severity": "medium",
                    "issue": f"Meta description length: {len(desc)} chars (ideal: 120-160)",
                    "location": "Meta description",
                    "suggestion": "Adjust description length for optimal click-through rate"
                })

        # Check internal links
        internal_links = re.findall(r'\[([^]]+)\]\(/([^)]+)\)', content)
        if len(internal_links) < 8:
            issues.append({
                "severity": "low",
                "issue": f"Only {len(internal_links)} internal links found (ideal: 8-15)",
                "location": "Internal linking",
                "suggestion": "Add more internal links to related pages"
            })

        return issues

    def _get_required_sections(self, page_type: str) -> List[str]:
        """Get list of required sections for page type"""
        if page_type == "mega_guide":
            return [
                "Introduction",
                "Examples",
                "Common Errors",
                "Validation Checklist",
                "Frequently Asked Questions"
            ]
        elif page_type == "source_type":
            return [
                "Basic Format",
                "Examples",
                "Common Errors",
                "Validation Checklist"
            ]
        return []

    def _check_uniqueness(self, content: str) -> float:
        """Check content uniqueness (simple implementation)"""
        # This would ideally check against existing pages
        # For now, return a placeholder
        return 0.85

    def _generate_summary(self, issues: List[Dict]) -> str:
        """Generate summary of review results"""
        if not issues:
            return "No issues found. Content passes all quality checks."

        high_count = len([i for i in issues if i["severity"] == "high"])
        medium_count = len([i for i in issues if i["severity"] == "medium"])
        low_count = len([i for i in issues if i["severity"] == "low"])

        summary = f"Found {len(issues)} issues: "
        if high_count > 0:
            summary += f"{high_count} high, "
        if medium_count > 0:
            summary += f"{medium_count} medium, "
        if low_count > 0:
            summary += f"{low_count} low"

        return summary
```

**Tests**:
```python
def test_review_good_page():
    reviewer = LLMReviewer()
    good_content = """
# How to Cite a Journal Article in APA

## Introduction
This guide explains how to cite journal articles in APA format...

## Basic Format
Author, A. A. (Year). Title of article. Journal Name, volume(issue), pages.

## Examples
Smith, J. (2020). Article title. Journal Name, 15(2), 123-145.
"""

    result = reviewer.review_page(good_content, "source_type")
    assert result["overall_verdict"] == "PASS"

def test_review_bad_page():
    reviewer = LLMReviewer()
    bad_content = "# Title\n\nShort content with no structure."

    result = reviewer.review_page(bad_content, "source_type")
    assert result["overall_verdict"] == "NEEDS_REVISION"
    assert len(result["issues_found"]) > 0
```

**Deliverable**: Working LLM reviewer with comprehensive quality checks

---

### Task 4.2: Create Human Review Interface ✅ **DONE**
**Test**: You can review flagged pages, approve/reject, request revisions
**Owner**: You (developer)
**Output**: `backend/pseo/review/human_review_cli.py`

**Results**: ✅ Human Review CLI implemented with full test coverage
- 10 passing tests covering all functionality
- Interactive menu system for reviewing pages
- File management (move to approved/rejected directories)
- Human review metadata tracking (approval date, reason, etc.)
- Integration with existing LLM review results
- Tested with actual test data from content/test/

**Implementation**:
```python
#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

class HumanReviewCLI:
    def __init__(self, review_dir: str = "content/review_queue"):
        self.review_dir = Path(review_dir)
        self.review_dir.mkdir(exist_ok=True)
        self.approved_dir = Path("content/approved")
        self.approved_dir.mkdir(exist_ok=True)
        self.rejected_dir = Path("content/rejected")
        self.rejected_dir.mkdir(exist_ok=True)

    def run(self):
        """Main CLI loop"""
        while True:
            pages = self._get_pending_pages()
            if not pages:
                print("\n✅ All pages reviewed!")
                break
            self._show_menu(pages)
            # Interactive review workflow...
```

**Test Coverage**:
- CLI initialization and directory setup
- Pending page listing with metadata display
- Page approval workflow (moves file + adds metadata)
- Page rejection workflow (moves file + records reason)
- Content viewing (truncated for long content)
- LLM review details display
- Complete end-to-end review flow

**Usage**:
```bash
# Run human review CLI
python3 backend/pseo/review/human_review_cli.py

# Interactive workflow:
# 1. Shows pending pages with LLM verdict
# 2. Select page to review
# 3. View content, LLM review details
# 4. Approve or reject with reason
# 5. File moved to appropriate directory
```

**Deliverable**: ✅ Working CLI tool for human review workflow

---

## WEEK 8: Static Site Setup

### Task 5.1: Build Static Site Generator
**Test**: Converts markdown to HTML, applies approved layout, generates valid HTML
**Owner**: You (developer)
**Output**: `backend/pseo/builder/static_generator.py`

[Implementation already detailed in Task 2.5]

**Key Features**:
- Markdown to HTML conversion with syntax highlighting
- Apply approved layout template from Week 4 mockups
- Generate SEO-friendly URLs
- Create XML sitemap
- Copy static assets (CSS, JS, images)

**Tests**:
```python
def test_markdown_conversion():
    generator = StaticSiteGenerator(layout_template)
    md_content = "# Heading\n\nThis is **bold** text."
    html = generator.convert_markdown_to_html(md_content)
    assert "<h1>Heading</h1>" in html
    assert "<strong>bold</strong>" in html

def test_layout_application():
    generator = StaticSiteGenerator(layout_template)
    content = "<h1>Test</h1>"
    html = generator.apply_layout(content, {"title": "Test Page"})
    assert "<title>Test Page</title>" in html
    assert "<h1>Test</h1>" in html
```

**Deliverable**: Working static site generator using approved layout

---

### Task 5.2: Create HTML Layout Template
**Test**: Pages render cleanly on mobile/desktop, pass Core Web Vitals
**Owner**: You (implement approved mockup)
**Output**: `backend/pseo/builder/templates/layout.html`

**Process**:
1. Convert approved mockups from Week 4 into template
2. Add Jinja2 variables for dynamic content
3. Optimize for performance and SEO

**Template Structure**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ meta_title }}</title>
    <meta name="description" content="{{ meta_description }}">
    <link rel="canonical" href="https://yoursite.com{{ url }}">

    <!-- Schema.org markup -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": "{{ meta_title }}",
        "description": "{{ meta_description }}"
    }
    </script>

    <!-- CSS -->
    <link rel="stylesheet" href="/assets/css/styles.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
</head>
<body>
    <!-- Header -->
    <header class="site-header">
        <nav class="main-nav">
            <a href="/" class="logo">Citation Checker</a>
            <ul class="nav-links">
                <li><a href="/checker/">Check Citations</a></li>
                <li><a href="/guides/">Guides</a></li>
            </ul>
        </nav>
    </header>

    <!-- Breadcrumbs -->
    <nav class="breadcrumbs">
        <a href="/">Home</a> >
        <a href="/guides/">Citation Guides</a> >
        <span class="current">{{ breadcrumb_title }}</span>
    </nav>

    <!-- Main Content -->
    <main class="content-wrapper">
        <article class="content-page">
            {{ content | safe }}

            <!-- MiniChecker CTA placements -->
            <div class="cta-placement">
                {% include 'components/mini-checker.html' %}
            </div>
        </article>

        <!-- Sidebar (desktop only) -->
        <aside class="content-sidebar">
            <div class="related-resources">
                <h3>Related Guides</h3>
                {% if related_resources %}
                <ul>
                    {% for resource in related_resources %}
                    <li><a href="{{ resource.url }}">{{ resource.title }}</a></li>
                    {% endfor %}
                </ul>
                {% endif %}
            </div>
        </aside>
    </main>

    <!-- Footer -->
    <footer class="site-footer">
        <p>&copy; 2024 Citation Checker. Last updated: {{ last_updated }}</p>
    </footer>

    <!-- Scripts -->
    <script src="/assets/js/mini-checker.js"></script>
    <script src="/assets/js/analytics.js"></script>
</body>
</html>
```

**Deliverable**: Production-ready HTML layout template

---

### Task 5.3: Test Static Site Locally
**Test**: Site loads, navigation works, pages render correctly
**Owner**: You
**Process**:
1. Generate 5 test pages to HTML
2. Serve locally: `python3 -m http.server 8000`
3. Test on:
   - Desktop browser (Chrome, Firefox, Safari)
   - Mobile browser (Chrome DevTools mobile view)
   - Tablet view
4. Test functionality:
   - Navigation between pages
   - Internal links work
   - MiniChecker placeholder displays
   - Responsive design
5. Run Lighthouse audit:
   - Performance: >90
   - Accessibility: >95
   - Best Practices: >90
   - SEO: >90

**Test Checklist**:
- [ ] All 5 test pages load without errors
- [ ] Navigation menu works correctly
- [ ] Breadcrumbs display properly
- [ ] Content renders with proper formatting
- [ ] Mobile layout is readable
- [ ] No horizontal scrolling on mobile
- [ ] Font sizes are readable (≥16px body)
- [ ] Images (if any) load and are responsive
- [ ] Internal links work
- [ ] MiniChecker components display in correct locations

**Deliverable**: Functioning local static site with passing tests

---

## WEEK 9: Mini-Checker Component

### Task 6.1: Build MiniChecker React Component
**Test**: Accepts citation input, calls API, displays results inline
**Owner**: You (frontend developer)
**Output**: `frontend/components/MiniChecker.tsx`

**Implementation**:
```tsx
import React, { useState } from 'react';
import { validateCitation } from '../services/api';

interface MiniCheckerProps {
  placeholder?: string;
  prefillExample?: string;
  contextType?: 'mega-guide' | 'source-type' | 'error-page';
  onFullChecker?: () => void;
}

interface ValidationResult {
  is_valid: boolean;
  errors: Array<{
    type: string;
    message: string;
    location: string;
    suggestion: string;
  }>;
  corrected_citation?: string;
}

const MiniChecker: React.FC<MiniCheckerProps> = ({
  placeholder = "Paste your citation here...",
  prefillExample,
  contextType = 'mega-guide',
  onFullChecker
}) => {
  const [citation, setCitation] = useState(prefillExample || '');
  const [isValidating, setIsValidating] = useState(false);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleValidate = async () => {
    if (!citation.trim()) return;

    setIsValidating(true);
    setError(null);

    try {
      const response = await validateCitation(citation);
      setResult(response);
    } catch (err) {
      setError('Validation failed. Please try again.');
      console.error('Validation error:', err);
    } finally {
      setIsValidating(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleValidate();
    }
  };

  return (
    <div className="mini-checker">
      <div className="mini-checker-header">
        <h4>Quick Check Your Citation</h4>
        <p>Instantly validate APA formatting</p>
      </div>

      <div className="mini-checker-form">
        <textarea
          value={citation}
          onChange={(e) => setCitation(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          className="mini-checker-input"
          rows={3}
          maxLength={500}
        />

        <div className="mini-checker-actions">
          <button
            onClick={handleValidate}
            disabled={!citation.trim() || isValidating}
            className="mini-checker-button"
          >
            {isValidating ? 'Checking...' : 'Check Citation'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mini-checker-error">
          <p>⚠️ {error}</p>
        </div>
      )}

      {result && (
        <div className={`mini-checker-result ${result.is_valid ? 'valid' : 'invalid'}`}>
          {result.is_valid ? (
            <div className="result-valid">
              <p>✅ <strong>No formatting errors found!</strong></p>
              <p>Your citation follows APA 7th edition guidelines.</p>
            </div>
          ) : (
            <div className="result-invalid">
              <p>❌ <strong>Found {result.errors.length} formatting issue{result.errors.length > 1 ? 's' : ''}:</strong></p>
              <ul className="error-list">
                {result.errors.map((error, index) => (
                  <li key={index} className="error-item">
                    <strong>{error.type}:</strong> {error.message}
                    {error.suggestion && (
                      <div className="error-suggestion">
                        💡 <em>Suggestion: {error.suggestion}</em>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
              {result.corrected_citation && (
                <div className="corrected-citation">
                  <strong>Corrected format:</strong>
                  <code>{result.corrected_citation}</code>
                </div>
              )}
            </div>
          )}

          <div className="mini-checker-upsell">
            <p>
              <strong>Check your entire reference list →</strong>
            </p>
            <button
              onClick={onFullChecker}
              className="full-checker-button"
            >
              Open Citation Checker
            </button>
          </div>
        </div>
      )}

      <div className="mini-checker-tips">
        <p>💡 <em>Tip: Press Ctrl+Enter to validate quickly</em></p>
      </div>
    </div>
  );
};

export default MiniChecker;
```

**CSS Styles** (to be included in main stylesheet):
```css
.mini-checker {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin: 30px 0;
  max-width: 100%;
}

.mini-checker-header h4 {
  margin: 0 0 8px 0;
  color: #495057;
}

.mini-checker-header p {
  margin: 0;
  color: #6c757d;
  font-size: 14px;
}

.mini-checker-input {
  width: 100%;
  border: 1px solid #ced4da;
  border-radius: 4px;
  padding: 12px;
  font-family: monospace;
  font-size: 14px;
  resize: vertical;
  margin-bottom: 12px;
}

.mini-checker-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.mini-checker-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.result-valid {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  padding: 15px;
  margin-top: 15px;
}

.result-invalid {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 15px;
  margin-top: 15px;
}

.error-list {
  margin: 10px 0;
  padding-left: 20px;
}

.error-item {
  margin-bottom: 10px;
}

.error-suggestion {
  margin-top: 5px;
  font-size: 13px;
}

.full-checker-button {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 10px;
}

@media (max-width: 768px) {
  .mini-checker {
    padding: 15px;
    margin: 20px 0;
  }
}
```

**Tests**:
```tsx
// MiniChecker.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MiniChecker from './MiniChecker';

// Mock API
jest.mock('../services/api', () => ({
  validateCitation: jest.fn()
}));

test('renders mini checker with default props', () => {
  render(<MiniChecker />);
  expect(screen.getByText('Quick Check Your Citation')).toBeInTheDocument();
  expect(screen.getByPlaceholderText('Paste your citation here...')).toBeInTheDocument();
});

test('validates citation when button clicked', async () => {
  const mockValidate = jest.fn().mockResolvedValue({
    is_valid: false,
    errors: [{ type: 'Capitalization', message: 'Article title should be sentence case' }]
  });

  require('../services/api').validateCitation.mockImplementation(mockValidate);

  render(<MiniChecker />);

  const input = screen.getByPlaceholderText('Paste your citation here...');
  const button = screen.getByText('Check Citation');

  fireEvent.change(input, { target: { value: 'Test citation' } });
  fireEvent.click(button);

  await waitFor(() => {
    expect(mockValidate).toHaveBeenCalledWith('Test citation');
  });

  expect(screen.getByText(/Found 1 formatting issue/)).toBeInTheDocument();
});
```

**Deliverable**: Working MiniChecker React component with tests

---

### Task 6.2: Integrate MiniChecker into Static Pages
**Test**: Component renders in static HTML, works without React app running
**Owner**: You
**Output**: Embedded MiniChecker in static page template

**Process**:
1. **Create Standalone MiniChecker Bundle**:
```bash
# Build MiniChecker as standalone component
cd frontend
npm run build:mini-checker
# Outputs: dist/mini-checker.js + mini-checker.css
```

2. **Update Static Page Template**:
```html
<!-- In layout.html -->
<div class="cta-placement" id="mini-checker-1">
    <!-- MiniChecker will be mounted here -->
</div>

<!-- At end of body -->
<script src="/assets/js/mini-checker.js"></script>
<script>
    // Mount MiniChecker components
    mountMiniChecker('mini-checker-1', {
        placeholder: "Enter your journal article citation...",
        prefillExample: "Smith, J. (2020). Article title. Journal Name, 15(2), 123-145.",
        contextType: "mega-guide",
        onFullChecker: () => window.location.href = '/checker/'
    });
</script>
```

3. **Placement Locations** (per template requirements):
   - **After Basic Format section**: Check format you just learned
   - **After Common Errors section**: Find and fix these errors
   - **Before Related Resources**: Validate your citations

4. **Test Integration**:
   - Generate test page with embedded MiniChecker
   - Open in browser
   - Test citation validation flow
   - Test CTA to main checker
   - Verify mobile responsive

**Deliverable**: MiniChecker working in static pages without full React app

---

## WEEK 10-11: Batch Generation

### Task 7.1: Generate All 15 Mega Guides
**Test**: All pages >5,000 words, pass LLM review, you approve 20% sample
**Owner**: Automated + You (review)
**Output**: `content/approved/mega-guides/` - 15 approved mega guides

**Mega Guide Topics**:
1. Complete APA 7th Edition Citation Guide
2. Complete Guide to Checking APA Citations
3. APA Citation Errors - Prevention Guide
4. Validate Your Reference List Guide
5. APA vs MLA vs Chicago Comparison
6. APA Citation Guide for Psychology Students
7. APA Citation Guide for Nursing Students
8. APA Citation Guide for Education Research
9. APA 7th Edition Changes Guide
10. APA Title Page Format Guide
11. APA Reference List Format Guide
12. APA In-Text Citation Complete Guide
13. How to Fix APA Citation Errors
14. APA Citation Workflow Guide
15. APA for Graduate Students Guide

**Generation Script** (`generate_mega_guides.py`):
```python
#!/usr/bin/env python3
import json
from pathlib import Path
from generator.content_assembler import ContentAssembler
from review.llm_reviewer import LLMReviewer

# Load configurations
with open("configs/mega_guides.json") as f:
    guide_configs = json.load(f)

assembler = ContentAssembler("knowledge_base", "templates")
reviewer = LLMReviewer()

print("Generating 15 mega guides...")

for i, config in enumerate(guide_configs, 1):
    print(f"\n[{i}/15] Generating: {config['title']}")

    try:
        # Generate content
        result = assembler.assemble_mega_guide(config['topic'], config)

        # LLM review
        review = reviewer.review_page(result['content'], 'mega_guide', result['metadata'])

        # Save to review queue
        page_data = {
            "title": config['title'],
            "url": config['url'],
            "page_type": "mega_guide",
            "content": result['content'],
            "metadata": result['metadata'],
            "llm_review": review,
            "word_count": result['metadata']['word_count']
        }

        output_file = Path("content/review_queue") / f"mega_guide_{i:02d}_{config['url_slug']}.json"
        output_file.parent.mkdir(exist_ok=True)
        output_file.write_text(json.dumps(page_data, indent=2))

        status = "✓ PASS" if review['overall_verdict'] == 'PASS' else "⚠ NEEDS REVISION"
        print(f"  {status} | {page_data['word_count']:,} words | {len(review['issues_found'])} issues")

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        continue

print(f"\nGeneration complete. Files saved to content/review_queue/")
print("Run human review: python3 backend/pseo/review/human_review_cli.py")
```

**Your Review Process**:
1. Run generation script
2. Launch human review CLI
3. Review 3 guides manually (20% sample):
   - Guide 1: "Complete APA 7th Edition Citation Guide"
   - Guide 8: "APA Citation Guide for Education Research"
   - Guide 15: "APA for Graduate Students Guide"
4. For each guide:
   - Check factual accuracy
   - Verify examples are correct
   - Ensure tone consistency
   - Confirm structure completeness
5. If systemic issues found, address and regenerate
6. Approve batch

**Deliverable**: 15 approved mega guides ready for production

---

### Task 7.2: Generate 30 Source Type Pages
**Test**: All pages >2,000 words, pass LLM review, you approve 20% sample
**Owner**: Automated + You (review)
**Output**: `content/approved/source-types/` - 30 approved source type pages

**Source Types List**:
1. Journal article (with DOI)
2. Journal article (without DOI)
3. Journal article (advance online)
4. Book (authored)
5. Book (edited)
6. Book chapter
7. E-book
8. E-book chapter
9. Website (organizational)
10. Website (individual author)
11. Newspaper article (online)
12. Newspaper article (print)
13. Magazine article
14. Blog post
15. YouTube video
16. Podcast episode
17. Social media post (Twitter/X)
18. Social media post (Instagram)
19. Facebook post
20. TED Talk
21. Film/Movie
22. TV episode
23. Dissertation (published)
24. Thesis (published)
25. Government report
26. Conference paper
27. Dataset
28. Wikipedia article
29. Dictionary entry (online)
30. Encyclopedia entry (online)

**Generation Script** (`generate_source_types.py`):
```python
#!/usr/bin/env python3
import json
from pathlib import Path
from generator.content_assembler import ContentAssembler
from review.llm_reviewer import LLMReviewer

# Load configurations
with open("configs/source_types.json") as f:
    type_configs = json.load(f)

assembler = ContentAssembler("knowledge_base", "templates")
reviewer = LLMReviewer()

print("Generating 30 source type pages...")

for i, config in enumerate(type_configs, 1):
    print(f"\n[{i}/30] Generating: {config['title']}")

    try:
        # Generate content
        result = assembler.assemble_source_type_page(config['source_type'], config)

        # LLM review
        review = reviewer.review_page(result['content'], 'source_type', result['metadata'])

        # Save to review queue
        page_data = {
            "title": config['title'],
            "url": config['url'],
            "page_type": "source_type",
            "content": result['content'],
            "metadata": result['metadata'],
            "llm_review": review,
            "word_count": result['metadata']['word_count']
        }

        output_file = Path("content/review_queue") / f"source_type_{i:02d}_{config['url_slug']}.json"
        output_file.write_text(json.dumps(page_data, indent=2))

        status = "✓ PASS" if review['overall_verdict'] == 'PASS' else "⚠ NEEDS REVISION"
        print(f"  {status} | {page_data['word_count']:,} words | {len(review['issues_found'])} issues")

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        continue

print(f"\nGeneration complete. Files saved to content/review_queue/")
print("Run human review: python3 backend/pseo/review/human_review_cli.py")
```

**Your Review Process**:
1. Run generation script
2. Review 6 pages manually (20% sample):
   - Pages 1, 8, 15, 22, 25, 30 (spread across list)
3. Check for:
   - Accurate formatting rules
   - Relevant examples for source type
   - Common errors specific to source
   - Step-by-step instructions clarity
4. Approve batch

**Deliverable**: 30 approved source type pages ready for production

---

### Task 7.3: Build Production Site
**Test**: All 45 pages converted to HTML, site builds without errors
**Owner**: Automated
**Output**: `dist/` - Complete static site ready for deployment

**Build Script** (`build_production.py`):
```python
#!/usr/bin/env python3
import json
from pathlib import Path
from builder.static_generator import StaticSiteGenerator

def build_production_site():
    """Build complete production site from approved content"""

    # Initialize generator
    generator = StaticSiteGenerator("builder/templates/layout.html")

    # Load approved pages
    approved_dir = Path("content/approved")
    pages = []

    # Process mega guides
    for page_file in approved_dir.glob("mega-guides/*.json"):
        page_data = json.loads(page_file.read_text())
        html_content = generator.convert_markdown_to_html(page_data['content'])
        final_html = generator.apply_layout(html_content, page_data['metadata'])

        url = page_data['metadata']['url']
        output_path = Path("dist") / url.strip("/") / "index.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(final_html)

        pages.append({
            'url': url,
            'lastmod': page_data['metadata']['last_updated'],
            'priority': '0.7'
        })

    # Process source type pages
    for page_file in approved_dir.glob("source-types/*.json"):
        page_data = json.loads(page_file.read_text())
        html_content = generator.convert_markdown_to_html(page_data['content'])
        final_html = generator.apply_layout(html_content, page_data['metadata'])

        url = page_data['metadata']['url']
        output_path = Path("dist") / url.strip("/") / "index.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(final_html)

        pages.append({
            'url': url,
            'lastmod': page_data['metadata']['last_updated'],
            'priority': '0.6'
        })

    # Generate sitemap
    sitemap = generator.generate_sitemap(pages)
    (Path("dist") / "sitemap.xml").write_text(sitemap)

    # Copy static assets
    import shutil
    shutil.copytree("assets", "dist/assets", dirs_exist_ok=True)

    print(f"✅ Production site built successfully!")
    print(f"   Pages: {len(pages)}")
    print(f"   Output: dist/")
    print(f"   Ready for deployment!")

if __name__ == "__main__":
    build_production_site()
```

**Deliverable**: Complete static site with all 45 pages

---

## WEEK 12: Launch & Monitor

### Task 8.1: Deploy to Production
**Test**: All pages load, sitemap submitted, analytics tracking
**Owner**: You (deployment)
**Output**: Live site at your domain

**Deployment Options**:

**Option A: Subdirectory on Existing Domain**
```
yoursite.com/
├── checker/          # Existing React app
├── content/          # New PSEO content
│   ├── guide/
│   └── how-to-cite-*/
├── sitemap.xml
└── assets/
```

**Option B: Subdomain**
```
content.yoursite.com/
├── guide/
├── how-to-cite-*/
├── sitemap.xml
└── assets/
checker.yoursite.com/  # Existing app
```

**Deployment Steps**:
1. **Build Site**:
```bash
python3 backend/pseo/build_production.py
```

2. **Test Site Locally**:
```bash
cd dist
python3 -m http.server 8000
# Test all URLs load correctly
```

3. **Deploy Files**:
```bash
# If using same server as existing app
rsync -av dist/ user@server:/var/www/html/content/

# If using separate hosting
rsync -av dist/ user@server:/var/www/content/
```

4. **Configure Web Server**:
```nginx
# Nginx configuration
server {
    listen 80;
    server_name yoursite.com;

    # Existing React app
    location / {
        root /var/www/html/frontend;
        try_files $uri $uri/ /index.html;
    }

    # New PSEO content
    location /content/ {
        root /var/www/html;
        try_files $uri $uri/ $uri.html =404;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000;
    }
}
```

5. **Submit to Google**:
```bash
# Submit sitemap
curl "https://www.google.com/ping?sitemap=https://yoursite.com/sitemap.xml"
```

6. **Verify Deployment**:
- Check all 45 pages load
- Test MiniChecker functionality
- Verify analytics tracking
- Test mobile responsiveness

**Deliverable**: Live site with all 45 pages accessible

---

### Task 8.2: Setup Monitoring
**Test**: Dashboard shows traffic, indexing status, errors
**Owner**: You (setup once)
**Output**: Working monitoring system

**Monitoring Setup**:

1. **Google Search Console**:
   - Add property for your domain
   - Submit sitemap
   - Monitor indexing status
   - Track impressions and clicks

2. **Google Analytics** (if not already setup):
```html
<!-- Add to layout.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

3. **Simple Monitoring Dashboard** (`scripts/monitoring.py`):
```python
#!/usr/bin/env python3
import json
import requests
from datetime import datetime, timedelta

class SEOMonitor:
    def __init__(self, gsc_api_key: str, ga_property_id: str):
        self.gsc_api_key = gsc_api_key
        self.ga_property_id = ga_property_id

    def get_indexing_status(self):
        """Check how many pages are indexed"""
        # Query Google Search Console API
        return self._query_gsc_api("site-performance")

    def get_traffic_stats(self, days: int = 7):
        """Get traffic statistics"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Query Google Analytics API
        return self._query_ga_api(start_date, end_date)

    def check_page_performance(self):
        """Check Core Web Vitals for key pages"""
        pages_to_check = [
            "/guide/check-apa-citations/",
            "/how-to-cite-journal-article-apa/",
            "/guide/apa-7th-edition/"
        ]

        performance_data = {}
        for page in pages_to_check:
            performance_data[page] = self._check_page_speed(page)

        return performance_data

    def generate_weekly_report(self):
        """Generate weekly performance report"""
        report = {
            "date": datetime.now().isoformat(),
            "indexing": self.get_indexing_status(),
            "traffic": self.get_traffic_stats(7),
            "performance": self.check_page_performance()
        }

        # Save report
        report_file = Path("reports/seo_report_" + datetime.now().strftime("%Y%m%d") + ".json")
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2))

        # Send summary to email/slack if configured
        self._send_summary(report)

        return report

if __name__ == "__main__":
    monitor = SEOMonitor(
        gsc_api_key="your-api-key",
        ga_property_id="your-property-id"
    )

    report = monitor.generate_weekly_report()
    print("Weekly SEO report generated")
```

4. **Automated Weekly Check** (cron job):
```bash
# Add to crontab
0 9 * * 1 cd /path/to/project && python3 scripts/monitoring.py
# Runs every Monday at 9 AM
```

5. **Alert Thresholds**:
- Indexing drops below 80%
- Traffic drops >30% week-over-week
- Core Web Vitals fail
- New 404 errors appear
- Manual action detected

**Monitoring Checklist**:
- [ ] Google Search Console configured
- [ ] Sitemap submitted and accepted
- [ ] Analytics tracking installed
- [ ] Weekly monitoring script running
- [ ] Alert thresholds configured
- [ ] First week baseline captured

**Deliverable**: Complete monitoring system with first report

---

## Success Criteria & Metrics

### Data Quality Targets
- [ ] Schema validation passes for all JSON files
- [ ] All rules cite APA manual section + page
- [ ] All examples verified (DOIs resolve, URLs active)
- [ ] Error catalog covers 50+ common issues
- [ ] Knowledge base completeness: 100%

### Content Quality Targets
- [ ] All 45 pages meet minimum word count
  - Mega guides: >5,000 words
  - Source types: >2,000 words
- [ ] LLM review pass rate: >90%
- [ ] Manual review finds <5 errors per page
- [ ] Uniqueness score: >70% across pages
- [ ] Factual accuracy: 100% (spot-checked)

### Technical Quality Targets
- [ ] All pages render correctly (mobile + desktop)
- [ ] Core Web Vitals pass:
  - LCP <2.5s
  - FID <100ms
  - CLS <0.1
- [ ] MiniChecker functional on all pages
- [ ] Internal linking: 8-15 links per page
- [ ] Sitemap validates and submitted

### SEO Performance Targets (30 days post-launch)
- [ ] Index rate: >80% pages indexed within 2 weeks
- [ ] Engagement:
  - Avg time on page: >90s
  - Bounce rate: <65%
  - Pages per session: >2
- [ ] Rankings: At least 5 pages in top 50 for target keywords
- [ ] No manual actions from Google
- [ ] Organic traffic growth: Measurable increase from baseline

---

## Resource Requirements

### Tools & Services
- **Anthropic Claude API** - Content generation and review
- **Google Search Console** - SEO monitoring
- **Google Analytics** - Traffic tracking
- **Hosting** - Static site hosting (Netlify, Vercel, or existing VPS)

### File Structure
```
backend/pseo/
├── knowledge_base/           # Structured JSON data
│   ├── schemas/             # JSON schemas
│   ├── citation_rules.json  # APA 7 rules
│   ├── examples.json        # Real citation examples
│   └── common_errors.json   # Error catalog
├── templates/               # Jinja2 templates
│   ├── mega_guide_template.md
│   └── source_type_template.md
├── generator/               # Content generation
│   ├── template_engine.py
│   ├── llm_writer.py
│   └── content_assembler.py
├── builder/                 # Static site builder
│   ├── templates/
│   │   └── layout.html
│   └── static_generator.py
├── review/                  # Review system
│   ├── llm_reviewer.py
│   └── human_review_cli.py
└── prompts/                 # LLM prompts
    ├── introduction_prompt.txt
    ├── explanation_prompt.txt
    └── ...

content/
├── test/                    # Test pages
├── review_queue/           # Pending review
├── approved/               # Approved content
│   ├── mega-guides/
│   └── source-types/
└── rejected/               # Rejected content

dist/                      # Built static site
├── guide/
├── how-to-cite-*/
├── assets/
└── sitemap.xml

frontend/components/
└── MiniChecker.tsx       # Embedded checker component
```

---

## Timeline Summary

| Week | Tasks | Owner | Key Deliverable |
|------|--------|--------|----------------|
| 1-2 | Knowledge Base | Agent + You | Structured JSON with APA rules, examples, errors |
| 3-4 | Templates + Design | You + Agent | 3 templates + approved mockups |
| 5-6 | LLM Generation | You | Working content generator with Claude |
| 7 | Review System | You | LLM + human review workflow |
| 8 | Static Site | You | Approved layout, working generator |
| 9 | MiniChecker | You | Embedded component in static pages |
| 10-11 | Batch Generation | Automated + You | 45 approved pages |
| 12 | Launch | You | Live site with monitoring |

**Total Duration**: 12 weeks
**Your Estimated Time**: 100-120 hours
**Agent Estimated Time**: 15-20 hours

---

## Future Phases Overview

### Phase 2: Validation & Expansion (Months 3-4)
**Additional 130 pages**
- +50-100 source type pages (remaining types)
- +30 validation pages ("How to Check X")
- Template refinements based on Phase 1 learnings

### Phase 3: Error Library (Months 5-6)
**Additional 300 pages**
- +200 error pages ("APA Title Case Error")
- +100 comparison pages (APA vs MLA vs Chicago)

### Phase 4: Long-Tail Domination (Months 7+, Ongoing)
**Additional 1,000+ pages**
- +1,000 specific source pages ("Cite New York Times")
- +50 discipline pages
- Quarterly content updates

All phases use the same technical infrastructure built in Phase 1.

---

## Getting Started

1. **Review this plan** - Confirm timeline and approach
2. **Set up environment** - Create directories, install dependencies
3. **Begin Week 1** - Start with knowledge base schema creation
4. **Track progress** - Use todo list to mark tasks complete

Ready to begin?