#!/usr/bin/env python3
"""
Preview scraped content from Purdue OWL pages
"""

import os
from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup
import re

def preview_content_from_page(url, page_name, max_examples=5):
    """Scrape and preview content from a specific page"""

    api_key = "LIBY0CW5QYMS826LW2M3YPF97V3RT7H7I89EFIISANIKDV5LWYF27N8K4JNPZA9AURXUJVRZYYQWARUR"
    client = ScrapingBeeClient(api_key=api_key)

    print(f"\n{'='*60}")
    print(f"PAGE: {page_name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        response = client.get(
            url,
            params={
                'render_js': True,
                'premium_proxy': True,
                'country_code': 'us'
            }
        )

        if response.status_code != 200:
            print(f"❌ Failed: HTTP {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find main content area
        main_content = soup.find('main') or soup.find('div', class_='main') or soup

        # Look for citation examples
        citation_examples = []

        # Search for common citation patterns
        citation_patterns = [
            r'\w+, \w+\. \(\d{4}\)\. .*?\.',
            r'\w+ & \w+, \w+\. \(\d{4}\)\. .*?\.',
            r'\(\w+, \d{4}\)\. .*?\.',
            r'_.*?_.*?\(\d{4}\)\.',
        ]

        for pattern in citation_patterns:
            matches = re.findall(pattern, main_content.get_text(), re.MULTILINE | re.DOTALL)
            for match in matches:
                if len(match.strip()) > 30 and len(match.strip()) < 200:
                    citation_examples.append(match.strip())

        # Also look for italics patterns (marked with underscores in APA)
        italic_pattern = r'_([^_]+)_'
        italic_matches = re.findall(italic_pattern, main_content.get_text())

        # Remove duplicates and limit examples
        unique_examples = list(set(citation_examples))[:max_examples]

        print(f"Total citation-like strings found: {len(citation_examples)}")
        print(f"Unique examples to show: {len(unique_examples)}")
        print(f"Italicized titles found: {len(italic_matches)}")

        if unique_examples:
            print(f"\n📝 CITATION EXAMPLES:")
            for i, example in enumerate(unique_examples, 1):
                print(f"{i}. {example}")
        else:
            print("❌ No clear citation examples found")

        # Show some italicized titles if found
        if italic_matches:
            print(f"\n📚 ITALICIZED TITLES (first {min(5, len(italic_matches))}):")
            for i, title in enumerate(italic_matches[:5], 1):
                print(f"{i}. _{title}_")

        # Show page structure
        print(f"\n🏗️  PAGE STRUCTURE:")
        headings = main_content.find_all(['h1', 'h2', 'h3', 'h4'])
        for heading in headings[:8]:
            print(f"  {heading.name.upper()}: {heading.get_text().strip()}")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    # Test a few key pages
    pages_to_test = [
        {
            'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html",
            'name': "Articles in Periodicals"
        },
        {
            'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_books.html",
            'name': "Books"
        },
        {
            'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_electronic_sources.html",
            'name': "Electronic Sources"
        }
    ]

    for page in pages_to_test:
        preview_content_from_page(page['url'], page['name'])