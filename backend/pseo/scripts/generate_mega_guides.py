#!/usr/bin/env python3
"""
Generate all 15 mega guides using ContentAssembler and LLM integration.
Outputs JSON files to content/review_queue/ for human review.
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

def load_mega_guide_configs():
    """Load mega guide configurations from JSON file."""
    config_file = Path(__file__).parent.parent / "configs" / "mega_guides.json"

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(config_file, 'r') as f:
        return json.load(f)

def generate_mega_guides():
    """Generate all 15 mega guides."""

    print("🚀 Starting generation of 15 mega guides...")
    print("=" * 60)

    # Load configurations
    try:
        configs = load_mega_guide_configs()
        print(f"✅ Loaded {len(configs)} guide configurations")
    except Exception as e:
        print(f"❌ Failed to load configurations: {e}")
        return False

    # Initialize assembler and reviewer
    try:
        knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"
        templates_dir = Path(__file__).parent.parent / "templates"

        assembler = ContentAssembler(str(knowledge_base_dir), str(templates_dir))
        reviewer = LLMReviewer()

        print("✅ Initialized ContentAssembler and LLMReviewer")
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return False

    # Create output directory
    output_dir = Path(__file__).parent.parent.parent / "content" / "review_queue"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track generation statistics
    stats = {
        "total_guides": len(configs),
        "successful": 0,
        "failed": 0,
        "total_words": 0,
        "total_cost": 0.0,
        "start_time": datetime.now().isoformat()
    }

    # Generate each guide
    for i, config in enumerate(configs, 1):
        print(f"\n[{i}/{len(configs)}] Generating: {config['title']}")
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

            # Update statistics
            stats["successful"] += 1
            stats["total_words"] += result["metadata"]["word_count"]

            # Display results
            status = "✅ PASS" if review["overall_verdict"] == "PASS" else "⚠️  NEEDS REVISION"
            print(f"  {status}")
            print(f"  📊 {result['metadata']['word_count']:,} words (target: {config['word_count_target']:,})")
            print(f"  🔢 {len(review['issues_found'])} issues found")
            print(f"  💾 Saved to: {filename}")

            if "generation_stats" in result.get("template_data", {}):
                cost = result["template_data"]["generation_stats"].get("total_cost", 0.0)
                stats["total_cost"] += cost
                print(f"  💰 Cost: ${cost:.4f}")

        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            stats["failed"] += 1
            continue

    # Final statistics
    stats["end_time"] = datetime.now().isoformat()

    print("\n" + "=" * 60)
    print("📊 GENERATION COMPLETE")
    print("=" * 60)
    print(f"✅ Successfully generated: {stats['successful']}/{stats['total_guides']} guides")
    print(f"❌ Failed: {stats['failed']}")
    print(f"📝 Total words: {stats['total_words']:,}")
    print(f"📈 Average words per guide: {stats['total_words'] // max(stats['successful'], 1):,}")
    print(f"💰 Total cost: ${stats['total_cost']:.4f}")
    print(f"📁 Output directory: {output_dir}")
    print(f"⏰ Started: {stats['start_time']}")
    print(f"⏰ Finished: {stats['end_time']}")

    # Save generation statistics
    stats_file = output_dir / "generation_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"\n📋 Statistics saved to: {stats_file}")
    print("\n👀 Next steps:")
    print("1. Run human review: python3 backend/pseo/review/human_review_cli.py")
    print("2. Review 3 guides manually (20% sample)")
    print("3. Approve guides for production")

    return stats["successful"] > 0

if __name__ == "__main__":
    success = generate_mega_guides()
    sys.exit(0 if success else 1)