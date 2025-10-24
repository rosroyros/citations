#!/usr/bin/env python3
"""
ScraperAPI integration script for citation extraction
Uses ScraperAPI to scrape content and extracts citations using existing pipeline
"""

import os
import json
import re
from datetime import datetime
from scraperapi_scraper import ScraperAPIClient
from bs4 import BeautifulSoup

class ScraperAPIScraper:
    def __init__(self):
        self.client = ScraperAPIClient()
        self.all_citations = []
        self.citation_counter = 1

    def scrape_page(self, url, page_category):
        """Scrape citations from a page using ScraperAPI"""

        print(f"\n{'='*60}")
        print(f"SCRAPING WITH SCRAPERAPI: {page_category}")
        print(f"URL: {url}")
        print(f"{'='*60}")

        try:
            # Scrape the page with JavaScript rendering
            html_content = self.client.scrape_with_render(url)

            if not html_content:
                print(f"❌ Failed: No content received")
                return []

            soup = BeautifulSoup(html_content, 'html.parser')
            main_content = soup.find('main') or soup.find('div', class_='main') or soup

            # Extract citations using multiple methods
            citations = self.extract_all_citations(main_content, url, page_category)

            print(f"✅ Extracted {len(citations)} citations from {page_category}")
            return citations

        except Exception as e:
            print(f"❌ Error scraping {page_category}: {type(e).__name__}: {e}")
            return []

    def extract_all_citations(self, content, url, page_category):
        """Extract citations using comprehensive methods with HTML formatting preservation"""

        citations = []
        seen_citations = set()

        # Method 1: Look for elements with class="APAformat" (specific to SUU library)
        apa_elements = content.find_all(['p', 'div'], class_='APAformat')
        for element in apa_elements:
            citation_html = str(element)
            citation_text = self.html_to_markdown_citation(citation_html)
            if citation_text and self.is_valid_citation(citation_text):
                if citation_text not in seen_citations:
                    citations.append(citation_text)
                    seen_citations.add(citation_text)

        # Method 2: Look for blockquote elements containing citations
        for blockquote in content.find_all('blockquote'):
            for element in blockquote.find_all(['p', 'div']):
                citation_html = str(element)
                citation_text = self.html_to_markdown_citation(citation_html)
                if citation_text and self.is_valid_citation(citation_text):
                    if citation_text not in seen_citations:
                        citations.append(citation_text)
                        seen_citations.add(citation_text)

        # Method 3: General citation detection with HTML preservation
        for element in content.find_all(['p', 'div', 'li']):
            citation_html = str(element)
            citation_text = self.html_to_markdown_citation(citation_html)
            if citation_text and self.is_valid_citation(citation_text):
                if citation_text not in seen_citations:
                    citations.append(citation_text)
                    seen_citations.add(citation_text)

        return citations

    def html_to_markdown_citation(self, html_content):
        """Convert HTML citation to markdown with proper underscore formatting"""

        # Remove HTML tags but preserve <em> as underscores
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Convert <em> tags to underscores before removing HTML
        for em_tag in soup.find_all('em'):
            em_tag.replace_with(f"_{em_tag.get_text()}_")

        # Convert <i> tags to underscores (alternative italic tag)
        for i_tag in soup.find_all('i'):
            i_tag.replace_with(f"_{i_tag.get_text()}_")

        # Get text with preserved underscores
        citation_text = soup.get_text().strip()

        # Clean up whitespace
        citation_text = re.sub(r'\s+', ' ', citation_text)

        # Remove leading/trailing punctuation
        citation_text = citation_text.strip(' .;:\n\t')

        return citation_text if citation_text else None

    def is_valid_citation(self, text):
        """Check if text looks like a valid APA citation"""

        # Must contain author and year pattern
        if not re.search(r'[A-Z][a-z]+,\s*[A-Z]\.\s*\(\d{4}\)', text):
            return False

        # Must be reasonable length
        if len(text) < 20 or len(text) > 500:
            return False

        # Must contain typical citation elements
        has_title = bool(re.search(r'\.\s*[A-Z]', text))  # Capitalized title
        has_publisher = bool(re.search(r'[A-Z][a-z]+\s*[A-Z][a-z]+', text.split('(')[-1])) if '(' in text else True

        return has_title and has_publisher

    def clean_citation_text(self, citation):
        """Clean citation text while preserving markdown underscores"""

        # Remove extra whitespace
        citation = re.sub(r'\s+', ' ', citation)

        # Remove leading/trailing punctuation but preserve internal formatting
        citation = citation.strip(' .;:\n\t')

        return citation

    def detect_source_type_from_citation(self, citation_text):
        """Detect source type from citation text"""

        text = citation_text.lower()

        # Journal article indicators
        if re.search(r'\d+\(\d+\),\s*\d+-\d+', text) or 'doi:' in text or re.search(r'journal', text):
            return 'journal article'

        # Book indicators
        if re.search(r'\([^)]*ed\.\)|\d+nd ed\.|\d+rd ed\.|\d+th ed\.', text) or \
           re.search(r'[A-Z][a-z]+ [A-Z][a-z]+:\s*[A-Z][a-z]+', citation_text) or \
           'press' in text or 'university' in text:
            return 'book'

        # Website indicators
        if 'retrieved from' in text or 'http' in text:
            return 'website'

        # Chapter indicators
        if 'in ' in text and re.search(r'[A-Z][a-z]+\s*\([A-Z][a-z]+\)', citation_text):
            return 'book chapter'

        # Default
        return 'other'

    def save_citations(self, citations, url, page_category):
        """Save citations to JSONL file matching existing dataset schema"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"datasets/scrpbee/scraperapi_{page_category}_{timestamp}.jsonl"

        # Ensure directory exists
        os.makedirs('datasets/scrpbee', exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            for citation in citations:
                citation_id = f"scrpbee_{self.citation_counter:03d}"
                source_type = self.detect_source_type_from_citation(citation)

                citation_data = {
                    'citation_id': citation_id,
                    'citation_text': citation,
                    'source_type': source_type,
                    'is_valid': True,
                    'metadata': {
                        'source': 'ScraperAPI',
                        'url': url,
                        'category': page_category,
                        'date_collected': datetime.now().isoformat(),
                        'formatting_preserved': True,
                        'verified_against_kb': False,
                        'scraping_method': 'scraperapi_v1'
                    }
                }
                f.write(json.dumps(citation_data, ensure_ascii=False) + '\n')
                self.citation_counter += 1

        print(f"📁 Saved {len(citations)} citations to {filename}")
        return filename

def main(url=None, category=None):
    """Main function for ScraperAPI citation extraction"""

    scraper = ScraperAPIScraper()

    if url is None:
        # Default test URL
        url = "https://library.suu.edu/LibraryResearch/APA-Examples"
        category = "suu_library_apa_examples"

    print(f"🚀 Testing ScraperAPI with: {url}")

    # Scrape the page
    citations = scraper.scrape_page(url, category)

    if citations:
        # Save citations
        filename = scraper.save_citations(citations, url, category)

        print(f"\n🎉 SUCCESS!")
        print(f"📊 Total citations extracted: {len(citations)}")
        print(f"📁 Saved to: {filename}")

        # Show first few citations as preview
        print(f"\n📋 Preview of extracted citations:")
        for i, citation in enumerate(citations[:5], 1):
            print(f"{i}. {citation[:100]}...")

        if len(citations) > 5:
            print(f"... and {len(citations) - 5} more")
        return citations
    else:
        print(f"\n❌ No citations extracted from {url}")
        return []

if __name__ == "__main__":
    main()