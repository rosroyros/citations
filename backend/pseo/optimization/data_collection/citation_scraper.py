"""
Web scrapers for collecting valid APA 7 citations from authoritative sources.
"""
import json
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
from pathlib import Path


class CitationScraper:
    """Scrape valid APA 7 citations from authoritative sources."""

    def __init__(self):
        self.citations = []
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)

    def scrape_apa_blog(self) -> List[Dict]:
        """
        Scrape APA Style Blog examples.

        URL: https://apastyle.apa.org/style-grammar-guidelines/references/examples
        """
        print("Scraping APA Style Blog...")

        url = "https://apastyle.apa.org/style-grammar-guidelines/references/examples"

        try:
            response = self.client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find citation examples (adjust selectors based on actual HTML structure)
            # APA blog typically uses specific CSS classes for examples
            citation_blocks = soup.find_all(['div', 'p', 'li'], class_=lambda x: x and ('example' in x.lower() or 'reference' in x.lower()))

            if not citation_blocks:
                # Fallback: look for common patterns
                citation_blocks = soup.find_all(['p', 'li'])

            citations_found = []
            citation_id = 1

            for block in citation_blocks:
                text = block.get_text(strip=True)

                # Filter for citation-like text (has author name pattern, year, etc.)
                if self._looks_like_citation(text):
                    # Determine source type
                    source_type = self._detect_source_type(text)

                    citation_data = {
                        "citation_id": f"apa_blog_{citation_id:03d}",
                        "citation_text": text,
                        "source_type": source_type,
                        "is_valid": True,
                        "metadata": {
                            "source": "APA Style Blog",
                            "url": url,
                            "section": "Reference Examples",
                            "date_collected": datetime.now().isoformat(),
                            "verified_against_kb": False  # Will verify later
                        }
                    }

                    citations_found.append(citation_data)
                    citation_id += 1

            print(f"✓ Found {len(citations_found)} citations from APA Blog")
            self.citations.extend(citations_found)
            return citations_found

        except Exception as e:
            print(f"✗ Error scraping APA Blog: {e}")
            return []

    def scrape_purdue_owl(self) -> List[Dict]:
        """
        Scrape Purdue OWL APA 7 examples.

        URLs:
        - Journal articles: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html
        - Books: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_books.html
        - Electronic sources: https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_electronic_sources.html
        """
        print("Scraping Purdue OWL...")

        urls = [
            ("https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html", "Journal Articles"),
            ("https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_books.html", "Books"),
            ("https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_electronic_sources.html", "Electronic Sources"),
        ]

        citations_found = []
        citation_id = 1

        for url, section in urls:
            try:
                response = self.client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Purdue OWL often uses specific divs or classes for examples
                example_blocks = soup.find_all(['div', 'p'], class_=lambda x: x and 'example' in x.lower())

                if not example_blocks:
                    # Look for indented or formatted citation examples
                    example_blocks = soup.find_all(['p', 'div'], style=lambda x: x and 'margin-left' in str(x).lower())

                if not example_blocks:
                    # Fallback: find paragraphs with citation patterns
                    all_paragraphs = soup.find_all('p')
                    example_blocks = [p for p in all_paragraphs if self._looks_like_citation(p.get_text(strip=True))]

                for block in example_blocks:
                    text = block.get_text(strip=True)

                    if self._looks_like_citation(text):
                        source_type = self._detect_source_type(text)

                        citation_data = {
                            "citation_id": f"purdue_owl_{citation_id:03d}",
                            "citation_text": text,
                            "source_type": source_type,
                            "is_valid": True,
                            "metadata": {
                                "source": "Purdue OWL",
                                "url": url,
                                "section": section,
                                "date_collected": datetime.now().isoformat(),
                                "verified_against_kb": False
                            }
                        }

                        citations_found.append(citation_data)
                        citation_id += 1

                print(f"✓ Found {len([c for c in citations_found if section in c['metadata']['section']])} citations from {section}")

            except Exception as e:
                print(f"✗ Error scraping {section}: {e}")

        print(f"✓ Total from Purdue OWL: {len(citations_found)} citations")
        self.citations.extend(citations_found)
        return citations_found

    def _looks_like_citation(self, text: str) -> bool:
        """Check if text looks like an APA citation."""
        # Basic heuristics
        if len(text) < 20 or len(text) > 1000:
            return False

        # Should contain year in parentheses
        if '(' not in text or ')' not in text:
            return False

        # Should have period (citations end with periods)
        if '.' not in text:
            return False

        # Should contain comma (author name separator)
        if ',' not in text:
            return False

        # Avoid non-citation text
        if text.startswith(('Note:', 'Example:', 'Format:', 'General', 'In-text')):
            return False

        return True

    def _detect_source_type(self, text: str) -> str:
        """Attempt to detect citation source type from text."""
        text_lower = text.lower()

        # Journal article indicators
        if any(word in text_lower for word in ['journal', 'vol.', 'volume', 'https://doi.org']):
            return "journal article"

        # Book indicators
        if any(word in text_lower for word in ['publisher', 'press', '(ed.)', '(eds.)']):
            # Check for book chapter
            if 'in ' in text_lower and '(eds.)' in text_lower:
                return "book chapter"
            return "book"

        # Webpage indicators
        if any(word in text_lower for word in ['http://', 'https://', 'retrieved from', 'www.']):
            return "webpage"

        return "other"

    def save_citations(self, output_path: str):
        """Save collected citations to JSONL file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            for citation in self.citations:
                f.write(json.dumps(citation) + '\n')

        print(f"\n✓ Saved {len(self.citations)} citations to {output_path}")

    def get_statistics(self) -> Dict:
        """Get collection statistics."""
        from collections import Counter

        stats = {
            "total_citations": len(self.citations),
            "by_source": Counter(c['metadata']['source'] for c in self.citations),
            "by_type": Counter(c['source_type'] for c in self.citations)
        }

        return stats


if __name__ == "__main__":
    scraper = CitationScraper()

    # Scrape APA Blog
    scraper.scrape_apa_blog()

    # Scrape Purdue OWL
    scraper.scrape_purdue_owl()

    # Save to JSONL
    output_file = "backend/pseo/optimization/datasets/valid_citations_raw.jsonl"
    scraper.save_citations(output_file)

    # Print statistics
    stats = scraper.get_statistics()
    print("\n" + "="*79)
    print("COLLECTION STATISTICS")
    print("="*79)
    print(f"Total citations collected: {stats['total_citations']}")
    print(f"\nBy source:")
    for source, count in stats['by_source'].items():
        print(f"  {source}: {count}")
    print(f"\nBy type:")
    for type_, count in stats['by_type'].items():
        print(f"  {type_}: {count}")
