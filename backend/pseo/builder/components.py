"""
Component system for rendering reusable page elements with proper HTML structure and CSS classes.
"""

from typing import Dict, List, Any, Optional
import re


class ComponentRegistry:
    """Registry for managing page components"""

    def __init__(self):
        self.components = {
            'tldr_box': TLDRBoxComponent,
            'mini_checker': MiniCheckerComponent,
            'citation_example': CitationExampleComponent,
            'error_example': ErrorExampleComponent,
            'sidebar': SidebarComponent,
            'toc': TableOfContentsComponent,
            'meta_badges': MetaBadgesComponent,
            'checklist': ChecklistComponent,
            'faq': FAQComponent
        }

    def register(self, name: str, component_class):
        """Register a new component"""
        self.components[name] = component_class

    def render_component(self, name: str, kwargs: dict = None):
        """Render a component by name"""
        if kwargs is None:
            kwargs = {}
        if name not in self.components:
            raise KeyError(f"Unknown component: {name}")

        component = self.components[name]()
        return component.render(**kwargs)

    def has_component(self, name: str) -> bool:
        """Check if component exists"""
        return name in self.components


class TLDRBoxComponent:
    """TL;DR (Too Long; Didn't Read) summary box component"""

    def render(self, title: str = "⚡ TL;DR - Quick Summary",
               points: List[str] = None,
               key_takeaway: str = None,
               **kwargs) -> str:
        """Render TL;DR box with summary points"""

        if points is None:
            points = []

        # Build points list
        points_html = ""
        for point in points:
            points_html += f"<li>{point}</li>\n"

        # Build key takeaway
        takeaway_html = ""
        if key_takeaway:
            takeaway_html = f'<p style="margin-top: 1rem;"><strong>Key Takeaway:</strong> {key_takeaway}</p>'

        return f'''<div class="tldr-box" id="tldr">
<h2>{title}</h2>
<ul>
{points_html}</ul>
{takeaway_html}
</div>'''


class MiniCheckerComponent:
    """MiniChecker citation validation component"""

    def render(self,
               placeholder: str = "Enter your citation here...",
               context_type: str = "mega-guide",
               title: str = "🔍 Quick Check Your Citation",
               description: str = "Paste a single citation to instantly validate APA formatting",
               button_text: str = "Check Citation",
               **kwargs) -> str:
        """Render MiniChecker component with interactive form"""

        return f'''<div class="mini-checker">
<h4>{title}</h4>
<p>{description}</p>
<textarea placeholder="{placeholder}" name="citation" rows="4" style="width: 100%; border: 2px solid #e5e7eb; border-radius: 0.5rem; padding: 0.75rem; font-family: 'Courier New', Courier, monospace; font-size: 0.875rem; resize: vertical; min-height: 80px;"></textarea>
<button onclick="checkCitation(this)" style="width: 100%; background: #9333ea; color: white; border: none; padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; margin-top: 1rem; transition: all 0.2s; box-shadow: 0 4px 12px rgba(147, 51, 234, 0.3);">{button_text}</button>
</div>'''


class CitationExampleComponent:
    """Citation example component with proper formatting"""

    def render(self,
               citation: str,
               title: str = "Example",
               source_type: str = None,
               in_text_citations: List[Dict] = None,
               **kwargs) -> str:
        """Render citation example with proper formatting"""

        if in_text_citations is None:
            in_text_citations = []

        # Process citation to ensure proper formatting
        formatted_citation = self._format_citation(citation)

        # Build in-text citations
        in_text_html = ""
        if in_text_citations:
            in_text_html = "<strong>In-Text Citations:</strong>\n<ul>\n"
            for citation_item in in_text_citations:
                citation_type = citation_item.get('type', 'narrative').title()
                citation_text = citation_item.get('citation', '')
                in_text_html += f'<li><strong>{citation_type}:</strong> {citation_text}</li>\n'
            in_text_html += "</ul>\n"

        # Add source type if provided
        source_type_html = ""
        if source_type:
            source_type_html = f'<p><strong>Source Type:</strong> {source_type}</p>'

        return f'''<div class="example-box">
<div class="example-variation">{title}</div>
<div class="citation-example">
{formatted_citation}
</div>

{in_text_html}
{source_type_html}
</div>'''

    def _format_citation(self, citation: str) -> str:
        """Format citation with proper emphasis"""
        # Don't over-format - just return as-is for now
        # The mockup expects journal names to be italicized, but we'll keep it simple
        return citation


class ErrorExampleComponent:
    """Error/correction example component"""

    def render(self,
               error_name: str,
               wrong_example: str,
               correct_example: str,
               why_it_happens: str = None,
               fix_instructions: str = None,
               **kwargs) -> str:
        """Render error/correction pair with explanation"""

        explanation_html = ""
        if why_it_happens or fix_instructions:
            explanation_html = '<div class="explanation-box">\n'
            if why_it_happens:
                explanation_html += f'<h4>Why This Happens:</h4>\n<p>{why_it_happens}</p>\n'
            if fix_instructions:
                explanation_html += f'<h4>How to Avoid It:</h4>\n<p>{fix_instructions}</p>\n'
            explanation_html += '</div>\n'

        return f'''<div class="error-example">
<h4>❌ {error_name}</h4>
<div class="wrong-example">
{wrong_example}
</div>
</div>

<div class="correction-box">
<h4>✓ Correct Format:</h4>
<div class="correct-example">
{correct_example}
</div>
</div>

{explanation_html}'''


class SidebarComponent:
    """Sidebar component with related content"""

    def render(self,
               page_type: str = "mega_guide",
               related_guides: List[Dict] = None,
               quick_tools: List[Dict] = None,
               pro_tip: str = None,
               page_info: Dict = None,
               **kwargs) -> str:
        """Render complete sidebar with all sections"""

        if related_guides is None:
            related_guides = []
        if quick_tools is None:
            quick_tools = []
        if page_info is None:
            page_info = {}

        # Default content based on page type
        if page_type == "mega_guide" and not related_guides:
            related_guides = [
                {"title": "How to Cite Journal Articles", "url": "/how-to-cite-journal-article-apa/"},
                {"title": "Complete APA 7th Edition Guide", "url": "/guide/apa-7th-edition/"},
                {"title": "Common Citation Errors", "url": "/guide/common-citation-errors/"},
                {"title": "APA Reference List Format", "url": "/guide/apa-reference-list-format/"}
            ]

        if page_type == "mega_guide" and not quick_tools:
            quick_tools = [
                {"title": "Citation Checker", "url": "/checker/"},
                {"title": "Format Generator", "url": "/generator/"},
                {"title": "Style Comparison", "url": "/style-comparison/"}
            ]

        if not pro_tip:
            pro_tip = "Check your citations as you write, not all at once at the end. This saves time and prevents errors from accumulating."

        # Build sidebar sections
        sidebar_html = '<aside class="content-sidebar">\n'

        # Related Guides section
        if related_guides:
            sidebar_html += '<div class="related-resources">\n'
            sidebar_html += '<h3>Related Guides</h3>\n<ul>\n'
            for guide in related_guides:
                url = guide.get('url', '#')
                title = guide.get('title', 'Guide')
                sidebar_html += f'<li><a href="{url}">{title}</a></li>\n'
            sidebar_html += '</ul>\n</div>\n'

        # Quick Tools section
        if quick_tools:
            sidebar_html += '<div class="related-resources">\n'
            sidebar_html += '<h3>Quick Tools</h3>\n<ul>\n'
            for tool in quick_tools:
                url = tool.get('url', '#')
                title = tool.get('title', 'Tool')
                sidebar_html += f'<li><a href="{url}">{title}</a></li>\n'
            sidebar_html += '</ul>\n</div>\n'

        # Pro Tip section
        sidebar_html += '<div class="related-resources">\n'
        sidebar_html += '<h3>💡 Pro Tip</h3>\n'
        sidebar_html += f'<p>{pro_tip}</p>\n'
        sidebar_html += '</div>\n'

        # Page Info section (for mega guides)
        if page_type == "mega_guide" and page_info:
            sidebar_html += '<div class="related-resources">\n'
            sidebar_html += '<h3>Page Info</h3>\n'

            if 'word_count' in page_info:
                sidebar_html += f'<p><strong>Word count:</strong> {page_info["word_count"]}</p>\n'
            if 'reading_time' in page_info:
                sidebar_html += f'<p><strong>Reading time:</strong> {page_info["reading_time"]}</p>\n'
            if 'last_updated' in page_info:
                sidebar_html += f'<p><strong>Last updated:</strong> {page_info["last_updated"]}</p>\n'

            sidebar_html += '</div>\n'

        sidebar_html += '</aside>\n'

        return sidebar_html


class TableOfContentsComponent:
    """Table of contents component"""

    def render(self, sections: List[Dict] = None, **kwargs) -> str:
        """Render table of contents from sections"""

        if sections is None:
            sections = []

        toc_html = '<div class="toc">\n'
        toc_html += '<h2>📑 Table of Contents</h2>\n'
        toc_html += '<ol>\n'

        # Add all sections from sections list
        for section in sections:
            title = section.get('title', 'Section')
            slug = section.get('slug', self._slugify(title))
            toc_html += f'<li><a href="#{slug}">{title}</a></li>\n'

        toc_html += '</ol>\n'
        toc_html += '</div>\n'

        return toc_html

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'\s+', '-', text.lower())
        # Remove special characters except hyphens
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        return slug


class MetaBadgesComponent:
    """Meta badges component for hero section metadata"""

    def render(self,
               reading_time: str = None,
               last_updated: str = None,
               edition: str = None,
               **kwargs) -> str:
        """Render meta badges in hero section"""

        badges_html = '<div class="meta-info">\n'

        if reading_time:
            badges_html += f'<span>📖 Reading time: {reading_time}</span>\n'

        if last_updated:
            badges_html += f'<span>🔄 Last updated: {last_updated}</span>\n'

        if edition:
            badges_html += f'<span>✅ {edition}</span>\n'

        badges_html += '</div>\n'

        return badges_html


class ChecklistComponent:
    """Checklist component for validation steps"""

    def render(self, items: List[str] = None, title: str = "Validation Checklist", **kwargs) -> str:
        """Render checklist with validation items"""

        if items is None:
            items = []

        checklist_html = '<div class="checklist">\n'
        checklist_html += f'<p>Use this checklist to {title.lower()}:</p>\n'
        checklist_html += '<ul>\n'

        for item in items:
            checklist_html += f'<li>{item}</li>\n'

        checklist_html += '</ul>\n'
        checklist_html += '</div>\n'

        return checklist_html


class FAQComponent:
    """FAQ component for questions and answers"""

    def render(self, faqs: List[Dict] = None, **kwargs) -> str:
        """Render FAQ section with questions and answers"""

        if faqs is None:
            faqs = []

        faq_html = ''

        for faq in faqs:
            question = faq.get('question', '')
            answer = faq.get('answer', '')

            faq_html += '<div class="faq-item">\n'
            faq_html += f'<div class="faq-question">{question}</div>\n'
            faq_html += f'<div class="faq-answer">{answer}</div>\n'
            faq_html += '</div>\n\n'

        return faq_html