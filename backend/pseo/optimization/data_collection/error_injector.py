"""
Programmatic error injection to create invalid citation variants.

Uses common_errors.json to inject realistic APA 7 violations into valid citations.
"""
import json
import re
import random
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class ErrorInjector:
    """Inject errors into valid citations based on common error patterns."""

    def __init__(self, kb_dir: str = "backend/pseo/knowledge_base"):
        self.kb_dir = Path(kb_dir)
        self.common_errors = self._load_common_errors()

    def _load_common_errors(self) -> List[Dict]:
        """Load common errors from knowledge base."""
        errors_path = self.kb_dir / "common_errors.json"
        with open(errors_path, 'r') as f:
            return json.load(f)

    def inject_title_case_error(self, citation: Dict) -> Dict:
        """Inject title case error in article/chapter titles."""
        text = citation['citation_text']

        # Find article title (usually after year and before journal name)
        # Pattern: (Year). Title of article. Journal Name
        match = re.search(r'\((\d{4})\)\.\s+([^.]+)\.', text)

        if match and citation['source_type'] in ['journal article', 'other']:
            title = match.group(2)
            # Convert to title case (wrong for articles)
            title_case = title.title()

            if title != title_case:
                new_text = text.replace(title, title_case)

                return {
                    "citation_text": new_text,
                    "source_type": citation['source_type'],
                    "is_valid": False,
                    "errors": [{
                        "component": "Title",
                        "problem": "Using title case instead of sentence case for article title",
                        "correction": f"Should be: {title}"
                    }],
                    "metadata": {
                        **citation['metadata'],
                        "derived_from": citation['citation_id'],
                        "error_injection_method": "programmatic",
                        "error_types": ["cap001"],
                        "date_created": datetime.now().isoformat()
                    }
                }

        return None

    def inject_missing_italics(self, citation: Dict) -> Dict:
        """Inject missing italics on journal/book names."""
        text = citation['citation_text']

        if citation['source_type'] == 'journal article':
            # Find journal name (after title, before volume)
            # Pattern: Title. Journal Name, volume
            match = re.search(r'\.\s+([A-Z][^,]+),\s+\d+', text)

            if match:
                journal = match.group(1).strip()

                return {
                    "citation_text": text,  # Keep same (can't show italics removal in plain text)
                    "source_type": citation['source_type'],
                    "is_valid": False,
                    "errors": [{
                        "component": "Journal",
                        "problem": "Journal name must be italicized",
                        "correction": f"{journal} should be italicized"
                    }],
                    "metadata": {
                        **citation['metadata'],
                        "derived_from": citation['citation_id'],
                        "error_injection_method": "programmatic",
                        "error_types": ["ital001"],
                        "date_created": datetime.now().isoformat()
                    }
                }

        return None

    def inject_ampersand_error(self, citation: Dict) -> Dict:
        """Replace & with 'and' (common error)."""
        text = citation['citation_text']

        if ' & ' in text:
            new_text = text.replace(' & ', ' and ', 1)  # Replace first occurrence

            return {
                "citation_text": new_text,
                "source_type": citation['source_type'],
                "is_valid": False,
                "errors": [{
                    "component": "Authors",
                    "problem": "Using 'and' instead of '&' before final author",
                    "correction": "Should use '&' in reference list"
                }],
                "metadata": {
                    **citation['metadata'],
                    "derived_from": citation['citation_id'],
                    "error_injection_method": "programmatic",
                    "error_types": ["auth001"],
                    "date_created": datetime.now().isoformat()
                }
            }

        return None

    def inject_old_doi_format(self, citation: Dict) -> Dict:
        """Change DOI to old format (dx.doi.org)."""
        text = citation['citation_text']

        # Find modern DOI
        if 'https://doi.org/' in text:
            new_text = text.replace('https://doi.org/', 'http://dx.doi.org/')

            return {
                "citation_text": new_text,
                "source_type": citation['source_type'],
                "is_valid": False,
                "errors": [{
                    "component": "DOI",
                    "problem": "Using old DOI format (dx.doi.org)",
                    "correction": "Should be: https://doi.org/"
                }],
                "metadata": {
                    **citation['metadata'],
                    "derived_from": citation['citation_id'],
                    "error_injection_method": "programmatic",
                    "error_types": ["doi001"],
                    "date_created": datetime.now().isoformat()
                }
            }

        return None

    def inject_publisher_location(self, citation: Dict) -> Dict:
        """Add publisher location (APA 6 style, wrong for APA 7)."""
        text = citation['citation_text']

        if citation['source_type'] == 'book':
            # Find publisher name (usually at the end before period)
            # Pattern: Publisher Name.
            match = re.search(r'([A-Z][^.]+)\.$', text)

            if match:
                publisher = match.group(1).strip()
                # Common publisher locations
                locations = {
                    "Wiley": "Hoboken, NJ",
                    "Press": "New York, NY",
                    "Oxford": "Oxford, UK",
                    "Cambridge": "Cambridge, UK",
                    "Routledge": "New York, NY"
                }

                location = "New York, NY"  # Default
                for pub_keyword, loc in locations.items():
                    if pub_keyword in publisher:
                        location = loc
                        break

                new_text = text.replace(publisher + '.', f'{location}: {publisher}.')

                return {
                    "citation_text": new_text,
                    "source_type": citation['source_type'],
                    "is_valid": False,
                    "errors": [{
                        "component": "Publisher",
                        "problem": "Including publisher location (removed in APA 7)",
                        "correction": f"Should be: {publisher}. (no location)"
                    }],
                    "metadata": {
                        **citation['metadata'],
                        "derived_from": citation['citation_id'],
                        "error_injection_method": "programmatic",
                        "error_types": ["pub001"],
                        "date_created": datetime.now().isoformat()
                    }
                }

        return None

    def create_error_variants(self, valid_citations: List[Dict], variants_per_citation: int = 2) -> List[Dict]:
        """
        Create error variants from valid citations.

        Args:
            valid_citations: List of valid citation dicts
            variants_per_citation: Number of error variants to create per citation

        Returns:
            List of invalid citation variants
        """
        error_methods = [
            self.inject_title_case_error,
            self.inject_ampersand_error,
            self.inject_old_doi_format,
            self.inject_missing_italics,
            self.inject_publisher_location
        ]

        invalid_citations = []
        citation_id = 1

        for citation in valid_citations:
            # Try each error injection method
            possible_errors = []

            for method in error_methods:
                try:
                    error_variant = method(citation)
                    if error_variant:
                        possible_errors.append(error_variant)
                except Exception as e:
                    continue

            # Select up to variants_per_citation errors
            selected = random.sample(possible_errors, min(len(possible_errors), variants_per_citation))

            for variant in selected:
                variant['citation_id'] = f"error_{citation_id:03d}"
                invalid_citations.append(variant)
                citation_id += 1

        return invalid_citations


if __name__ == "__main__":
    # Load valid citations
    valid_file = Path("backend/pseo/optimization/datasets/valid_citations_merged.jsonl")
    valid_citations = []

    with open(valid_file, 'r') as f:
        for line in f:
            valid_citations.append(json.loads(line.strip()))

    print(f"Loaded {len(valid_citations)} valid citations")

    # Create error injector
    injector = ErrorInjector()

    # Generate error variants
    invalid_citations = injector.create_error_variants(valid_citations, variants_per_citation=2)

    # Save to file
    output_file = Path("backend/pseo/optimization/datasets/invalid_citations_programmatic.jsonl")
    with open(output_file, 'w') as f:
        for citation in invalid_citations:
            f.write(json.dumps(citation) + '\n')

    print(f"\n✓ Generated {len(invalid_citations)} invalid citation variants")
    print(f"✓ Saved to: {output_file}")

    # Statistics
    from collections import Counter
    error_types = []
    for cit in invalid_citations:
        error_types.extend(cit['metadata'].get('error_types', []))

    print(f"\nError types distribution:")
    for error_type, count in Counter(error_types).items():
        print(f"  {error_type}: {count}")
