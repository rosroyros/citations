#!/usr/bin/env python3
"""
Re-scrape citations from authoritative sources with formatting preserved.

Key improvements:
1. Preserve italics from source HTML
2. Convert to markdown underscores (_text_) immediately
3. Escape literal underscores
4. Normalize HTML to prevent spacing issues
5. Replace duplicates by citation_id
"""

import json
import httpx
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime
from typing import List, Dict
from pathlib import Path
import re


def normalize_html_spacing(html: str) -> str:
    """
    Normalize HTML to prevent spacing issues.

    Issues to fix:
    - No space after closing tags: </i>Text -> </i> Text
    - Multiple spaces: "Text  Text" -> "Text Text"
    - No space between sentences: "title.Next" -> "title. Next"
    """
    # Add space after closing italic/em tags if followed by letter
    html = re.sub(r'</(i|em)>([A-Z])', r'</\1> \2', html)

    # Add space after period if followed by capital letter (new sentence)
    html = re.sub(r'\.([A-Z])', r'. \1', html)

    # Add space after comma if followed by letter
    html = re.sub(r',([A-Za-z])', r', \1', html)

    return html


def convert_html_to_markdown_italics(html: str) -> str:
    """
    Convert HTML with <i>/<em> tags to markdown with underscore italics.

    Steps:
    1. Normalize HTML spacing
    2. Replace <i> and <em> tags with markdown underscores
    3. Extract clean text
    4. Escape literal underscores (preserve markdown italic underscores)
    5. Normalize whitespace

    Example:
        Input:  "Article title. <i>Journal Name</i>, <i>45</i>(2)"
        Output: "Article title. _Journal Name_, _45_(2)"
    """
    # Normalize spacing first
    html = normalize_html_spacing(html)

    # Parse HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Replace italic tags with markdown underscores
    for tag in soup.find_all(['i', 'em']):
        # Insert underscores instead of [ITALIC] markers
        tag.insert_before('_')
        tag.insert_after('_')
        # Remove tag but keep content
        tag.unwrap()

    # Get text
    text = soup.get_text()

    # Escape literal underscores (preserve markdown italic underscores)
    # Strategy: Use placeholder for markdown underscores, escape others, restore
    import uuid
    placeholder = f"__MDITALIC_{uuid.uuid4().hex}__"

    # Replace markdown underscore pairs with placeholder
    text = re.sub(r'_([^_]+)_', lambda m: f'{placeholder}{m.group(1)}{placeholder}', text)

    # Escape remaining underscores (these are literal)
    text = text.replace('_', r'\_')

    # Restore markdown underscores
    text = text.replace(placeholder, '_')

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces -> single space
    text = text.strip()

    # Fix common spacing issues
    text = re.sub(r'\s+([,.])', r'\1', text)  # Remove space before punctuation
    text = re.sub(r'([,.])\s*([,.])', r'\1\2', text)  # Fix "word. ." -> "word."

    return text


class FormattingPreservingScraper:
    """Scraper that preserves italic formatting from sources."""

    def __init__(self):
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)

    def scrape_purdue_owl(self, url: str, section: str) -> List[Dict]:
        """
        Scrape Purdue OWL with formatting preserved.

        Args:
            url: Purdue OWL page URL
            section: Section name (e.g., "Journal Articles", "Books")

        Returns:
            List of citation dictionaries with [ITALIC] markers
        """
        print(f"\nScraping Purdue OWL: {section}")
        print(f"URL: {url}")

        try:
            response = self.client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Purdue OWL uses specific patterns for citations
            # Look for paragraph blocks with citation-like content
            citation_blocks = soup.find_all(['p', 'div', 'li'])

            citations_found = []
            citation_id = 1

            for block in citation_blocks:
                # Get HTML content
                html = str(block)

                # Skip if no actual content or too short
                text_preview = block.get_text(strip=True)
                if len(text_preview) < 20:
                    continue

                # Check if looks like a citation
                if self._looks_like_citation(text_preview):
                    # Convert HTML to markdown underscores
                    citation_text = convert_html_to_markdown_italics(html)

                    # Detect source type
                    source_type = self._detect_source_type(citation_text)

                    # Create citation data
                    citation_data = {
                        "citation_id": f"purdue_owl_{citation_id:03d}",
                        "citation_text": citation_text,
                        "source_type": source_type,
                        "is_valid": True,
                        "metadata": {
                            "source": "Purdue OWL",
                            "url": url,
                            "section": section,
                            "date_collected": datetime.now().isoformat(),
                            "formatting_preserved": True,
                            "verified_against_kb": False
                        }
                    }

                    citations_found.append(citation_data)
                    citation_id += 1

                    # Debug: Print first few
                    if citation_id <= 3:
                        print(f"\n  Example {citation_id}:")
                        print(f"    {citation_text[:100]}...")

            print(f"✓ Found {len(citations_found)} citations")
            return citations_found

        except Exception as e:
            print(f"✗ Error scraping {url}: {e}")
            return []

    def scrape_apa_blog(self, url: str) -> List[Dict]:
        """Scrape APA Style Blog with formatting preserved."""
        print(f"\nScraping APA Style Blog")
        print(f"URL: {url}")

        try:
            response = self.client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # APA blog structure (adjust based on actual HTML)
            citation_blocks = soup.find_all(['p', 'li', 'div'], class_=lambda x: x and 'reference' in x.lower())

            if not citation_blocks:
                citation_blocks = soup.find_all(['p', 'li'])

            citations_found = []
            citation_id = 1

            for block in citation_blocks:
                html = str(block)
                text_preview = block.get_text(strip=True)

                if len(text_preview) < 20:
                    continue

                if self._looks_like_citation(text_preview):
                    citation_text = convert_html_to_markdown_italics(html)
                    source_type = self._detect_source_type(citation_text)

                    citation_data = {
                        "citation_id": f"apa_blog_{citation_id:03d}",
                        "citation_text": citation_text,
                        "source_type": source_type,
                        "is_valid": True,
                        "metadata": {
                            "source": "APA Style Blog",
                            "url": url,
                            "section": "Reference Examples",
                            "date_collected": datetime.now().isoformat(),
                            "formatting_preserved": True,
                            "verified_against_kb": True
                        }
                    }

                    citations_found.append(citation_data)
                    citation_id += 1

            print(f"✓ Found {len(citations_found)} citations")
            return citations_found

        except Exception as e:
            print(f"✗ Error scraping APA blog: {e}")
            return []

    def _looks_like_citation(self, text: str) -> bool:
        """Check if text looks like a citation."""
        # Must have year in parentheses
        has_year = bool(re.search(r'\(\d{4}\)', text))

        # Must have author pattern (Last, F.) or organization
        has_author = bool(re.search(r'[A-Z][a-z]+,\s+[A-Z]\.', text))

        # Should have some length
        has_length = len(text) > 30

        # Shouldn't be instructional text
        not_instruction = not any(word in text.lower() for word in [
            'format:', 'example:', 'note:', 'structure:', 'use this'
        ])

        return (has_year or has_author) and has_length and not_instruction

    def _detect_source_type(self, text: str) -> str:
        """Detect source type from citation text."""
        text_lower = text.lower()

        if 'https://doi.org' in text_lower or 'retrieved' not in text_lower:
            if '(' in text and ')' in text and ',' in text:
                # Has volume/issue pattern -> likely journal
                return 'journal article'

        if '(ed' in text_lower or 'editor' in text_lower:
            if 'in ' in text_lower and '(pp.' in text_lower:
                return 'book chapter'
            return 'book'

        if 'retrieved' in text_lower or 'http' in text_lower:
            if any(word in text_lower for word in ['tweet', 'facebook', 'instagram', 'youtube']):
                return 'social media'
            return 'webpage'

        return 'other'


def merge_with_existing(new_citations: List[Dict], existing_file: Path) -> List[Dict]:
    """
    Merge new citations with existing, replacing duplicates by citation_id.

    Args:
        new_citations: Newly scraped citations
        existing_file: Path to existing citations file

    Returns:
        Merged list with duplicates replaced
    """
    print(f"\nMerging with existing data from {existing_file.name}")

    # Load existing citations
    existing = {}
    if existing_file.exists():
        with open(existing_file) as f:
            for line in f:
                data = json.loads(line)
                existing[data['citation_id']] = data

    print(f"  Existing citations: {len(existing)}")

    # Replace duplicates
    replaced_count = 0
    added_count = 0

    for citation in new_citations:
        cid = citation['citation_id']
        if cid in existing:
            replaced_count += 1
        else:
            added_count += 1
        existing[cid] = citation

    print(f"  Replaced: {replaced_count}")
    print(f"  Added: {added_count}")
    print(f"  Total: {len(existing)}")

    return list(existing.values())


def main():
    """Re-scrape citations with formatting preserved."""
    print("="*80)
    print("RE-SCRAPING CITATIONS WITH FORMATTING PRESERVED")
    print("="*80)

    scraper = FormattingPreservingScraper()
    all_citations = []

    # Purdue OWL pages
    purdue_urls = [
        ("https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html", "Journal Articles"),
        ("https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_books.html", "Books"),
        ("https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_electronic_sources.html", "Electronic Sources"),
    ]

    for url, section in purdue_urls:
        citations = scraper.scrape_purdue_owl(url, section)
        all_citations.extend(citations)

    # APA Style Blog
    apa_citations = scraper.scrape_apa_blog(
        "https://apastyle.apa.org/style-grammar-guidelines/references/examples/journal-article-references"
    )
    all_citations.extend(apa_citations)

    # Save raw scraped data
    output_dir = Path(__file__).parent.parent / "datasets"
    output_dir.mkdir(exist_ok=True)

    raw_output = output_dir / "valid_citations_rescraped_raw.jsonl"
    with open(raw_output, 'w') as f:
        for citation in all_citations:
            f.write(json.dumps(citation) + '\n')

    print(f"\n✓ Saved {len(all_citations)} citations to {raw_output.name}")

    # Merge with existing (replacing duplicates)
    existing_file = output_dir / "valid_citations_merged.jsonl"
    merged_citations = merge_with_existing(all_citations, existing_file)

    # Save merged data
    merged_output = output_dir / "valid_citations_with_formatting.jsonl"
    with open(merged_output, 'w') as f:
        for citation in merged_citations:
            f.write(json.dumps(citation) + '\n')

    print(f"✓ Saved {len(merged_citations)} merged citations to {merged_output.name}")

    # Verify spacing quality (sample check)
    print("\n" + "="*80)
    print("SPACING QUALITY CHECK (Sample)")
    print("="*80)

    spacing_issues = []
    for citation in all_citations[:10]:
        text = citation['citation_text']

        # Check for common spacing issues
        if '.https://' in text or ',https://' in text:
            spacing_issues.append(f"{citation['citation_id']}: Missing space before URL")
        if re.search(r'[a-z][A-Z]', text):  # lowercase followed by uppercase
            spacing_issues.append(f"{citation['citation_id']}: Missing space between words")

    if spacing_issues:
        print("\n⚠️  Found spacing issues:")
        for issue in spacing_issues:
            print(f"  - {issue}")
    else:
        print("\n✓ No spacing issues detected in sample")

    print("\n" + "="*80)
    print("RE-SCRAPING COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review spacing quality in full dataset")
    print("2. Update invalid_citations to match")
    print("3. Regenerate train/val/test splits")
    print("4. Re-run GEPA optimization")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
