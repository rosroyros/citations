# Specific-Source Pages (`cite-*`) Deployment Guide

## Overview

This guide documents the **CORRECT** process for deploying specific-source pages (e.g., `cite-youtube-apa`, `cite-wikipedia-apa`, etc.) to production.

## ⚠️ CRITICAL: Use the CORRECT Layout Template

**MUST USE:** `backend/pseo/builder/templates/layout.html`

This template has:
- ✅ `async function checkCitation` (inline validation)
- ✅ Correct API response parsing (`data.results[0].errors`)
- ✅ Displays validation results inline on the page

**DO NOT USE:** `backend/pseo/templates/layout.html` (old template, redirects instead of validating inline)

## Complete Deployment Workflow

### Step 1: Generate Markdown Content (LLM)

```python
from pseo.generator.content_assembler import ContentAssembler
from pathlib import Path

# Initialize
knowledge_base_dir = Path("pseo/knowledge_base")
templates_dir = Path("pseo/templates")
assembler = ContentAssembler(str(knowledge_base_dir), str(templates_dir))

# Generate content for a specific source
source_id = "youtube"  # or "wikipedia", "cdc", etc.
result = assembler.assemble_specific_source_page(source_id)

# Save markdown
markdown_content = result["content"]
output_file = Path(f"test_output/{source_id}.md")
output_file.write_text(markdown_content)

print(f"✅ Generated: {output_file}")
print(f"📊 Cost: ${result['token_usage']['total_cost_usd']:.4f}")
```

**This generates:**
- `test_output/youtube.md` (markdown content)
- Token usage and cost information

### Step 2: Convert Markdown → HTML (CRITICAL STEP!)

**Use the CORRECT template:**

```python
from pseo.builder.static_generator import StaticSiteGenerator
from pathlib import Path

# Load the CORRECT template (with inline validation)
layout_file = Path("pseo/builder/templates/layout.html")
layout_template = layout_file.read_text()

# Verify it's the correct template
assert "async function checkCitation" in layout_template, "❌ Wrong template!"
assert "data.results[0].errors" in layout_template, "❌ Wrong API parsing!"
print("✅ Using correct template with inline validation")

# Initialize generator
generator = StaticSiteGenerator(
    layout_template,
    base_url="https://citationformatchecker.com"
)

# Build HTML from markdown
md_dir = Path("test_output")
output_dir = Path("test_output/html_output")
generator.build_site(str(md_dir), str(output_dir))

print(f"✅ HTML generated in: {output_dir}")
```

**This creates:**
- `test_output/html_output/cite-youtube-apa/index.html`
- Ready-to-deploy HTML with the CORRECT template

### Step 3: Deploy to Production

```bash
# Deploy via SCP
cd test_output/html_output
scp -r cite-{source}-apa/ deploy@178.156.161.140:/opt/citations/frontend/frontend/dist/

# Example for YouTube:
scp -r cite-youtube-apa/ deploy@178.156.161.140:/opt/citations/frontend/frontend/dist/
```

### Step 4: Verify Deployment

```bash
# Test with cache-buster
curl -s "https://citationformatchecker.com/cite-youtube-apa/?v=$(date +%s)" | grep "async function checkCitation"

# If you see output, deployment successful!
```

**Test in browser:**
1. Visit `https://citationformatchecker.com/cite-youtube-apa/?v=123`
2. Paste a citation in the mini-checker
3. Click "Check Citation"
4. Should show validation results INLINE (not redirect)

### Step 5: Update Sitemap (If New Page)

If deploying a NEW specific-source page (not an update):

```python
from pseo.utils.sitemap_generator import SitemapGenerator
import json
from pathlib import Path

# Load sitemap
sitemap_path = "/opt/citations/frontend/frontend/dist/sitemap.xml"
sitemap_gen = SitemapGenerator(sitemap_path)

# Load specific sources config
config_file = Path("pseo/configs/specific_sources.json")
with open(config_file) as f:
    sources = json.load(f)["sources"]

# Generate sitemap entries
entries = sitemap_gen.generate_specific_source_entries(sources)

# Update sitemap
sitemap_gen.add_entries_to_sitemap(entries, sitemap_path)

print(f"✅ Sitemap updated with {len(entries)} entries")
```

## Quick Regeneration Script

For regenerating ALL cite-* pages with the new template:

```bash
cd backend
python3 regenerate_cite_specific_pages.py
```

This script:
1. Loads existing markdown from `test_output/*.md`
2. Applies the NEW template
3. Outputs to `test_output/cite_pages_updated/`
4. Ready for deployment

## Common Issues & Solutions

### Issue 1: Mini-checker redirects instead of validating inline

**Cause:** Using OLD template (`pseo/templates/layout.html`)

**Fix:** Use `pseo/builder/templates/layout.html`

### Issue 2: Mini-checker shows "Citation looks good" for garbage input

**Cause:** Wrong API response parsing

**Fix:** Ensure template has `data.results[0].errors` (not `data.errors`)

### Issue 3: Page deployed but mini-checker still doesn't work

**Cause:** Browser cache or CDN cache

**Fix:**
- Clear browser cache
- Use cache-buster: `?v=123`
- Hard refresh (Cmd+Shift+R)

## File Locations

| File/Directory | Purpose |
|---------------|---------|
| `pseo/configs/specific_sources.json` | Source configurations (YouTube, Wikipedia, etc.) |
| `pseo/templates/specific_source_template.md` | Markdown template for content generation |
| `pseo/builder/templates/layout.html` | **CORRECT** HTML layout template |
| `pseo/templates/layout.html` | OLD template (DO NOT USE) |
| `test_output/*.md` | Generated markdown content |
| `test_output/cite_pages_updated/` | Regenerated HTML (ready to deploy) |

## Verification Checklist

Before deploying, verify:

- [ ] Used `pseo/builder/templates/layout.html` (not `pseo/templates/layout.html`)
- [ ] HTML contains `async function checkCitation`
- [ ] HTML contains `data.results[0].errors`
- [ ] Tested mini-checker locally in browser
- [ ] Content matches existing production page (if updating)
- [ ] Sitemap updated (if new page)

## Emergency Rollback

If deployment breaks production:

```bash
# Re-deploy from backup
cd backend/test_output/backup_cite_pages
scp -r cite-{source}-apa/ deploy@178.156.161.140:/opt/citations/frontend/frontend/dist/
```

---

**Last Updated:** October 30, 2025
**Updated By:** Claude Code Assistant
**Status:** ✅ All cite-* pages regenerated and deployed with new template
