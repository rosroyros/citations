#!/usr/bin/env python3
"""
Improved ScrapingBee scraper with better error handling
"""

import os
import json
import re
from datetime import datetime
from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup

class ScrpbeeScraperV2:
    def __init__(self, api_key):
        self.client = ScrapingBeeClient(api_key=api_key)
        self.all_citations = []
        self.citation_counter = 1

    def scrape_purdue_page(self, url, page_category):
        """Scrape citations from a Purdue OWL page with robust extraction"""

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

            # Extract citations with improved methods
            citations = self.extract_citations_improved(main_content, url, page_category)

            print(f"✅ Extracted {len(citations)} citations from {page_category}")
            return citations

        except Exception as e:
            print(f"❌ Error scraping {page_category}: {type(e).__name__}: {e}")
            return []

    def extract_citations_improved(self, content, url, page_category):
        """Extract citations with improved pattern matching"""

        citations = []
        text_content = content.get_text()

        # Split into lines and process each
        lines = text_content.split('\n')

        for line in lines:
            line = line.strip()

            # Skip empty lines and obvious non-citations
            if len(line) < 30 or not line:
                continue

            # Skip navigation and UI text
            skip_phrases = [
                'apa style', 'purdue owl', 'copyright', 'all rights reserved',
                'example:', 'note:', 'click here', 'for more information',
                'see also', 'please note', 'the following', 'these examples',
                'basic format', 'general format', 'note that'
            ]

            if any(phrase in line.lower() for phrase in skip_phrases):
                continue

            # Look for citation patterns
            if self.looks_like_citation(line):
                clean_citation = self.clean_citation_text(line)
                if clean_citation and len(clean_citation) >= 30:
                    citations.append(clean_citation)

        # Also look for multi-line citations
        citations.extend(self.find_multiline_citations(text_content))

        # Deduplicate and validate
        unique_citations = []
        seen = set()

        for citation in citations:
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
                        "scraping_method": "scrapingbee_v2"
                    }
                }

                unique_citations.append(citation_data)
                self.citation_counter += 1

        return unique_citations

    def looks_like_citation(self, text):
        """Quick check if text looks like a citation"""

        # Must have author-year pattern
        if not re.search(r'[A-Z][a-z]+,\s*[A-Z]\.?\s*\(\d{4}\)', text):
            return False

        # Must have some publication indicator
        pub_indicators = [
            r'\d+\(\d+\)',  # volume(issue)
            r'press',       # publisher
            r'university',  # university publisher
            r'https?://',   # URL
            r'doi:',        # DOI
            r'\. \w',       # sentence ending + capital letter (continuation)
            r'pp\.\s*\d+',  # page numbers
            r'retrieved'    # electronic source
        ]

        return any(re.search(pattern, text, re.I) for pattern in pub_indicators)

    def find_multiline_citations(self, text):
        """Find citations that span multiple lines"""

        citations = []
        lines = text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # If line starts with author pattern, try to build complete citation
            if re.match(r'^[A-Z][a-z]+,\s*[A-Z]\.?\s*\(\d{4}\)', line):
                citation_lines = [line]
                i += 1

                # Add subsequent lines until we hit a complete citation
                while i < len(lines) and len(citation_lines) < 5:
                    next_line = lines[i].strip()

                    # Stop if we hit another citation start or empty line
                    if not next_line or re.match(r'^[A-Z][a-z]+,\s*[A-Z]\.?\s*\(\d{4}\)', next_line):
                        break

                    # Stop if line looks like navigation/UI text
                    if any(phrase in next_line.lower() for phrase in ['apa style', 'purdue owl', 'example']):
                        break

                    citation_lines.append(next_line)
                    i += 1

                # Combine lines
                full_citation = ' '.join(citation_lines)
                if len(full_citation) >= 30 and self.is_valid_citation(full_citation):
                    citations.append(full_citation)
            else:
                i += 1

        return citations

    def clean_citation_text(self, text):
        """Clean and normalize citation text"""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Fix spacing around punctuation
        text = re.sub(r'\s*,\s*', ', ', text)
        text = re.sub(r'\s*\.\s*', '. ', text)
        text = re.sub(r'\(\s*', '(', text)
        text = re.sub(r'\s*\)', ')', text)

        # Fix italics
        text = self.fix_italics(text)

        # Fix common formatting issues
        text = re.sub(r'_([^_]+)_\s*,\s*([^,]+),', r'_\1_, \2,', text)  # Fix italicized journal names

        return text

    def fix_italics(self, text):
        """Fix italics formatting"""

        # Known titles that should be italicized
        titles_to_italicize = [
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
            "Encyclopedia of big data",
            "UpToDate",
            "Art Institute of Chicago"
        ]

        for title in titles_to_italicize:
            if title in text and not f"_{title}_" in text:
                text = text.replace(title, f"_{title}_")

        # Italicize journal names before volume numbers
        text = re.sub(r'([A-Z][a-zA-Z\s&]+),\s*(\d+\(\d+\))', lambda m: f"_{m.group(1)}_, {m.group(2)}", text)

        # Italicize book titles (after author, year)
        text = re.sub(r'\(\d{4}\)\.\s*([^.]+?)\.\s*([A-Z][^.]*(?:Press|University))', lambda m: f"({m.group(1)}). _{m.group(2)}_", text)

        return text

    def is_valid_citation(self, text):
        """Validate citation format"""

        # Must have author and year
        if not re.search(r'[A-Z][a-z]+,\s*[A-Z]\.?\s*\(\d{4}\)', text):
            return False

        # Must have publication info
        if not any([
            re.search(r'\d+\(\d+\)', text),  # volume(issue)
            re.search(r'press|university', text, re.I),  # publisher
            re.search(r'https?://', text),   # URL
            re.search(r'retrieved', text, re.I),  # electronic source
            re.search(r'\. [A-Z]', text)    # complete sentence structure
        ]):
            return False

        # Reasonable length
        if len(text) < 30 or len(text) > 500:
            return False

        # Exclude obvious non-citations
        exclude_phrases = [
            'example:', 'note:', 'click here', 'see also',
            'for more information', 'available at', 'doi:'
        ]

        return not any(phrase in text.lower() for phrase in exclude_phrases)

    def determine_source_type(self, citation):
        """Determine citation type"""

        citation_lower = citation.lower()

        if re.search(r'\d+\(\d+\)', citation):
            return 'journal article'
        elif 'press' in citation_lower or 'university' in citation_lower:
            return 'book'
        elif 'retrieved' in citation_lower or 'http' in citation_lower:
            return 'webpage'
        elif any(x in citation_lower for x in ['painting', 'photograph', 'artwork']):
            return 'other'
        elif any(x in citation_lower for x in ['manuscript', 'unpublished']):
            return 'other'
        elif re.search(r'\bin\s+[^.]+?\s*\(eds?\.\)', citation):
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

        print("🚀 Starting improved ScrapingBee extraction...")

        for page in pages:
            citations = self.scrape_purdue_page(page['url'], page['category'])
            all_citations.extend(citations)

        return all_citations

def main():
    """Main execution"""

    api_key = "LIBY0CW5QYMS826LW2M3YPF97V3RT7H7I89EFIISANIKDV5LWYF27N8K4JNPZA9AURXUJVRZYYQWARUR"

    scraper = ScrpbeeScraperV2(api_key)
    citations = scraper.scrape_all_pages()

    # Save valid citations
    output_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations.jsonl"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for citation in citations:
            f.write(json.dumps(citation, ensure_ascii=False) + '\n')

    print(f"\n{'='*60}")
    print("IMPROVED SCRAPINGBEE SCRAPING COMPLETE")
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

    # Show all citations
    print(f"\nAll extracted citations:")
    for i, citation in enumerate(citations, 1):
        print(f"{i}. {citation['citation_text']}")
        print(f"   Type: {citation['source_type']} | ID: {citation['citation_id']}")
        print()

    return citations

if __name__ == "__main__":
    main()