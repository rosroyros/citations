"""
Enhanced error injector with multi-error combinations and cross-type errors.
"""
import json
import re
import random
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from error_injector import ErrorInjector


class EnhancedErrorInjector(ErrorInjector):
    """Enhanced error injector with cross-type and multi-error capabilities."""

    def inject_cross_type_error(self, citation: Dict) -> Dict:
        """
        Inject cross-type formatting errors.
        E.g., treating a journal article like a book, webpage like journal, etc.
        """
        text = citation['citation_text']
        true_type = citation['source_type']

        # Journal article treated as book (missing italics on journal, wrong punctuation)
        if true_type == 'journal article' and ',' in text:
            # Remove comma before volume (book style)
            new_text = re.sub(r',\s+(\d+)\(', r'. \\1(', text)
            if new_text != text:
                return {
                    "citation_text": new_text,
                    "source_type": true_type,  # Keep for reference, won't give to LLM
                    "is_valid": False,
                    "errors": [{
                        "component": "Format",
                        "problem": "Using book formatting for journal article (period instead of comma before volume)",
                        "correction": "Journal articles use comma before volume number"
                    }],
                    "metadata": {
                        **citation['metadata'],
                        "derived_from": citation['citation_id'],
                        "error_injection_method": "cross_type",
                        "error_types": ["cross_type_book_journal"],
                        "date_created": datetime.now().isoformat()
                    }
                }

        # Webpage treated as journal (adding volume/issue that doesn't exist)
        if true_type == 'webpage' and 'http' in text:
            # Try to add fake volume/issue before URL
            match = re.search(r'(\.)\s+(https?://)', text)
            if match:
                new_text = text.replace(match.group(0), f'. 12(3), {match.group(2)}')
                return {
                    "citation_text": new_text,
                    "source_type": true_type,
                    "is_valid": False,
                    "errors": [{
                        "component": "Format",
                        "problem": "Adding volume/issue numbers to webpage citation (journal article format)",
                        "correction": "Webpages don't have volume or issue numbers"
                    }],
                    "metadata": {
                        **citation['metadata'],
                        "derived_from": citation['citation_id'],
                        "error_injection_method": "cross_type",
                        "error_types": ["cross_type_webpage_journal"],
                        "date_created": datetime.now().isoformat()
                    }
                }

        return None

    def create_multi_error_variant(self, citation: Dict) -> Dict:
        """Create citation with 2-3 simultaneous errors."""
        text = citation['citation_text']
        errors = []
        error_types = []

        # Apply 2-3 different errors
        # Error 1: Ampersand
        if ' & ' in text:
            text = text.replace(' & ', ' and ', 1)
            errors.append({
                "component": "Authors",
                "problem": "Using 'and' instead of '&' before final author",
                "correction": "Should use '&' in reference list"
            })
            error_types.append("auth001")

        # Error 2: Title case
        match = re.search(r'\((\d{4})\)\.\s+([^.]+)\.', text)
        if match:
            title = match.group(2)
            title_case = title.title()
            if title != title_case:
                text = text.replace(title, title_case)
                errors.append({
                    "component": "Title",
                    "problem": "Using title case instead of sentence case",
                    "correction": f"Should be: {title}"
                })
                error_types.append("cap001")

        # Error 3: Old DOI format
        if 'https://doi.org/' in text and random.random() > 0.5:  # 50% chance
            text = text.replace('https://doi.org/', 'http://dx.doi.org/')
            errors.append({
                "component": "DOI",
                "problem": "Using old DOI format (dx.doi.org)",
                "correction": "Should be: https://doi.org/"
            })
            error_types.append("doi001")

        if len(errors) >= 2:  # Only return if we got at least 2 errors
            return {
                "citation_text": text,
                "source_type": citation['source_type'],
                "is_valid": False,
                "errors": errors,
                "metadata": {
                    **citation['metadata'],
                    "derived_from": citation['citation_id'],
                    "error_injection_method": "multi_error",
                    "error_types": error_types,
                    "date_created": datetime.now().isoformat()
                }
            }

        return None

    def create_comprehensive_error_variants(self, valid_citations: List[Dict]) -> List[Dict]:
        """
        Create comprehensive error variants including:
        - Single errors
        - Multi-errors (2-3 combined)
        - Cross-type errors
        """
        all_invalid = []
        citation_id = 1

        # Get single errors from parent class
        single_errors = super().create_error_variants(valid_citations, variants_per_citation=2)
        all_invalid.extend(single_errors)
        citation_id = len(single_errors) + 1

        # Add multi-error combinations
        for citation in valid_citations:
            multi_error = self.create_multi_error_variant(citation)
            if multi_error:
                multi_error['citation_id'] = f"error_{citation_id:03d}"
                all_invalid.append(multi_error)
                citation_id += 1

        # Add cross-type errors
        for citation in valid_citations:
            cross_error = self.inject_cross_type_error(citation)
            if cross_error:
                cross_error['citation_id'] = f"error_{citation_id:03d}"
                all_invalid.append(cross_error)
                citation_id += 1

        return all_invalid


if __name__ == "__main__":
    # Load valid citations
    valid_file = Path("backend/pseo/optimization/datasets/valid_citations_merged.jsonl")
    valid_citations = []

    with open(valid_file, 'r') as f:
        for line in f:
            valid_citations.append(json.loads(line.strip()))

    print(f"Loaded {len(valid_citations)} valid citations")

    # Create enhanced error injector
    injector = EnhancedErrorInjector()

    # Generate comprehensive error variants
    invalid_citations = injector.create_comprehensive_error_variants(valid_citations)

    # Save to file
    output_file = Path("backend/pseo/optimization/datasets/invalid_citations_enhanced.jsonl")
    with open(output_file, 'w') as f:
        for citation in invalid_citations:
            f.write(json.dumps(citation) + '\n')

    print(f"\n✓ Generated {len(invalid_citations)} invalid citation variants")
    print(f"✓ Saved to: {output_file}")

    # Statistics
    from collections import Counter

    methods = Counter(c['metadata']['error_injection_method'] for c in invalid_citations)
    print(f"\nBy injection method:")
    for method, count in methods.items():
        print(f"  {method}: {count}")

    error_types = []
    for cit in invalid_citations:
        error_types.extend(cit['metadata'].get('error_types', []))

    print(f"\nError types distribution:")
    for error_type, count in Counter(error_types).most_common():
        print(f"  {error_type}: {count}")

    # Calculate ratio
    print(f"\nFinal Dataset Ratio:")
    print(f"  Valid: {len(valid_citations)} ({len(valid_citations)/(len(valid_citations)+len(invalid_citations))*100:.1f}%)")
    print(f"  Invalid: {len(invalid_citations)} ({len(invalid_citations)/(len(valid_citations)+len(invalid_citations))*100:.1f}%)")
    print(f"  Total: {len(valid_citations) + len(invalid_citations)}")
