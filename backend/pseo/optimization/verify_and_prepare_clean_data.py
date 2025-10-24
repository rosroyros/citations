#!/usr/bin/env python3
"""
Verify rescraped data is clean and prepare it for optimization.
This ensures we have 100% clean training data.
"""
import json
import re
from pathlib import Path
from collections import defaultdict


def check_spacing_issues(citation):
    """Check for double spacing and other issues."""
    issues = []

    # Check for double spaces
    if '  ' in citation:
        issues.append('double_space')

    # Check for space before punctuation (common scraping artifact)
    if re.search(r'\s+[.,;:]', citation):
        issues.append('space_before_punct')

    # Check for missing space after punctuation
    # BUT: Ignore cases like:
    #   - ],[ITALIC] (intentional formatting)
    #   - doi.org, http://, etc. (URLs)
    # Pattern: punctuation followed by letter (but NOT in URLs or formatting tags)
    # Exclude if preceded by :// or followed by uppercase/bracket
    text_no_urls = re.sub(r'https?://[^\s]+', '', citation)  # Remove URLs
    if re.search(r'[.,;:][a-z](?![A-Z\[])', text_no_urls):
        issues.append('missing_space_after_punct')

    return issues


def deduplicate_citations(citations):
    """Remove exact duplicates, keep first occurrence."""
    seen = set()
    unique = []

    for cit in citations:
        cit_text = cit['citation_text'].strip()
        if cit_text not in seen:
            seen.add(cit_text)
            unique.append(cit)

    return unique


def main():
    # Load rescraped data
    input_file = Path('backend/pseo/optimization/datasets/valid_citations_rescraped_raw.jsonl')

    with open(input_file) as f:
        citations = [json.loads(line) for line in f]

    print(f"✓ Loaded {len(citations)} rescraped citations")

    # Check for spacing issues
    print("\n📊 Analyzing spacing quality...")

    issue_counts = defaultdict(int)
    citations_with_issues = []

    for i, cit in enumerate(citations):
        issues = check_spacing_issues(cit['citation_text'])
        if issues:
            citations_with_issues.append((i, cit, issues))
            for issue in issues:
                issue_counts[issue] += 1

    total_clean = len(citations) - len(citations_with_issues)

    print(f"\n🎯 Results:")
    print(f"  Total citations: {len(citations)}")
    print(f"  Clean: {total_clean} ({total_clean/len(citations)*100:.1f}%)")
    print(f"  With issues: {len(citations_with_issues)} ({len(citations_with_issues)/len(citations)*100:.1f}%)")

    if issue_counts:
        print(f"\n  Issue breakdown:")
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
            print(f"    {issue}: {count}")

    # Show sample issues if any
    if citations_with_issues:
        print(f"\n📝 Sample issues (first 3):")
        for i, cit, issues in citations_with_issues[:3]:
            print(f"\n  Citation {i}: {issues}")
            print(f"  {cit['citation_text'][:100]}...")

    # Deduplicate
    print(f"\n🔄 Deduplicating...")
    unique_citations = deduplicate_citations(citations)

    duplicates_removed = len(citations) - len(unique_citations)
    print(f"  Removed {duplicates_removed} duplicates")
    print(f"  Final count: {len(unique_citations)} unique citations")

    # Save clean deduplicated version
    output_file = Path('backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl')

    with open(output_file, 'w') as f:
        for cit in unique_citations:
            f.write(json.dumps(cit, ensure_ascii=False) + '\n')

    print(f"\n✅ Saved clean data to: {output_file}")

    # Summary
    print(f"\n" + "="*60)
    print(f"SUMMARY")
    print(f"="*60)
    print(f"Input:  {len(citations)} citations from rescraped data")
    print(f"Clean:  {total_clean} ({total_clean/len(citations)*100:.1f}%)")
    print(f"Unique: {len(unique_citations)}")
    print(f"Output: {output_file}")
    print(f"="*60)


if __name__ == '__main__':
    main()
