"""
MLA 9th Edition Static Site Generator

Extends EnhancedStaticSiteGenerator to create MLA-specific PSEO pages with:
- Data-attribute mini-checker configuration
- Cross-style linking banners
- MLA-specific sidebar content
- MLA 9th Edition schema markup
"""

import logging
from typing import Dict
from enhanced_static_generator import EnhancedStaticSiteGenerator

logger = logging.getLogger(__name__)


class MLAStaticSiteGenerator(EnhancedStaticSiteGenerator):
    """Generator for MLA 9th Edition PSEO pages"""

    STYLE = "mla9"
    STYLE_NAME = "MLA 9th Edition"
    STYLE_DISPLAY = "MLA 9"

    def _get_minichecker_config(self, context: str) -> dict:
        """
        Get MLA-specific mini-checker configuration

        Args:
            context: Page context (e.g., 'book', 'website', 'youtube')

        Returns:
            Dict with style and placeholder for MLA
        """
        # MLA citation format examples
        placeholders = {
            'book': 'Morrison, Toni. *Beloved*. Knopf, 1987.',
            'website': 'Smith, John. "Article Title." *Website Name*, 15 Jan. 2020, www.example.com/article.',
            'journal': 'Johnson, Mary. "Article Title." *Journal Name*, vol. 15, no. 2, 2020, pp. 123-145.',
            'youtube': 'Username. "Video Title." *YouTube*, 15 Jan. 2020, www.youtube.com/watch?v=example.',
            'newspaper': 'Brown, Sarah. "Article Title." *The New York Times*, 15 Jan. 2020, p. A1.',
            'default': 'Author Last Name, First Name. "Title of Source." *Title of Container*, Other contributors, Version, Number, Publisher, Publication Date, Location.'
        }

        placeholder = placeholders.get(context, placeholders['default'])

        return {
            "style": "mla9",
            "placeholder": placeholder
        }

    def _generate_cross_style_banner(self, source_id: str) -> str:
        """
        Generate cross-style linking banner (MLA -> APA)

        Args:
            source_id: Source identifier (e.g., 'youtube', 'book')

        Returns:
            HTML banner with link to APA version
        """
        apa_url = f"/cite-{source_id}-apa/"

        return f'''<div class="style-alternate" style="background: #f0f9ff; border: 2px solid #0ea5e9; border-radius: 0.5rem; padding: 1rem; margin: 1.5rem 0; text-align: center;">
    <strong>Need APA format instead?</strong>
    <a href="{apa_url}" style="color: #0ea5e9; font-weight: 600; text-decoration: underline;">View APA 7 version →</a>
</div>'''

    def _process_minichecker_placeholders(self, html: str) -> str:
        """
        Convert MiniChecker placeholder divs to MLA-configured components

        Args:
            html: HTML with placeholder divs

        Returns:
            HTML with MLA mini-checker components using data attributes
        """
        logger.debug("Processing MiniChecker placeholders for MLA")

        import re

        # Pattern to match placeholder divs
        placeholder_pattern = r'<div class="cta-placement"[^>]*id="([^"]*)"[^>]*>.*?</div>'

        def replace_placeholder(match):
            placeholder_id = match.group(0)
            div_id_match = re.search(r'id="([^"]*)"', placeholder_id)
            div_id = div_id_match.group(1) if div_id_match else 'mini-checker-1'

            # Determine context and content based on ID
            if 'intro' in div_id:
                title = "🔍 Quick Check Your Citation"
                description = "Paste a single citation to instantly validate MLA 9 formatting"
                placeholder = "Morrison, Toni. *Beloved*. Knopf, 1987."
            elif 'test' in div_id:
                title = "🔍 Test What You've Learned"
                description = "Try checking one of your own MLA citations"
                placeholder = "Paste your MLA citation here..."
            else:
                title = "🔍 Quick Check Your Citation"
                description = "Validate MLA 9 formatting instantly"
                placeholder = "Enter your MLA citation here..."

            # Render MiniChecker with data-style attribute for resilient config
            return f'''<div class="mini-checker" data-style="mla9">
<h4>{title}</h4>
<p>{description}</p>
<textarea placeholder="{placeholder}" name="citation" rows="4" style="width: 100%; border: 2px solid #e5e7eb; border-radius: 0.5rem; padding: 0.75rem; font-family: 'Courier New', Courier, monospace; font-size: 0.875rem; resize: vertical; min-height: 80px;"></textarea>
<button onclick="checkCitation(this)" style="width: 100%; background: #9333ea; color: white; border: none; padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; margin-top: 1rem; transition: all 0.2s; box-shadow: 0 4px 12px rgba(147, 51, 234, 0.3);">Check Citation</button>
</div>'''

        # Replace all placeholders
        enhanced_html = re.sub(placeholder_pattern, replace_placeholder, html, flags=re.DOTALL)

        return enhanced_html

    def generate_url_structure(self, page_type: str, page_name: str) -> str:
        """
        Create MLA-specific SEO-friendly URLs

        Args:
            page_type: Type of page (mega_guide, source_type, specific_source)
            page_name: URL slug for page (from config)

        Returns:
            URL path string for MLA page
        """
        if page_type == "mega_guide":
            # Mega guide slugs are already complete (e.g., "mla-9th-edition")
            # URL pattern: /guide/[slug]/
            url = f"/guide/{page_name}/"
        elif page_type == "source_type":
            # Source type slugs may have -mla suffix (e.g., "book-mla")
            # Remove -mla suffix if present to avoid duplication
            base_name = page_name.replace("-mla", "") if page_name.endswith("-mla") else page_name
            url = f"/how-to-cite-{base_name}-mla/"
        elif page_type == "specific_source":
            # Specific source uses id (e.g., "youtube")
            url = f"/cite-{page_name}-mla/"
        else:
            url = f"/{page_name}/"

        logger.debug(f"Generated MLA URL: {url} for type={page_type}, name={page_name}")
        return url

    def apply_layout(self, html_content: str, metadata: dict) -> str:
        """
        Apply layout with MLA-specific enhancements

        Args:
            html_content: HTML content string
            metadata: Page metadata dict

        Returns:
            Complete HTML page with MLA enhancements
        """
        # Add cross-style banner if this is a specific source page
        if metadata.get('page_type') == 'specific_source' and metadata.get('source_id'):
            source_id = metadata['source_id']
            banner = self._generate_cross_style_banner(source_id)
            # Insert banner after first paragraph or heading
            import re
            html_content = re.sub(r'(</h1>.*?</p>)', r'\1' + banner, html_content, count=1, flags=re.DOTALL)

        # Add MLA-specific metadata
        metadata['citation_style'] = self.STYLE
        metadata['citation_style_name'] = self.STYLE_NAME
        metadata['citation_style_display'] = self.STYLE_DISPLAY

        # Add MLA-specific analytics
        metadata['analytics_props'] = {
            'citation_style': 'mla9',
            'page_type': metadata.get('page_type', 'unknown')
        }

        # Call parent apply_layout (uses default template sidebar)
        return super().apply_layout(html_content, metadata)

    def generate_schema_markup(self, metadata: dict) -> dict:
        """
        Generate MLA-specific schema.org markup

        Args:
            metadata: Page metadata

        Returns:
            Schema.org JSON-LD dict
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": metadata.get('title', ''),
            "description": metadata.get('meta_description', ''),
            "author": {
                "@type": "Organization",
                "name": "Citation Format Checker"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Citation Format Checker",
                "url": self.base_url
            },
            "datePublished": metadata.get('date_published', ''),
            "dateModified": metadata.get('last_updated', ''),
            "about": {
                "@type": "Thing",
                "name": "MLA 9th Edition Citation Format"
            },
            "keywords": "MLA 9, MLA citation, citation format, bibliography, works cited"
        }

        return schema
