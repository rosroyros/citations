#!/usr/bin/env python3
"""
Test generation with just 3 mega guides to verify the process works.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from generator.content_assembler import ContentAssembler
from review.llm_reviewer import LLMReviewer

def main():
    """Generate first 3 mega guides as a test."""

    print("🧪 Testing generation with 3 mega guides...")
    print("=" * 60)

    # Load configurations
    config_file = Path(__file__).parent.parent / "configs" / "mega_guides.json"
    with open(config_file, 'r') as f:
        configs = json.load(f)

    # Take only first 3 for testing
    test_configs = configs[:3]
    print(f"✅ Testing with {len(test_configs)} guides")

    # Initialize assembler and reviewer
    knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"
    templates_dir = Path(__file__).parent.parent / "templates"

    assembler = ContentAssembler(str(knowledge_base_dir), str(templates_dir))
    reviewer = LLMReviewer()

    print("✅ Initialized ContentAssembler and LLMReviewer")

    # Create output directory
    output_dir = Path(__file__).parent.parent.parent / "content" / "review_queue"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate each guide
    for i, config in enumerate(test_configs, 1):
        print(f"\n[{i}/{len(test_configs)}] Generating: {config['title']}")
        print("-" * 40)

        try:
            # Prepare configuration for assembler
            assembler_config = {
                "title": config["title"],
                "description": config["description"],
                "keywords": config["keywords"],
                "pain_points": config["pain_points"],
                "target_audience": config["target_audience"],
                "url_slug": config["url_slug"]
            }

            # Generate content
            print("  📝 Generating content...")
            result = assembler.assemble_mega_guide(config["topic"], assembler_config)

            # Run LLM review
            print("  🔍 Running LLM review...")
            review = reviewer.review_page(
                result["content"],
                "mega_guide",
                result["metadata"]
            )

            # Prepare page data for saving
            page_data = {
                "guide_id": config["id"],
                "title": config["title"],
                "url": config["url"],
                "page_type": "mega_guide",
                "topic": config["topic"],
                "target_audience": config["target_audience"],
                "content": result["content"],
                "metadata": result["metadata"],
                "llm_review": review,
                "generation_timestamp": datetime.now().isoformat(),
                "word_count": result["metadata"]["word_count"],
                "target_word_count": config["word_count_target"]
            }

            # Save to review queue
            filename = f"mega_guide_{i:02d}_{config['url_slug']}.json"
            output_file = output_dir / filename

            with open(output_file, 'w') as f:
                json.dump(page_data, f, indent=2)

            # Display results
            status = "✅ PASS" if review["overall_verdict"] == "PASS" else "⚠️  NEEDS REVISION"
            print(f"  {status}")
            print(f"  📊 {result['metadata']['word_count']:,} words (target: {config['word_count_target']:,})")
            print(f"  🔢 {len(review['issues_found'])} issues found")
            print(f"  💾 Saved to: {filename}")

        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n✅ Test generation complete!")

if __name__ == "__main__":
    main()