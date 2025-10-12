# Citation Format Checker - Requirements Document
## Part 1: Overview and Architecture

**Document Version:** 1.0  
**Last Updated:** October 2025  
**Document Purpose:** Functional requirements for programmatic SEO content system

---

## 1. PROJECT OVERVIEW & OBJECTIVES

### 1.1 Primary Goal
Create 1,500-2,000 SEO-optimized content pages that:
- Drive organic traffic through long-tail citation-related keywords
- Educate users about APA 7th edition citation formatting
- Guide users to the citation checker tool
- Position the site as the authority on citation validation (not generation)

### 1.2 Unique Value Proposition
Unlike competitors (Scribbr, EasyBib, Purdue OWL) who focus on citation **generation**, this site focuses on citation **validation and error prevention**.

**Key Differentiator:** Address the research finding that 90.9% of papers contain three or more reference formatting errors, and users spend 3-5 minutes manually correcting each auto-generated citation.

### 1.3 Target Audience
- **Primary:** Graduate students (Master's and PhD), undergraduate students
- **Secondary:** Academic researchers, faculty, journal editors
- **Disciplines:** Psychology, Education, Nursing, Social Work, Business, and other APA-using fields

### 1.4 Content Tone & Voice
- **Style:** Conversational yet professional
- **Approach:** Problem-solving focused, empathetic to citation struggles
- **Tone Reference:** Similar to Scribbr's approachable style, but with heavier emphasis on error prevention
- **Avoid:** Overly academic jargon, condescension, assumptions of prior knowledge
- **Language:** Use "you" to address reader directly; active voice preferred

**Example tone:**
- ✅ "This is one of the most common errors students make - let's fix it."
- ❌ "This error demonstrates a fundamental misunderstanding of APA guidelines."

### 1.5 Success Metrics
- **Traffic:** Organic search traffic from citation-related queries
- **Engagement:** Click-through rate to checker tool (target: 15-25%)
- **Quality:** Time on page >2 minutes (indicates content value)
- **Navigation:** Internal link clicks (indicates content discoverability)
- **Conversion:** Checker tool usage from content pages

---

## 2. CONTENT ARCHITECTURE & SITE STRUCTURE

### 2.1 Overall Site Structure

```
Homepage
│
├── Mega Guides (15 pages)
│   ├── Complete APA 7th Edition Guide
│   ├── Complete Guide to Checking APA Citations
│   ├── APA Citation Errors Guide
│   ├── Validation Guides
│   └── Comparison Guides
│
├── Source Type Pages (100-150 pages)
│   ├── Textual Works (journal, book, article, etc.)
│   ├── Academic Sources (dissertation, thesis, etc.)
│   ├── Gray Literature (reports, white papers, etc.)
│   ├── Online Content (webpages, social media, etc.)
│   └── Audiovisual & Data
│
├── Validation Pages (50-100 pages)
│   ├── Element Checking (capitalization, italics, etc.)
│   ├── List Checking (reference list, in-text citations)
│   └── Document Checking (full paper validation)
│
├── Error Pages (200-300 pages)
│   ├── Capitalization Errors
│   ├── Italics Errors
│   ├── Punctuation Errors
│   ├── Author Formatting Errors
│   ├── DOI/URL Errors
│   └── Other Common Errors
│
├── Discipline Pages (50-100 pages)
│   ├── Psychology, Nursing, Education, etc.
│   └── Field-specific citation guides
│
├── Comparison Pages (100 pages)
│   └── APA vs MLA vs Chicago for each source type
│
└── Specific Source Pages (1,000+ pages)
    ├── Major Publications (NYT, WSJ, etc.)
    ├── Government Sources (CDC, NIH, etc.)
    ├── Social Platforms (YouTube, Instagram, etc.)
    └── Academic Platforms (JSTOR, PubMed, etc.)
```

### 2.2 URL Structure Standards

**Principles:**
- Descriptive, keyword-rich URLs
- Consistent structure within page types
- No unnecessary parameters or dates
- Human-readable, intuitive hierarchy
- All lowercase with hyphens for word separation

**URL Patterns:**

| Page Type | URL Pattern | Example | SEO Keywords |
|-----------|-------------|---------|--------------|
| Mega Guide | `/guide/[topic-name]/` | `/guide/check-apa-citations/` | "check APA citations" |
| Source Type | `/how-to-cite-[source]-apa/` | `/how-to-cite-journal-article-apa/` | "how to cite journal article APA" |
| Validation | `/how-to-check-[element]-apa/` | `/how-to-check-capitalization-apa/` | "check capitalization APA" |
| Error Page | `/apa-[error-type]-error/` | `/apa-title-case-error/` | "APA title case error" |
| Discipline | `/apa-[discipline]-guide/` | `/apa-psychology-guide/` | "APA psychology guide" |
| Comparison | `/cite-[source]-comparison/` | `/cite-journal-comparison/` | "cite journal APA MLA" |
| Specific | `/cite-[specific-source]-apa/` | `/cite-new-york-times-apa/` | "cite New York Times APA" |

**URL Rules:**
- Maximum 5 words in URL slug
- Use full words (avoid abbreviations except "apa")
- No stop words unless necessary for clarity
- Version numbers in content, not URLs (for future-proofing)

### 2.3 Page Count Targets by Type

| Page Type | Target Count | Priority Level | Phase |
|-----------|--------------|----------------|-------|
| Mega Guides | 15 | Critical | Phase 1 |
| Source Type Pages | 100-150 | High | Phase 1-2 |
| Validation Pages | 50-100 | High | Phase 2 |
| Error Pages | 200-300 | Medium | Phase 2-3 |
| Discipline Pages | 50-100 | Medium | Phase 2-3 |
| Comparison Pages | 100 | Low | Phase 3 |
| Specific Sources | 1,000+ | Ongoing | Phase 3-4 |
| **TOTAL** | **1,500-2,000+** | | |

### 2.4 Content Hierarchy & Relationships

**Hub Pages** (Mega Guides):
- Serve as authoritative, comprehensive resources
- Link out to all related spoke pages
- Receive links from all related pages
- Updated regularly with new content

**Spoke Pages** (Specific guides):
- Focus on single topic in depth
- Link to related spokes
- Always link back to relevant hub
- Create topical clusters

**Cluster Strategy:**

```
[Hub: Complete APA Guide]
    ├── [Cluster: Journal Citations]
    │   ├── How to cite journal article
    │   ├── Check journal citation
    │   ├── Journal citation errors
    │   └── Cite specific journals
    │
    ├── [Cluster: Capitalization]
    │   ├── Title case guide
    │   ├── Sentence case guide
    │   ├── Check capitalization
    │   └── Capitalization errors
    │
    └── [Cluster: DOI/URL]
        ├── DOI formatting guide
        ├── Check DOI format
        ├── DOI vs URL
        └── DOI errors
```

### 2.5 Content Freshness Strategy

**Update Frequency:**
- **Mega Guides:** Quarterly review, update as APA changes
- **Source Type Pages:** Annual review
- **Error Pages:** As needed when new errors identified
- **Examples:** Use recent publications (2020-2024)

**Versioning Notes:**
- Focus on APA 7th edition (current)
- Include APA 6 vs 7 comparisons where relevant
- Do not create separate pages for APA 6
- Prepare structure for potential APA 8 in future

---

## 3. CONTENT STANDARDS & REQUIREMENTS

### 3.1 Writing Standards

**Quality Requirements:**
- Original content (no copying from competitors or APA manual)
- Clear, concise sentences (aim for 15-20 words average)
- Active voice preferred (80%+ of sentences)
- Scannable format (use headers, lists, tables)
- Accessible language (reading level: grades 10-12)

**Content Accuracy:**
- All rules must cite official APA sources
- Examples must be realistic and accurate
- Cross-reference Citation Rules Knowledge Base
- Fact-check against official APA Style website

**Formatting Standards:**
- Use proper markdown formatting
- Headers in sentence case
- Bold for emphasis (sparingly)
- Italics shown correctly in examples
- Code blocks for citation templates

### 3.2 Example Standards

**Every Page Must Include:**
- Minimum examples per page type:
  - Mega guides: 10+ examples
  - Source type pages: 5+ examples
  - Validation pages: 5+ examples
  - Error pages: 5+ examples
  - Discipline pages: 8+ examples

**Example Requirements:**
- Use real sources (from Google Scholar, PubMed, arXiv, etc.)
- Include publication dates 2020-2024 (recent)
- Show complete citation (not partial/truncated)
- Include both reference list and in-text citations
- Annotate formatting elements
- Provide variety (different authors, journals, scenarios)

**Example Format:**
```markdown
**Example: Journal article with DOI**

Reference list format:
Shrout, P. E., & Rodgers, J. L. (2018). Psychology, science, and knowledge construction: Broadening perspectives from the replication crisis. *Annual Review of Psychology*, *69*(1), 487-510. https://doi.org/10.1146/annurev-psych-122216-011845

In-text citation (parenthetical): (Shrout & Rodgers, 2018)
In-text citation (narrative): Shrout and Rodgers (2018)

Notes: Journal name and volume number are italicized; issue number in parentheses is not italicized.
```

### 3.3 Common Sections All Pages Must Include

**Required on Every Page:**
1. Meta title and description (specified in SEO section)
2. H1 heading (unique, keyword-optimized)
3. Introduction paragraph (2-3 sentences setting context)
4. At least one CTA to checker tool
5. Related resources section
6. Last updated date

**Recommended on Most Pages:**
- Quick reference box or summary
- Visual examples (text formatting shown)
- Checklist or table
- FAQ section (for SEO)
- Before/after examples

### 3.4 Accessibility Requirements

**Text Accessibility:**
- Minimum font size: 16px body text
- Line height: 1.5-1.6
- High contrast text/background
- No color-only information

**Structural Accessibility:**
- Proper heading hierarchy (H1 → H2 → H3, no skipping)
- Alt text for any images
- Table headers properly marked
- Lists using proper HTML/markdown structure

**Content Accessibility:**
- Define acronyms on first use
- Explain jargon when necessary
- Provide context for examples
- Link text is descriptive (not "click here")

---

## 4. CONTENT SOURCE REQUIREMENTS

### 4.1 Official APA Sources

**Primary Sources** (use for all rule citations):
1. **APA Style Website** (apastyle.org)
   - Style and Grammar Guidelines section
   - Reference Examples section
   - Common Questions
   
2. **APA Publication Manual, 7th Edition**
   - Official formatting rules
   - Chapter references when citing rules

**Secondary Sources** (for clarification/examples):
1. **Purdue OWL APA Guide**
2. **APA Style Blog**
3. **University library guides** (for additional examples)

**Citation Format for Rules:**
```markdown
According to APA 7th edition, journal article titles should use sentence case (American Psychological Association, 2020, p. 184).
```

### 4.2 Example Sources

**Academic Databases for Real Citations:**
1. **Google Scholar** (scholar.google.com)
   - Recent publications (2020-2024)
   - High-impact journals
   - Diverse fields

2. **PubMed** (pubmed.ncbi.nlm.nih.gov)
   - Health sciences sources
   - Biomedical research

3. **arXiv** (arxiv.org)
   - Preprints in various fields
   - STEM sources

4. **SSRN** (ssrn.com)
   - Social sciences
   - Business research

**Non-Academic Sources:**
- Major newspapers: New York Times, Wall Street Journal, Washington Post
- News organizations: Reuters, AP, BBC News
- Government websites: CDC, NIH, EPA, FDA
- Non-profit organizations: WHO, UN agencies

### 4.3 Prohibited Sources

**Do Not Use Examples From:**
- Other citation guides (copyright issues)
- Student papers or examples
- Predatory journals
- Unreliable sources
- Outdated publications (pre-2015 for examples)

---

## 5. TECHNICAL REQUIREMENTS

### 5.1 Content Format

**Storage Format:**
- Markdown (.md) for content
- YAML front matter for metadata
- Structured data for citation rules

**Required Metadata (YAML Front Matter):**
```yaml
---
title: "How to Cite a Journal Article in APA Format"
description: "Complete guide to citing journal articles in APA 7th edition with examples, common errors, and validation tips."
keywords: "APA journal citation, cite journal article APA, APA 7th edition journal"
url: "/how-to-cite-journal-article-apa/"
page_type: "source_type"
parent_category: "textual_works"
last_updated: "2024-10-15"
reading_time: "8 minutes"
related_pages:
  - "/how-to-cite-magazine-article-apa/"
  - "/how-to-check-journal-citation-apa/"
  - "/apa-journal-title-error/"
common_errors:
  - "article_title_italicized"
  - "missing_issue_number"
  - "title_case_article_title"
examples_count: 6
checklist_items: 12
---
```

### 5.2 Content Management Requirements

**System Must Support:**
- Template-based page generation
- Variable injection (e.g., source type name)
- Content reuse across pages
- Batch updates when rules change
- Version control for content
- Preview before publish

**Content Generation Workflow:**
1. Define page type and variables
2. Generate from template
3. Inject structured data (rules, examples)
4. Add unique content sections
5. Generate related links automatically
6. Validate formatting and links
7. Generate SEO metadata
8. Publish

### 5.3 Quality Assurance Requirements

**Automated Checks:**
- H1 uniqueness across site
- Meta description length (150-160 chars)
- Title tag length (50-60 chars)
- Internal link validity
- Example formatting correctness
- No broken external links
- Proper markdown formatting

**Manual Review Checklist:**
- Content accuracy
- Example authenticity
- Tone consistency
- Readability
- CTA placement
- Related links relevance

---

## 6. PROJECT SCOPE BOUNDARIES

### 6.1 In Scope

**Citation Styles:**
- APA 7th edition (primary focus)
- APA 6th edition (comparison only, no separate pages)
- MLA 9th edition (comparison pages only)
- Chicago 17th edition (comparison pages only)

**Source Types:**
- All common academic sources
- Digital/online sources
- Multimedia sources
- Government/gray literature
- Social media

**Validation Focus:**
- Format checking
- Error identification
- Element validation
- Consistency checking

### 6.2 Out of Scope (Initial Launch)

**Not Included:**
- Citation generation (users go to checker tool)
- Reference manager integration
- Browser extensions
- Mobile apps
- Other citation styles (IEEE, Harvard, Vancouver, etc.)
- Non-English language citations
- Plagiarism checking
- Paraphrasing guidance
- Writing advice beyond citations

**Future Consideration:**
- Additional citation styles (Phase 5+)
- International citation standards
- Citation in other languages
- Advanced checker features

---

## NEXT STEPS

This document establishes the foundation. Subsequent documents will detail:
- **Part 2:** Citation Rules Knowledge Base
- **Part 3:** Mega Guide Page Templates
- **Part 4:** Source Type & Validation Templates
- **Part 5:** Error & Discipline Page Templates
- **Part 6:** Comparison & Specific Source Templates
- **Part 7:** Real Examples Database Specifications
- **Part 8:** CTA and Internal Linking Strategy
- **Part 9:** SEO Specifications
- **Part 10:** Implementation Phases & Priorities
