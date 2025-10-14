"""Static Site Generator for PSEO pages"""
import logging
import markdown
import yaml
from jinja2 import Template
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class StaticSiteGenerator:
    """Converts markdown content to HTML static site"""

    def __init__(self, layout_template: str, base_url: str = "https://yoursite.com"):
        """
        Initialize generator with layout template

        Args:
            layout_template: Jinja2 template string for page layout
            base_url: Base URL for the site (e.g., "https://example.com")
        """
        self.layout = Template(layout_template)
        self.base_url = base_url.rstrip('/')  # Remove trailing slash
        logger.info(f"StaticSiteGenerator initialized with base_url={self.base_url}")

    def convert_markdown_to_html(self, md_content: str) -> str:
        """
        Convert markdown to HTML with extensions

        Args:
            md_content: Markdown content string

        Returns:
            HTML string
        """
        logger.debug(f"Converting markdown to HTML ({len(md_content)} chars)")

        md = markdown.Markdown(extensions=[
            'extra',  # Includes tables, fenced_code, and allows HTML
            'toc',
            'nl2br',
            'sane_lists'
        ])

        html = md.convert(md_content)
        logger.debug(f"Converted to HTML ({len(html)} chars)")

        return html

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
        result = self.layout.render(content=html_content, **template_data)

        logger.debug(f"Layout applied, final size: {len(result)} chars")
        return result

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
        Convert all markdown files to HTML

        Args:
            input_dir: Directory containing markdown files
            output_dir: Directory to write HTML files
        """
        logger.info(f"Building site from {input_dir} to {output_dir}")

        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        pages = []
        processed_count = 0
        error_count = 0

        for md_file in input_path.glob("**/*.md"):
            try:
                logger.info(f"Processing: {md_file.name}")

                # Read markdown
                md_content = md_file.read_text(encoding='utf-8')

                # Extract front matter
                front_matter, content = self._extract_front_matter(md_content)

                # Skip if missing required fields
                if not all(k in front_matter for k in ['page_type', 'url_slug']):
                    logger.warning(f"Skipping {md_file.name}: missing required front matter")
                    error_count += 1
                    continue

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
                output_file.write_text(final_html, encoding='utf-8')
                logger.info(f"Written: {output_file}")

                # Track for sitemap
                pages.append({
                    'url': url,
                    'lastmod': front_matter.get('last_updated', datetime.now().strftime('%Y-%m-%d')),
                    'priority': '0.7' if front_matter['page_type'] == 'mega_guide' else '0.6'
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
            logger.info(f"Sitemap written: {sitemap_file}")

        logger.info(f"Build complete: {processed_count} pages generated, {error_count} errors")


if __name__ == "__main__":
    # Example usage
    layout_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
</head>
<body>
    {{ content | safe }}
</body>
</html>"""

    generator = StaticSiteGenerator(layout_template)
    print("StaticSiteGenerator ready. Call build_site() to generate HTML.")
