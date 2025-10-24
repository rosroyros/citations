#!/usr/bin/env python3
"""
Generate all 15 mega guides without LLM review for speed.
Outputs JSON files to content/review_queue/ for later review.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from generator.content_assembler import ContentAssembler

def main():
    """Generate all 15 mega guides."""

    print("🚀 Generating all 15 mega guides...")
    print("=" * 60)

    # Load configurations
    config_file = Path(__file__).parent.parent / "configs" / "mega_guides.json"
    with open(config_file, 'r') as f:
        configs = json.load(f)

    print(f"✅ Loaded {len(configs)} guide configurations")

    # Initialize assembler
    knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"
    templates_dir = Path(__file__).parent.parent / "templates"

    assembler = ContentAssembler(str(knowledge_base_dir), str(templates_dir))
    print("✅ Initialized ContentAssembler")

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
            result = assembler.assemble_mega_guide(config["topic"], assembler_config)

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
                "generation_timestamp": datetime.now().isoformat(),
                "word_count": result["metadata"]["word_count"],
                "target_word_count": config["word_count_target"],
                "generation_status": "generated_without_review"
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
            print(f"  ✅ Generated {result['metadata']['word_count']:,} words (target: {config['word_count_target']:,})")
            print(f"  💾 Saved to: {filename}")

            if "generation_stats" in result.get("template_data", {}):
                cost = result["template_data"]["generation_stats"].get("total_cost", 0.0)
                stats["total_cost"] += cost
                print(f"  💰 Cost: ${cost:.4f}")

        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
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
    print("1. Run LLM review on generated guides")
    print("2. Review 3 guides manually (20% sample)")
    print("3. Approve guides for production")

    return stats["successful"] > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)