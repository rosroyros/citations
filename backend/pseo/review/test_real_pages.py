"""
Test LLM reviewer against real generated pages from Task 3.4
"""

import json
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.pseo.review.llm_reviewer import LLMReviewer


def extract_front_matter(content: str) -> tuple:
    """Extract YAML front matter from markdown."""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    # Simple YAML parsing (just key: value pairs)
    front_matter = {}
    for line in parts[1].strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            front_matter[key.strip()] = value.strip().strip('"\'')

    return front_matter, parts[2].strip()


def review_page(page_path: Path, reviewer: LLMReviewer):
    """Review a single page."""
    print(f"\n{'='*60}")
    print(f"Reviewing: {page_path.name}")
    print('='*60)

    # Read content
    content = page_path.read_text()
    front_matter, main_content = extract_front_matter(content)

    # Load stats if available
    stats_path = page_path.parent / f"{page_path.stem}_stats.json"
    stats = {}
    if stats_path.exists():
        stats = json.loads(stats_path.read_text())

    # Determine page type from filename
    page_type = "mega_guide" if "check-apa" in page_path.stem or "errors" in page_path.stem else "source_type"

    # Build metadata
    metadata = {
        "meta_title": front_matter.get('title', ''),
        "meta_description": front_matter.get('description', ''),
        "word_count": stats.get('word_count', len(main_content.split())),
        "reading_time": stats.get('reading_time', 'Unknown'),
        "last_updated": front_matter.get('date', '2024-10-13')
    }

    # Review
    result = reviewer.review_page(main_content, page_type, metadata)

    # Display results
    print(f"\nPage Type: {page_type}")
    print(f"Word Count: {result['word_count']:,}")
    print(f"Uniqueness Score: {result['uniqueness_score']:.2f}")
    print(f"\nOverall Verdict: {result['overall_verdict']}")
    print(f"Summary: {result['review_summary']}")

    if result['issues_found']:
        print(f"\nIssues Found ({len(result['issues_found'])}):")
        for i, issue in enumerate(result['issues_found'], 1):
            icon = "🔴" if issue['severity'] == "high" else "🟡" if issue['severity'] == "medium" else "🟢"
            print(f"\n{i}. {icon} [{issue['severity'].upper()}] {issue['issue']}")
            print(f"   Location: {issue['location']}")
            print(f"   Suggestion: {issue['suggestion']}")
    else:
        print("\n✅ No issues found!")

    return result


def main():
    """Review all test pages."""
    reviewer = LLMReviewer()

    content_dir = Path(__file__).parent.parent.parent.parent / "content" / "test"

    if not content_dir.exists():
        print(f"❌ Content directory not found: {content_dir}")
        return

    # Find all markdown files (exclude stats files)
    md_files = [f for f in content_dir.glob("*.md")]

    if not md_files:
        print(f"❌ No markdown files found in {content_dir}")
        return

    print(f"\n📝 Found {len(md_files)} pages to review")

    results = {}
    for md_file in sorted(md_files):
        result = review_page(md_file, reviewer)
        results[md_file.name] = result

    # Summary
    print(f"\n\n{'='*60}")
    print("REVIEW SUMMARY")
    print('='*60)

    pass_count = sum(1 for r in results.values() if r['overall_verdict'] == 'PASS')
    needs_revision = sum(1 for r in results.values() if r['overall_verdict'] == 'NEEDS_REVISION')

    print(f"\nTotal Pages: {len(results)}")
    print(f"✅ PASS: {pass_count}")
    print(f"⚠️  NEEDS REVISION: {needs_revision}")

    if needs_revision > 0:
        print(f"\nPages needing revision:")
        for name, result in results.items():
            if result['overall_verdict'] == 'NEEDS_REVISION':
                high_issues = [i for i in result['issues_found'] if i['severity'] == 'high']
                print(f"  - {name}: {len(high_issues)} high-severity issues")

    # Save full results to JSON
    results_file = content_dir / "_review_results.json"
    results_data = {
        name: {
            'verdict': result['overall_verdict'],
            'word_count': result['word_count'],
            'issues_count': len(result['issues_found']),
            'issues': result['issues_found']
        }
        for name, result in results.items()
    }
    results_file.write_text(json.dumps(results_data, indent=2))
    print(f"\n💾 Full results saved to: {results_file}")


if __name__ == "__main__":
    main()
