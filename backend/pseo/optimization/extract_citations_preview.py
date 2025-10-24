#!/usr/bin/env python3
"""
Better extraction and preview of citation examples from Purdue OWL
"""

import os
from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup
import re
import json

def extract_citations_from_page(url, page_name):
    """Extract complete citation examples with better parsing"""

    api_key = "LIBY0CW5QYMS826LW2M3YPF97V3RT7H7I89EFIISANIKDV5LWYF27N8K4JNPZA9AURXUJVRZYYQWARUR"
    client = ScrapingBeeClient(api_key=api_key)

    print(f"\n{'='*80}")
    print(f"EXTRACTING CITATIONS FROM: {page_name}")
    print(f"URL: {url}")
    print(f"{'='*80}")

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
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find main content area
        main_content = soup.find('main') or soup.find('div', class_='main') or soup

        citations = []

        # Look for example blocks (common in Purdue OWL)
        example_blocks = main_content.find_all(['p', 'div'], string=re.compile(r'example|Example', re.I))

        for block in example_blocks:
            # Check following siblings for actual examples
            next_sibling = block.find_next_sibling(['p', 'div', 'blockquote'])
            if next_sibling:
                text = next_sibling.get_text().strip()
                if len(text) > 50 and '(' in text and ')' in text and any(char in text for char in '.&'):
                    citations.append(text)

        # Look for code blocks or pre elements that might contain citations
        code_blocks = main_content.find_all(['code', 'pre', 'blockquote'])
        for block in code_blocks:
            text = block.get_text().strip()
            if len(text) > 30 and '(' in text and ')' in text and any(char in text for char in '.&'):
                citations.append(text)

        # Look for paragraphs that look like citations
        paragraphs = main_content.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            # Better citation detection patterns
            if re.search(r'[A-Z][a-z]+, [A-Z]\.?\s*\(\d{4}\)', text) and len(text) > 40:
                citations.append(text)

        # Remove duplicates and clean up
        unique_citations = []
        seen = set()

        for citation in citations:
            # Clean up citation
            citation = re.sub(r'\s+', ' ', citation).strip()

            # Filter out non-citation content
            if len(citation) < 30 or 'click here' in citation.lower():
                continue

            if citation not in seen:
                seen.add(citation)
                unique_citations.append(citation)

        # Display results
        print(f"Found {len(unique_citations)} unique citations:")

        for i, citation in enumerate(unique_citations[:10], 1):  # Show max 10
            print(f"\n{i}. {citation}")

            # Analyze citation components
            analysis = analyze_citation(citation)
            print(f"   Type: {analysis['type']}")
            print(f"   Has DOI: {analysis['has_doi']}")
            print(f"   Has URL: {analysis['has_url']}")
            print(f"   Italics count: {analysis['italics_count']}")

        if len(unique_citations) > 10:
            print(f"\n... and {len(unique_citations) - 10} more citations")

        return unique_citations

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return []

def analyze_citation(citation):
    """Analyze citation structure"""

    return {
        'type': determine_citation_type(citation),
        'has_doi': bool(re.search(r'doi\.org|dx\.doi\.org|doi:', citation, re.I)),
        'has_url': bool(re.search(r'https?://', citation)),
        'italics_count': citation.count('_') // 2,  # Underscores indicate italics
        'has_edition': bool(re.search(r'\d+(?:st|nd|rd|th)\s*ed\.?|\(\d+ed\.?\)', citation, re.I)),
        'has_volume': bool(re.search(r'\d+\(\d+\)', citation)),
        'has_pages': bool(re.search(r'pp?\.\s*\d+|\d+-\d+', citation))
    }

def determine_citation_type(citation):
    """Determine citation type based on patterns"""

    citation_lower = citation.lower()

    if 'doi:' in citation_lower or 'doi.org' in citation_lower:
        return 'Journal Article (with DOI)'
    elif re.search(r'\d+\(\d+\)', citation):
        return 'Journal Article (volume/issue)'
    elif 'ed.' in citation_lower or 'edition' in citation_lower:
        return 'Book'
    elif 'trans.' in citation_lower or 'translator' in citation_lower:
        return 'Translated Book'
    elif 'http://' in citation or 'https://' in citation:
        return 'Electronic Source'
    elif 'press' in citation_lower or 'publisher' in citation_lower:
        return 'Book'
    else:
        return 'Other'

if __name__ == "__main__":
    # Test multiple pages
    pages = [
        {
            'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html",
            'name': "Articles in Periodicals"
        },
        {
            'url': "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_books.html",
            'name': "Books"
        }
    ]

    all_citations = []

    for page in pages:
        citations = extract_citations_from_page(page['url'], page['name'])
        all_citations.extend(citations)

    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    print(f"Total citations from all pages: {len(all_citations)}")

    if all_citations:
        types = {}
        for citation in all_citations:
            analysis = analyze_citation(citation)
            cite_type = analysis['type']
            types[cite_type] = types.get(cite_type, 0) + 1

        print("\nAll citation types found:")
        for cite_type, count in types.items():
            print(f"  {cite_type}: {count}")

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total citations extracted: {len(citations)}")

    if citations:
        types = {}
        for citation in citations:
            analysis = analyze_citation(citation)
            cite_type = analysis['type']
            types[cite_type] = types.get(cite_type, 0) + 1

        print("\nCitation types found:")
        for cite_type, count in types.items():
            print(f"  {cite_type}: {count}")