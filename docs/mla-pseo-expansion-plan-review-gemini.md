# MLA PSEO Expansion Plan Review

> **Date**: December 30, 2024
> **Reviewer**: Antigravity

## Executive Summary

The proposal provides a solid, low-risk strategy for expanding into MLA PSEO content. The "Minimal Changes" architecture is excellent for protecting the existing APA revenue stream. However, the plan has a few gaps regarding **content generation logistics** (specifically example generation) and **frontend UX** that need addressing to ensure high conversion rates.

## Strengths

1.  **Risk Isolation**: The decision to use a parallel directory structure (`knowledge_base/mla9/` vs root/implicit APA) and a subclassed `MLAStaticSiteGenerator` is the correct architectural choice. It ensures zero regression risk for APA pages.
2.  **Thin Wrapper Approach**: Subclassing `EnhancedStaticSiteGenerator` maximizes code reuse while allowing style-specific overrides (like the mini-checker placeholder).
3.  **SEO Strategy**: The "Specific Source" tiering (Journals, Databases) aligns well with search intent.
4.  **Quality Gates**: Explicit similarity checks (TF-IDF) against APA pages are crucial to avoid duplicate content penalties.

## Identified Gaps & Risks

### 1. Example Generation Logic (Critical)
The plan lists `knowledge_base/mla9/examples.json`, but `backend/pseo/generate_examples.py` is currently hardcoded for APA (uses `&` for authors, APA date formats, etc.).
*   **Risk**: You cannot simply "create" the JSON without the logic to generate the hundreds of fictional examples needed for the pages.
*   **Fix**: You need a `generate_mla_examples.py` script (or refactor existing) that implements MLA formatting rules (e.g., "and" instead of "&", Date position, etc.) to populate this JSON.

### 2. Frontend Footer Bloat
Adding 15-20 MLA links to the existing Footer grid (which already has ~20 APA links) will create a "link farm" look that degrades UX.
*   **Fix**: Restructure the footer into "Citation Style" tabs (APA | MLA) or distinct columns.

### 3. Rollback Destructiveness
The rollback plan relies on `rm -rf`. This is risky and irreversible.
*   **Fix**: Implement a "hide" mechanism (e.g., a build flag that excludes MLA from the sitemap and output directory) rather than physical deletion.

## Detailed Recommendations

### A. Technical Implementation
*   **Create `generate_mla_examples.py`**: Do not try to hand-write `examples.json`. Clone `generate_examples.py` and modify formatting logic for MLA (Validation: `backend/pseo/generate_examples.py` lines 70-84 hardcode APA style).
*   **Style-Agnostic Components**: Ensure `components.py` (specifically `CitationExampleComponent`) doesn't have hidden APA bias. (Audit: It seems generic, which is good).

### B. User Experience (Ergonomics)
*   **"Copy Citation" Button**: Add a simple "Copy" button to every citation example on the PSEO pages. This is a high-value ergonomic win for students.
*   **Dynamic Landing**: If a user comes to `/how-to-cite-book-mla/`, the "Try it now" mini-checker should *effectively* default to MLA. The plan mentions passing `?style=mla9` to the iframe—ensure the iframe consumes this parameter!

### C. SEO & Content
*   **Titles**: Ensure page titles are "How to Cite [Source] in MLA 9" to aggressively target the long-tail keywords. Only "How to Cite [Source]" (ambiguous) usually goes to APA, so explicit "in MLA" is your key differentiator.

## Proposed Action Items

1.  [ ] **Approve** the Core Plan (Files & Structure).
2.  [ ] **Add Task**: Create `backend/pseo/scripts/generate_mla_examples.py`.
3.  [ ] **Refine**: Footer design (Move to Tabs/Columns).
4.  [ ] **Add**: "Copy to Clipboard" feature for examples.

---
## Questions for User
1.  **Footer**: Do you prefer a "Tabbed" approach (cleaner) or "Columns" (more visible links)?
2.  **Examples**: Do you want to auto-generate the MLA examples (recommended) or hand-curate a small set?
