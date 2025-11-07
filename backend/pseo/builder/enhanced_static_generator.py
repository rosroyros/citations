"""
Enhanced Static Site Generator with CSS preservation and semantic HTML structure.
"""

import logging
import markdown
import yaml
import re
from jinja2 import Template
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

from .components import ComponentRegistry

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EnhancedStaticSiteGenerator:
    """Enhanced markdown to HTML converter with CSS preservation and semantic structure"""

    def __init__(self, layout_template: str, base_url: str = "https://citationchecker.com"):
        """
        Initialize enhanced generator with layout template

        Args:
            layout_template: Jinja2 template string for page layout
            base_url: Base URL for the site
        """
        self.layout = Template(layout_template)
        self.base_url = base_url.rstrip('/')
        self.component_registry = ComponentRegistry()
        logger.info(f"EnhancedStaticSiteGenerator initialized with base_url={self.base_url}")

    def convert_markdown_to_html(self, md_content: str) -> str:
        """
        Convert markdown to HTML with CSS preservation and semantic structure

        Args:
            md_content: Markdown content string

        Returns:
            Enhanced HTML string with semantic structure
        """
        logger.debug(f"Converting enhanced markdown to HTML ({len(md_content)} chars)")

        # Extract and remove front matter first
        front_matter, content = self._extract_front_matter(md_content)
        logger.debug(f"Extracted front matter: {list(front_matter.keys())}")

        # First, process custom component syntax
        processed_content = self._process_custom_components(content)

        # Convert markdown to HTML without TOC extension (we'll build it manually)
        md = markdown.Markdown(extensions=[
            'extra',  # Includes tables, fenced_code, and allows HTML
            'nl2br',
            'sane_lists'
        ])

        html = md.convert(processed_content)
        logger.debug(f"Markdown converted to HTML ({len(html)} chars)")

        # Enhance with semantic structure
        enhanced_html = self._add_semantic_structure(html)

        # Process MiniChecker placeholders
        enhanced_html = self._process_minichecker_placeholders(enhanced_html)

        logger.debug(f"Enhanced HTML generated ({len(enhanced_html)} chars)")
        return enhanced_html

    def _process_custom_components(self, content: str) -> str:
        """
        Process custom component syntax like {% tldr_box %}

        Args:
            content: Content with custom component syntax

        Returns:
            Content with components rendered as HTML
        """
        logger.debug("Processing custom components")

        # Process TL;DR boxes
        content = self._process_tldr_boxes(content)

        # Process citation examples
        content = self._process_citation_examples(content)

        # Process error examples
        content = self._process_error_examples(content)

        # Process checklists
        content = self._process_checklists(content)

        # Process FAQs
        content = self._process_faqs(content)

        return content

    def _process_tldr_boxes(self, content: str) -> str:
        """Process {% tldr_box %} components"""
        pattern = r'{%\s*tldr_box\s*(.*?)\s*%}(.*?){%\s*endtldr_box\s*%}'

        def replace_tldr(match):
            args_str = match.group(1)
            box_content = match.group(2).strip()

            # Parse arguments
            args = self._parse_component_args(args_str)

            # Extract points from content
            points = []
            for line in box_content.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    points.append(line[2:])

            # Extract key takeaway if present
            key_takeaway = None
            if 'Key Takeaway:' in box_content:
                takeaway_line = [line for line in box_content.split('\n') if 'Key Takeaway:' in line][0]
                key_takeaway = takeaway_line.replace('**Key Takeaway:**', '').strip()

            # Render component
            return self.component_registry.render_component('tldr_box', {
                'title': args.get('title', 'TL;DR - Quick Summary'),
                'points': points,
                'key_takeaway': key_takeaway
            })

        return re.sub(pattern, replace_tldr, content, flags=re.DOTALL)

    def _process_citation_examples(self, content: str) -> str:
        """Process citation example components"""
        # This is a simplified version - in production you'd have more sophisticated parsing
        return content  # Placeholder for future implementation

    def _process_error_examples(self, content: str) -> str:
        """Process error example components"""
        # This is a simplified version - in production you'd have more sophisticated parsing
        return content  # Placeholder for future implementation

    def _process_checklists(self, content: str) -> str:
        """Process checklist components"""
        # This is a simplified version - in production you'd have more sophisticated parsing
        return content  # Placeholder for future implementation

    def _process_faqs(self, content: str) -> str:
        """Process FAQ components"""
        # This is a simplified version - in production you'd have more sophisticated parsing
        return content  # Placeholder for future implementation

    def _parse_component_args(self, args_str: str) -> Dict[str, str]:
        """Parse component arguments like title="TL;DR" """
        args = {}
        if args_str:
            # Simple regex-based parsing for title="value" format
            pattern = r'(\w+)=["\']([^"\']+)["\']'
            matches = re.findall(pattern, args_str)
            for key, value in matches:
                args[key] = value
        return args

    def _add_semantic_structure(self, html: str) -> str:
        """
        Add semantic HTML structure to markdown-generated content

        Args:
            html: Basic HTML from markdown conversion

        Returns:
            Enhanced HTML with semantic structure
        """
        logger.debug("Adding semantic structure to HTML")

        # Add IDs to headings without making them links
        html = self._add_heading_ids(html)

        # Wrap h2 headers in semantic sections
        html = self._wrap_headers_in_sections(html, level=2)

        # Add proper CSS classes to common elements
        html = self._add_css_classes(html)

        return html

    def _wrap_headers_in_sections(self, html: str, level: int = 2) -> str:
        """
        Wrap headers of specified level in semantic sections

        Args:
            html: HTML content
            level: Header level to wrap (1-6)

        Returns:
            HTML with headers wrapped in sections
        """
        header_pattern = f'<h{level}([^>]*)id="([^"]*)"([^>]*)>(.*?)</h{level}>'

        def wrap_header(match):
            attrs_before = match.group(1)
            section_id = match.group(2)
            attrs_after = match.group(3)
            header_text = match.group(4)

            # Special handling for TL;DR section - don't wrap it, the heading is already inside the tldr-box
            # Check for multiple variations of TL;DR text
            tldr_indicators = ["tl;dr", "tldr", "quick summary", "summary"]
            header_text_lower = header_text.lower()

            if any(indicator in header_text_lower for indicator in tldr_indicators):
                return match.group(0)  # Return the original header without wrapping

            # Create semantic section
            section_class = "content-section"
            if section_id and any(indicator in section_id.lower() for indicator in tldr_indicators):
                section_class += " tldr-section"

            return f'''<section class="{section_class}" id="{section_id}">
<h{level}{attrs_before}{attrs_after}>{header_text}</h{level}>'''

        # Wrap all headers of specified level
        wrapped_html = re.sub(header_pattern, wrap_header, html)

        # Close sections before next ## header or end of content
        lines = wrapped_html.split('\n')
        result_lines = []
        open_sections = 0

        for i, line in enumerate(lines):
            # Check if this line starts a new section
            if re.match(r'<section class="content-section"', line):
                # Close previous section if open
                if open_sections > 0:
                    result_lines.append('</section>')
                open_sections += 1

            result_lines.append(line)

        # Close any remaining open sections
        if open_sections > 0:
            result_lines.append('</section>')

        return '\n'.join(result_lines)

    def _add_css_classes(self, html: str) -> str:
        """
        Add appropriate CSS classes to HTML elements

        Args:
            html: HTML content

        Returns:
            HTML with CSS classes added
        """
        # Add classes to existing elements
        html = re.sub(r'<div class="hero">', '<div class="hero">', html)  # Already has class

        # Ensure proper class names for common patterns
        html = re.sub(r'<table>', '<table class="comparison-table">', html)
        html = re.sub(r'<blockquote>', '<blockquote class="citation-example">', html)

        return html

    def _add_heading_ids(self, html: str) -> str:
        """
        Add ID attributes to headings for anchor links

        Args:
            html: HTML content

        Returns:
            HTML with IDs added to headings
        """
        def add_id(match):
            level = match.group(1)
            text = match.group(2)
            # Generate ID from text
            heading_id = re.sub(r'\s+', '-', text.lower())
            heading_id = re.sub(r'[^a-z0-9-]', '', heading_id)
            return f'<h{level} id="{heading_id}">{text}</h{level}>'

        # Add IDs to h2 and h3 headings
        html = re.sub(r'<h([23])>([^<]+)</h\1>', add_id, html)
        return html

    def _process_minichecker_placeholders(self, html: str) -> str:
        """
        Convert MiniChecker placeholder divs to actual components

        Args:
            html: HTML with placeholder divs

        Returns:
            HTML with actual MiniChecker components
        """
        logger.debug("Processing MiniChecker placeholders")

        # Pattern to match placeholder divs
        placeholder_pattern = r'<div class="cta-placement"[^>]*id="([^"]*)"[^>]*>.*?</div>'

        def replace_placeholder(match):
            placeholder_id = match.group(0)
            div_id_match = re.search(r'id="([^"]*)"', placeholder_id)
            div_id = div_id_match.group(1) if div_id_match else 'mini-checker-1'

            # Determine context and content based on ID
            if 'intro' in div_id:
                title = "🔍 Quick Check Your Citation"
                description = "Paste a single citation to instantly validate APA formatting"
                placeholder = "Smith, J. A. (2020). Article title goes here. Journal Name, 15(2), 123-145. https://doi.org/10.1234/example"
            elif 'test' in div_id:
                title = "🔍 Test What You've Learned"
                description = "Try checking one of your own citations"
                placeholder = "Paste your citation here..."
            else:
                title = "🔍 Quick Check Your Citation"
                description = "Validate APA formatting instantly"
                placeholder = "Enter your citation here..."

            # Render MiniChecker component
            return self.component_registry.render_component('mini_checker', {
                'title': title,
                'description': description,
                'placeholder': placeholder,
                'context_type': "mega-guide"
            })

        # Replace all placeholders
        enhanced_html = re.sub(placeholder_pattern, replace_placeholder, html, flags=re.DOTALL)

        return enhanced_html

    def apply_layout(self, html_content: str, metadata: dict) -> str:
        """
        Wrap content in layout template

        Args:
            html_content: HTML content string
            metadata: Page metadata dict

        Returns:
            Complete HTML page string
        """
        logger.debug(f"Applying layout with metadata: {list(metadata.keys())}")

        # Add base_url to metadata for template
        template_data = {**metadata, 'base_url': self.base_url}

        # Add sidebar content if it's a mega guide
        if metadata.get('page_type') == 'mega_guide':
            template_data['sidebar_content'] = self._generate_sidebar_content(metadata)

        result = self.layout.render(content=html_content, **template_data)

        logger.debug(f"Layout applied, final size: {len(result)} chars")
        return result

    def _generate_sidebar_content(self, metadata: dict) -> str:
        """
        Generate sidebar content for mega guide pages

        Args:
            metadata: Page metadata

        Returns:
            Sidebar HTML content
        """
        # Sidebar content matching mockup design with proper CSS classes
        sidebar_html = """
<aside class="sidebar">
    <div class="sidebar-section">
        <h3>Related Guides</h3>
        <ul>
            <li><a href="/how-to-cite-journal-article-apa/">📄 APA 7th Edition Guide</a></li>
            <li><a href="/how-to-cite-journal-article-apa/">📰 Journal Articles</a></li>
            <li><a href="/how-to-cite-book-apa/">📖 Books in APA</a></li>
            <li><a href="/how-to-cite-website-apa/">🌐 Websites in APA</a></li>
        </ul>
    </div>

    <div class="sidebar-section">
        <h3>Quick Tools</h3>
        <ul>
            <li><a href="/">Citation Checker</a></li>
            <li><a href="/generator/">Format Generator</a></li>
            <li><a href="/tools/style-comparison/">Style Comparison</a></li>
        </ul>
    </div>

    <div class="sidebar-section sidebar-pro-tip">
        <h3>💡 Pro Tip</h3>
        <p>Check your citations as you write, not all at once at the end. This saves time and prevents errors from accumulating.</p>
    </div>

    <div class="sidebar-section">
        <h3>Page Info</h3>
        <p><strong>Word count:</strong> {word_count}</p>
        <p><strong>Reading time:</strong> {reading_time}</p>
        <p><strong>Last updated:</strong> {last_updated}</p>
    </div>
</aside>
        """.format(
            word_count=metadata.get('word_count', 'Unknown'),
            reading_time=metadata.get('reading_time', 'Unknown'),
            last_updated=metadata.get('last_updated', 'Unknown')
        )

        return sidebar_html

    def generate_url_structure(self, page_type: str, page_name: str) -> str:
        """
        Create SEO-friendly URLs per spec

        Args:
            page_type: Type of page (mega_guide, source_type, other)
            page_name: URL slug for page

        Returns:
            URL path string
        """
        if page_type == "mega_guide":
            url = f"/guide/{page_name}/"
        elif page_type == "source_type":
            url = f"/how-to-cite-{page_name}-apa/"
        else:
            url = f"/{page_name}/"

        logger.debug(f"Generated URL: {url} for type={page_type}, name={page_name}")
        return url

    def generate_sitemap(self, pages: List[Dict]) -> str:
        """
        Create XML sitemap for all pages

        Args:
            pages: List of page dicts with url, lastmod, priority

        Returns:
            XML sitemap string
        """
        logger.info(f"Generating sitemap for {len(pages)} pages")

        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

        for page in pages:
            sitemap += f"""  <url>
    <loc>{self.base_url}{page['url']}</loc>
    <lastmod>{page['lastmod']}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{page['priority']}</priority>
  </url>
"""

        sitemap += '</urlset>'

        logger.info("Sitemap generated successfully")
        return sitemap

    def _extract_front_matter(self, md_content: str) -> Tuple[Dict, str]:
        """
        Extract YAML front matter from markdown

        Args:
            md_content: Markdown content with optional front matter

        Returns:
            Tuple of (front_matter_dict, content_string)
        """
        lines = md_content.split('\n')

        # Check for front matter
        if not lines or lines[0].strip() != '---':
            logger.debug("No front matter found")
            return {}, md_content

        # Find end of front matter
        try:
            end_idx = lines[1:].index('---') + 1
        except ValueError:
            logger.warning("Front matter not properly closed")
            return {}, md_content

        # Extract and parse front matter
        front_matter_text = '\n'.join(lines[1:end_idx])
        content = '\n'.join(lines[end_idx + 1:])

        try:
            front_matter = yaml.safe_load(front_matter_text) or {}
            logger.debug(f"Extracted front matter: {list(front_matter.keys())}")
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse front matter: {e}")
            front_matter = {}

        return front_matter, content

    def build_site(self, input_dir: str, output_dir: str) -> None:
        """
        Convert all markdown files to HTML with enhanced processing

        Args:
            input_dir: Directory containing markdown files
            output_dir: Directory to write HTML files
        """
        logger.info(f"Building enhanced site from {input_dir} to {output_dir}")

        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        pages = []
        processed_count = 0
        error_count = 0

        for md_file in input_path.glob("**/*.md"):
            try:
                logger.info(f"Processing enhanced: {md_file.name}")

                # Read markdown
                md_content = md_file.read_text(encoding='utf-8')

                # Extract front matter
                front_matter, content = self._extract_front_matter(md_content)

                # Skip if missing required fields
                if not all(k in front_matter for k in ['page_type', 'url_slug']):
                    logger.warning(f"Skipping {md_file.name}: missing required front matter")
                    error_count += 1
                    continue

                # Convert to enhanced HTML
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
                output_file.write_text(final_html, encoding='utf-8')
                logger.info(f"Enhanced HTML written: {output_file}")

                # Track for sitemap
                page_type = front_matter['page_type']
                # Set priority based on page type
                if page_type == 'mega_guide':
                    priority = '0.7'
                elif page_type == 'validation':
                    priority = '0.6'
                elif page_type == 'source_type':
                    priority = '0.6'
                else:
                    priority = '0.5'

                pages.append({
                    'url': url,
                    'lastmod': front_matter.get('last_updated', datetime.now().strftime('%Y-%m-%d')),
                    'priority': priority
                })

                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing {md_file.name}: {e}", exc_info=True)
                error_count += 1
                continue

        # Generate sitemap
        if pages:
            sitemap = self.generate_sitemap(pages)
            sitemap_file = output_path / "sitemap.xml"
            sitemap_file.write_text(sitemap, encoding='utf-8')
            logger.info(f"Enhanced sitemap written: {sitemap_file}")

        logger.info(f"Enhanced build complete: {processed_count} pages generated, {error_count} errors")