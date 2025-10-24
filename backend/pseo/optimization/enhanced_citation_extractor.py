#!/usr/bin/env python3
"""
Enhanced citation extractor that finds more examples from Purdue OWL pages
"""

import os
import json
import re
from datetime import datetime
from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup

class EnhancedCitationExtractor:
    def __init__(self, api_key):
        self.client = ScrapingBeeClient(api_key=api_key)
        self.all_citations = []
        self.citation_id_counter = 1

    def extract_citations_from_page(self, url, page_name, source_type):
        """Enhanced citation extraction using multiple strategies"""

        print(f"\n📄 Processing: {page_name}")

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
                print(f"❌ HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.find('main') or soup.find('div', class_='main') or soup

            citations = []

            # Strategy 1: Look for all text content and extract citation patterns
            all_text = main_content.get_text()
            citation_patterns = self.find_citation_patterns(all_text)

            # Strategy 2: Look for specific HTML structures
            structured_citations = self.extract_structured_citations(main_content)

            # Strategy 3: Manual patterns for known Purdue OWL formatting
            manual_citations = self.extract_manual_patterns(main_content)

            # Combine all citations
            all_found = citation_patterns + structured_citations + manual_citations

            # Deduplicate and validate
            unique_citations = []
            seen = set()

            for citation_text in all_found:
                citation_text = citation_text.strip()

                if len(citation_text) < 40 or citation_text in seen:
                    continue

                # Validate it looks like a citation
                if not self.validate_citation(citation_text):
                    continue

                seen.add(citation_text)

                citation_data = {
                    "citation_id": f"purdue_{self.sanitize_page_name(page_name)}_{self.citation_id_counter:03d}",
                    "citation_text": citation_text,
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

            print(f"✅ Found {len(unique_citations)} citations")
            return unique_citations

        except Exception as e:
            print(f"❌ Error: {e}")
            return []

    def find_citation_patterns(self, text):
        """Find citations using regex patterns"""

        citations = []

        # Pattern 1: Standard APA format with year
        pattern1 = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]\.\s*(?:&\s*[A-Z][a-z]+,\s*[A-Z]\.\s*)*\(\d{4}\)[^.]+\.)'
        matches1 = re.findall(pattern1, text)
        citations.extend(matches1)

        # Pattern 2: Multiple authors with year
        pattern2 = r'([A-Z][a-z]+,\s*[A-Z]\.\s*&\s*[A-Z][a-z]+,\s*[A-Z]\.\s*\(\d{4}\)[^.]+\.)'
        matches2 = re.findall(pattern2, text)
        citations.extend(matches2)

        # Pattern 3: Article with journal volume/issue
        pattern3 = r'([^.]*\(\d{4}\)[^.]*\w+,\s*\d+\(\d+\)[^.]*\d+-\d+\.)'
        matches3 = re.findall(pattern3, text)
        citations.extend(matches3)

        # Pattern 4: Book with publisher
        pattern4 = r'([^.]*\(\d{4}\)[^.]*\w+\s+Press[^.]*\.)'
        matches4 = re.findall(pattern4, text)
        citations.extend(matches4)

        # Pattern 5: Electronic sources with URLs/DOIs
        pattern5 = r'([^.]*\(\d{4}\)[^.]*https?://[^.]*\.)'
        matches5 = re.findall(pattern5, text)
        citations.extend(matches5)

        return citations

    def extract_structured_citations(self, content):
        """Extract citations from HTML structures"""

        citations = []

        # Look for text in specific elements
        elements_to_check = [
            content.find_all('p'),
            content.find_all('div'),
            content.find_all('li'),
            content.find_all('blockquote'),
            content.find_all('code'),
            content.find_all('pre')
        ]

        for element_list in elements_to_check:
            for element in element_list:
                text = element.get_text().strip()
                if self.validate_citation(text) and len(text) > 40:
                    citations.append(text)

        return citations

    def extract_manual_patterns(self, content):
        """Manual extraction based on known Purdue OWL patterns"""

        citations = []
        text = content.get_text()

        # Look for lines that start with author names
        lines = text.split('\n')
        for line in lines:
            line = line.strip()

            # Skip if too short or contains non-citation text
            if len(line) < 40:
                continue

            if any(skip in line.lower() for skip in ['example', 'click', 'note:', 'see also', 'for more']):
                continue

            # Check if it starts with an author pattern
            if re.match(r'^[A-Z][a-z]+,\s*[A-Z]\.', line):
                if self.validate_citation(line):
                    citations.append(line)

        return citations

    def validate_citation(self, text):
        """Enhanced citation validation"""

        # Must have year in parentheses
        if not re.search(r'\(\d{4}\)', text):
            return False

        # Must have author format
        if not re.search(r'[A-Z][a-z]+,\s*[A-Z]\.?\s*\(\d{4}\)', text):
            return False

        # Must have publication info
        has_publication = any([
            re.search(r'\w+,\s*\d+\(\d+\)', text),  # journal volume/issue
            re.search(r'\w+\s+Press', text),       # publisher
            re.search(r'University', text),        # university publisher
            re.search(r'https?://', text),         # URL
            re.search(r'doi:', text, re.I)         # DOI
        ])

        return has_publication

    def sanitize_page_name(self, page_name):
        """Convert page name to safe filename format"""
        return re.sub(r'[^a-z0-9_]', '', page_name.lower().replace(' ', '_'))

    def scrape_all_pages(self):
        """Scrape all Purdue OWL pages"""

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

        print("🚀 Starting enhanced citation extraction...")

        for page in pages:
            citations = self.extract_citations_from_page(page['url'], page['name'], page['source_type'])
            all_citations.extend(citations)

        return all_citations

def main():
    """Main execution"""

    api_key = "LIBY0CW5QYMS826LW2M3YPF97V3RT7H7I89EFIISANIKDV5LWYF27N8K4JNPZA9AURXUJVRZYYQWARUR"

    extractor = EnhancedCitationExtractor(api_key)

    citations = extractor.scrape_all_pages()

    # Save results
    output_file = "backend/pseo/optimization/datasets/valid_citations_enhanced.jsonl"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for citation in citations:
            f.write(json.dumps(citation, ensure_ascii=False) + '\n')

    print(f"\n{'='*60}")
    print("ENHANCED SCRAPING COMPLETE")
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

    print(f"\n✅ Saved to: {output_file}")

if __name__ == "__main__":
    main()