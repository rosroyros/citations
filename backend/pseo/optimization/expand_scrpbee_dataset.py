#!/usr/bin/env python3
"""
Expand ScrpBee dataset by scraping additional APA citation examples
from multiple authoritative sources
"""

import os
import json
import re
from datetime import datetime
from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

class ExpandedScrpBeeScraper:
    def __init__(self, api_key):
        self.client = ScrapingBeeClient(api_key=api_key)
        self.all_citations = []
        self.citation_counter = 1
        self.visited_urls = set()

    def scrape_main_sources(self):
        """Scrape the main sources and explore their sub-pages"""

        sources = [
            {
                'name': 'APA Official Examples',
                'url': 'https://apastyle.apa.org/style-grammar-guidelines/references/examples#textual-works',
                'base_url': 'https://apastyle.apa.org'
            },
            {
                'name': 'Penn State Quick Guide',
                'url': 'https://guides.libraries.psu.edu/apaquickguide/intext',
                'base_url': 'https://guides.libraries.psu.edu'
            },
            {
                'name': 'CSUDH Citation Guide',
                'url': 'https://libguides.csudh.edu/citation/apa-7#s-lg-box-22358979',
                'base_url': 'https://libguides.csudh.edu'
            }
        ]

        all_found_citations = []

        for source in sources:
            print(f"\n{'='*80}")
            print(f"SCRAPING: {source['name']}")
            print(f"URL: {source['url']}")
            print(f"{'='*80}")

            # Scrape main page
            citations = self.scrape_apa_source(source['url'], source['name'], source['base_url'])
            all_found_citations.extend(citations)

            # Look for sub-pages to explore
            subpage_links = self.find_subpage_links(source['url'], source['base_url'])
            print(f"Found {len(subpage_links)} potential sub-pages to explore")

            # Explore up to 3 sub-pages per source
            for link in subpage_links[:3]:
                if link not in self.visited_urls:
                    print(f"\n🔗 Exploring sub-page: {link}")
                    sub_citations = self.scrape_apa_source(link, f"{source['name']} - Subpage", source['base_url'])
                    all_found_citations.extend(sub_citations)
                    time.sleep(1)  # Rate limiting

        return all_found_citations

    def scrape_apa_source(self, url, source_name, base_url):
        """Scrape citations from an APA source page"""

        if url in self.visited_urls:
            return []

        self.visited_urls.add(url)

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
            main_content = self.find_main_content(soup)

            citations = self.extract_citations_comprehensive(main_content, url, source_name)

            print(f"✅ Extracted {len(citations)} citations from {source_name}")
            return citations

        except Exception as e:
            print(f"❌ Error scraping {url}: {type(e).__name__}: {e}")
            return []

    def find_main_content(self, soup):
        """Find the main content area of the page"""

        # Try different selectors for main content
        selectors = [
            'main',
            'article',
            '.main-content',
            '.content',
            '.s-lg-guide-main',
            '#s-lg-guide-main',
            '.s-lib-box-content',
            '#s-lg-content-main'
        ]

        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                return content

        # Fallback to body if no main content found
        return soup.find('body') or soup

    def find_subpage_links(self, url, base_url):
        """Find links to sub-pages that might contain more citation examples"""

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
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            links = []

            # Look for links that might contain citation examples
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                text = link.get_text().strip().lower()

                # Skip empty or invalid links
                if not href or href.startswith('#') or href.startswith('mailto:'):
                    continue

                # Look for citation-related keywords in link text
                citation_keywords = [
                    'example', 'citation', 'reference', 'journal', 'book',
                    'article', 'website', 'electronic', 'periodical',
                    'database', 'report', 'thesis', 'dissertation'
                ]

                if any(keyword in text for keyword in citation_keywords):
                    # Convert relative URL to absolute
                    absolute_url = urljoin(base_url, href)

                    # Only include links from the same domain
                    if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                        links.append(absolute_url)

            return list(set(links))  # Remove duplicates

        except Exception as e:
            print(f"⚠️  Error finding subpage links: {e}")
            return []

    def extract_citations_comprehensive(self, content, url, source_name):
        """Extract citations using multiple comprehensive methods"""

        citations = []
        text_content = content.get_text()

        # Method 1: Advanced regex patterns for APA citations
        advanced_patterns = [
            # Journal articles with DOI
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]\.\s*(?:&\s*[A-Z][a-z]+,\s*[A-Z]\.\s*)*\(\d{4}\)\.\s*[^.]+?\.\s*_[^_]+?_,\s*\d+\(\d+\),\s*\d+-\d+\.?\s*https?://doi\.org/[^.\s]+)',
            # Journal articles without DOI
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]\.\s*(?:&\s*[A-Z][a-z]+,\s*[A-Z]\.\s*)*\(\d{4}\)\.\s*[^.]+?\.\s*_[^_]+?_,\s*\d+\(\d+\),\s*\d+-\d+\.?)',
            # Books with publishers
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]\.\s*\(\d{4}\)\.\s*_[^_]+?_\.\s*[^.]+?(?:Press|University|Publishing|Books|Publisher)\.?)',
            # Electronic sources with retrieval dates
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]\.\s*\(\d{4}\)\.\s*[^.]+?\.\s*Retrieved\s+[^.]+?\.\s*https?://[^.\s]+)',
            # Book chapters
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]\.\s*\(\d{4}\)\.\s*[^.]+?\.?\s*In\s+[^.]+?\s*\([^)]*eds?\.\)[^.]*?\.\s*pp\.\s*\d+-\d+\.?)',
            # General pattern with volume/issue
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]\.\s*(?:&\s*[A-Z][a-z]+,\s*[A-Z]\.\s*)*\(\d{4}\)\.\s*[^.]+?\.\s*[^,]+,\s*\d+\(\d+\)[^.]*\.?)'
        ]

        for pattern in advanced_patterns:
            matches = re.findall(pattern, text_content, re.MULTILINE | re.DOTALL)
            for match in matches:
                cleaned_match = self.clean_citation_text(match)
                if self.is_valid_citation(cleaned_match):
                    citations.append(cleaned_match)

        # Method 2: Look for code blocks, examples, or highlighted text
        for element in content.find_all(['code', 'pre', 'blockquote', 'div.example', 'div.footnote', 'span.citation']):
            element_text = element.get_text().strip()
            if self.is_valid_citation(element_text):
                citations.append(element_text)

        # Method 3: Find lines starting with author patterns (multi-line approach)
        lines = text_content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()

            # If line starts with author pattern, try to build complete citation
            if re.match(r'^[A-Z][a-z]+,\s*[A-Z]\.?\s*\(\d{4}\)', line):
                # Look ahead for continuation lines
                citation_lines = [line]
                j = i + 1

                while j < len(lines) and len(citation_lines) < 4:  # Limit to 4 lines
                    next_line = lines[j].strip()

                    # Stop conditions
                    if not next_line:
                        break
                    if re.match(r'^[A-Z][a-z]+,\s*[A-Z]\.?\s*\(\d{4}\)', next_line):
                        break  # Start of next citation
                    if next_line.lower() in ['example:', 'note:', 'see also:', 'for example:']:
                        break  # Navigation text

                    citation_lines.append(next_line)
                    j += 1

                full_citation = ' '.join(citation_lines)
                if self.is_valid_citation(full_citation):
                    citations.append(full_citation)

        # Method 4: Look for specific container elements
        container_selectors = [
            '.s-lib-box-content',
            '.citation-example',
            '.example-box',
            '.reference-example',
            '.apa-example'
        ]

        for selector in container_selectors:
            for container in content.select(selector):
                container_text = container.get_text().strip()
                if len(container_text) > 50 and len(container_text) < 500:
                    for line in container_text.split('\n'):
                        line = line.strip()
                        if self.is_valid_citation(line):
                            citations.append(line)

        # Deduplicate and validate
        unique_citations = []
        seen = set()

        for citation in citations:
            citation = self.clean_citation_text(citation)

            if not citation or len(citation) < 40 or citation in seen:
                continue

            if self.is_valid_citation(citation) and not self.contains_placeholder(citation):
                seen.add(citation)

                citation_data = {
                    "citation_id": f"scrpbee_exp_{self.citation_counter:03d}",
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
                        "scraping_method": "scrapingbee_expanded"
                    }
                }

                unique_citations.append(citation_data)
                self.citation_counter += 1

        return unique_citations

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

        # Remove common artifacts
        text = re.sub(r'\s*→\s*', ' ', text)  # Remove arrows
        text = re.sub(r'\s*•\s*', ' ', text)    # Remove bullets
        text = re.sub(r'\s*▪\s*', ' ', text)    # Remove other bullets

        return text

    def fix_italics(self, text):
        """Fix italics formatting"""

        # Common journal/book titles that should be italicized
        titles_to_italicize = [
            "The New Yorker", "The New York Times", "The Washington Post",
            "Time Magazine", "Scientific American", "Nature", "Science",
            "Journal of", "Review of", "Handbook of", "Annual Review of",
            "Psychological Bulletin", "Psychological Review", "Journal of Personality and Social Psychology"
        ]

        for title in titles_to_italicize:
            if title in text and not f"_{title}_" in text:
                text = text.replace(title, f"_{title}_")

        # Italicize journal names before volume numbers
        text = re.sub(r'([A-Z][a-zA-Z\s&]+Journal),\s*(\d+\(\d+\))', lambda m: f"_{m.group(1)}_, {m.group(2)}", text)
        text = re.sub(r'([A-Z][a-zA-Z\s&]+Review),\s*(\d+\(\d+\))', lambda m: f"_{m.group(1)}_, {m.group(2)}", text)

        return text

    def contains_placeholder(self, text):
        """Check if citation contains placeholder text"""

        placeholder_patterns = [
            r'\bYear\b',
            r'\bMonth Date\b',
            r'Title of (article|work|book|post|page|chapter)',
            r'Author, [A-Z]\. [A-Z]\.',
            r'Lastname, F\. M\.',
            r'\(n\.d\.\)',
            r'Publisher Name',
            r'Site Name',
            r'DOI \(if available\)',
            r'Retrieved Month Date, Year',
            r'Volume number',
            r'Issue number'
        ]

        for pattern in placeholder_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def is_valid_citation(self, text):
        """Check if text is a valid APA citation"""

        # Must have author and year
        if not re.search(r'[A-Z][a-z]+,\s*[A-Z]\.?\s*\(\d{4}\)', text):
            return False

        # Must have publication info
        if not any([
            re.search(r'\d+\(\d+\)', text),  # volume(issue)
            re.search(r'press|university|publishing', text, re.I),  # publisher
            re.search(r'https?://', text),   # URL
            re.search(r'retrieved', text, re.I),  # electronic source
            re.search(r'\. [A-Z]', text)    # complete sentence structure
        ]):
            return False

        # Reasonable length
        if len(text) < 40 or len(text) > 600:
            return False

        # Exclude obvious non-citations
        exclude_phrases = [
            'example:', 'note:', 'click here', 'see also',
            'for more information', 'available at', 'doi:',
            'cite this', 'how to cite', 'apa format'
        ]

        return not any(phrase in text.lower() for phrase in exclude_phrases)

    def determine_source_type(self, citation):
        """Determine citation type based on content"""

        citation_lower = citation.lower()

        if re.search(r'\d+\(\d+\)', citation):
            return 'journal article'
        elif 'press' in citation_lower or 'university' in citation_lower:
            return 'book'
        elif 'retrieved' in citation_lower or 'http' in citation_lower:
            return 'webpage'
        elif any(x in citation_lower for x in ['painting', 'photograph', 'artwork', 'song', 'album']):
            return 'other'
        elif any(x in citation_lower for x in ['manuscript', 'unpublished', 'dissertation', 'thesis']):
            return 'other'
        elif re.search(r'\bin\s+[^.]+?\s*\(eds?\.\)', citation):
            return 'book chapter'
        elif 'doi:' in citation_lower or 'doi.org' in citation_lower:
            return 'journal article'
        else:
            return 'other'

    def merge_with_existing_dataset(self, new_citations):
        """Merge new citations with existing scrpbee dataset"""

        # Load existing valid citations
        existing_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations_clean.jsonl"
        existing_citations = []

        if os.path.exists(existing_file):
            with open(existing_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        existing_citations.append(json.loads(line))

        print(f"Loaded {len(existing_citations)} existing citations")

        # Find and remove duplicates
        existing_texts = set(citation['citation_text'] for citation in existing_citations)
        unique_new_citations = []

        for citation in new_citations:
            if citation['citation_text'] not in existing_texts:
                unique_new_citations.append(citation)

        print(f"Found {len(new_citations) - len(unique_new_citations)} duplicates")
        print(f"Adding {len(unique_new_citations)} unique new citations")

        # Combine datasets
        combined_citations = existing_citations + unique_new_citations

        # Update IDs for new citations
        max_id = max(int(c['citation_id'].split('_')[1]) for c in existing_citations if c['citation_id'].startswith('scrpbee_'))
        for i, citation in enumerate(unique_new_citations):
            citation['citation_id'] = f"scrpbee_{max_id + i + 1:03d}"

        return combined_citations, unique_new_citations

def main():
    """Main execution"""

    api_key = "LIBY0CW5QYMS826LW2M3YPF97V3RT7H7I89EFIISANIKDV5LWYF27N8K4JNPZA9AURXUJVRZYYQWARUR"

    scraper = ExpandedScrpBeeScraper(api_key)

    print("🚀 EXPANDING SCRPBEE DATASET")
    print("=" * 80)

    # Scrape new sources
    new_citations = scraper.scrape_main_sources()

    print(f"\n{'='*80}")
    print("EXPANSION COMPLETE")
    print(f"{'='*80}")
    print(f"Total new citations found: {len(new_citations)}")

    # Type breakdown
    type_counts = {}
    for citation in new_citations:
        source_type = citation['source_type']
        type_counts[source_type] = type_counts.get(source_type, 0) + 1

    print("\nNew citations by type:")
    for source_type, count in sorted(type_counts.items()):
        print(f"  {source_type}: {count}")

    # Show sample new citations
    print(f"\n📝 Sample new citations:")
    for i, citation in enumerate(new_citations[:3], 1):
        print(f"{i}. {citation['citation_text']}")
        print(f"   Type: {citation['source_type']} | Source: {citation['metadata']['category']}")
        print()

    # Merge with existing dataset
    combined_citations, unique_new = scraper.merge_with_existing_dataset(new_citations)

    print(f"\n{'='*80}")
    print("FINAL DATASET SUMMARY")
    print(f"{'='*80}")
    print(f"Total citations after merging: {len(combined_citations)}")
    print(f"Original citations: {len(combined_citations) - len(unique_new)}")
    print(f"New unique citations added: {len(unique_new)}")

    # Save expanded dataset
    output_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations_expanded.jsonl"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for citation in combined_citations:
            f.write(json.dumps(citation, ensure_ascii=False) + '\n')

    print(f"✅ Saved expanded dataset to: {output_file}")

    return combined_citations, unique_new

if __name__ == "__main__":
    main()