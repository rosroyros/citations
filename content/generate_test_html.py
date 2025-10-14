#!/usr/bin/env python3
"""Generate HTML from test markdown files using StaticSiteGenerator"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.pseo.builder.static_generator import StaticSiteGenerator
from pathlib import Path

def main():
    """Generate HTML from test markdown files"""

    # Load the layout template
    layout_file = Path(__file__).parent.parent / "backend" / "pseo" / "builder" / "templates" / "layout.html"
    layout_content = layout_file.read_text(encoding='utf-8')

    # Initialize generator
    generator = StaticSiteGenerator(layout_content, base_url="http://localhost:8000")

    # Build site from test content
    input_dir = Path(__file__).parent / "test"
    output_dir = Path(__file__).parent / "dist"

    print(f"Building site from {input_dir} to {output_dir}")

    # Clear output directory first
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)

    # Generate HTML
    generator.build_site(str(input_dir), str(output_dir))

    print(f"\n✅ Site generated successfully!")
    print(f"   Output directory: {output_dir}")
    print(f"   Run: python3 -m http.server --directory {output_dir} 8000")

    # List generated pages
    html_files = list(output_dir.glob("**/*.html"))
    print(f"\nGenerated {len(html_files)} pages:")
    for file in sorted(html_files):
        rel_path = file.relative_to(output_dir)
        url = f"http://localhost:8000/{rel_path}"
        print(f"   - {url}")

if __name__ == "__main__":
    main()