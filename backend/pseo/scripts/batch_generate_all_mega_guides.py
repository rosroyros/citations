#!/usr/bin/env python3
"""
Batch generate all 15 mega guides with LLM review and HTML build.

This script:
1. Loads all mega guide configs
2. Generates each guide (markdown + LLM content)
3. Runs LLM quality review
4. Converts to HTML
5. Saves results to review queue
6. Reports summary statistics

Usage:
    python3 batch_generate_all_mega_guides.py
"""

import json
import sys
import logging
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.content_assembler import ContentAssembler
from review.llm_reviewer import LLMReviewer
from builder.static_generator import StaticSiteGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Batch generate all mega guides"""

    logger.info("=" * 80)
    logger.info("BATCH MEGA GUIDE GENERATION")
    logger.info("=" * 80)

    # Load configurations
    config_file = Path(__file__).parent.parent / "configs" / "mega_guides.json"
    with open(config_file, 'r') as f:
        configs = json.load(f)

    logger.info(f"\n📘 Generating {len(configs)} mega guides")
    logger.info(f"Estimated cost: ${len(configs) * 0.003:.2f} (~$0.003 per guide)")

    # Initialize
    knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"
    templates_dir = Path(__file__).parent.parent / "templates"

    assembler = ContentAssembler(str(knowledge_base_dir), str(templates_dir))
    reviewer = LLMReviewer()

    # Load layout template
    layout_file = Path(__file__).parent.parent / "builder" / "templates" / "layout.html"
    layout_template = layout_file.read_text()
    generator = StaticSiteGenerator(layout_template)

    # Output directories
    test_dir = Path(__file__).parent.parent.parent.parent / "content" / "test"
    review_queue_dir = Path(__file__).parent.parent.parent.parent / "content" / "review_queue"
    output_dir = Path(__file__).parent.parent.parent.parent / "content" / "dist"

    test_dir.mkdir(parents=True, exist_ok=True)
    review_queue_dir.mkdir(parents=True, exist_ok=True)

    # Track statistics
    stats = {
        "total": len(configs),
        "generated": 0,
        "passed": 0,
        "needs_revision": 0,
        "failed": 0,
        "total_words": 0,
        "total_cost": 0.0,
        "issues": []
    }

    # Generate each guide
    for i, config in enumerate(configs):
        guide_num = i + 1
        logger.info(f"\n{'=' * 80}")
        logger.info(f"[{guide_num}/{len(configs)}] {config['title']}")
        logger.info(f"{'=' * 80}")

        try:
            # Prepare config
            assembler_config = {
                "title": config["title"],
                "description": config["description"],
                "keywords": config["keywords"],
                "pain_points": config["pain_points"],
                "target_audience": config["target_audience"],
                "url_slug": config["url_slug"],
                "url": config["url"]
            }

            # Generate content
            logger.info("Generating content...")
            result = assembler.assemble_mega_guide(config["topic"], assembler_config)
            word_count = result['metadata']['word_count']
            logger.info(f"✓ Generated {word_count:,} words")

            # Update stats
            stats["total_words"] += word_count
            stats["generated"] += 1

            # LLM review
            logger.info("Running LLM review...")
            review = reviewer.review_page(
                result['content'],
                'mega_guide',
                result['metadata']
            )

            verdict = review['overall_verdict']
            issues_count = len(review['issues_found'])
            high_issues = len([i for i in review['issues_found'] if i['severity'] == 'high'])

            logger.info(f"✓ Review complete: {verdict} ({issues_count} issues, {high_issues} high)")

            if verdict == 'PASS':
                stats["passed"] += 1
            else:
                stats["needs_revision"] += 1
                stats["issues"].append({
                    "guide": config["title"],
                    "issues": review['issues_found']
                })

            # Save markdown
            front_matter = f"""---
title: {config['title']}
description: {config['description']}
page_type: mega_guide
url_slug: {config['url_slug']}
url: {config['url']}
last_updated: {datetime.now().strftime('%Y-%m-%d')}
word_count: {result['metadata']['word_count']}
reading_time: {result['metadata']['reading_time']}
---

"""
            markdown_filename = f"{config['url_slug']}.md"
            markdown_file = test_dir / markdown_filename

            with open(markdown_file, 'w') as f:
                f.write(front_matter + result['content'])

            logger.info(f"✓ Markdown: content/test/{markdown_filename}")

            # Save to review queue
            page_data = {
                "guide_id": config["id"],
                "title": config["title"],
                "url": config["url"],
                "page_type": "mega_guide",
                "content": result["content"],
                "metadata": result["metadata"],
                "llm_review": review,
                "word_count": result["metadata"]["word_count"],
                "generated_at": datetime.now().isoformat()
            }

            json_filename = f"mega_guide_{i:02d}_{config['url_slug']}.json"
            json_file = review_queue_dir / json_filename

            with open(json_file, 'w') as f:
                json.dump(page_data, f, indent=2)

            logger.info(f"✓ Review queue: {json_filename}")

        except Exception as e:
            logger.error(f"✗ FAILED: {e}")
            stats["failed"] += 1
            import traceback
            traceback.print_exc()
            continue

    # Build all HTML files
    logger.info(f"\n{'=' * 80}")
    logger.info("BUILDING HTML FILES")
    logger.info(f"{'=' * 80}")

    try:
        generator.build_site(str(test_dir), str(output_dir))
        logger.info("✓ HTML generation complete")

        # Copy assets
        assets_src = Path(__file__).parent.parent / "builder" / "assets"
        assets_dest = output_dir / "assets"

        if assets_src.exists():
            if assets_dest.exists():
                shutil.rmtree(assets_dest)
            shutil.copytree(assets_src, assets_dest)
            logger.info("✓ Assets copied")

    except Exception as e:
        logger.error(f"✗ HTML generation failed: {e}")
        import traceback
        traceback.print_exc()

    # Final summary
    logger.info(f"\n{'=' * 80}")
    logger.info("BATCH GENERATION COMPLETE")
    logger.info(f"{'=' * 80}")

    logger.info(f"\n📊 STATISTICS:")
    logger.info(f"   Total guides: {stats['total']}")
    logger.info(f"   ✓ Generated: {stats['generated']}")
    logger.info(f"   ✓ Passed review: {stats['passed']}")
    logger.info(f"   ⚠ Needs revision: {stats['needs_revision']}")
    logger.info(f"   ✗ Failed: {stats['failed']}")
    logger.info(f"   Total words: {stats['total_words']:,}")
    logger.info(f"   Avg words/guide: {stats['total_words']//stats['generated'] if stats['generated'] > 0 else 0:,}")

    logger.info(f"\n💰 ESTIMATED COST:")
    logger.info(f"   ~${stats['generated'] * 0.003:.3f} (actual cost tracked in individual logs)")

    if stats['needs_revision'] > 0:
        logger.info(f"\n⚠️  {stats['needs_revision']} guides need revision:")
        for issue_data in stats['issues'][:5]:  # Show first 5
            logger.info(f"   - {issue_data['guide']}: {len(issue_data['issues'])} issues")

    logger.info(f"\n📁 OUTPUT:")
    logger.info(f"   Markdown: content/test/")
    logger.info(f"   Review queue: content/review_queue/")
    logger.info(f"   HTML: content/dist/")

    logger.info(f"\n🌐 TEST LOCALLY:")
    logger.info(f"   cd content/dist")
    logger.info(f"   python3 -m http.server 8003 --bind 0.0.0.0")
    logger.info(f"   open http://localhost:8003/guide/")

    logger.info("=" * 80)

    return 0 if stats['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
