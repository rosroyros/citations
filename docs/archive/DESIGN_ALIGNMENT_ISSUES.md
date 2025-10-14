# Design Alignment Issues - Task 5.2

## Status: CRITICAL MISMATCH

The production layout template (`backend/pseo/builder/templates/layout.html`) does NOT match the approved mockup design (`design/mocks/source_type_mockup.html`).

## Critical Issues

### 1. Layout Structure ⚠️ CRITICAL
**Problem:** Implementation uses 2-column grid with sidebar, mockup is single-column.

**Mockup:**
```css
.content-wrapper {
    max-width: 900px;  /* Single column, no sidebar */
    margin: 0 auto;
    padding: 2rem;
}
```

**Current Implementation:**
```css
.content-wrapper {
    max-width: 1200px;
    display: grid;
    grid-template-columns: 1fr 300px;  /* Two columns with sidebar */
    gap: 3rem;
}
```

**Fix:** Decide on layout strategy:
- **Option A:** Make sidebar optional (hide when no related_resources)
- **Option B:** Change to single-column like mockup
- **Option C:** Create separate templates for different page types

### 2. Related Resources Placement ⚠️ CRITICAL
**Problem:** Mockup shows grid at bottom, implementation has sidebar list.

**Mockup:**
```html
<div class="related-box">
    <h3>Related Source Types</h3>
    <div class="related-grid">
        <a href="#" class="related-link">📖 How to Cite Books</a>
        <!-- Grid of 6 items in 2-3 columns -->
    </div>
</div>
```

**Implementation:**
```html
<aside class="content-sidebar">
    <div class="related-resources">
        <h3>Related Guides</h3>
        <ul>
            <li><a href="#">Link</a></li>
        </ul>
    </div>
</aside>
```

**Fix:** Add `.related-box` and `.related-grid` to template, move to bottom of content.

### 3. Footer Styling ⚠️ MEDIUM
**Problem:** Colors don't match.

**Mockup:** Dark footer (`background: #1f2937`, white text)
**Implementation:** Light footer (`background: white`, gray text)

**Fix:** Update `styles.css` lines 364-375 to match mockup:
```css
.site-footer {
    background: #1f2937;
    color: white;
    padding: 3rem 2rem;
    margin-top: 4rem;
}

.site-footer p {
    color: #9ca3af;
    font-size: 0.875rem;
}
```

### 4. MiniChecker Design ⚠️ LOW (Blocked by Task 6.1)
**Problem:** Implementation shows placeholder, mockup shows full component design.

**Note:** This is expected until Task 6.1/6.2 are complete. The mockup shows the TARGET design.

**Mockup styling needed:**
- Visible textarea with placeholder
- Full-width purple button with shadow
- More prominent visual design

### 5. Content Elements Missing ⚠️ MEDIUM
**Problem:** Mockup has rich content styling that implementation CSS has but templates may not generate.

**Missing styled elements:**
- `.element-list` grid for required/optional elements
- `.step-box` with numbered circles (CSS counter)
- `.error-example` / `.correction-box` (red/green backgrounds)
- `.note-box` (yellow/amber styling)
- `.checklist` with custom checkmarks

**Status:** These styles exist in both `styles.css` and mockup. May need template updates to use correct CSS classes.

## Recommended Action Plan

### Phase 1: Immediate Fixes
1. ✅ Fix domain hardcoding (Task 5.1)
2. ✅ Fix footer colors (Task 5.2)
3. ✅ Update tests to match external CSS approach

### Phase 2: Layout Decision (BEFORE generating 45 pages)
**DECISION REQUIRED:** Which layout to use?

**Option A: Keep sidebar (current)**
- Pro: More navigation options, compact
- Con: Doesn't match approved mockup
- Con: Narrower content area

**Option B: Single-column (mockup)**
- Pro: Matches approved design
- Pro: Wider content area, better for examples
- Con: Need to relocate sidebar content
- Con: Requires template refactor

**Option C: Hybrid**
- Pro: Different layouts for different page types
- Con: More complexity

**BLOCKER:** This decision affects content generation. Must resolve before Task 7.1/7.2.

### Phase 3: After Layout Decision
1. Move related resources to bottom grid (if Option B)
2. Add rich content element classes to templates
3. Verify all mockup styles are used
4. Re-test with real content

## Test Suite Issues
Already documented - tests expect inline CSS but implementation uses external CSS. Fix separately.
