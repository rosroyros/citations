#!/usr/bin/env python3
"""
Alternative scraper for APA citations with different sources and methods
"""

import os
import json
import re
from datetime import datetime
from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup

class AlternativeAPAScraper:
    def __init__(self, api_key):
        self.client = ScrapingBeeClient(api_key)
        self.citation_counter = 1

    def scrape_alternative_sources(self):
        """Scrape alternative APA citation sources"""

        # Try different academic sources that might have APA examples
        sources = [
            {
                'name': 'Purdue OWL - Additional Pages',
                'urls': [
                    "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/in_text_citations_author_date.html",
                    "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_basic_rules.html",
                    "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_author_authors.html"
                ]
            },
            {
                'name': 'University Writing Centers',
                'urls': [
                    "https://writingcenter.unc.edu/tips-and-tools/apa-citation/",
                    "https://writing.wisc.edu/Handbook/DocAPA.html",
                    "https://writing.fsu.edu/guides/research/apa_style/"
                ]
            }
        ]

        all_citations = []

        for source in sources:
            print(f"\n{'='*60}")
            print(f"SCRAPING: {source['name']}")
            print(f"{'='*60}")

            for url in source['urls']:
                print(f"\n🔗 Trying: {url}")
                citations = self.scrape_single_url(url, source['name'])
                all_citations.extend(citations)

        return all_citations

    def scrape_single_url(self, url, source_name):
        """Scrape a single URL for citations"""

        try:
            # Try different request parameters
            response = self.client.get(
                url,
                params={
                    'render_js': False,  # Try without JS first
                    'premium_proxy': True,
                    'country_code': 'us'
                }
            )

            if response.status_code != 200:
                print(f"❌ Failed: HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.find('main') or soup.find('div', class_='main-content') or soup

            # Extract citations using comprehensive patterns
            citations = self.extract_citations_from_content(content, url, source_name)

            print(f"✅ Found {len(citations)} citations")
            return citations

        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
            return []

    def extract_citations_from_content(self, content, url, source_name):
        """Extract citations from page content"""

        citations = []
        text = content.get_text()

        # Look for example sections
        example_sections = []

        # Find text containing "Example" or similar indicators
        example_patterns = [
            r'Example[:\s]+([^.]*?\([A-Z][a-z]+,\s*[A-Z]\.\s*\(\d{4}\)[^.]*?\.)',
            r'For example[:\s]+([^.]*?\([A-Z][a-z]+,\s*[A-Z]\.\s*\(\d{4}\)[^.]*?\.)',
            r'e\.g\.[:\s]+([^.]*?\([A-Z][a-z]+,\s*[A-Z]\.\s*\(\d{4}\)[^.]*?\.)',
        ]

        for pattern in example_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                if self.is_valid_citation(match):
                    citations.append(match)

        # Look for code blocks or formatted examples
        for element in content.find_all(['code', 'pre', 'blockquote', 'tt']):
            element_text = element.get_text().strip()
            if self.is_valid_citation(element_text):
                citations.append(element_text)

        # Look for italics patterns (_text_) that might be journal titles
        italics_matches = re.findall(r'(_[^_]+_)', text)
        for italicized in italics_matches:
            # Look for citations containing this italicized text
            context_pattern = rf'[^.]*{re.escape(italicized)}[^.]*\(\d{{4}}\)[^.]*\.'
            context_matches = re.findall(context_pattern, text)
            for match in context_matches:
                if self.is_valid_citation(match):
                    citations.append(match)

        # General pattern matching for author-year citations
        author_year_patterns = [
            r'([A-Z][a-z]+,\s*[A-Z]\.\s*\(\d{4}\)\.\s*[^.]+\.\s*[^,]+,\s*\d+\(\d+\),\s*\d+-\d+\.?)',
            r'([A-Z][a-z]+,\s*[A-Z]\.\s*&\s*[A-Z][a-z]+,\s*[A-Z]\.\s*\(\d{4}\)\.\s*[^.]+?\.)',
            r'([A-Z][a-z]+,\s*[A-Z]\.\s*\(\d{4}\)\.\s*_[^_]+_\.\s*[^.]+?\.)',
        ]

        for pattern in author_year_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                if self.is_valid_citation(match):
                    citations.append(match)

        # Clean and deduplicate
        unique_citations = []
        seen = set()

        for citation in citations:
            citation = self.clean_citation(citation)

            if not citation or len(citation) < 40 or citation in seen:
                continue

            if self.is_valid_citation(citation):
                seen.add(citation)

                citation_data = {
                    "citation_id": f"scrpbee_alt_{self.citation_counter:03d}",
                    "citation_text": citation,
                    "source_type": self.determine_source_type(citation),
                    "is_valid": True,
                    "metadata": {
                        "source": f"{source_name} (ScrapingBee)",
                        "url": url,
                        "category": source_name,
                        "date_collected": datetime.now().isoformat(),
                        "formatting_preserved": True,
                        "verified_against_kb": False,
                        "scraping_method": "scrapingbee_alternative"
                    }
                }

                unique_citations.append(citation_data)
                self.citation_counter += 1

        return unique_citations

    def clean_citation(self, text):
        """Clean citation text"""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Fix spacing around punctuation
        text = re.sub(r'\s*,\s*', ', ', text)
        text = re.sub(r'\s*\.\s*', '. ', text)

        # Fix italics
        text = self.fix_italics(text)

        return text

    def fix_italics(self, text):
        """Fix italics formatting"""

        # Common patterns for italicization
        text = re.sub(r'([A-Z][a-zA-Z\s&]+Journal),\s*(\d+\(\d+\))', lambda m: f"_{m.group(1)}_, {m.group(2)}", text)
        text = re.sub(r'([A-Z][a-zA-Z\s&]+Review),\s*(\d+\(\d+\))', lambda m: f"_{m.group(1)}_, {m.group(2)}", text)

        return text

    def is_valid_citation(self, text):
        """Check if text is a valid APA citation"""

        # Must have author and year
        if not re.search(r'[A-Z][a-z]+,\s*[A-Z]\.?\s*\(\d{4}\)', text):
            return False

        # Must have publication info
        if not any([
            re.search(r'\d+\(\d+\)', text),  # volume(issue)
            re.search(r'press|university', text, re.I),  # publisher
            re.search(r'https?://', text),   # URL
            re.search(r'_.*_', text),        # italics
            re.search(r'\. [A-Z]', text)    # sentence structure
        ]):
            return False

        # Reasonable length
        if len(text) < 40 or len(text) > 500:
            return False

        return True

    def determine_source_type(self, citation):
        """Determine citation type"""

        if re.search(r'\d+\(\d+\)', citation):
            return 'journal article'
        elif 'press' in citation.lower() or 'university' in citation.lower():
            return 'book'
        elif 'http' in citation.lower():
            return 'webpage'
        else:
            return 'other'

def main():
    """Main execution"""

    api_key = "LIBY0CW5QYMS826LW2M3YPF97V3RT7H7I89EFIISANIKDV5LWYF27N8K4JNPZA9AURXUJVRZYYQWARUR"

    scraper = AlternativeAPAScraper(api_key)

    print("🔍 TRYING ALTERNATIVE APA SOURCES")
    print("=" * 60)

    citations = scraper.scrape_alternative_sources()

    print(f"\n{'='*60}")
    print("ALTERNATIVE SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total citations found: {len(citations)}")

    if citations:
        # Show breakdown
        type_counts = {}
        for citation in citations:
            source_type = citation['source_type']
            type_counts[source_type] = type_counts.get(source_type, 0) + 1

        print("\nCitations by type:")
        for source_type, count in sorted(type_counts.items()):
            print(f"  {source_type}: {count}")

        print(f"\n📝 Sample citations:")
        for i, citation in enumerate(citations[:3], 1):
            print(f"{i}. {citation['citation_text']}")
            print(f"   Type: {citation['source_type']}")
            print(f"   Source: {citation['metadata']['category']}")
            print()

        # Save to file
        output_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_additional_citations.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for citation in citations:
                f.write(json.dumps(citation, ensure_ascii=False) + '\n')

        print(f"✅ Saved to: {output_file}")
    else:
        print("No additional citations found with alternative sources.")

if __name__ == "__main__":
    main()