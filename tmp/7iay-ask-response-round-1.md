Perfect! Oracle has completed the review. Here's the summary:

## Oracle Review Results for MLA Pages Configuration

### ✅ **What's Working Well (4/6)**

1. **Structure Validation**: JSON syntax valid, all fields complete, consistent structure
2. **Content Completeness**: All 69 entries properly formatted with required fields  
3. **Priority Assignment**: Well-distributed values (0.54-1.0) make sense for SEO
4. **SEO Optimization**: Excellent title format with "MLA 9" specificity and natural language

### ❌ **CRITICAL BLOCKER (P0)**

**Generator Compatibility Issue:**
- The generator expects **3 separate files**: `mega_guides.json`, `source_type_guides.json`, `specific_sources.json`
- You created **1 unified file**: `mla_pages.json`  
- **This will cause the generator to fail**

**Fix Required**: Split into 3 files (recommended) OR modify generator code

### ⚠️ **High-Value Improvements (P1)**

**Missing MLA-Specific Sources** (4 sources):
- Norton Anthology (extremely common in English courses)
- Project MUSE (humanities database)
- LION (Literature Online)  
- CliffsNotes (similar to SparkNotes)

**Priority Adjustments** (4 items):
- Poetry Foundation: 0.78 → **0.85** (Tier 1) - core MLA use case
- Shakespeare: 0.85 → **0.88** - most cited literary source
- Poem (source type): 0.8 → **0.85** - fundamental to MLA
- Play (source type): 0.78 → **0.82** - drama courses

### 📋 **Recommended Next Actions**

Before proceeding to generation scripts (citations-7o50):

1. **P0**: Split `mla_pages.json` into 3 separate files for generator compatibility
2. **P1**: Add 4 missing sources (Norton, MUSE, LION, CliffsNotes)
3. **P1**: Adjust 4 priorities (Poetry Foundation, Shakespeare, Poem, Play)

Full Oracle response saved to: `tmp/7iay-ask-response-round-1.md` (234 lines)
efore proceeding to generation scripts.
break on unexpected fields
2. **URL slugs consistency**: 
   - Specific sources use `youtube` (no style suffix)
   - Generator adds `-mla` suffix in `generate_url_structure()` → final URL: `/cite-youtube-mla/`
   - This is correct and matches APA pattern

---

### 3. PRIORITY ASSIGNMENT ✅ **GOOD (with recommendations)**

**Current Priority Distribution:**

**Mega Guides (0.6-1.0):**
- 1.0: Complete MLA 9 Guide ✅
- 0.9: Works Cited, In-Text Citations ✅
- 0.8: Check Citations ✅
- 0.7: Fix Errors ✅
- 0.6: English Majors, Literature Studies ✅

**Source Type Guides (0.7-1.0):**
- 1.0: Book, YouTube ✅
- 0.95: Website ✅
- 0.9: Journal ✅
- 0.88: Newspaper ✅
- 0.85: Book Chapter ✅
- 0.8: Poem ✅
- Lower: Film (0.75), Short Story (0.75), Dictionary (0.7), etc.

**Specific Sources (0.54-1.0 across 50 sources):**
- Tier 1 (8): YouTube (1.0), Wikipedia (0.95), NYT (0.9), JSTOR (0.85), Shakespeare (0.85), Bible (0.82), SparkNotes (0.82), TED (0.8) ✅
- Tier 2 (26): Major newspapers, databases, magazines (0.62-0.78) ✅
- Tier 3 (16): Streaming, social media, niche (0.54-0.62) ✅

**Recommendations:**

1. **Consider MLA-specific adjustments:**
   - **Poetry Foundation**: Currently 0.78 (Tier 2) → Recommend **0.85** (Tier 1)
     - **Rationale**: MLA is THE citation style for literature; poetry is core use case
   - **Shakespeare**: Currently 0.85 → Good, maybe bump to **0.88**
     - **Rationale**: Most cited literary source in MLA; English students cite Shakespeare extensively
   - **JSTOR**: Currently 0.85 → Consider **0.88**
     - **Rationale**: Primary academic database for humanities/literature research

2. **Social Media Priority:**
   - TikTok (0.62), Instagram (0.64) seem appropriate for MLA audience (less used than in APA/sciences)
   - Twitter/X (0.66) could be slightly higher (0.68) given use in literary criticism

3. **Consider adding (if missing):**
   - **Norton Anthology** (if not covered by "anthology" source type)
   - **Literary criticism databases** (ProjectMUSE, LION)

---

### 4. SEO OPTIMIZATION ✅ **EXCELLENT**

**Title Format Analysis:**
- ✅ All titles contain "MLA 9" or "MLA 9th Edition" (not just "MLA") - excellent for SEO differentiation
- ✅ Clear format: "How to Cite [X] in MLA 9" or "How to [Action] in MLA 9"
- ✅ Natural language, search-friendly
- ✅ Specific edition mentioned (disambiguates from MLA 8)

**URL Structure:**
- ✅ Mega guides: `/guide/mla-[topic]/` (e.g., `/guide/mla-9th-edition/`)
- ✅ Source types: `/how-to-cite-[type]-mla/` (e.g., `/how-to-cite-book-mla/`)
- ✅ Specific sources: `/cite-[source]-mla/` (e.g., `/cite-youtube-mla/`)

**SEO Best Practices:**
- ✅ Keywords in titles
- ✅ Pain points identified (helps with content targeting)
- ✅ Target audience defined (helps with tone/language)
- ✅ Description follows search intent

---

### 5. MLA-SPECIFIC CONSIDERATIONS ⚠️ **NEEDS ATTENTION**

**Strengths:**
- ✅ Includes MLA-specific sources: Shakespeare, Bible, Poetry Foundation, SparkNotes
- ✅ Literary sources prioritized appropriately
- ✅ Includes literary forms: Poem, Short Story, Play (not in APA)

**Critical Gaps:**

1. **Missing High-Value MLA Sources:**
   - **Norton Anthology** (extremely common in English courses)
   - **CliffsNotes** (similar to SparkNotes, widely used)
   - **Project MUSE** (humanities database, critical for MLA users)
   - **LION (Literature Online)** (major literary database)
   - **Poetry.org** (Academy of American Poets)

2. **Consider Adding Source Types:**
   - **Sacred Text** (beyond Bible - Quran, Torah, Bhagavad Gita)
   - **Liner Notes** (album liner notes - common in music courses)
   - **Lecture/Class Notes** (common student question)

3. **Priority Adjustments Needed:**
   - **Book**: 1.0 ✅ (correct - books are foundational in MLA)
   - **Journal**: 0.9 ✅ (correct - slightly less critical than in APA)
   - **Poem**: 0.8 → Consider **0.85** (core MLA use case)
   - **Play**: 0.78 → Consider **0.82** (Shakespeare/drama courses)
   - **Short Story**: 0.75 → Consider **0.80** (very common in lit courses)

---

### 6. STRUCTURAL ISSUE: ⚠️ **CRITICAL**

**Problem**: The generator script expects **separate config files** but you created a **unified config file**.

**Generator Code (`generate_mla_pages.py:59`):**
```python
config_file = Path(__file__).parent.parent / "configs" / f"{config_type}.json"
```

**Expected files:**
- `backend/pseo/configs/mega_guides.json` (for MLA mega guides)
- `backend/pseo/configs/source_type_guides.json` (for MLA source types)
- `backend/pseo/configs/specific_sources.json` (for MLA specific sources)

**Current file:**
- `backend/pseo/configs/mla_pages.json` (all-in-one)

**Solutions:**

**Option A: Split the file** (matches existing APA pattern):
```bash
# Extract each section into separate JSON files
python3 -c "
import json
with open('backend/pseo/configs/mla_pages.json') as f:
    data = json.load(f)

# Save each section
with open('backend/pseo/configs/mla_mega_guides.json', 'w') as f:
    json.dump(data['mega_guides'], f, indent=2)

with open('backend/pseo/configs/mla_source_type_guides.json', 'w') as f:
    json.dump(data['source_type_guides'], f, indent=2)

with open('backend/pseo/configs/mla_specific_sources.json', 'w') as f:
    json.dump({'sources': data['specific_sources']}, f, indent=2)
"
```

**Option B: Modify generator** (cleaner, but requires code change):
- Update `load_config()` to check for `mla_pages.json` first
- Fall back to separate files if unified file doesn't exist
- Allows both patterns to coexist

**Recommendation**: **Option A** for immediate compatibility, then **Option B** as enhancement.

---

### SUMMARY

| **Area** | **Status** | **Priority** |
|----------|-----------|-------------|
| Structure Validation | ✅ PASS | - |
| Content Completeness | ✅ PASS | - |
| Priority Assignment | ✅ GOOD | P2: Adjust literary sources (Poetry Foundation, Shakespeare) |
| SEO Optimization | ✅ EXCELLENT | - |
| MLA-Specific Sources | ⚠️ GAPS | P1: Add Norton, Project MUSE, LION |
| Generator Compatibility | ❌ **CRITICAL** | P0: Split file OR modify generator |

---

### IMMEDIATE ACTION ITEMS

**P0 (Blocker):**
1. ✅ Split `mla_pages.json` into 3 separate files to match generator expectations
   - OR modify generator to load unified file

**P1 (High-Value MLA Sources):**
2. Add missing sources: Norton Anthology, Project MUSE, LION, CliffsNotes
3. Adjust priorities: Poetry Foundation (0.85), Shakespeare (0.88), Poem type (0.85), Play type (0.82)

**P2 (Polish):**
4. Review word count targets vs actual generation capacity
5. Validate all URL slugs are SEO-friendly and unique

The configuration is **excellent quality** overall. Main issue is file structure mismatch with generator. Content, SEO, and priority strategy are sound. MLA-specific considerations show good understanding of the audience, with room for a few high-value additions.
