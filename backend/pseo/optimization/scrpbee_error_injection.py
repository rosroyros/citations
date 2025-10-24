#!/usr/bin/env python3
"""
Generate invalid citations from clean scrpbee valid citations using error injection.
Creates diverse error types for robust training.
"""

import json
import random
import re
from datetime import datetime

class ScrpbeeErrorInjector:
    def __init__(self):
        self.error_counter = 1

    def inject_title_case_error(self, citation):
        """Convert article titles from sentence case to title case"""
        text = citation['citation_text']

        # Find article title (between year and journal)
        match = re.search(r'\(\d{4}\)\.\s*([^._]+?)\.\s*[^,]+,', text)
        if match:
            title = match.group(1)
            title_case = self.to_title_case(title)
            new_text = text.replace(title, title_case, 1)

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "title", "Using title case instead of sentence case for article title",
                f"Should be: {title}",
                citation['citation_id'],
                ["cap001"]
            )
        return None

    def inject_and_vs_ampersand_error(self, citation):
        """Replace '&' with 'and' in author list"""
        text = citation['citation_text']

        if ' & ' in text:
            new_text = text.replace(' & ', ' and ')

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "authors", "Using 'and' instead of '&' before final author",
                "Should use '&' in reference list",
                citation['citation_id'],
                ["auth001"]
            )
        return None

    def inject_missing_period_error(self, citation):
        """Remove period after author initial"""
        text = citation['citation_text']

        # Find author initials and remove period
        match = re.search(r'([A-Z])\.(\s*[^,]+)', text)
        if match and match.group(2).strip():
            initial = match.group(1)
            rest = match.group(2)
            new_text = text.replace(f"{initial}.{rest}", f"{initial}{rest}", 1)

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "authors", "Missing period after author initial",
                f"Should be: {initial}.",
                citation['citation_id'],
                ["punc001"]
            )
        return None

    def inject_missing_comma_error(self, citation):
        """Remove comma in author list"""
        text = citation['citation_text']

        # Find comma after author name
        match = re.search(r'([A-Z][a-z]+),\s*', text)
        if match:
            author = match.group(1)
            new_text = text.replace(f"{author}, ", f"{author} ", 1)

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "authors", "Missing comma after author name",
                f"Should be: {author},",
                citation['citation_id'],
                ["punc002"]
            )
        return None

    def inject_missing_parentheses_error(self, citation):
        """Remove parentheses around year"""
        text = citation['citation_text']

        match = re.search(r'\((\d{4})\)', text)
        if match:
            year = match.group(1)
            new_text = text.replace(f"({year})", year, 1)

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "publication_date", "Missing parentheses around publication year",
                f"Should be: ({year})",
                citation['citation_id'],
                ["date001"]
            )
        return None

    def inject_italic_format_error(self, citation):
        """Remove underscores from italicized text"""
        text = citation['citation_text']

        # Find and remove underscores
        if '_' in text:
            # Count underscores
            underscore_count = text.count('_')
            if underscore_count >= 2:  # Need at least 2 for proper italics
                # Remove first pair of underscores
                first_underscore = text.find('_')
                second_underscore = text.find('_', first_underscore + 1)

                if second_underscore > first_underscore:
                    # Remove underscores but keep the text
                    new_text = text[:first_underscore] + text[first_underscore+1:second_underscore] + text[second_underscore+1:]

                    return self.create_invalid_citation(
                        new_text, citation['source_type'],
                        "formatting", "Missing italics for journal/book title",
                        "Title should be italicized (with underscores)",
                        citation['citation_id'],
                        ["ital001"]
                    )
        return None

    def inject_space_error(self, citation):
        """Add extra spaces in various places"""
        text = citation['citation_text']

        errors = [
            # Extra space after comma
            (re.search(r',(\s*[A-Z])', text), lambda m: m.group(0).replace(m.group(1), '  ' + m.group(1))),
            # Extra space before parentheses
            (re.search(r'\s*\(', text), lambda m: m.group(0).replace('(', '  (')),
            # Extra space before period
            (re.search(r'\s*\.', text), lambda m: m.group(0).replace('.', '  .')),
        ]

        for pattern, replacement in errors:
            if pattern:
                try:
                    new_text = text.replace(pattern.group(0), replacement(pattern.group(0)), 1)
                    if new_text != text:
                        return self.create_invalid_citation(
                            new_text, citation['source_type'],
                            "spacing", "Extra spacing in citation",
                            "Remove extra spaces",
                            citation['citation_id'],
                            ["space001"]
                        )
                except:
                    continue
        return None

    def inject_missing_comma_before_edition(self, citation):
        """Remove comma before edition information"""
        text = citation['citation_text']

        # Look for edition patterns
        edition_patterns = [
            r'\((\d+nd ed\.)\)',
            r'\((\d+rd ed\.)\)',
            r'\((\d+th ed\.)\)',
            r'\((\d+st ed\.)\)'
        ]

        for pattern in edition_patterns:
            match = re.search(pattern, text)
            if match:
                edition = match.group(1)
                # Check if there's a comma before the edition
                comma_pos = text.find(f" ({edition})")
                if comma_pos > 0:
                    # Remove the comma
                    new_text = text.replace(f" ({edition})", f"({edition})", 1)

                    return self.create_invalid_citation(
                        new_text, citation['source_type'],
                        "edition", "Missing comma before edition information",
                        f"Should be: ({edition})",
                        citation['citation_id'],
                        ["edn001"]
                    )
        return None

    def inject_doi_format_error(self, citation):
        """Convert DOI to old format"""
        text = citation['citation_text']

        # Look for https://doi.org/ pattern
        match = re.search(r'https://doi\.org/([^.\s]+)', text)
        if match:
            doi = match.group(1)
            old_doi = f"http://dx.doi.org/{doi}"
            new_text = text.replace(match.group(0), old_doi)

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "doi", "Using old DOI format (dx.doi.org)",
                "Should use: https://doi.org/",
                citation['citation_id'],
                ["doi001"]
            )
        return None

    def to_title_case(self, text):
        """Convert text to title case (for error injection)"""
        # Simple title case conversion
        words = text.split()
        title_words = []
        for word in words:
            if len(word) > 1:
                title_words.append(word[0].upper() + word[1:].lower())
            else:
                title_words.append(word.upper())
        return ' '.join(title_words)

    def create_invalid_citation(self, citation_text, source_type, component, problem, correction, derived_from, error_types):
        """Create an invalid citation entry"""

        return {
            "citation_text": citation_text,
            "source_type": source_type,
            "is_valid": False,
            "errors": [{
                "component": component,
                "problem": problem,
                "correction": correction
            }],
            "metadata": {
                "source": "Purdue OWL (ScrapingBee)",
                "section": "Error Injection",
                "date_collected": datetime.now().isoformat(),
                "verified_against_kb": False,
                "derived_from": derived_from,
                "error_injection_method": "programmatic",
                "error_types": error_types,
                "date_created": datetime.now().isoformat()
            },
            "citation_id": f"scrpbee_error_{self.error_counter:03d}"
        }

    def generate_errors_for_citation(self, citation):
        """Generate multiple errors for a single valid citation"""
        errors = []

        # List of error injection methods
        error_methods = [
            self.inject_title_case_error,
            self.inject_and_vs_ampersand_error,
            self.inject_missing_period_error,
            self.inject_missing_comma_error,
            self.inject_missing_parentheses_error,
            self.inject_italic_format_error,
            self.inject_space_error,
            self.inject_missing_comma_before_edition,
            self.inject_doi_format_error
        ]

        # Shuffle methods for randomness
        random.shuffle(error_methods)

        # Generate 1-3 errors per citation
        num_errors = min(random.randint(1, 3), len(error_methods))

        for i, method in enumerate(error_methods[:num_errors]):
            try:
                error = method(citation)
                if error:
                    errors.append(error)
                    self.error_counter += 1
            except Exception as e:
                print(f"⚠️  Error generating {method.__name__}: {e}")
                continue

        return errors

    def generate_invalid_dataset(self, valid_citations_file, output_file):
        """Generate invalid citations from valid ones"""

        # Load valid citations
        valid_citations = []
        with open(valid_citations_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    valid_citations.append(json.loads(line))

        print(f"📚 Loaded {len(valid_citations)} valid citations")

        # Generate errors
        all_invalid_citations = []

        for citation in valid_citations:
            errors = self.generate_errors_for_citation(citation)
            all_invalid_citations.extend(errors)

        # Save invalid citations
        with open(output_file, 'w', encoding='utf-8') as f:
            for citation in all_invalid_citations:
                f.write(json.dumps(citation, ensure_ascii=False) + '\n')

        return all_invalid_citations

def main():
    print("=" * 80)
    print("GENERATING INVALID CITATIONS FOR SCRPBEE DATASET")
    print("=" * 80)

    injector = ScrpbeeErrorInjector()

    valid_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations_clean.jsonl"
    invalid_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_invalid_citations.jsonl"

    invalid_citations = injector.generate_invalid_dataset(valid_file, invalid_file)

    print(f"\n{'='*80}")
    print("ERROR INJECTION COMPLETE")
    print(f"{'='*80}")
    print(f"Generated {len(invalid_citations)} invalid citations")
    print(f"Saved to: {invalid_file}")

    # Error type breakdown
    error_types = {}
    source_types = {}

    for citation in invalid_citations:
        source_type = citation['source_type']
        source_types[source_type] = source_types.get(source_type, 0) + 1

        for error_type in citation['metadata']['error_types']:
            error_types[error_type] = error_types.get(error_type, 0) + 1

    print(f"\n📊 Invalid citations by source type:")
    for source_type, count in sorted(source_types.items()):
        print(f"   {source_type}: {count}")

    print(f"\n🔧 Error types generated:")
    for error_type, count in sorted(error_types.items()):
        print(f"   {error_type}: {count}")

    # Show sample errors
    print(f"\n📝 Sample invalid citations:")
    for i, citation in enumerate(invalid_citations[:3], 1):
        print(f"{i}. {citation['citation_text']}")
        print(f"   Error: {citation['errors'][0]['problem']}")
        print(f"   Type: {citation['source_type']} | ID: {citation['citation_id']}")
        print()

if __name__ == "__main__":
    main()