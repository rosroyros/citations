#!/usr/bin/env python3
"""
End-to-end script to generate 1 complete source type guide and build it to HTML.

This validates the entire pipeline:
1. Generate markdown content (LLM)
2. Run LLM quality review
3. Save to review_queue/
4. Convert to HTML
5. Deploy to content/dist/
6. Report results

Usage:
    python3 generate_and_build_one_source_type.py [source_type_number]

    source_type_number: 0-26 (default: 0 = "Conference Paper")
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
    """Generate and build one complete source type guide"""

    # Which source type to generate?
    source_type_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    logger.info("=" * 80)
    logger.info("END-TO-END SOURCE TYPE GUIDE GENERATION & BUILD")
    logger.info("=" * 80)

    # ========================================
    # STEP 1: Load configuration
    # ========================================
    config_file = Path(__file__).parent.parent / "configs" / "source_type_guides.json"
    with open(config_file, 'r') as f:
        configs = json.load(f)

    if source_type_index >= len(configs):
        logger.error(f"Invalid source type index: {source_type_index} (max: {len(configs)-1})")
        sys.exit(1)

    config = configs[source_type_index]

    logger.info(f"\n📘 Generating Source Type Guide #{source_type_index}: {config['title']}")
    logger.info(f"   Topic: {config['topic']}")
    logger.info(f"   Target: {config['word_count_target']:,} words")
    logger.info(f"   URL: {config['url']}")

    # ========================================
    # STEP 2: Generate content
    # ========================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1: GENERATING CONTENT (LLM)")
    logger.info("=" * 80)

    knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"
    templates_dir = Path(__file__).parent.parent / "templates"

    assembler = ContentAssembler(str(knowledge_base_dir), str(templates_dir))

    assembler_config = {
        "title": config["title"],
        "description": config["description"],
        "keywords": config["keywords"],
        "pain_points": config["pain_points"],
        "target_audience": config["target_audience"],
        "url_slug": config["url_slug"],
        "url": config["url"]
    }

    try:
        # Use assemble_source_type_page instead of assemble_mega_guide
        result = assembler.assemble_source_type_page(config["topic"], assembler_config)
        word_count = result['metadata']['word_count']
        logger.info(f"✅ Content generated: {word_count:,} words")

        if word_count < config['word_count_target']:
            logger.warning(f"⚠️  Below target by {config['word_count_target'] - word_count:,} words")

    except Exception as e:
        logger.error(f"❌ Content generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ========================================
    # STEP 3: LLM quality review
    # ========================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: LLM QUALITY REVIEW")
    logger.info("=" * 80)

    reviewer = LLMReviewer()

    try:
        review = reviewer.review_page(
            result['content'],
            'source_type',  # Changed from 'mega_guide'
            result['metadata']
        )

        logger.info(f"Verdict: {review['overall_verdict']}")
        logger.info(f"Issues found: {len(review['issues_found'])}")

        if review['issues_found']:
            logger.info("\nIssues breakdown:")
            high = [i for i in review['issues_found'] if i['severity'] == 'high']
            medium = [i for i in review['issues_found'] if i['severity'] == 'medium']
            low = [i for i in review['issues_found'] if i['severity'] == 'low']

            if high:
                logger.warning(f"  🔴 High: {len(high)}")
                for issue in high[:3]:  # Show first 3
                    logger.warning(f"     - {issue['issue']}")
            if medium:
                logger.info(f"  🟡 Medium: {len(medium)}")
                for issue in medium[:3]:
                    logger.info(f"     - {issue['issue']}")
            if low:
                logger.info(f"  🟢 Low: {len(low)}")
        else:
            logger.info("✅ No issues found!")

    except Exception as e:
        logger.error(f"❌ Review failed: {e}")
        review = {"overall_verdict": "REVIEW_FAILED", "issues_found": []}

    # ========================================
    # STEP 4: Save to review queue
    # ========================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: SAVING TO REVIEW QUEUE")
    logger.info("=" * 80)

    review_queue_dir = Path(__file__).parent.parent.parent.parent / "content" / "review_queue"
    review_queue_dir.mkdir(parents=True, exist_ok=True)

    page_data = {
        "guide_id": config["id"],
        "title": config["title"],
        "url": config["url"],
        "page_type": "source_type",  # Changed from 'mega_guide'
        "content": result["content"],
        "metadata": result["metadata"],
        "llm_review": review,
        "word_count": result["metadata"]["word_count"],
        "generated_at": datetime.now().isoformat()
    }

    json_filename = f"source_type_{source_type_index:02d}_{config['url_slug']}.json"
    json_file = review_queue_dir / json_filename

    with open(json_file, 'w') as f:
        json.dump(page_data, f, indent=2)

    logger.info(f"✅ Saved to: {json_filename}")

    # ========================================
    # STEP 5: Save markdown for manual inspection
    # ========================================
    test_dir = Path(__file__).parent.parent.parent.parent / "content" / "test"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create front matter
    front_matter = f"""---
title: {config['title']}
description: {config['description']}
meta_title: {config['title']}
meta_description: {config['description']}
page_type: source_type
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

    logger.info(f"✅ Markdown saved to: content/test/{markdown_filename}")

    # ========================================
    # STEP 6: Convert to HTML
    # ========================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: CONVERTING TO HTML")
    logger.info("=" * 80)

    # Load layout template
    layout_file = Path(__file__).parent.parent / "builder" / "templates" / "layout.html"
    if not layout_file.exists():
        logger.error(f"Layout template not found: {layout_file}")
        sys.exit(1)

    layout_template = layout_file.read_text()
    generator = StaticSiteGenerator(layout_template)

    # Build just this one page
    output_dir = Path(__file__).parent.parent.parent.parent / "content" / "dist"

    try:
        generator.build_site(str(test_dir), str(output_dir))
        logger.info("✅ HTML generated successfully")
    except Exception as e:
        logger.error(f"❌ HTML generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ========================================
    # STEP 7: Copy assets
    # ========================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 5: COPYING ASSETS")
    logger.info("=" * 80)

    assets_src = Path(__file__).parent.parent / "builder" / "assets"
    assets_dest = output_dir / "assets"

    if assets_src.exists():
        if assets_dest.exists():
            shutil.rmtree(assets_dest)
        shutil.copytree(assets_src, assets_dest)
        logger.info(f"✅ Assets copied")

        # Count files
        css_files = list((assets_dest / "css").glob("*")) if (assets_dest / "css").exists() else []
        js_files = list((assets_dest / "js").glob("*")) if (assets_dest / "js").exists() else []
        logger.info(f"   CSS: {len(css_files)} files")
        logger.info(f"   JS: {len(js_files)} files")
    else:
        logger.warning(f"⚠️  Assets directory not found: {assets_src}")

    # ========================================
    # STEP 8: Final summary
    # ========================================
    logger.info("\n" + "=" * 80)
    logger.info("GENERATION COMPLETE! 🎉")
    logger.info("=" * 80)

    logger.info(f"\n📊 STATS:")
    logger.info(f"   Title: {config['title']}")
    logger.info(f"   Word count: {word_count:,} words")
    logger.info(f"   Target: {config['word_count_target']:,} words")
    logger.info(f"   LLM verdict: {review['overall_verdict']}")
    logger.info(f"   Issues: {len(review['issues_found'])} ({len([i for i in review['issues_found'] if i['severity']=='high'])} high)")

    logger.info(f"\n📁 FILES GENERATED:")
    logger.info(f"   Markdown: content/test/{markdown_filename}")
    logger.info(f"   JSON: content/review_queue/{json_filename}")
    logger.info(f"   HTML: content/dist{config['url']}/index.html")

    logger.info(f"\n🌐 TEST LOCALLY:")
    logger.info(f"   cd content/dist")
    logger.info(f"   python3 -m http.server 8002")
    logger.info(f"   open http://localhost:8002{config['url']}")

    # Determine if manual review needed
    if review['overall_verdict'] == 'NEEDS_REVISION':
        logger.warning(f"\n⚠️  MANUAL REVIEW NEEDED")
        logger.warning(f"   High-priority issues found. Review before deploying.")
    else:
        logger.info(f"\n✅ READY FOR DEPLOYMENT")
        logger.info(f"   No high-priority issues. Safe to proceed with batch generation.")

    logger.info("=" * 80)

    return 0 if review['overall_verdict'] == 'PASS' else 1


if __name__ == "__main__":
    sys.exit(main())
