#!/usr/bin/env python3
"""
Clean ScrapingBee scraper for Purdue OWL APA citations
Creates fresh dataset with scrpbee_ prefix
"""

import os
import json
import re
from datetime import datetime
from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup

class ScrpbeeScraper:
    def __init__(self, api_key):
        self.client = ScrapingBeeClient(api_key=api_key)
        self.all_citations = []
        self.citation_counter = 1

    def scrape_purdue_page(self, url, page_category):
        """Scrape citations from a Purdue OWL page with clean extraction"""

        print(f"\n{'='*60}")
        print(f"SCRAPING: {page_category}")
        print(f"URL: {url}")
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

            # Extract citations using multiple methods
            citations = self.extract_all_citations(main_content, url, page_category)

            print(f"✅ Extracted {len(citations)} citations from {page_category}")
            return citations

        except Exception as e:
            print(f"❌ Error scraping {page_category}: {type(e).__name__}: {e}")
            return []

    def extract_all_citations(self, content, url, page_category):
        """Extract citations using comprehensive methods"""

        citations = []
        text_content = content.get_text()

        # Method 1: Regex patterns for APA citations
        citation_patterns = [
            # Standard journal article pattern
            r'([A-Z][a-z]+, [A-Z]\.\s*(?:&\s*[A-Z][a-z]+, [A-Z]\.\s*)*\(\d{4}\)\.\s*[^.]+\.\s*[^,]+,\s*\d+\(\d+\),\s*\d+-\d+\.?)',
            # Book pattern
            r'([A-Z][a-z]+, [A-Z]\.\s*\(\d{4}\)\.\s*_[^_]+_\.\s*[^.]+\.)',
            # Electronic source pattern
            r'([A-Z][a-z]+, [A-Z]\.\s*\(\d{4}\)\.\s*[^.]+\.\s*Retrieved\s+[^.]+\.\s*https?://[^.]+)',
            # General pattern with author and year
            r'([A-Z][a-z]+, [A-Z]\.\s*(?:&\s*[A-Z][a-z]+, [A-Z]\.\s*)*\(\d{4}\)\.\s*[^.]+?\.[^.]*?\.)'
        ]

        for pattern in citation_patterns:
            matches = re.findall(pattern, text_content, re.MULTILINE | re.DOTALL)
            for match in matches:
                if self.is_valid_citation(match):
                    citations.append(match)

        # Method 2: Look for block elements containing citations
        for element in content.find_all(['p', 'div', 'blockquote', 'li']):
            element_text = element.get_text().strip()
            if self.is_valid_citation(element_text):
                citations.append(element_text)

        # Method 3: Find lines starting with author patterns
        lines = text_content.split('\n')
        for line in lines:
            line = line.strip()
            if re.match(r'^[A-Z][a-z]+,\s*[A-Z]\.\s*\(\d{4}\)', line):
                if self.is_valid_citation(line):
                    citations.append(line)

        # Deduplicate and clean
        unique_citations = []
        seen = set()

        for citation in citations:
            citation = self.clean_citation_text(citation)

            if not citation or len(citation) < 30 or citation in seen:
                continue

            if self.is_valid_citation(citation):
                seen.add(citation)

                citation_data = {
                    "citation_id": f"scrpbee_{self.citation_counter:03d}",
                    "citation_text": citation,
                    "source_type": self.determine_source_type(citation),
                    "is_valid": True,
                    "metadata": {
                        "source": "Purdue OWL (ScrapingBee)",
                        "url": url,
                        "category": page_category,
                        "date_collected": datetime.now().isoformat(),
                        "formatting_preserved": True,
                        "verified_against_kb": False,
                        "scraping_method": "scrapingbee"
                    }
                }

                unique_citations.append(citation_data)
                self.citation_counter += 1

        return unique_citations

    def clean_citation_text(self, text):
        """Clean and normalize citation text"""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Fix common formatting issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces
        text = re.sub(r'\s*,\s*', ', ', text)  # Space around commas
        text = re.sub(r'\s*\.\s*', '. ', text)  # Space around periods
        text = re.sub(r'\(\s*', '(', text)  # Space after opening paren
        text = re.sub(r'\s*\)', ')', text)  # Space before closing paren

        # Ensure proper italics (underscore format)
        text = self.fix_italics(text)

        return text

    def fix_italics(self, text):
        """Fix italics formatting in citations"""

        # Known journal/book titles that should be italicized
        known_titles = [
            "The New Criterion",
            "Writing Center Journal",
            "Time",
            "The Country Today",
            "Contemporary Psychology",
            "SubStance",
            "Alexander the Great: A life in legend",
            "Writing your journal article in twelve weeks: A guide to academic publishing success",
            "Le morte darthur",
            "A new companion to Malory",
            "Symposium",
            "Nighthawks",
            "Sea smoke on Lake Michigan",
            "Encyclopedia of big data"
        ]

        # Italicize known titles
        for title in known_titles:
            if title in text and not f"_{title}_" in text:
                text = text.replace(title, f"_{title}_")

        # Italicize journal names before volume numbers
        text = re.sub(r'([A-Z][a-zA-Z\s&]+),\s*(\d+\(\d+\))', r'_\1_, \2', text)

        return text

    def is_valid_citation(self, text):
        """Check if text is a valid APA citation"""

        # Must have author and year
        if not re.search(r'[A-Z][a-z]+,\s*[A-Z]\.?\s*\(\d{4}\)', text):
            return False

        # Must have publication info
        has_pub_info = any([
            re.search(r'\d+\(\d+\)', text),  # volume(issue)
            re.search(r'Press', text),       # publisher
            re.search(r'University', text),  # university
            re.search(r'https?://', text),   # URL
            re.search(r'Retrieved', text),   # electronic source
            re.search(r'\. ', text)          # sentence ending (indicates complete citation)
        ])

        # Reasonable length
        if len(text) < 30 or len(text) > 500:
            return False

        # Exclude obvious non-citations
        exclude_phrases = [
            'click here', 'for more information', 'see also',
            'example:', 'note:', 'available at', ' retrieved from',
            'doi:', 'http://dx.doi.org'  # old DOI format
        ]

        if any(phrase in text.lower() for phrase in exclude_phrases):
            return False

        return has_pub_info

    def determine_source_type(self, citation):
        """Determine citation type based on content"""

        citation_lower = citation.lower()

        if re.search(r'\d+\(\d+\)', citation):
            return 'journal article'
        elif 'press' in citation_lower or 'university' in citation_lower:
            return 'book'
        elif 'retrieved' in citation_lower or 'http' in citation_lower:
            return 'webpage'
        elif '[painting]' in citation_lower or '[photograph]' in citation_lower:
            return 'other'
        elif '[manuscript' in citation_lower:
            return 'other'
        elif 'in ' + citation.lower().split(' in ')[1].split(' ')[0] + ' (ed.' in citation_lower:
            return 'book chapter'
        else:
            return 'other'

    def scrape_all_pages(self):
        """Scrape all Purdue OWL pages"""

        pages = [
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html",
                'category': "Journal Articles"
            },
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_books.html",
                'category': "Books"
            },
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_electronic_sources.html",
                'category': "Electronic Sources"
            },
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_audiovisual_media.html",
                'category': "Audiovisual Media"
            },
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_other_print_sources.html",
                'category': "Other Print Sources"
            },
            {
                'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_other_non_print_sources.html",
                'category': "Other Non-Print Sources"
            }
        ]

        all_citations = []

        print("🚀 Starting fresh ScrapingBee extraction...")

        for page in pages:
            citations = self.scrape_purdue_page(page['url'], page['category'])
            all_citations.extend(citations)

        return all_citations

def main():
    """Main execution"""

    api_key = "LIBY0CW5QYMS826LW2M3YPF97V3RT7H7I89EFIISANIKDV5LWYF27N8K4JNPZA9AURXUJVRZYYQWARUR"

    scraper = ScrpbeeScraper(api_key)
    citations = scraper.scrape_all_pages()

    # Save valid citations
    output_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations.jsonl"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for citation in citations:
            f.write(json.dumps(citation, ensure_ascii=False) + '\n')

    print(f"\n{'='*60}")
    print("SCRAPINGBEE SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total citations extracted: {len(citations)}")
    print(f"Saved to: {output_file}")

    # Type breakdown
    type_counts = {}
    for citation in citations:
        source_type = citation['source_type']
        type_counts[source_type] = type_counts.get(source_type, 0) + 1

    print("\nCitations by type:")
    for source_type, count in sorted(type_counts.items()):
        print(f"  {source_type}: {count}")

    print(f"\nSample citations:")
    for i, citation in enumerate(citations[:3], 1):
        print(f"{i}. {citation['citation_text']}")
        print(f"   Type: {citation['source_type']}")
        print(f"   ID: {citation['citation_id']}")

    return citations

if __name__ == "__main__":
    main()