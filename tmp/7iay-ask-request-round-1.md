You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-7iay

**Title**: MLA PSEO: Create MLA Page Configuration
**Status**: open (needs-review)
**Priority**: P1
**Type**: task

### Current Status

✅ **Task Completed**

Created comprehensive MLA pages configuration file at `backend/pseo/configs/mla_pages.json` with:

- **Total Pages**: 69 (7 mega + 12 source type + 50 specific)
- **JSON Validation**: ✓ Valid syntax
- **Count Validation**: ✓ 69 entries

Structure:
```json
{
  "style": "mla9",
  "style_name": "MLA 9th Edition",
  "mega_guides": [...],      // 7 guides
  "source_type_guides": [...], // 12 guides
  "specific_sources": [...]   // 50 sources
}
```

### The Question/Problem/Dilemma

User wants to focus on: "Structure validation, content completeness, priority assignment, SEO optimization, and MLA-specific considerations for the newly created mla_pages.json configuration"

I need technical guidance on:
1. **Structure validation**: Is the JSON structure correct and consistent with existing APA configs?
2. **Content completeness**: Are all 69 entries properly formatted with required fields?
3. **Priority assignment**: Do the priority values (0.54 to 1.0) make sense for SEO and generation order?
4. **Title SEO**: Do titles follow best practices for search optimization?
5. **MLA-specific considerations**: Are there MLA-specific sources or priorities that should be adjusted?

### Relevant Context

**Background**:
- This is part of the MLA PSEO expansion (epic citations-yivs)
- The config will be used by generation scripts to create 69 static SEO pages
- Existing APA configs are in `backend/pseo/configs/` (mega_guides.json, source_type_guides.json, specific_sources.json)
- MLA is primarily used by English/Literature students (different audience than APA's psychology/sciences)

**Key Decisions Made**:
- Used existing APA configs as structural reference
- Added explicit "MLA 9" in all titles (not just "MLA") for SEO clarity
- Included MLA-specific sources (Shakespeare, Bible, SparkNotes, Poetry Foundation)
- Organized specific sources by 3-tier priority system
- Set YouTube and Book as highest priority (1.0) for both source types

**Content Breakdown**:

**Mega Guides (7):**
1. Complete MLA 9th Edition Guide (priority 1.0)
2. MLA Works Cited Page Guide (0.9)
3. MLA In-Text Citations Guide (0.9)
4. Check MLA Citations (0.8)
5. Fix MLA Citation Errors (0.7)
6. MLA for English Majors (0.6)
7. MLA for Literature Studies (0.6)

**Source Type Guides (12):**
- Book (1.0), YouTube (1.0), Website (0.95), Journal (0.9), Newspaper (0.88)
- Film (0.75), Poem (0.8), Short Story (0.75), Play (0.78)
- Dictionary (0.7), Interview (0.72), Book Chapter (0.85)

**Specific Sources (50):**
- Tier 1 (8 sources): YouTube, Wikipedia, NYT, JSTOR, Shakespeare, Bible, SparkNotes, TED
- Tier 2 (26 sources): Major newspapers, magazines, databases, platforms
- Tier 3 (16 sources): Streaming services, social media, niche publications

### Supporting Information

**Recent commit**:
```
feat(mla-pseo): create MLA pages configuration with 69 entries

Create comprehensive MLA PSEO configuration file with:
- 7 mega guides (complete MLA guide, works cited, in-text citations, etc.)
- 12 source type guides (book, journal, website, YouTube, etc.)
- 50 specific sources sorted by priority (YouTube 1.0 to TikTok 0.62)

All titles use "How to Cite [Source] in MLA 9" format for SEO.
Priority-based generation order with 3-tier system.
```

**File created**: `backend/pseo/configs/mla_pages.json` (810 lines)

**Validation performed**:
```
✓ JSON syntax valid (python -m json.tool)
✓ 69 total entries (7 + 12 + 50)
✓ All titles contain "MLA"
✓ Priorities set for all entries
✓ Tier assignments complete
```

**Questions for Oracle**:
1. Are there any structural issues or missing fields that would cause problems for the generator?
2. Do the priority assignments make sense given MLA's primary audience (English/Literature students)?
3. Should any MLA-specific sources be prioritized higher (e.g., Shakespeare, Poetry Foundation)?
4. Are the title formats optimal for SEO, or should they be adjusted?
5. Are there any critical MLA sources missing from the 50 specific sources?
6. Is the tier system (1/2/3) appropriate for the generation order?

**Comparison with APA configs**:
- APA specific_sources.json uses flat `"sources": [...]` structure WITHOUT priority/tier fields
- MLA config adds `priority` and `tier` fields to each specific source for generation ordering
- This is a departure from APA structure - is this intentional and acceptable for the generator?

**File samples**:

**APA specific_sources.json structure** (for comparison):
```json
{
  "sources": [
    {
      "name": "youtube",
      "title": "How to Cite YouTube Videos in APA Format",
      "slug": "youtube",
      "description": "...",
      "priority": 1.0
    }
  ]
}
```

**MLA mla_pages.json specific_sources structure**:
```json
{
  "specific_sources": [
    {
      "name": "youtube",
      "title": "How to Cite YouTube Videos in MLA 9",
      "slug": "youtube",
      "description": "...",
      "priority": 1.0,
      "tier": 1
    }
  ]
}
```

**Key difference**: MLA config adds `tier` field to each specific source entry. Is this intentional and compatible with the generator?
