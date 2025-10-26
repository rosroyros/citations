# PSEO Source Type Guide Generation Plan

**Date**: October 25, 2024
**Status**: Ready for Execution
**Phase**: Post-Mega-Guides (15 guides deployed)

---

## Current State Analysis

### ✅ What's Already Complete

**Infrastructure** (from `pseo-phase-1-implementation-plan.md`):
- ✅ Week 1-2: Knowledge base foundation (47 rules, 100 examples, 50 errors)
- ✅ Week 3-4: Templates (`source_type_template.md` + `layout.html`)
- ✅ Week 5-6: LLM generation (GPT-4o-mini, $0.026 for 5 pages)
- ✅ Week 7: Review system (LLM + human review CLI)
- ✅ Week 8: Static site builder (`StaticSiteGenerator`)
- ✅ Week 9: MiniChecker component (embedded in pages)
- ✅ Week 10-11: **15 mega guides generated & deployed** to `/guide/*`

**Existing Guides**:
- 15 mega guides deployed (`/guide/apa-7th-edition/`, etc.)
- 3 source type guides deployed (`/how-to-cite-journal-article-apa/`, `/how-to-cite-book-apa/`, `/how-to-cite-website-apa/`)

**Working Components**:
- `backend/pseo/generator/content_assembler.py` - Has `assemble_source_type_page()` method
- `backend/pseo/generator/llm_writer.py` - GPT-4o-mini integration with prompt templates
- `backend/pseo/builder/static_generator.py` - Battle-tested (15 guides deployed)
- `backend/pseo/templates/source_type_template.md` - Ready to use
- `backend/pseo/builder/templates/layout.html` - Matches mockup design (purple #9333ea)

**Knowledge Base**:
- `backend/pseo/knowledge_base/citation_rules.json` - 47 APA 7 rules
- `backend/pseo/knowledge_base/common_errors.json` - 50 common errors
- `backend/pseo/knowledge_base/examples.json` - 100 examples with source_type tags

**Prompt Templates**:
- `backend/pseo/prompts/introduction_prompt.txt`
- `backend/pseo/prompts/explanation_prompt.txt`
- `backend/pseo/prompts/step_by_step_prompt.txt`
- `backend/pseo/prompts/faq_prompt.txt`
- `backend/pseo/prompts/error_explanation_prompt.txt`

### ❌ What's Missing

**Critical Gap**:
- ❌ NO `backend/pseo/configs/source_type_guides.json` - Config file defining 27 source types
- ❌ NO source type definitions with metadata (pain points, keywords, descriptions per type)

**Explanation**:
- `mega_guides.json` defines 15 mega guides with all metadata
- Need equivalent `source_type_guides.json` for source type pages
- Examples exist in knowledge base BUT configs don't

---

## Design Specifications

### Template Design (`source_type_template.md`)

**Structure** (10 sections):
1. Hero Section with Quick Reference (TL;DR box - purple bg)
2. Basic Format Explanation (LLM-generated)
3. Required vs Optional Elements (from knowledge base)
4. Reference List Examples (5-10 variations from knowledge base)
5. In-Text Citation Guidelines (from rules)
6. Step-by-Step Instructions (LLM-generated)
7. Common Errors Section (5-10 errors from knowledge base)
8. Validation Checklist (from rules)
9. Special Cases (LLM-generated)
10. FAQ Section (5-8 Q&A, LLM-generated)

**CSS Classes** (from `layout.html`):
- `.quick-ref-box` - Purple TL;DR box (#9333ea background)
- `.template-box` - Citation template display
- `.example-box` - Example containers
- `.citation-example` - Monospace citation text
- `.error-example` - Red error boxes
- `.correction-box` - Green correction boxes
- `.note-box` - Yellow note boxes
- `.checklist` - Checklist with checkmarks
- `.mini-checker` - Embedded checker CTAs

**Mobile Responsive**: All classes have `@media (max-width: 768px)` rules

### Content Generation Flow

```
Config (source_type_guides.json)
    ↓
ContentAssembler.assemble_source_type_page()
    ↓ Loads knowledge base data
    ├── citation_rules.json (filtered by source type)
    ├── examples.json (filtered by source_type tag)
    └── common_errors.json (filtered by source type)
    ↓ Generates LLM sections
    ├── LLMWriter.generate_explanation() → Basic Format
    ├── LLMWriter.generate_step_by_step() → Instructions
    ├── LLMWriter.generate_faq() → FAQ section
    └── Custom logic → Special Cases
    ↓ Combines with template
TemplateEngine.inject_variables(source_type_template.md)
    ↓ Outputs markdown
Markdown file with front matter
    ↓
StaticSiteGenerator.convert_markdown_to_html()
    ↓
StaticSiteGenerator.apply_layout(layout.html)
    ↓
Final HTML → content/dist/how-to-cite-{source}-apa/index.html
```

---

## Source Type Priority List (27 Total)

### Tier 1: Core Academic Sources (8 guides) - **GENERATE FIRST**

Target: 3,500-4,000 words each

1. **Conference Paper** - `/how-to-cite-conference-paper-apa/`
   - Keywords: "cite conference paper APA", "APA conference citation", "conference proceedings APA"
   - Pain points: "unclear proceedings format", "conference vs journal confusion", "presentation formats"
   - Variations: Published proceedings, unpublished paper, presentation

2. **Dissertation** - `/how-to-cite-dissertation-apa/`
   - Keywords: "cite dissertation APA", "APA dissertation citation", "ProQuest citation"
   - Pain points: "published vs unpublished", "ProQuest format", "institutional repositories"
   - Variations: Published, unpublished, ProQuest, institutional repository

3. **Thesis** - `/how-to-cite-thesis-apa/`
   - Keywords: "cite thesis APA", "master's thesis APA", "thesis citation format"
   - Pain points: "thesis vs dissertation terminology", "institutional format requirements"
   - Variations: Master's thesis, honors thesis, unpublished thesis

4. **Book Chapter** - `/how-to-cite-chapter-apa/`
   - Keywords: "cite book chapter APA", "chapter in edited book APA"
   - Pain points: "editor vs author confusion", "chapter vs book citation"
   - Variations: Edited book chapter, anthology chapter, reprint chapter

5. **Edited Book** - `/how-to-cite-edited-book-apa/`
   - Keywords: "cite edited book APA", "book with editors APA"
   - Pain points: "Ed. vs Eds. formatting", "editor placement"
   - Variations: Single editor, multiple editors, edition info

6. **Report** - `/how-to-cite-report-apa/`
   - Keywords: "cite report APA", "technical report APA", "research report citation"
   - Pain points: "report number formatting", "organizational author", "gray literature"
   - Variations: Technical report, research report, issue brief

7. **Government Report** - `/how-to-cite-government-report-apa/`
   - Keywords: "cite government report APA", "government document APA", "agency report"
   - Pain points: "agency authorship", "report numbers", "access URLs"
   - Variations: Federal, state, agency reports, congressional documents

8. **Dataset** - `/how-to-cite-dataset-apa/`
   - Keywords: "cite dataset APA", "data citation APA", "cite data APA"
   - Pain points: "version numbers", "repository URLs", "contributor roles"
   - Variations: Repository dataset, supplemental data, reanalysis dataset

### Tier 2: Online & Popular Sources (10 guides) - **GENERATE SECOND**

Target: 3,000-3,500 words each

9. **Newspaper Article (Online)** - `/how-to-cite-newspaper-apa/`
10. **Newspaper Article (Print)** - `/how-to-cite-newspaper-print-apa/`
11. **Magazine Article** - `/how-to-cite-magazine-apa/`
12. **Blog Post** - `/how-to-cite-blog-apa/`
13. **YouTube Video** - `/how-to-cite-youtube-apa/`
14. **Podcast** - `/how-to-cite-podcast-apa/`
15. **TED Talk** - `/how-to-cite-ted-talk-apa/`
16. **Wikipedia** - `/how-to-cite-wikipedia-apa/`
17. **Dictionary Entry (Online)** - `/how-to-cite-dictionary-apa/`
18. **Encyclopedia Entry (Online)** - `/how-to-cite-encyclopedia-apa/`

### Tier 3: Multimedia & Social Media (9 guides) - **GENERATE THIRD**

Target: 2,500-3,000 words each

19. **Film/Movie** - `/how-to-cite-film-apa/`
20. **TV Episode** - `/how-to-cite-tv-episode-apa/`
21. **Twitter/X Post** - `/how-to-cite-twitter-apa/`
22. **Instagram Post** - `/how-to-cite-instagram-apa/`
23. **Facebook Post** - `/how-to-cite-facebook-apa/`
24. **LinkedIn Post** - `/how-to-cite-linkedin-apa/`
25. **Software/App** - `/how-to-cite-software-apa/`
26. **Patent** - `/how-to-cite-patent-apa/`
27. **Artwork** - `/how-to-cite-artwork-apa/`

---

## Implementation Tasks

---

## ✅ TIER 1 COMPLETION STATUS (2025-01-26)

**8 Tier 1 Source Type Guides - COMPLETE**

All guides generated, reviewed, and design-matched to mockup:

1. ✅ Conference Paper - 4,859 words - http://10.0.0.222:8002/how-to-cite-conference-paper-apa/
2. ✅ Dissertation - 5,149 words - http://10.0.0.222:8002/how-to-cite-dissertation-apa/
3. ✅ Thesis - 5,034 words - http://10.0.0.222:8002/how-to-cite-thesis-apa/
4. ✅ Book Chapter - 5,732 words - http://10.0.0.222:8002/how-to-cite-book-chapter-apa/
5. ✅ Edited Book - 5,440 words - http://10.0.0.222:8002/how-to-cite-edited-book-apa/
6. ✅ Report - 5,464 words - http://10.0.0.222:8002/how-to-cite-report-apa/
7. ✅ Government Report - 5,395 words - http://10.0.0.222:8002/how-to-cite-government-report-apa/
8. ✅ Dataset - 5,016 words - http://10.0.0.222:8002/how-to-cite-dataset-apa/

**Stats:**
- Average: 5,261 words (50% above 3,500 target)
- Total LLM cost: ~$0.022
- Design matches mockup completely
- Generic common errors (source-specific errors for Tier 2/3)

**Files Created/Modified:**
- `backend/pseo/configs/source_type_guides.json` - 8 source type configs
- `backend/pseo/scripts/generate_and_build_one_source_type.py` - Generator script
- `backend/pseo/templates/source_type_template.md` - Updated with mini-checkers, related links
- `backend/pseo/builder/assets/css/styles.css` - Added step-box, related-box, source_type wrapper
- `backend/pseo/builder/templates/layout.html` - Fixed header icon (checkmark)
- `backend/pseo/generator/content_assembler.py` - Added quick reference templates

**Next Steps:**
- Deploy Tier 1 to production
- Generate Tier 2 (10 guides)
- Generate Tier 3 (9 guides)

---

### Task 1: Create Source Type Config File ✅ **DONE**

**File**: `backend/pseo/configs/source_type_guides.json`

**Structure** (matches `mega_guides.json` format):
```json
[
  {
    "id": "source_type_01",
    "title": "How to Cite a Conference Paper in APA Format",
    "topic": "conference paper citation",
    "url": "/how-to-cite-conference-paper-apa/",
    "url_slug": "how-to-cite-conference-paper-apa",
    "description": "Complete guide to citing conference papers in APA 7. Includes format rules, examples for proceedings, presentations, and unpublished papers.",
    "keywords": [
      "cite conference paper APA",
      "APA conference citation",
      "conference proceedings APA",
      "cite presentation APA"
    ],
    "pain_points": [
      "unclear proceedings vs paper format",
      "conference vs journal confusion",
      "multiple presentation formats",
      "unpublished vs published papers"
    ],
    "target_audience": "graduate students and researchers",
    "word_count_target": 3500
  }
  // ... 26 more entries
]
```

**Required Fields** (per entry):
- `id` - Unique identifier (source_type_01 to source_type_27)
- `title` - H1 title for page
- `topic` - LLM generation topic
- `url` - Full URL path (for sitemap)
- `url_slug` - URL slug (for file naming)
- `description` - Meta description (150-160 chars)
- `keywords` - Array of 3-5 target keywords
- `pain_points` - Array of 3-5 common user frustrations
- `target_audience` - Primary audience
- `word_count_target` - Minimum word count (3000-4000)

**Deliverable**: JSON file with all 27 source type definitions

**Time Estimate**: 2-3 hours (research keywords, pain points for each)

---

### Task 2: Verify Generator Compatibility

**Script to Check**: `backend/pseo/scripts/generate_and_build_one_guide.py`

**Current State**:
```python
# Line 54: Hardcoded to mega_guides.json
config_file = Path(__file__).parent.parent / "configs" / "mega_guides.json"

# Line 92: Calls assemble_mega_guide()
result = assembler.assemble_mega_guide(config["topic"], assembler_config)
```

**Options**:

**Option A: Modify Existing Script** (Add parameter)
```python
# Add argument for config type
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--config', default='mega_guides.json')
parser.add_argument('--index', type=int, default=0)
args = parser.parse_args()

# Use appropriate method
if 'source_type' in args.config:
    result = assembler.assemble_source_type_page(config["topic"], assembler_config)
else:
    result = assembler.assemble_mega_guide(config["topic"], assembler_config)
```

**Option B: Create New Script** (Copy & modify)
```bash
# Create new script
cp backend/pseo/scripts/generate_and_build_one_guide.py \
   backend/pseo/scripts/generate_and_build_one_source_type.py

# Modify to use source_type_guides.json and assemble_source_type_page()
```

**Recommendation**: **Option B** (cleaner separation, no breaking changes)

**Deliverable**: `generate_and_build_one_source_type.py` script

**Time Estimate**: 30 minutes

---

### Task 3: Generate Test Guide (Conference Paper)

**Command**:
```bash
cd /Users/roy/Documents/Projects/citations
source venv/bin/activate

python3 backend/pseo/scripts/generate_and_build_one_source_type.py --index 0
```

**Expected Output**:
```
content/review_queue/source_type_01_how-to-cite-conference-paper-apa.json
content/test/how-to-cite-conference-paper-apa.md
content/dist/how-to-cite-conference-paper-apa/index.html
```

**Generated Content Should Include**:
- 3,500+ words
- TL;DR Quick Reference box (purple)
- 5-8 citation examples (proceedings, presentation, unpublished)
- 8-12 common errors
- Step-by-step instructions
- Special cases section
- 5-8 FAQ questions
- Mini-checker CTAs embedded
- Related resources grid

**Verification Checklist**:
- [ ] Matches mockup design (`design/mocks/source_type_mockup.html`)
- [ ] TL;DR box has purple background (#9333ea)
- [ ] Examples properly formatted (monospace, correct italics)
- [ ] Common errors section has red/green boxes
- [ ] Mini-checker components render
- [ ] Mobile responsive (test at 375px width)
- [ ] LLM review passes (PASS or low-severity issues only)
- [ ] No template variable failures (`{{variable}}` visible)
- [ ] Internal links work
- [ ] Related resources relevant

**Test Locally**:
```bash
cd content/dist
python3 -m http.server 8002
# Open: http://localhost:8002/how-to-cite-conference-paper-apa/
```

**Manual Review Questions**:
1. Are citation examples accurate per APA 7?
2. Do pain points address real user frustrations?
3. Is step-by-step clear and actionable?
4. Are common errors actually common?
5. Does FAQ answer likely search queries?

**Deliverable**: Approved Conference Paper guide

**Time Estimate**: 30 mins generation + 30 mins review = 1 hour

---

### Task 4: Batch Generate Tier 1 (8 Guides)

**After Conference Paper approval**, generate remaining Tier 1:

**Create Batch Script** (if doesn't exist):
```python
#!/usr/bin/env python3
"""
Batch generate source type guides from config file

Usage:
    python3 batch_generate_source_types.py --start 0 --end 7  # Tier 1
    python3 batch_generate_source_types.py --all              # All 27
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_and_build_one_source_type import main

# Loop through index range and call main()
```

**Command**:
```bash
python3 backend/pseo/scripts/batch_generate_source_types.py --start 0 --end 7
```

**Expected Output**:
```
✅ 1/8: Conference Paper (3,587 words, PASS)
✅ 2/8: Dissertation (3,912 words, PASS)
✅ 3/8: Thesis (3,456 words, PASS)
✅ 4/8: Book Chapter (3,678 words, PASS)
✅ 5/8: Edited Book (3,501 words, PASS)
✅ 6/8: Report (3,723 words, PASS)
✅ 7/8: Government Report (3,834 words, PASS)
✅ 8/8: Dataset (3,412 words, PASS)

Total cost: ~$0.04 (8 pages × $0.005/page)
```

**Human Review** (per `pseo-req-10-Content-Production-Workflow.md`):
- Review 20% sample = 2 guides manually
- Sample #1 (Conference Paper) + #4 (Book Chapter)
- Check: accuracy, examples, tone, structure

**Deliverable**: 8 approved Tier 1 guides in `content/review_queue/`

**Time Estimate**: 1 hour generation + 1 hour review = 2 hours

---

### Task 5: Build & Deploy Tier 1

**Build HTML**:
```bash
# Already built during generation, but verify
python3 backend/pseo/scripts/build_production.py
```

**Test Locally**:
```bash
cd content/dist
python3 -m http.server 8002

# Test all 8 pages:
# http://localhost:8002/how-to-cite-conference-paper-apa/
# http://localhost:8002/how-to-cite-dissertation-apa/
# ... etc
```

**Deploy to VPS**:
```bash
# SSH to production
ssh deploy@178.156.161.140

# Navigate to project
cd /opt/citations

# Pull latest (or rsync content/dist)
git pull origin main

# Run deployment script
./deployment/scripts/deploy.sh
```

**Verification on Production**:
- [ ] All 8 pages accessible
- [ ] Sitemap updated
- [ ] Google Analytics tracking
- [ ] Mini-checker functional
- [ ] Mobile responsive
- [ ] Internal links work

**Deliverable**: 8 source type guides live on production

**Time Estimate**: 30 mins

---

### Task 6: Generate & Deploy Tiers 2-3 (Optional)

**After Tier 1 success**, repeat process:

**Tier 2** (10 guides):
```bash
python3 backend/pseo/scripts/batch_generate_source_types.py --start 8 --end 17
```

**Tier 3** (9 guides):
```bash
python3 backend/pseo/scripts/batch_generate_source_types.py --start 18 --end 26
```

**Total for all 27 guides**:
- Generation time: ~2 hours
- Review time (20% sample): ~2 hours
- Cost: ~$0.14 total (27 × $0.005)
- Deployment: 30 mins

**Deliverable**: All 27 source type guides deployed

**Time Estimate**: 4-5 hours total

---

## Quality Standards (from `pseo-req-07-Content-Quality-Standards.md`)

### Content Depth
- ✅ Minimum 3,000 words per page (excluding boilerplate)
- ✅ At least 5 detailed examples per source type
- ✅ Compare correct vs incorrect formatting
- ✅ Explain WHY the error matters (not just WHAT)
- ✅ Include edge cases and variations

### Anti-Thin Content
- ✅ Original explanation (not paraphrased from style guide)
- ✅ Visual formatting examples (monospace code blocks)
- ✅ Common student mistakes specific to that source type
- ✅ Step-by-step correction process
- ✅ Related sources users should check

### User Value Validation
Must answer:
1. What specific format do I need for this source type?
2. How do I identify required vs optional elements?
3. What does the correct format look like?
4. What are common mistakes for this source?
5. How do I validate my citation is correct?

### Success Metrics (post-launch)
- Average time on page: >90 seconds
- Bounce rate: <60%
- Pages per session: >2
- LLM review pass rate: >90%
- Index rate within 2 weeks: >80%

---

## Cost Analysis

### Per-Page Cost (GPT-4o-mini)
Based on 5 test pages = $0.026 total:
- **Average per page**: $0.005
- **3,500 words**: ~130 input tokens, ~2,400 output tokens
- **Input cost**: $0.15/1M tokens = $0.00002
- **Output cost**: $0.60/1M tokens = $0.00144
- **Total per page**: ~$0.00146

### Total Project Cost
- **Tier 1** (8 guides): 8 × $0.005 = **$0.04**
- **Tier 2** (10 guides): 10 × $0.005 = **$0.05**
- **Tier 3** (9 guides): 9 × $0.005 = **$0.045**
- **All 27 guides**: **~$0.14 total**

**Extremely affordable** - entire project < $0.20

---

## Timeline Estimate

### Conservative Approach (Recommended)
1. **Task 1**: Create config file (2-3 hours)
2. **Task 2**: Modify/create generator script (30 mins)
3. **Task 3**: Generate & review Conference Paper (1 hour)
4. **Approval checkpoint** → Get user approval
5. **Task 4**: Generate Tier 1 batch (2 hours)
6. **Task 5**: Deploy Tier 1 (30 mins)
7. **Task 6**: Generate & deploy Tiers 2-3 (4 hours)

**Total time**: **10-11 hours** (including reviews)
**Can be done over**: 2-3 work sessions

### Aggressive Approach
1. Create config + generate all 27 in one batch (3 hours)
2. Review 20% sample (2 hours)
3. Deploy all (30 mins)

**Total time**: **5-6 hours**

---

## Risk Mitigation

### Potential Issues

**Issue 1**: Content too similar across source types
- **Risk**: Thin content penalty
- **Mitigation**: Each source type has unique pain points, examples, special cases
- **Test**: Run Copyscape on 3 random pages before full batch

**Issue 2**: Examples not accurate for source type
- **Risk**: User confusion, loss of credibility
- **Mitigation**: Knowledge base has source_type tags, LLM filters by type
- **Test**: Manual review verifies examples match source type

**Issue 3**: Word count too low
- **Risk**: Thin content, poor rankings
- **Mitigation**: word_count_target enforced, LLM review checks
- **Test**: All pages must meet 3000+ word minimum

**Issue 4**: Template variables not replaced
- **Risk**: Broken pages with `{{variable}}` visible
- **Mitigation**: LLM reviewer checks for template failures
- **Test**: Automated check for `{{` in generated HTML

**Issue 5**: Generator breaks with source types
- **Risk**: Batch generation fails
- **Mitigation**: Test single page first (Conference Paper)
- **Test**: Full end-to-end test before batch

---

## Success Criteria

### Immediate (Post-Generation)
- [ ] All 27 source type configs created
- [ ] Conference Paper guide approved
- [ ] All pages meet word count minimums
- [ ] LLM review pass rate >90%
- [ ] No template variable failures
- [ ] Manual review finds <5 errors per page
- [ ] All pages render correctly (mobile + desktop)

### Short-Term (2 weeks post-deploy)
- [ ] All pages indexed by Google (>80%)
- [ ] No manual actions from Google
- [ ] Average time on page >90s
- [ ] Bounce rate <65%
- [ ] Internal linking working
- [ ] Mini-checker functional on all pages

### Long-Term (30 days post-deploy)
- [ ] At least 5 pages ranking top 50 for target keywords
- [ ] Organic traffic increase measurable
- [ ] Pages per session >2
- [ ] Featured snippet capture rate >5%

---

## Next Steps

### Immediate Actions
1. ✅ **Review this plan** - Confirm approach
2. ⬜ **Approve Task 1** - Create source_type_guides.json config
3. ⬜ **Execute Task 2** - Create generator script
4. ⬜ **Execute Task 3** - Generate Conference Paper test
5. ⬜ **Manual review** - Approve or request changes
6. ⬜ **Proceed to batch** - Generate remaining guides

### Questions to Answer Before Starting
1. **Priority**: Generate Tier 1 only (8 guides) or all 27?
2. **Review approach**: 20% sample (6 guides) or higher percentage?
3. **Deployment**: Deploy incrementally (Tier 1 → 2 → 3) or all at once?
4. **Timeline**: Complete in 1-2 days or spread over a week?

---

## References

**Implementation Plan**: `pseo-phase-1-implementation-plan.md`
- Lines 2128-2160: Source type list
- Lines 66-109: Task 1.2 Curate APA 7 Citation Rules ✅ DONE
- Lines 143-198: Task 1.3 Curate Real Citation Examples ✅ DONE

**Requirements Docs**:
- `docs/pseo-req-01-overview.md` - Lines 60-94: Content architecture
- `docs/pseo-req-07-Content-Quality-Standards.md` - Quality requirements
- `docs/pseo-req-10-Content-Production-Workflow.md` - Production workflow

**Design Reference**: `design/mocks/source_type_mockup.html`

**Existing Infrastructure**:
- Generator: `backend/pseo/scripts/generate_and_build_one_guide.py`
- Template: `backend/pseo/templates/source_type_template.md`
- Layout: `backend/pseo/builder/templates/layout.html`
- Assembler: `backend/pseo/generator/content_assembler.py`
- LLM Writer: `backend/pseo/generator/llm_writer.py`
- Static Builder: `backend/pseo/builder/static_generator.py`

**Knowledge Base**:
- Rules: `backend/pseo/knowledge_base/citation_rules.json`
- Examples: `backend/pseo/knowledge_base/examples.json`
- Errors: `backend/pseo/knowledge_base/common_errors.json`

**Prompts**:
- `backend/pseo/prompts/introduction_prompt.txt`
- `backend/pseo/prompts/explanation_prompt.txt`
- `backend/pseo/prompts/step_by_step_prompt.txt`
- `backend/pseo/prompts/faq_prompt.txt`

---

**Ready to execute? Awaiting approval to begin Task 1.**
