"""
Build comprehensive citation validation prompt from knowledge base.
"""
import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


class PromptBuilder:
    """Build validation prompt from citation_rules.json and common_errors.json"""

    def __init__(self, kb_dir: str = "backend/pseo/knowledge_base"):
        self.kb_dir = Path(kb_dir)
        self.rules = self._load_citation_rules()
        self.common_errors = self._load_common_errors()

    def _load_citation_rules(self) -> List[Dict]:
        """Load citation rules from knowledge base."""
        rules_path = self.kb_dir / "citation_rules.json"
        with open(rules_path, 'r') as f:
            return json.load(f)

    def _load_common_errors(self) -> List[Dict]:
        """Load common errors from knowledge base."""
        errors_path = self.kb_dir / "common_errors.json"
        with open(errors_path, 'r') as f:
            return json.load(f)

    def build_comprehensive_prompt(self) -> str:
        """
        Build comprehensive validation prompt from all 47 rules.

        Structure:
        1. Introduction
        2. Universal rules (author/date)
        3. Source-type specific rules (journal/book/chapter/webpage)
        4. Common errors to catch
        5. Output format specification
        """
        prompt = []

        # 1. Introduction
        prompt.append("You are an APA 7th edition citation validator. Validate each citation below against comprehensive APA 7th edition rules.")
        prompt.append("\n━━━ APA 7TH EDITION COMPREHENSIVE RULES ━━━\n")

        # 2. Organize rules by category
        rules_by_category = defaultdict(list)
        for rule in self.rules:
            category = rule.get('category', 'other')
            rules_by_category[category].append(rule)

        # 3. Universal/Author formatting rules
        prompt.append("UNIVERSAL RULES (ALL SOURCES):")
        if 'author_formatting' in rules_by_category:
            for rule in rules_by_category['author_formatting']:
                prompt.append(f"✓ {rule['description'][:150]}...")  # Truncate long descriptions
                # Add key examples
                for ex in rule.get('examples', [])[:2]:  # Show 2 examples max
                    if ex['type'] == 'correct':
                        prompt.append(f"  ✓ Example: {ex['citation']}")

        # 4. Date formatting rules
        if 'date_formatting' in rules_by_category:
            prompt.append("\nDATE FORMATTING:")
            for rule in rules_by_category['date_formatting']:
                prompt.append(f"✓ {rule['description'][:150]}...")

        # 5. Title capitalization rules
        if 'title_capitalization' in rules_by_category:
            prompt.append("\nTITLE CAPITALIZATION:")
            for rule in rules_by_category['title_capitalization']:
                prompt.append(f"✓ {rule['description'][:150]}...")

        # 6. Italics usage rules
        if 'italics_usage' in rules_by_category:
            prompt.append("\nITALICS USAGE:")
            for rule in rules_by_category['italics_usage']:
                prompt.append(f"✓ {rule['description'][:150]}...")

        # 7. DOI/URL formatting rules
        if 'doi_url_formatting' in rules_by_category:
            prompt.append("\nDOI/URL FORMATTING:")
            for rule in rules_by_category['doi_url_formatting']:
                prompt.append(f"✓ {rule['description'][:150]}...")

        # 8. Common errors to catch
        prompt.append("\nCOMMON ERRORS TO CATCH:")
        for error in self.common_errors[:15]:  # Top 15 most common
            prompt.append(f"- {error['error_name']}: {error['wrong_example']} → {error['correct_example']}")

        # 9. Output format specification
        prompt.append("\n" + "="*79)
        prompt.append("\nOUTPUT FORMAT FOR EACH CITATION:")
        prompt.append("\n" + "="*79)
        prompt.append("\nCITATION #[number]")
        prompt.append("="*79)
        prompt.append("\nORIGINAL:")
        prompt.append("[exact citation text]")
        prompt.append("\nSOURCE TYPE: [journal article/book/book chapter/webpage/other]")
        prompt.append("\nVALIDATION RESULTS:")
        prompt.append("\n[Either:]")
        prompt.append("\n✓ No APA 7 formatting errors detected")
        prompt.append("\n[Or list each error as:]")
        prompt.append("\n❌ [Component]: [What's wrong]")
        prompt.append("   Should be: [Correct format]")
        prompt.append("\n" + "-"*79)
        prompt.append("\nCITATIONS TO VALIDATE:")

        return "\n".join(prompt)

    def save_prompt(self, output_path: str):
        """Save generated prompt to file."""
        prompt = self.build_comprehensive_prompt()
        with open(output_path, 'w') as f:
            f.write(prompt)
        print(f"✓ Comprehensive prompt saved to: {output_path}")
        print(f"✓ Total rules incorporated: {len(self.rules)}")
        print(f"✓ Common errors included: {len(self.common_errors[:15])}")


if __name__ == "__main__":
    builder = PromptBuilder()

    # Generate and save comprehensive prompt
    output_file = "backend/pseo/optimization/comprehensive_validator_prompt.txt"
    builder.save_prompt(output_file)

    # Show preview
    prompt = builder.build_comprehensive_prompt()
    print("\n" + "="*79)
    print("PROMPT PREVIEW (first 1000 chars):")
    print("="*79)
    print(prompt[:1000] + "...")
