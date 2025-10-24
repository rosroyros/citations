#!/usr/bin/env python3
"""
Comprehensive scraping of all Purdue OWL APA citation examples
"""

import os
import json
import re
from datetime import datetime
from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup

class PurdueCitationScraper:
    def __init__(self, api_key):
        self.client = ScrapingBeeClient(api_key=api_key)
        self.all_citations = []
        self.citation_id_counter = 1

    def scrape_page(self, url, page_name, source_type):
        """Scrape citations from a single Purdue OWL page"""

        print(f"\n{'='*60}")
        print(f"SCRAPING: {page_name}")
        print(f"URL: {url}")
        print(f"Source Type: {source_type}")
        print(f"{'='*60}")

        try:
            response = self.client.get(
                url,
                params={
                    'render_js': True,
                    'premium_proxy': True,
                    'country_code': 'us'
                }
            )

            if response.status_code != 200:
                print(f"❌ Failed: HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.find('main') or soup.find('div', class_='main') or soup

            citations = self.extract_citations_from_content(main_content, url, page_name, source_type)

            print(f"✅ Extracted {len(citations)} citations from {page_name}")
            return citations

        except Exception as e:
            print(f"❌ Error scraping {page_name}: {type(e).__name__}: {e}")
            return []

    def extract_citations_from_content(self, content, url, page_name, source_type):
        """Extract citation examples from page content"""

        citations = []

        # Method 1: Look for code blocks and blockquotes
        code_blocks = content.find_all(['code', 'pre', 'blockquote'])
        for block in code_blocks:
            text = block.get_text().strip()
            if self.is_valid_citation(text):
                citations.append(text)

        # Method 2: Look for paragraphs following "Example" text
        example_paragraphs = content.find_all(['p', 'div'], string=re.compile(r'example|Example', re.I))
        for example_p in example_paragraphs:
            # Check following elements
            next_elements = example_p.find_next_siblings(['p', 'div', 'blockquote'])[:3]
            for elem in next_elements:
                text = elem.get_text().strip()
                if self.is_valid_citation(text):
                    citations.append(text)

        # Method 3: Look for paragraphs with citation patterns
        paragraphs = content.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if self.is_valid_citation(text):
                citations.append(text)

        # Method 4: Look for list items that might contain citations
        list_items = content.find_all('li')
        for li in list_items:
            text = li.get_text().strip()
            if self.is_valid_citation(text):
                citations.append(text)

        # Clean and deduplicate
        unique_citations = []
        seen = set()

        for citation in citations:
            # Normalize spacing
            citation = re.sub(r'\s+', ' ', citation).strip()

            # Additional validation
            if len(citation) < 40 or 'click here' in citation.lower():
                continue

            if citation not in seen:
                seen.add(citation)

                # Convert to JSONL format
                citation_data = {
                    "citation_id": f"purdue_{page_name.lower().replace(' ', '_')}_{self.citation_id_counter:03d}",
                    "citation_text": citation,
                    "source_type": source_type,
                    "is_valid": True,
                    "metadata": {
                        "source": "Purdue OWL",
                        "url": url,
                        "section": page_name,
                        "date_collected": datetime.now().isoformat(),
                        "formatting_preserved": True,
                        "verified_against_kb": False
                    }
                }

                unique_citations.append(citation_data)
                self.citation_id_counter += 1

        return unique_citations

    def is_valid_citation(self, text):
        """Check if text looks like a valid APA citation"""

        # Must have year in parentheses
        if not re.search(r'\(\d{4}\)', text):
            return False

        # Must have author format (Name, I.)
        if not re.search(r'[A-Z][a-z]+, [A-Z]\.?\s*\(\d{4}\)', text):
            return False

        # Must have some kind of source indicator (journal, publisher, etc.)
        source_indicators = [
            r'\w+\s+Press',
            r'\w+,\s+\d+\(\d+\)',
            r'\w+,\s+\d+\(\d+\),\s+\d+-\d+',
            r'University',
            r'Publishing',
            r'&',
            r'eds?\.'
        ]

        has_source_indicator = any(re.search(pattern, text, re.I) for pattern in source_indicators)

        # Reasonable length check
        if len(text) < 30 or len(text) > 500:
            return False

        # Filter out obvious non-citations
        exclude_phrases = [
            'click here',
            'for more information',
            'see also',
            'example',
            'note:',
            'available at'
        ]

        if any(phrase in text.lower() for phrase in exclude_phrases):
            return False

        return has_source_indicator

    def scrape_all_pages(self):
        """Scrape all target Purdue OWL pages"""

        # Define all pages to scrape
        pages = [
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html",
                'name': "Articles in Periodicals",
                'source_type': "journal article"
            },
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_books.html",
                'name': "Books",
                'source_type': "book"
            },
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_electronic_sources.html",
                'name': "Electronic Sources",
                'source_type': "webpage"
            },
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_audiovisual_media.html",
                'name': "Audiovisual Media",
                'source_type': "other"
            },
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_other_print_sources.html",
                'name': "Other Print Sources",
                'source_type': "other"
            },
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_other_non_print_sources.html",
                'name': "Other Non-Print Sources",
                'source_type': "other"
            }
        ]

        all_citations = []

        for page in pages:
            citations = self.scrape_page(page['url'], page['name'], page['source_type'])
            all_citations.extend(citations)

        return all_citations

    def save_citations(self, citations, filename):
        """Save citations to JSONL file"""

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            for citation in citations:
                f.write(json.dumps(citation, ensure_ascii=False) + '\n')

        print(f"✅ Saved {len(citations)} citations to {filename}")

def main():
    """Main execution function"""

    api_key = "LIBY0CW5QYMS826LW2M3YPF97V3RT7H7I89EFIISANIKDV5LWYF27N8K4JNPZA9AURXUJVRZYYQWARUR"

    scraper = PurdueCitationScraper(api_key)

    print("🔍 Starting comprehensive Purdue OWL citation scraping...")

    # Scrape all pages
    citations = scraper.scrape_all_pages()

    # Save results
    output_file = "backend/pseo/optimization/datasets/valid_citations_scraped_new.jsonl"
    scraper.save_citations(citations, output_file)

    # Print summary
    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total citations extracted: {len(citations)}")

    # Type breakdown
    type_counts = {}
    for citation in citations:
        source_type = citation['source_type']
        type_counts[source_type] = type_counts.get(source_type, 0) + 1

    print("\nCitation types:")
    for source_type, count in sorted(type_counts.items()):
        print(f"  {source_type}: {count}")

    # Show first few examples
    print(f"\nFirst 3 citation examples:")
    for i, citation in enumerate(citations[:3], 1):
        print(f"{i}. {citation['citation_text']}")
        print(f"   Type: {citation['source_type']}")
        print(f"   ID: {citation['citation_id']}")

if __name__ == "__main__":
    main()