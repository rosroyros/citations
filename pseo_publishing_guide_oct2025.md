# PSEO Source Type Guide Publishing Process

**Last Updated:** October 26, 2025
**Status:** Production-ready process for generating 27 source type guides

## Overview

End-to-end workflow for generating, reviewing, and deploying APA citation source type guides using LLM-powered content generation with template-based assembly.

---

## Architecture

### Components

1. **Content Assembler** (`backend/pseo/generator/content_assembler.py`)
   - Loads knowledge base data (examples, errors, validation rules)
   - Generates LLM content sections (format explanation, steps, special cases, FAQ)
   - Renders Jinja2 templates with combined static + dynamic content
   - Validates word count (target: 2,500 words)

2. **LLM Writer** (`backend/pseo/generator/llm_writer.py`)
   - Uses GPT-4o-mini for content generation
   - System prompt: "Expert academic writing assistant specializing in APA citation guides"
   - Cost tracking: $0.15/1M input tokens, $0.60/1M output tokens
   - Average cost per guide: ~$0.003

3. **Template Engine** (`backend/pseo/generator/template_engine.py`)
   - Jinja2 template: `backend/pseo/templates/source_type_template.md`
   - Layout wrapper: `backend/pseo/templates/layout.html`
   - Variables: title, quick_reference, examples, errors, FAQ, etc.

4. **Static Site Generator** (`backend/pseo/builder/static_generator.py`)
   - Converts markdown → HTML using Python-Markdown
   - Injects layout wrapper with header, footer, CSS
   - Generates sitemap.xml automatically
   - Adds Google Analytics (G-RZWHZQP8N9)

5. **LLM Reviewer** (`backend/pseo/review/llm_reviewer.py`)
   - Automated quality check (meta description, word count, structure)
   - Verdict: PASS | NEEDS_REVISION
   - Flags high/medium/low priority issues

---

## Configuration Files

### Source Type Metadata
**File:** `backend/pseo/configs/source_type_guides.json`

Each source type has:
```json
{
  "id": "source_type_19",
  "title": "How to Cite a Twitter/X Post in APA Format (7th Edition)",
  "topic": "twitter citation",
  "url": "/how-to-cite-twitter-apa/",
  "url_slug": "twitter",
  "description": "Complete guide...",
  "keywords": ["cite Twitter APA", ...],
  "pain_points": ["username vs real name", ...],
  "target_audience": "undergraduate and graduate students",
  "word_count_target": 2500
}
```

**27 Total Source Types:**
- Tier 1 (Academic): conference paper, dissertation, thesis, book chapter, edited book, report, government report, dataset
- Tier 2 (Popular): newspaper, magazine, blog, youtube, podcast, ted-talk, wikipedia, dictionary, encyclopedia, film
- Tier 3 (Social/Media): tv-episode, twitter, instagram, facebook, linkedin, software, patent, artwork, music

### Quick Reference Templates
**File:** `backend/pseo/generator/content_assembler.py` lines 704-737

Must add template for each source type:
```python
"twitter citation": "Author [@username]. (Year, Month Day). <em>First 20 words of tweet</em> [Tweet]. Twitter. https://twitter.com/username/status/xxxxx"
```

### Knowledge Base Filtering

**Common Errors** (`backend/pseo/knowledge_base/common_errors.json`):
- 50 errors with `affected_source_types` tags
- Filtering: source-specific preferred, generic fallback if < 5 matches
- Mapping in `_load_errors()` method (lines 392-449)

**Examples** (`backend/pseo/knowledge_base/examples.json`):
- Only Tier 1 has source-specific examples
- Tier 2/3 return empty list → template hides Examples section with `{% if examples %}`

---

## Generation Workflow

### Step 1: Add Source Type Config

1. Add entry to `backend/pseo/configs/source_type_guides.json`
2. Add quick reference template to `content_assembler.py:_generate_quick_reference_template()`
3. Add source type mapping to `content_assembler.py:_load_errors()` (for error filtering)

### Step 2: Generate Single Guide (Testing)

```bash
cd /Users/roy/Documents/Projects/citations/backend/pseo
source ../../venv/bin/activate
python3 scripts/generate_and_build_one_source_type.py <index>
```

**What happens:**
1. Loads source type config by index
2. Generates 4 LLM sections (~90-120 seconds):
   - Format explanation
   - Step-by-step instructions
   - Special cases
   - FAQ (6 items)
3. Assembles with template + knowledge base data
4. Runs LLM quality review
5. Saves to:
   - `content/review_queue/source_type_<index>_<slug>.json`
   - `content/test/<slug>.md`
   - `content/dist/how-to-cite-<slug>-apa/index.html`
6. Outputs verdict + issue count

### Step 3: Review Locally

```bash
cd /Users/roy/Documents/Projects/citations/content/dist
python3 -m http.server 8002
```

Open: `http://10.0.0.222:8002/how-to-cite-<slug>-apa/`

**Check:**
- Citation format examples are correct (especially formatting rules)
- No markdown showing as raw text
- No duplicate sections
- Step-by-step renders as HTML list
- Examples section hidden if empty
- Related Source Types appears once
- Google Analytics present (2 instances of G-RZWHZQP8N9)

### Step 4: Batch Generation

```bash
cd /Users/roy/Documents/Projects/citations/backend/pseo
source ../../venv/bin/activate
python3 -c "
import subprocess, time
for i in range(18, 27):  # Tier 3 indices
    print(f'\n=== Generating guide {i} ===')
    subprocess.run(['python3', 'scripts/generate_and_build_one_source_type.py', str(i)], timeout=180)
    time.sleep(1)
print('\n✅ All guides generated')
"
```

**Timing:** ~2 minutes per guide = ~18 minutes for 9 guides

### Step 5: Deploy to Production

```bash
# Deploy individual guide
scp -r /Users/roy/Documents/Projects/citations/content/dist/how-to-cite-<slug>-apa \
  deploy@178.156.161.140:/opt/citations/frontend/frontend/dist/

# Deploy multiple guides
cd /Users/roy/Documents/Projects/citations/content/dist
scp -r how-to-cite-twitter-apa how-to-cite-instagram-apa ... \
  deploy@178.156.161.140:/opt/citations/frontend/frontend/dist/

# Deploy sitemap
scp sitemap.xml deploy@178.156.161.140:/opt/citations/frontend/frontend/dist/
```

**Verify production:** `http://178.156.161.140/how-to-cite-<slug>-apa/`

---

## Template Structure

### Sections in Order

1. **Title + Description** (from config)
2. **Quick Reference Box** (from template mapping)
3. **Mini Checker** (placeholder UI)
4. **Format Explanation** (LLM-generated, ~500-800 words)
5. **Step-by-Step Instructions** (LLM-generated, ~400-600 words)
6. **Reference List Examples** (from knowledge base, conditional `{% if examples %}`)
7. **Common Errors** (filtered from knowledge base, 5-10 errors)
8. **Validation Checklist** (from knowledge base, 6 rules)
9. **Special Cases** (LLM-generated, ~500-700 words)
10. **FAQ** (LLM-generated, 6 Q&A pairs)
11. **Last Updated + Reading Time** (auto-generated)

### HTML Layout Features

- Responsive design (mobile-friendly)
- Google Analytics tracking
- Related Source Types sidebar
- Mini citation checker placeholders
- Structured data ready (future enhancement)

---

## Common Issues & Fixes

### Issue 1: Step-by-Step Shows as Raw Markdown
**Cause:** HTML wrapper prevents markdown conversion
**Fix:** Remove `<div>` wrappers around `{{ step_by_step_instructions }}` in template

### Issue 2: Duplicate Related Source Types
**Cause:** Section in both template AND layout
**Fix:** Remove from template, keep only in layout.html

### Issue 3: Wrong Examples Showing
**Cause:** Fallback to generic examples when source-specific not found
**Fix:** Return empty list from `_load_examples_for_source_type()`, use `{% if examples %}`

### Issue 4: Generic Errors for All Sources
**Cause:** No source type filtering in `_load_errors()`
**Fix:** Add source type mapping + filter by `affected_source_types` tags

### Issue 5: LLM Generates Incorrect Citation Format
**Cause:** GPT-4o-mini misinterprets APA rules (e.g., Twitter quotes)
**Fix:** Regenerate (LLM has variability) or add examples to knowledge base

---

## Verification Checklist

Before deploying a batch:

- [ ] All guides generated without errors
- [ ] LLM verdicts: PASS or acceptable NEEDS_REVISION (no high issues)
- [ ] Sample guides reviewed locally (at least 2 per tier)
- [ ] Citation format examples are correct
- [ ] No markdown rendering issues
- [ ] Sitemap includes all new guides
- [ ] Google Analytics present in all pages
- [ ] Deployed to production server
- [ ] Production URLs verified (spot check 3-5 guides)

---

## File Locations

**Local:**
- Configs: `/Users/roy/Documents/Projects/citations/backend/pseo/configs/`
- Templates: `/Users/roy/Documents/Projects/citations/backend/pseo/templates/`
- Knowledge Base: `/Users/roy/Documents/Projects/citations/backend/pseo/knowledge_base/`
- Scripts: `/Users/roy/Documents/Projects/citations/backend/pseo/scripts/`
- Output: `/Users/roy/Documents/Projects/citations/content/dist/`
- Review Queue: `/Users/roy/Documents/Projects/citations/content/review_queue/`

**Production:**
- Web Root: `/opt/citations/frontend/frontend/dist/`
- Guides: `/opt/citations/frontend/frontend/dist/how-to-cite-<slug>-apa/`
- Sitemap: `/opt/citations/frontend/frontend/dist/sitemap.xml`

---

## Key Learnings

1. **Template design matters:** Markdown won't convert inside HTML blocks. Keep dynamic content outside HTML wrappers.

2. **LLM variability is real:** Same prompt can produce different results. Regenerate if format is wrong (faster than debugging prompts).

3. **Knowledge base filtering is critical:** Without source-type-specific filtering, all guides look the same (generic errors/examples).

4. **Conditional rendering prevents issues:** Use `{% if examples %}` to hide sections when data is empty (better than showing wrong content).

5. **Batch generation requires patience:** ~2 min/guide with 4 LLM calls. Plan for 30+ min batches for 10+ guides.

6. **Automated review catches 80% of issues:** LLM reviewer finds structural issues, but human spot-check still needed for APA accuracy.

---

## Future Enhancements

1. **Add more examples to knowledge base** for Tier 2/3 sources
2. **Implement internal linking** between related guides (currently 0 internal links)
3. **Improve meta descriptions** (many are <120 chars, ideal is 120-160)
4. **Add structured data** (Schema.org markup for HowTo guides)
5. **Create example variation generator** to show multiple citation formats per source
6. **Add pre-commit hooks** to validate templates before generation
7. **Implement caching** for LLM responses to reduce regeneration costs

---

## Cost Analysis

**Per Guide:**
- Input tokens: ~2,200 ($0.00033)
- Output tokens: ~3,900 ($0.00234)
- Total: ~$0.0027/guide

**Full 27 Guides:**
- Total cost: ~$0.073
- Time: ~54 minutes (sequential)
- Parallelization possible for faster batches

**Knowledge Base ROI:**
- 50 common errors → reused across all guides
- Template system → consistent structure
- One-time investment, infinite regenerations
