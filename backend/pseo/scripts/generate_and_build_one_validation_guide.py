#!/usr/bin/env python3
"""
End-to-end script to generate 1 complete validation guide and build it to HTML.

This validates the entire pipeline:
1. Generate markdown content (LLM)
2. Run LLM quality review
3. Save to review_queue/
4. Convert to HTML
5. Deploy to content/dist/
6. Report results

Usage:
    python3 generate_and_build_one_validation_guide.py [validation_guide_number]

    validation_guide_number: 0-14 (default: 0 = "Capitalization")
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
    """Generate and build one complete validation guide"""

    # Which validation guide to generate?
    validation_guide_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    logger.info("=" * 80)
    logger.info("END-TO-END VALIDATION GUIDE GENERATION & BUILD")
    logger.info("=" * 80)

    # Load validation guide configurations
    config_file = Path(__file__).parent.parent / "configs" / "validation_guides.json"
    logger.info(f"Loading validation guide configs from: {config_file}")

    with open(config_file, 'r', encoding='utf-8') as f:
        validation_guides = json.load(f)

    # Validate index
    if validation_guide_index >= len(validation_guides):
        logger.error(f"Invalid validation guide index: {validation_guide_index}")
        logger.error(f"Available indices: 0-{len(validation_guides)-1}")
        sys.exit(1)

    config = validation_guides[validation_guide_index]
    validation_element = config["element_focus"]
    logger.info(f"Generating validation guide #{validation_guide_index}: {config['title']}")
    logger.info(f"URL: {config['url']}")
    logger.info(f"Element focus: {validation_element}")

    try:
        # Initialize components
        logger.info("Step 0: Initializing components...")
        knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"
        templates_dir = Path(__file__).parent.parent / "templates"
        content_dir = Path(__file__).parent.parent.parent.parent / "content"
        review_queue_dir = content_dir / "review_queue"
        dist_dir = content_dir / "dist"

        assembler = ContentAssembler(str(knowledge_base_dir), str(templates_dir))
        reviewer = LLMReviewer()
        static_generator = StaticSiteGenerator(str(templates_dir))

        # Ensure directories exist
        review_queue_dir.mkdir(parents=True, exist_ok=True)
        dist_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate validation guide content
        logger.info("Step 1: Generating validation guide content...")
        result = assembler.assemble_validation_page(validation_element, config)

        if not result or "content" not in result:
            raise Exception("Failed to generate validation guide content")

        content = result["content"]
        template_data = result["template_data"]
        token_usage = result.get("token_usage", {})

        logger.info(f"✅ Generated {len(content)} characters of content")

        # Step 2: Run LLM quality review
        logger.info("Step 2: Running LLM quality review...")
        review_result = reviewer.review_page(
            content=content,
            page_type="validation",
            metadata=result.get("metadata", {})
        )

        verdict = review_result.get("verdict", "NEEDS_REVISION")
        issues = review_result.get("issues", [])
        word_count = review_result.get("word_count", 0)

        logger.info(f"✅ Review complete: {verdict}")
        logger.info(f"Word count: {word_count} (target: {config.get('word_count_target', 2000)})")
        if issues:
            logger.info(f"Issues found: {len(issues)}")
            for issue in issues[:3]:  # Show first 3 issues
                logger.info(f"  - {issue.get('type', 'Unknown')}: {issue.get('description', 'No description')}")

        # Step 3: Save to review_queue
        logger.info("Step 3: Saving to review_queue...")
        review_filename = f"validation_{validation_guide_index:02d}_{config['url_slug']}.json"
        review_path = review_queue_dir / review_filename

        review_data = {
            "config": config,
            "content": content,
            "template_data": template_data,
            "review": review_result,
            "token_usage": token_usage,
            "generated_at": datetime.now().isoformat()
        }

        with open(review_path, 'w', encoding='utf-8') as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Saved to review_queue: {review_filename}")

        # Step 4: Save test markdown
        logger.info("Step 4: Saving test markdown...")
        test_dir = content_dir / "test"
        test_dir.mkdir(exist_ok=True)
        test_md_path = test_dir / f"{config['url_slug']}.md"

        with open(test_md_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ Saved test markdown: {config['url_slug']}.md")

        # Step 5: Convert to HTML
        logger.info("Step 5: Converting to HTML...")

        # Load layout template
        layout_file = Path(__file__).parent.parent / "builder" / "templates" / "layout.html"
        if not layout_file.exists():
            logger.error(f"Layout template not found: {layout_file}")
            sys.exit(1)

        layout_template = layout_file.read_text()
        generator = StaticSiteGenerator(layout_template)

        # Build just this one page
        try:
            generator.build_site(str(test_dir), str(dist_dir))
            logger.info("✅ HTML generated successfully")
        except Exception as e:
            logger.error(f"❌ HTML generation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)

        # Step 6: Verify deployment
        logger.info("Step 6: Verifying deployment...")
        deploy_dir = dist_dir / config["url"].strip("/")
        if deploy_dir.exists():
            logger.info(f"✅ Deployed to: {deploy_dir}")
        else:
            logger.warning(f"⚠️  Deployment directory not found: {deploy_dir}")

        # Step 7: Report results
        logger.info("=" * 80)
        logger.info("GENERATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Validation Guide: {config['title']}")
        logger.info(f"URL: {config['url']}")
        logger.info(f"Element: {validation_element}")
        logger.info(f"Review Verdict: {verdict}")
        logger.info(f"Word Count: {word_count}")
        logger.info(f"Issues: {len(issues)}")
        if token_usage:
            total_tokens = sum(token_usage.values()) if isinstance(token_usage, dict) else token_usage
            logger.info(f"Tokens Used: {total_tokens:,}")

        # Show file locations
        logger.info("\nGenerated Files:")
        logger.info(f"  Review queue: {review_path}")
        logger.info(f"  Test markdown: {test_md_path}")
        if deploy_dir.exists():
            html_files = list(deploy_dir.glob("*.html"))
            md_files = list(deploy_dir.glob("*.md"))
            if html_files:
                logger.info(f"  Production HTML: {html_files[0]}")
            if md_files:
                logger.info(f"  Production MD: {md_files[0]}")
        else:
            logger.info(f"  Production files: BuildSite processed from test directory")

        # Show high-priority issues if any
        high_priority_issues = [i for i in issues if i.get("priority") == "high"]
        if high_priority_issues:
            logger.info(f"\n⚠️  HIGH PRIORITY ISSUES ({len(high_priority_issues)}):")
            for issue in high_priority_issues:
                logger.info(f"  - {issue.get('description', 'No description')}")

        # Show next steps
        logger.info(f"\nNext Steps:")
        if verdict == "PASS":
            logger.info("  ✅ Ready for production deployment")
            logger.info(f"  📋 Review locally: http://localhost:8002{config['url']}")
        else:
            logger.info("  ⚠️  Review content before production deployment")
            logger.info("  📝 Check review_queue for detailed feedback")
            logger.info(f"  🌐 Review locally: http://localhost:8002{config['url']}")

        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()