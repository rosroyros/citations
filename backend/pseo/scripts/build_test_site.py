#!/usr/bin/env python3
"""
Build static HTML site from markdown files in content/test/

This script:
1. Reads markdown files from content/test/
2. Converts them to HTML using the approved layout template
3. Copies assets (CSS, JS, including MiniChecker bundle)
4. Outputs to content/dist/ for local testing
"""
import sys
import logging
import shutil
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.pseo.builder.static_generator import StaticSiteGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Build the test static site"""
    logger.info("=" * 80)
    logger.info("BUILDING TEST STATIC SITE")
    logger.info("=" * 80)

    # Define paths
    project_root = Path(__file__).parent.parent.parent.parent
    templates_dir = project_root / "backend" / "pseo" / "builder" / "templates"
    input_dir = project_root / "content" / "test"
    output_dir = project_root / "content" / "dist"
    assets_src = project_root / "backend" / "pseo" / "builder" / "assets"

    logger.info(f"Input: {input_dir}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Templates: {templates_dir}")
    logger.info(f"Assets: {assets_src}")

    # Load layout template
    layout_file = templates_dir / "layout.html"
    if not layout_file.exists():
        logger.error(f"Layout template not found: {layout_file}")
        sys.exit(1)

    layout_template = layout_file.read_text()
    logger.info("✓ Layout template loaded")

    # Initialize generator
    generator = StaticSiteGenerator(layout_template)

    # Build site
    logger.info("\nBuilding site...")
    generator.build_site(str(input_dir), str(output_dir))
    logger.info("✓ Site built successfully")

    # Copy assets
    logger.info("\nCopying assets...")
    assets_dest = output_dir / "assets"

    if assets_src.exists():
        if assets_dest.exists():
            shutil.rmtree(assets_dest)
        shutil.copytree(assets_src, assets_dest)
        logger.info(f"✓ Assets copied to {assets_dest}")

        # List what was copied
        for subdir in ["js", "css"]:
            subdir_path = assets_dest / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("*"))
                logger.info(f"  {subdir}/: {len(files)} files")
                for f in files:
                    logger.info(f"    - {f.name}")
    else:
        logger.warning(f"Assets directory not found: {assets_src}")

    # Summary
    pages = list(output_dir.rglob("index.html"))
    logger.info("\n" + "=" * 80)
    logger.info("BUILD COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Pages generated: {len(pages)}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("\nTo test locally, run:")
    logger.info(f"  cd {output_dir}")
    logger.info(f"  python3 -m http.server 8002")
    logger.info(f"  open http://localhost:8002")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
