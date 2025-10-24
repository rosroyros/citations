#!/usr/bin/env python3
"""
Run LLM review on all generated guides in the review queue.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from review.llm_reviewer import LLMReviewer

def main():
    """Run LLM review on all guides in review queue."""

    print("🔍 Running LLM review on generated guides...")
    print("=" * 60)

    # Find all mega guide files
    # Look in both possible locations
    possible_paths = [
        Path(__file__).parent.parent / "content" / "review_queue",  # backend/content/review_queue
        Path(__file__).parent.parent.parent / "content" / "review_queue"  # content/review_queue
    ]

    review_queue_dir = None
    mega_guide_files = []

    for path in possible_paths:
        if path.exists():
            review_queue_dir = path
            mega_guide_files = list(path.glob("mega_guide_*.json"))
            if mega_guide_files:
                break

    if not mega_guide_files:
        print("❌ No mega guide files found in review queue")
        return False

    print(f"✅ Found {len(mega_guide_files)} guides to review")

    # Initialize reviewer
    reviewer = LLMReviewer()
    print("✅ Initialized LLMReviewer")

    # Track review statistics
    stats = {
        "total_guides": len(mega_guide_files),
        "reviewed": 0,
        "passed": 0,
        "needs_revision": 0,
        "failed": 0,
        "total_issues": 0,
        "start_time": datetime.now().isoformat()
    }

    # Review each guide
    for i, guide_file in enumerate(mega_guide_files, 1):
        print(f"\n[{i}/{len(mega_guide_files)}] Reviewing: {guide_file.name}")
        print("-" * 40)

        try:
            # Load guide data
            with open(guide_file, 'r') as f:
                guide_data = json.load(f)

            print(f"  📄 {guide_data['title']}")
            print(f"  📊 {guide_data['word_count']:,} words")

            # Run LLM review
            print("  🔍 Running LLM review...")
            review = reviewer.review_page(
                guide_data["content"],
                guide_data["page_type"],
                guide_data["metadata"]
            )

            # Add review to guide data
            guide_data["llm_review"] = review
            guide_data["llm_review_timestamp"] = datetime.now().isoformat()

            # Save updated guide data
            with open(guide_file, 'w') as f:
                json.dump(guide_data, f, indent=2)

            # Update statistics
            stats["reviewed"] += 1
            stats["total_issues"] += len(review["issues_found"])

            # Display results
            if review["overall_verdict"] == "PASS":
                stats["passed"] += 1
                print(f"  ✅ PASS - {len(review['issues_found'])} issues found")
            else:
                stats["needs_revision"] += 1
                print(f"  ⚠️  NEEDS_REVISION - {len(review['issues_found'])} issues found")

            # Show top issues
            if review["issues_found"]:
                print("  📋 Top issues:")
                for issue in review["issues_found"][:3]:
                    print(f"     - {issue['severity']}: {issue['issue'][:60]}...")

        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            stats["failed"] += 1
            continue

    # Final statistics
    stats["end_time"] = datetime.now().isoformat()

    print("\n" + "=" * 60)
    print("📊 REVIEW COMPLETE")
    print("=" * 60)
    print(f"✅ Reviewed: {stats['reviewed']}/{stats['total_guides']} guides")
    print(f"📈 Passed: {stats['passed']}")
    print(f"⚠️  Needs revision: {stats['needs_revision']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"🔢 Total issues found: {stats['total_issues']}")
    print(f"📋 Average issues per guide: {stats['total_issues'] // max(stats['reviewed'], 1)}")

    # Save review statistics
    stats_file = review_queue_dir / "review_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"\n📋 Review statistics saved to: {stats_file}")
    print("\n👀 Next steps:")
    print("1. Review guides that need revision")
    print("2. Approve guides for production")
    print("3. Move approved guides to content/approved/mega-guides/")

    return stats["reviewed"] > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)