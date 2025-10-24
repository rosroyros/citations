"""Analyze spacing issues across different citation file versions."""
import json
import re
from pathlib import Path

def analyze_spacing_patterns(filepath):
    """Find patterns of missing/extra spaces in citations."""

    spacing_issues = {
        'missing_after_period': [],  # "word.Word"
        'missing_after_comma': [],   # "word,Word"
        'missing_before_paren': [],  # "word(word"
        'missing_after_paren': [],   # "word)word"
        'double_spaces': [],         # "word  word"
        'clean': []
    }

    with open(filepath) as f:
        for i, line in enumerate(f, 1):
            data = json.loads(line)
            citation = data['citation_text']

            # Check patterns
            has_issue = False

            # Pattern: word.Word (missing space after period)
            if re.search(r'\.\s*[A-Z](?=[a-z])', citation):
                # This is normal (e.g., "J. S." initials)
                pass
            if re.search(r'[a-z]\.[A-Z]', citation):
                spacing_issues['missing_after_period'].append({
                    'line': i,
                    'citation': citation[:100],
                    'matches': re.findall(r'[a-z]\.[A-Z][a-z]+', citation)
                })
                has_issue = True

            # Pattern: word,Word (missing space after comma)
            if re.search(r',[A-Z]', citation):
                spacing_issues['missing_after_comma'].append({
                    'line': i,
                    'citation': citation[:100],
                    'matches': re.findall(r',[A-Z][a-z]+', citation)
                })
                has_issue = True

            # Pattern: word(word (missing space before paren)
            if re.search(r'[a-z]\(', citation):
                spacing_issues['missing_before_paren'].append({
                    'line': i,
                    'citation': citation[:100],
                    'matches': re.findall(r'[a-z]\([a-z]+', citation)
                })
                has_issue = True

            # Pattern: word)word (missing space after paren)
            if re.search(r'\)[a-z]', citation):
                spacing_issues['missing_after_paren'].append({
                    'line': i,
                    'citation': citation[:100],
                    'matches': re.findall(r'\)[a-z]+', citation)
                })
                has_issue = True

            # Pattern: double spaces
            if '  ' in citation:
                spacing_issues['double_spaces'].append({
                    'line': i,
                    'citation': citation[:100]
                })
                has_issue = True

            if not has_issue:
                spacing_issues['clean'].append(i)

    return spacing_issues

def main():
    base_path = Path('backend/pseo/optimization/datasets')

    files_to_check = [
        'valid_citations_raw.jsonl',
        'valid_citations_rescraped_raw.jsonl',
        'valid_citations_merged.jsonl',
        'valid_citations_deduplicated.jsonl'
    ]

    print("="*100)
    print("SPACING ANALYSIS ACROSS CITATION FILES")
    print("="*100)

    for filename in files_to_check:
        filepath = base_path / filename
        if not filepath.exists():
            print(f"\n❌ {filename}: NOT FOUND")
            continue

        print(f"\n{'='*100}")
        print(f"FILE: {filename}")
        print(f"{'='*100}")

        issues = analyze_spacing_patterns(filepath)

        # Count lines
        with open(filepath) as f:
            total_lines = sum(1 for _ in f)

        print(f"\nTotal citations: {total_lines}")
        print(f"Clean citations: {len(issues['clean'])} ({len(issues['clean'])/total_lines:.1%})")

        print(f"\n--- ISSUES FOUND ---")
        print(f"Missing space after period (.Word): {len(issues['missing_after_period'])}")
        print(f"Missing space after comma (,Word): {len(issues['missing_after_comma'])}")
        print(f"Missing space before paren (word(: {len(issues['missing_before_paren'])}")
        print(f"Missing space after paren ()word: {len(issues['missing_after_paren'])}")
        print(f"Double spaces: {len(issues['double_spaces'])}")

        # Show examples
        if issues['missing_after_period']:
            print(f"\n📝 Examples of missing space after period:")
            for ex in issues['missing_after_period'][:3]:
                print(f"  Line {ex['line']}: {ex['citation']}")
                print(f"    Matches: {ex['matches']}")

        if issues['missing_after_comma']:
            print(f"\n📝 Examples of missing space after comma:")
            for ex in issues['missing_after_comma'][:3]:
                print(f"  Line {ex['line']}: {ex['citation']}")
                print(f"    Matches: {ex['matches']}")

        if issues['missing_before_paren']:
            print(f"\n📝 Examples of missing space before paren:")
            for ex in issues['missing_before_paren'][:3]:
                print(f"  Line {ex['line']}: {ex['citation']}")
                print(f"    Matches: {ex['matches']}")

if __name__ == "__main__":
    main()
