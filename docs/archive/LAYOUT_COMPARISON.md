# Layout Comparison: Mockup vs Implementation

## Side-by-Side Structure

### 📱 Approved Mockup (source_type_mockup.html)

```
┌─────────────────────────────────────────┐
│          Header (white)                  │
│  Logo + "Citation Checker"               │
└─────────────────────────────────────────┘
│        Breadcrumbs                       │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│                                          │
│         SINGLE COLUMN CONTENT            │
│         (max-width: 900px)               │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Hero Section                      │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Quick Reference (purple box)      │ │
│  │  ┌──────────────────────────────┐  │ │
│  │  │ Template (white box inside)  │  │ │
│  │  └──────────────────────────────┘  │ │
│  └────────────────────────────────────┘ │
│                                          │
│  Basic Format Explanation                │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ Required Elements (grid layout)    │ │
│  │ ┌────────┐ ┌────────┐ ┌────────┐  │ │
│  │ │Element │ │Element │ │Element │  │ │
│  │ └────────┘ └────────┘ └────────┘  │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  MiniChecker (full design)         │ │
│  │  [Textarea]                        │ │
│  │  [Check Citation Button]           │ │
│  └────────────────────────────────────┘ │
│                                          │
│  Examples...                             │
│  Step-by-Step (numbered circles)...      │
│  Common Errors (red/green boxes)...      │
│  Validation Checklist...                 │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Related Sources (purple box)      │ │
│  │  ┌───────┐ ┌───────┐ ┌───────┐    │ │
│  │  │ Link  │ │ Link  │ │ Link  │    │ │
│  │  └───────┘ └───────┘ └───────┘    │ │
│  │  ┌───────┐ ┌───────┐ ┌───────┐    │ │
│  │  │ Link  │ │ Link  │ │ Link  │    │ │
│  │  └───────┘ └───────┘ └───────┘    │ │
│  └────────────────────────────────────┘ │
│                                          │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│    Footer (DARK #1f2937, white text)    │
└─────────────────────────────────────────┘
```

---

### 💻 Current Implementation (layout.html)

```
┌─────────────────────────────────────────┐
│          Header (white)                  │
│  Logo + "Citation Checker"               │
└─────────────────────────────────────────┘
│        Breadcrumbs                       │
└─────────────────────────────────────────┘
┌──────────────────────┬──────────────────┐
│                      │                  │
│  MAIN CONTENT        │   SIDEBAR        │
│  (wider, 1fr)        │   (300px)        │
│                      │                  │
│  Hero Section        │ ┌──────────────┐ │
│                      │ │ Related      │ │
│  Quick Reference?    │ │ Guides       │ │
│                      │ │ - Link 1     │ │
│  Basic Format...     │ │ - Link 2     │ │
│                      │ │ - Link 3     │ │
│  Examples...         │ └──────────────┘ │
│                      │                  │
│  ┌─────────────────┐ │ ┌──────────────┐ │
│  │ MiniChecker     │ │ │ Page Info    │ │
│  │ (placeholder)   │ │ │ Word count   │ │
│  │ - No textarea   │ │ │ Reading time │ │
│  │ - No button     │ │ │ Last updated │ │
│  └─────────────────┘ │ └──────────────┘ │
│                      │                  │
│  Common Errors...    │                  │
│  Validation...       │                  │
│                      │                  │
│  (NO RELATED GRID    │                  │
│   AT BOTTOM)         │                  │
│                      │                  │
└──────────────────────┴──────────────────┘
┌─────────────────────────────────────────┐
│    Footer (LIGHT white, gray text)      │
└─────────────────────────────────────────┘
```

---

## Key Structural Differences

### 1. Layout Grid ⚠️ CRITICAL

**Mockup:**
```css
.content-wrapper {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
    /* Single column */
}
```

**Implementation:**
```css
.content-wrapper {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    display: grid;
    grid-template-columns: 1fr 300px;  /* Two columns! */
    gap: 3rem;
}
```

**Impact:**
- Content is narrower in implementation (due to sidebar)
- Related resources moved from bottom to sidebar
- Different visual hierarchy

---

### 2. Related Resources ⚠️ CRITICAL

**Mockup:**
```html
<div class="related-box">
    <h3>Related Source Types</h3>
    <div class="related-grid">
        <a href="#" class="related-link">📖 How to Cite Books</a>
        <a href="#" class="related-link">🌐 How to Cite Websites</a>
        <!-- 6 items in responsive grid -->
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
            <!-- Simple list -->
        </ul>
    </div>
</aside>
```

---

### 3. Footer Styling ⚠️ MEDIUM

**Mockup:**
```css
.footer {
    background: #1f2937;  /* Dark */
    color: white;
    padding: 3rem 2rem;
}

.footer-text {
    color: #9ca3af;
}
```

**Implementation:**
```css
.site-footer {
    background: var(--bg-white);  /* Light */
    border-top: 1px solid var(--border-gray);
    padding: 2rem;
}

.site-footer p {
    color: var(--text-secondary);
}
```

---

### 4. Visual Elements

**Mockup Has (styled in CSS):**
- ✅ `.element-list` with grid layout
- ✅ `.element-item` with colored borders (purple/gray)
- ✅ `.step-box` with CSS counter circles
- ✅ `.error-example` (red background)
- ✅ `.correction-box` (green background)
- ✅ `.note-box` (yellow/amber)
- ✅ `.checklist` with checkmark bullets
- ✅ `.citation-example` (monospace, bordered)

**Implementation:**
- ⚠️ CSS exists but markdown templates may not use these classes
- ⚠️ Depends on content generation to apply correct classes

---

## CSS Comparison

### Mockup CSS Features
- Inline styles in mockup HTML (lines 7-459)
- Rich visual elements
- Numbered step circles (CSS counter)
- Color-coded boxes
- Dark footer
- Centered 900px layout

### Implementation CSS Features
- External stylesheet (`styles.css`)
- Same purple branding (#9333ea) ✅
- Same gradient background ✅
- Different layout structure (grid with sidebar)
- Light footer
- Wider 1200px with sidebar

---

## Which Design is Correct?

### Evidence for Mockup Being Correct:
1. Task 2.4 shows mockup **APPROVED** ✅
2. Plan says: "Once approved, move to static site builder"
3. Mockup labeled as "approved Week 4 mockups"

### Why Implementation Differs:
- May have been created before mockup approval
- Or intentional decision not documented
- Or misinterpretation of mockup structure

---

## Recommended Fix

### Option A: Match Mockup (Recommended)
Remove sidebar, switch to single-column centered layout:

```css
/* Update styles.css */
.content-wrapper {
    max-width: 900px;  /* Match mockup */
    margin: 0 auto;
    padding: 2rem;
    /* Remove: display: grid; */
    /* Remove: grid-template-columns: 1fr 300px; */
}

/* Hide sidebar */
.content-sidebar {
    display: none;
}

/* Add related grid at bottom */
.related-box {
    background: #f3e8ff;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-top: 3rem;
}

.related-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem;
}

.related-link {
    background: white;
    padding: 0.75rem;
    border-radius: 0.5rem;
    /* ... rest of styling */
}

/* Update footer */
.site-footer {
    background: #1f2937;
    color: white;
    padding: 3rem 2rem;
}
```

### Option B: Get Explicit Approval
If current two-column design is preferred:
1. Update mockup to match implementation
2. Get formal approval
3. Document decision

---

## Impact on Page Generation

⚠️ **CRITICAL:** This must be decided **BEFORE** generating 45 pages (Tasks 7.1/7.2)

**If we generate with current layout then need to change:**
- Must regenerate all 45 pages
- Waste of LLM API costs
- Delay in timeline

**Better:** Fix layout now, then generate once correctly.

---

## Visual Quality Comparison

### Mockup Advantages:
- ✅ Wider content area for examples
- ✅ Better visual hierarchy
- ✅ More engaging visual elements
- ✅ Related resources more prominent
- ✅ Consistent dark footer

### Implementation Advantages:
- ✅ Sidebar useful for navigation
- ✅ Compact page info visible
- ✅ Less vertical scrolling

### User Experience:
- **Mockup:** Better for reading long content, examples stand out
- **Implementation:** Better for quick navigation, more compact

---

## Decision Time

**Question for Roy:** Which layout do you prefer?

1. **Mockup (Single-column, 900px, no sidebar)**
   - Matches approved design
   - Better for content readability
   - Requires template updates

2. **Current (Two-column, sidebar)**
   - Already implemented
   - More navigation options
   - Doesn't match mockup

**Recommendation:** Go with **Option 1** (mockup) since it was formally approved in Task 2.4.
