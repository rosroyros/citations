#!/usr/bin/env python3
"""
MLA PSEO Page Generation Script

Generates MLA 9th Edition PSEO pages using MLAStaticSiteGenerator.
Supports pilot mode (3 pages), type-specific generation, and full generation.

Usage:
    python generate_mla_pages.py --pilot                    # Generate 3 pilot pages
    python generate_mla_pages.py --type mega                # Generate all mega guides
    python generate_mla_pages.py --type source-type         # Generate source type guides
    python generate_mla_pages.py --type specific            # Generate specific sources
    python generate_mla_pages.py --all                      # Generate all 69 pages
    python generate_mla_pages.py --source youtube           # Generate specific source by ID

Examples:
    # Canary deployment (pilot pages)
    python generate_mla_pages.py --pilot

    # Full deployment
    python generate_mla_pages.py --all
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'builder'))

from builder.mla_generator import MLAStaticSiteGenerator
from generator.content_assembler import ContentAssembler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pilot pages for canary deployment
# Format: (page_id, page_type, config_type)
PILOT_PAGES = [
    ('mla_mega_01', 'mega_guide', 'mega_guides'),  # Complete MLA 9th Edition Guide
    ('mla_source_type_01', 'source_type', 'source_type_guides'),  # How to Cite Book in MLA
    ('youtube', 'specific_source', 'specific_sources'),  # Cite YouTube in MLA
]


def load_config(config_type: str) -> list:
    """
    Load configuration file for page type

    Args:
        config_type: Type of config (mega_guides, source_type_guides, specific_sources)

    Returns:
        List of page configurations
    """
    # Use MLA-specific config files
    config_file = Path(__file__).parent.parent / "configs" / f"mla_{config_type}.json"

    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        return []

    with open(config_file, 'r') as f:
        data = json.load(f)

    # specific_sources has a different structure
    if config_type == "specific_sources":
        return data.get("sources", [])

    return data


def load_layout_template() -> str:
    """Load the layout template"""
    template_file = Path(__file__).parent.parent / "builder" / "templates" / "layout.html"

    if not template_file.exists():
        logger.error(f"Template file not found: {template_file}")
        sys.exit(1)

    return template_file.read_text(encoding='utf-8')


def generate_page(generator: MLAStaticSiteGenerator, page_config: dict, page_type: str, output_dir: Path, content_assembler: ContentAssembler = None) -> bool:
    """
    Generate a single MLA page

    Args:
        generator: MLAStaticSiteGenerator instance
        page_config: Page configuration dict
        page_type: Type of page (mega_guide, source_type, specific_source)
        output_dir: Output directory for HTML files
        content_assembler: ContentAssembler instance for LLM content generation

    Returns:
        True if successful, False otherwise
    """
    try:
        page_name = page_config.get('url_slug') or page_config.get('id')
        logger.info(f"Generating {page_type}: {page_name}")

        # Generate content using ContentAssembler
        if content_assembler:
            logger.info(f"  Using ContentAssembler for LLM content generation")
            
            if page_type == 'mega_guide':
                topic = page_config.get('topic', 'MLA 9th Edition citations')
                result = content_assembler.assemble_mega_guide(topic, page_config)
            elif page_type == 'source_type':
                source_type = page_config.get('topic', page_config.get('title', 'source'))
                result = content_assembler.assemble_source_type_page(source_type, page_config)
            elif page_type == 'specific_source':
                # Specific sources use source_type_page assembly
                source_name = page_config.get('name', page_config.get('id', 'source'))
                result = content_assembler.assemble_source_type_page(source_name, page_config)
            else:
                raise ValueError(f"Unknown page type: {page_type}")
            
            # Get content and metadata from result
            markdown_content = result['content']
            content_metadata = result['metadata']
            
            # Convert markdown to HTML
            html_content = generator.convert_markdown_to_html(markdown_content)
            word_count = content_metadata.get('word_count', 'Unknown')
            reading_time = content_metadata.get('reading_time', 'Unknown')
        else:
            # Fallback to placeholder content if no ContentAssembler
            logger.warning(f"  No ContentAssembler - using placeholder content")
            html_content = f"""
<div class="hero">
    <h1>{page_config.get('title') or page_config.get('name')}</h1>
    <p>{page_config.get('description', '')}</p>
</div>

<section class="content-section">
    <h2>Overview</h2>
    <p>This page provides guidance on citing sources in MLA 9th Edition format.</p>
</section>

<div class="cta-placement" id="mini-checker-intro">
    <!-- Mini-checker will be injected here -->
</div>

<section class="content-section">
    <h2>Citation Format</h2>
    <p>MLA 9 uses a flexible container system. Follow the core elements in order:</p>
    <ol>
        <li>Author</li>
        <li>Title of source</li>
        <li>Title of container</li>
        <li>Other contributors</li>
        <li>Version</li>
        <li>Number</li>
        <li>Publisher</li>
        <li>Publication date</li>
        <li>Location</li>
    </ol>
</section>
"""
            word_count = 'TBD'
            reading_time = 'TBD'

        # Create metadata for page
        # Prefer title from ContentAssembler (which may have auto-generated it)
        if content_assembler and 'content_metadata' in dir():
            page_title = content_metadata.get('meta_title') or page_config.get('title') or page_config.get('name')
        else:
            page_title = page_config.get('title') or page_config.get('name')
        metadata = {
            'page_type': page_type,
            'title': page_title,
            'meta_title': page_title,  # For <title> tag
            'meta_description': page_config.get('description', ''),
            'url_slug': page_name,
            'source_id': page_config.get('id'),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'date_published': datetime.now().strftime('%Y-%m-%d'),
            'word_count': word_count,
            'reading_time': reading_time
        }


        # Generate URL
        url = generator.generate_url_structure(page_type, page_name)

        # Convert to final HTML
        final_html = generator.apply_layout(html_content, metadata)

        # Write to output directory
        output_file = output_dir / url.strip("/") / "index.html"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(final_html, encoding='utf-8')

        logger.info(f"✅ Generated: {url}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to generate {page_type}/{page_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_pages(args):
    """Main generation logic"""

    logger.info("=" * 80)
    logger.info("MLA PSEO PAGE GENERATION")
    logger.info("=" * 80)

    # Load layout template
    layout_template = load_layout_template()

    # Initialize generator
    base_url = "https://citationformatchecker.com"
    generator = MLAStaticSiteGenerator(layout_template, base_url)

    # Set output directory
    output_dir = Path(__file__).parent.parent / "dist" / "mla"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Output directory: {output_dir}")

    # Initialize ContentAssembler with MLA knowledge base
    content_assembler = None
    if args.use_llm:
        knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base" / "mla9"
        templates_dir = Path(__file__).parent.parent / "templates"
        
        if knowledge_base_dir.exists() and templates_dir.exists():
            try:
                content_assembler = ContentAssembler(
                    str(knowledge_base_dir),
                    str(templates_dir),
                    citation_style="MLA 9th edition"
                )
                logger.info(f"✅ ContentAssembler initialized with MLA knowledge base")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize ContentAssembler: {e}")
                logger.warning("   Continuing with placeholder content")
        else:
            logger.warning(f"⚠️ Knowledge base or templates not found")
            logger.warning(f"   KB: {knowledge_base_dir.exists()}, Templates: {templates_dir.exists()}")
    else:
        logger.info("📝 LLM content generation disabled (use --use-llm to enable)")

    # Track statistics
    total_attempted = 0
    total_success = 0
    total_failed = 0

    # Pilot mode - generate 3 pages for canary
    if args.pilot:
        logger.info("\n🚀 PILOT MODE: Generating 3 pages for canary deployment")

        for page_id, page_type, config_type in PILOT_PAGES:
            configs = load_config(config_type)
            page_config = next((c for c in configs if c['id'] == page_id), None)

            if page_config:
                total_attempted += 1
                if generate_page(generator, page_config, page_type, output_dir, content_assembler):
                    total_success += 1
                else:
                    total_failed += 1
            else:
                logger.warning(f"Page config not found: {page_id} in {config_type}")

    # Specific source by ID
    elif args.source:
        logger.info(f"\n📄 Generating specific source: {args.source}")
        configs = load_config("specific_sources")
        page_config = next((c for c in configs if c['id'] == args.source), None)

        if page_config:
            total_attempted += 1
            if generate_page(generator, page_config, 'specific_source', output_dir, content_assembler):
                total_success += 1
            else:
                total_failed += 1
        else:
            logger.error(f"Source not found: {args.source}")

    # Type-specific generation
    elif args.type:
        if args.type == "mega":
            logger.info("\n📚 Generating MEGA GUIDES")
            configs = load_config("mega_guides")
            page_type = "mega_guide"
        elif args.type == "source-type":
            logger.info("\n📝 Generating SOURCE TYPE GUIDES")
            configs = load_config("source_type_guides")
            page_type = "source_type"
        elif args.type == "specific":
            logger.info("\n🎯 Generating SPECIFIC SOURCE PAGES")
            configs = load_config("specific_sources")
            page_type = "specific_source"
        else:
            logger.error(f"Unknown type: {args.type}")
            sys.exit(1)

        for config in configs:
            total_attempted += 1
            if generate_page(generator, config, page_type, output_dir, content_assembler):
                total_success += 1
            else:
                total_failed += 1

    # Full generation
    elif args.all:
        logger.info("\n🌍 FULL GENERATION: All 69 pages")

        # Mega guides
        logger.info("\n📚 Generating MEGA GUIDES...")
        for config in load_config("mega_guides"):
            total_attempted += 1
            if generate_page(generator, config, 'mega_guide', output_dir, content_assembler):
                total_success += 1
            else:
                total_failed += 1

        # Source type guides
        logger.info("\n📝 Generating SOURCE TYPE GUIDES...")
        for config in load_config("source_type_guides"):
            total_attempted += 1
            if generate_page(generator, config, 'source_type', output_dir, content_assembler):
                total_success += 1
            else:
                total_failed += 1

        # Specific sources
        logger.info("\n🎯 Generating SPECIFIC SOURCE PAGES...")
        for config in load_config("specific_sources"):
            total_attempted += 1
            if generate_page(generator, config, 'specific_source', output_dir, content_assembler):
                total_success += 1
            else:
                total_failed += 1

    # Report results
    logger.info("\n" + "=" * 80)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total attempted: {total_attempted}")
    logger.info(f"✅ Success: {total_success}")
    logger.info(f"❌ Failed: {total_failed}")

    if total_failed > 0:
        logger.warning(f"⚠️  {total_failed} pages failed to generate")
        sys.exit(1)
    else:
        logger.info("🎉 All pages generated successfully!")


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description="Generate MLA PSEO pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--pilot', action='store_true',
                        help='Generate 3 pilot pages for canary deployment')
    parser.add_argument('--type', choices=['mega', 'source-type', 'specific'],
                        help='Generate specific type of pages')
    parser.add_argument('--source', type=str,
                        help='Generate specific source by ID (e.g., youtube)')
    parser.add_argument('--all', action='store_true',
                        help='Generate all 69 MLA pages')
    parser.add_argument('--use-llm', action='store_true', dest='use_llm',
                        help='Enable LLM content generation (requires API keys)')

    args = parser.parse_args()

    # Validate arguments
    if not any([args.pilot, args.type, args.source, args.all]):
        parser.print_help()
        sys.exit(1)

    generate_pages(args)


if __name__ == "__main__":
    main()
