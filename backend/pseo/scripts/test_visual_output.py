#!/usr/bin/env python3
"""Generate a test page for visual comparison with mockup."""

import sys
from pathlib import Path
from jinja2 import Template

sys.path.append(str(Path(__file__).parent.parent))

def main():
    # Read layout template
    layout_path = Path(__file__).parent.parent / "builder" / "templates" / "layout.html"
    layout_template = layout_path.read_text()

    # Create mock content similar to mockup
    content = """
    <div class="hero">
        <h1>Complete Guide to Checking APA Citations</h1>
        <p class="hero-description">Master the art of validating APA 7th edition citations with our comprehensive, step-by-step guide. Learn how to catch errors before submission.</p>
        <div class="meta-info">
            <span>📖 Reading time: 25 minutes</span>
            <span>🔄 Last updated: December 2024</span>
            <span>✅ APA 7th Edition</span>
        </div>
    </div>

    <div class="toc">
        <h2>📑 Table of Contents</h2>
        <ol>
            <li><a href="#tldr">Quick Summary</a></li>
            <li><a href="#introduction">Introduction</a></li>
            <li><a href="#why-check">Why Checking Citations Matters</a></li>
        </ol>
    </div>

    <div class="tldr-box" id="tldr">
        <h2>⚡ TL;DR - Quick Summary</h2>
        <ul>
            <li>90.9% of academic papers contain at least one citation error</li>
            <li>Author name formatting errors are the #1 most common mistake</li>
            <li>Always check: author names, dates, titles, DOIs, and punctuation</li>
        </ul>
    </div>

    <section class="content-section" id="introduction">
        <h2>Introduction</h2>
        <p>You've spent weeks researching, writing, and revising your paper. The content is solid, your arguments are compelling, and you're ready to submit. But there's one critical step that many researchers overlook: thoroughly checking their citations.</p>
        <p>Research shows that over 90% of academic papers contain citation errors. These mistakes range from minor formatting issues to serious problems like incorrect author names or missing publication years.</p>
    </section>

    <div class="mini-checker">
        <h4>🔍 Quick Check Your Citation</h4>
        <p>Paste a single citation to instantly validate APA formatting</p>
        <textarea placeholder="Smith, J. A. (2020). Article title goes here. Journal Name, 15(2), 123-145. https://doi.org/10.1234/example"></textarea>
        <button>Check Citation</button>
    </div>

    <section class="content-section">
        <h2>Most Common Citation Errors</h2>
        <p>Based on analysis of thousands of academic papers, these are the most frequent citation mistakes:</p>

        <h3>1. Author Name Formatting (45% of errors)</h3>

        <div class="error-example">
            <strong>❌ Incorrect:</strong>
            <p>John Smith, Mary Jones, and Robert Lee (2020)...</p>
        </div>

        <div class="correction-box">
            <strong>✓ Correct:</strong>
            <p>Smith, J., Jones, M., & Lee, R. (2020)...</p>
        </div>
    </section>
    """

    # Metadata
    metadata = {
        "meta_title": "Complete Guide to Checking APA Citations - Test",
        "meta_description": "Master the art of validating APA 7th edition citations",
        "url": "/guide/checking-apa-citations/",
        "base_url": "https://citationchecker.com",
        "page_type": "mega_guide",
        "breadcrumb_title": "Checking APA Citations",
        "word_count": "5,000",
        "reading_time": "25 minutes",
        "last_updated": "December 2024"
    }

    # Render template
    template = Template(layout_template)
    html = template.render(content=content, **metadata)

    # Save output
    output_dir = Path(__file__).parent.parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "test_page.html"
    output_file.write_text(html)

    print(f"Generated test page: {output_file}")
    print(f"Open in browser to compare with mockup at:")
    print(f"  Mockup: design/mocks/mega_guide_mockup.html")
    print(f"  Generated: {output_file}")

if __name__ == "__main__":
    main()
