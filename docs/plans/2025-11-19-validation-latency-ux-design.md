# Validation Latency UX Improvement Design

**Issue:** citations-6sk
**Date:** 2025-11-19
**Status:** Design validated, ready for implementation
**Scope:** Validation table redesign + Site-wide design system improvements

## Problem Statement

GPT-5-mini validation takes 45-60s to complete (vs GPT-4o-mini's 10-20s). Users experience a lengthy delay with no feedback, creating poor UX due to:
- **Uncertainty** - Users don't know if it's working or broken
- **Boredom** - Long wait with nothing to look at feels even longer
- **Perceived slowness** - The wait feels unacceptable despite the accuracy improvement (75.2% vs 57%)

## Solution Overview

Redesign the validation results presentation and loading experience using a table-based layout with progressive text reveal and rotating status messages. This creates the perception of active processing while maintaining design quality.

Additionally, refine the site-wide design system to create a more cohesive, academic, and professional aesthetic that moves away from generic "startup SaaS" patterns toward a refined editorial style.

## Design Details

### 1. Overall UX Flow

**When user clicks "Check My Citations":**

1. **Immediate feedback** (0-500ms)
   - Button changes to disabled state with "Validating..." text
   - Loading state appears below the editor

2. **Progressive text reveal** (0-10s)
   - Show table with headers: # | Citation | Status | Actions
   - Capture HTML from editor (`editor.getHTML()`)
   - Split by `<p>` tags (TipTap wraps each Enter-separated line in a paragraph)
   - Render rows progressively:
     - One row per `<p>` tag (actual newline in user's text)
     - 200-300ms delay between rows
     - Blank lines (`<p></p>` or `<p><br></p>`) create 500-800ms pause but don't create table rows
     - Each row shows: citation number, citation text (with italics via `dangerouslySetInnerHTML`), spinning loader + "Analyzing..."
   - Visual wrapping (CSS) does NOT create new rows - only actual Enter keypresses

3. **Rotating validation messages** (10s-60s)
   - After all rows revealed, Status column cycles through messages every 4-6 seconds:
     - "Checking format..."
     - "Verifying authors..."
     - "Analyzing structure..."
     - "Reviewing punctuation..."
     - "Cross-referencing APA 7..."
     - Loop back to start if still waiting

4. **Results appear** (when API responds)
   - Loading table fades out (300-500ms transition)
   - Results table fades in with actual validation data
   - No jarring layout shift - same table structure

### 2. Table Structure & Layout

#### Desktop Table

```
┌────────────────────────────────────────────────────────────────┐
│  Validation Results                                             │
│  5 citations • 3 perfect • 2 need fixes                        │
├────┬─────────────────────────────────────┬──────────┬─────────┤
│  # │ Citation                            │ Status   │ Actions │
├────┼─────────────────────────────────────┼──────────┼─────────┤
│  1 │ Smith, J. (2023). Research meth...  │ ✓ Perfect│   ⌄     │
├────┼─────────────────────────────────────┼──────────┼─────────┤
│  2 │ Johnson, A. (2024). Title of...     │ ✗ 3 issu │   ⌃     │
│    │   • Author formatting: Missing...   │          │         │
│    │     Should be: Johnson, A., &...    │          │         │
│    │   • Title: Incorrect capital...     │          │         │
│    │     Should be: Title of the...      │          │         │
└────┴─────────────────────────────────────┴──────────┴─────────┘
```

**Column specifications:**
- **#**: Fixed width (40px), citation number
- **Citation**: Flexible width (50-60%), citation text with expand/collapse behavior
- **Status**: Fixed width (120px), icon + status text or error count
- **Actions**: Fixed width (60px), expand/collapse chevron icon

**Summary header:**
- "Validation Results" heading
- Inline stats: "X citations • Y perfect • Z need fixes"
- Follows data table best practices for summary presentation
- During loading: Shows "Processing..." or spinner until results arrive

#### Row States

**Valid citations (no errors):**
- **Collapsed by default** - Citation truncated to ~80 characters + "..."
- Light green/success indicator: ✓ icon + "Perfect"
- Click anywhere on row OR chevron to expand
- Expanded shows: Full citation text + "Source type: [type]" in muted text below

**Invalid citations (has errors):**
- **Expanded by default** - Full citation + error details visible immediately
- Red/amber indicator: ✗ icon + "[N] issues"
- Click chevron to collapse (still shows full citation, hides error details)
- Error details displayed below citation with clear visual hierarchy:
  - Indented content
  - Light red/amber background tint
  - Slightly smaller font
  - Format: `• [Component]: [Problem]` on first line, `Should be: [Correction]` indented below
  - Matches current error data structure from backend

#### Mobile Layout

**Responsive behavior:**
- Desktop: Full table layout as described above
- Mobile (<768px): Stack into card-based layout
  - Each citation becomes a card
  - Card contains: #, Status badge, Citation text, Errors (if any)
  - Maintains expand/collapse behavior
  - Summary view: List of cards with "Citation #1 [✓ Perfect]", "Citation #2 [✗ 3 issues]"
  - Tap card to expand and see full citation + errors
  - Errors still expanded by default for invalid citations

### 3. Icon Design

**Status icons:**
- ✓ Perfect → Circle with checkmark (success green, subtle/clean style)
- ✗ Errors → Circle with X or alert icon (error red/amber)
- Use icon library (lucide-react or heroicons) for consistency
- More sophisticated than emoji - professional, polished appearance

**Expand/collapse:**
- Chevron down (⌄) when collapsed
- Chevron up (⌃) when expanded
- Or use plus/minus in circles
- Consistent with icon library choice

**Loading:**
- Spinning loader icon during progressive reveal and rotation phases

### 4. Visual Design & Styling

#### Table-Specific Styling

**Compactness & Row Separation:**

To address white-on-white issue and improve scannability:

```css
/* Reduced padding for compactness */
.validation-table tbody td {
    padding: 0.75rem 1rem;  /* Reduced from 1rem */
}

/* Alternating row backgrounds for visual rhythm */
.validation-table tbody tr {
    border-bottom: 1px solid #f3f4f6;
    transition: background-color 0.15s ease;
}

.validation-table tbody tr:nth-child(even) {
    background: #fafbfc;  /* Subtle alternation */
}

.validation-table tbody tr:hover {
    background: #f3f4f6;  /* Slightly darker on hover */
}

/* Expanded rows - stronger visual treatment */
.validation-table tbody tr.expanded {
    background: #fffbeb;  /* Amber tint for error rows */
    border-left: 3px solid #fcd34d;  /* Editorial accent */
}
```

**Typography:**
- **Headers**: Work Sans, 0.8125rem, 600 weight, uppercase, 0.05em letter-spacing
- **Citation numbers**: JetBrains Mono, 0.875rem, medium weight
- **Citation text**: JetBrains Mono, 0.875rem, 1.6 line-height
- **Status text**: Work Sans, 0.875rem, 500 weight
- **Error details**: Work Sans, 0.8125rem for labels, JetBrains Mono for corrections

**Color Palette (Table):**
```css
/* Success (sage green) */
--color-success: #047857;
--color-success-bg: #ecfdf5;
--color-success-border: #a7f3d0;

/* Error (warm amber - less aggressive than red) */
--color-error: #b45309;
--color-error-bg: #fffbeb;
--color-error-border: #fcd34d;

/* Processing (indigo) */
--color-processing: #6366f1;
--color-processing-bg: #eef2ff;

/* Backgrounds */
--color-bg-primary: #ffffff;
--color-bg-secondary: #fafbfc;
--color-bg-tertiary: #f3f4f6;

/* Borders */
--border-color: #e5e7eb;
```

**Shadows:**
```css
/* Light, refined shadows - no heavy-handed effects */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
```

**Status Icons:**
```css
.status-icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
}

.status-icon.success {
    background: var(--color-success-bg);
    color: var(--color-success);
    border: 1.5px solid var(--color-success-border);
}

.status-icon.error {
    background: var(--color-error-bg);
    color: var(--color-error);
    border: 1.5px solid var(--color-error-border);
}
```

**Error Details Section:**
```css
.error-details {
    padding: 1rem;
    margin-top: 0.75rem;
    background: var(--color-error-bg);
    border-left: 3px solid var(--color-error);
    border-radius: 4px;
}

.error-component {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--color-error);
}

.error-correction {
    font-family: var(--font-mono);
    font-size: 0.8125rem;
    background: rgba(255, 255, 255, 0.6);
    padding: 0.5rem 1rem;
    border-radius: 4px;
    margin-top: 0.375rem;
}
```

**Animations:**
```css
/* Fade transition between loading and results */
.fade-out {
    animation: fadeOut 0.4s ease-out forwards;
}

.fade-in {
    animation: fadeIn 0.4s ease-in forwards;
}

@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* Progressive reveal */
.loading-row {
    animation: slideIn 0.3s ease-in;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(-4px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Spinner animation */
.status-icon.processing {
    animation: spin 1.5s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
```

#### Site-Wide Design System Improvements

**Purpose:** Create a more cohesive, refined, and academic aesthetic across the entire site.

**1. Global Color System**

Replace current purple-heavy palette with refined, editorial colors:

```css
:root {
    /* Typography */
    --font-body: 'Work Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-heading: 'Work Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'JetBrains Mono', 'Courier New', monospace;

    /* Brand color - use sparingly (CTAs only) */
    --color-brand: #9333ea;
    --color-brand-hover: #7c3aed;
    --color-brand-light: rgba(147, 51, 234, 0.1);

    /* Text hierarchy */
    --color-text-primary: #1a1f36;      /* Deep navy - better readability */
    --color-text-secondary: #4a5568;    /* Medium gray */
    --color-text-tertiary: #718096;     /* Light gray for labels/metadata */

    /* Semantic colors */
    --color-success: #047857;           /* Sage green */
    --color-success-bg: #ecfdf5;
    --color-success-border: #a7f3d0;

    --color-error: #b45309;             /* Warm amber (less aggressive than red) */
    --color-error-bg: #fffbeb;
    --color-error-border: #fcd34d;

    --color-info: #0369a1;              /* Blue for informational */
    --color-info-bg: #e0f2fe;

    /* Backgrounds */
    --color-bg-primary: #ffffff;
    --color-bg-secondary: #fafbfc;      /* Slight tint */
    --color-bg-tertiary: #f3f4f6;       /* Cards/elevated surfaces */

    /* Refined gradient background */
    --gradient-bg: linear-gradient(135deg, #f0f9ff 0%, #faf5ff 50%, #fdf4ff 100%);

    /* Borders & shadows */
    --border-color: #e5e7eb;
    --border-color-light: #f3f4f6;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.03);

    /* Spacing system */
    --space-xs: 0.25rem;
    --space-sm: 0.5rem;
    --space-md: 1rem;
    --space-lg: 1.5rem;
    --space-xl: 2rem;
    --space-2xl: 3rem;
    --space-3xl: 4rem;
}

body {
    background: var(--gradient-bg);
    color: var(--color-text-secondary);  /* Not pure black */
}
```

**Key changes:**
- Purple reserved for CTAs (buttons, links on hover) - not backgrounds
- Navy text instead of pure black - easier on eyes
- Sage green for success, amber for errors - more sophisticated than bright green/red
- Refined gradient with lighter, subtler tones

**2. Typography Refinements**

Create stronger hierarchy with intentional use of weight, size, and spacing:

```css
/* Heading hierarchy */
h1 {
    font-family: var(--font-heading);
    font-size: 2.5rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--color-text-primary);
    line-height: 1.1;
}

h2 {
    font-size: 1.875rem;
    font-weight: 600;
    letter-spacing: -0.015em;
    color: var(--color-text-primary);
    line-height: 1.2;
}

h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-text-primary);
    line-height: 1.3;
}

/* Body text */
body {
    font-size: 1rem;
    line-height: 1.6;
    font-weight: 400;
}

/* Labels and metadata */
.label, .meta-text, .section-label {
    font-size: 0.8125rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-tertiary);
}

/* Citations - always monospace */
.citation-text, .citation-editor {
    font-family: var(--font-mono);
    font-size: 0.875rem;
    line-height: 1.6;
}
```

**Usage rules:**
- Work Sans: UI, headings, body copy
- JetBrains Mono: Citations ONLY (don't overuse)
- Letter-spacing: Tighter for headings (-0.02em), wider for labels (+0.05em)

**3. Button Refinements**

```css
button, .btn {
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: 500;
    font-family: var(--font-heading);
    transition: all 0.2s ease;
    cursor: pointer;
    border: none;
}

/* Primary CTA - purple brand color */
.btn-primary, button[type="submit"] {
    background: var(--color-brand);
    color: white;
}

.btn-primary:hover {
    background: var(--color-brand-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(147, 51, 234, 0.2);
}

/* Secondary buttons - no purple */
.btn-secondary {
    background: var(--color-bg-tertiary);
    color: var(--color-text-primary);
    border: 1px solid var(--border-color);
}

.btn-secondary:hover {
    background: var(--color-bg-secondary);
    border-color: var(--color-text-tertiary);
}

button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
}
```

**4. Card/Surface Styling**

```css
.card, .surface, .section {
    background: var(--color-bg-primary);
    border-radius: 12px;
    padding: var(--space-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-color);
}

/* Elevated cards (slight emphasis) */
.card-elevated {
    box-shadow: var(--shadow-md);
}

/* No heavy shadows - keep it light and refined */
```

**5. Input/Editor Styling**

```css
.citation-editor {
    border: 2px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    background: var(--color-bg-secondary);
    font-family: var(--font-mono);
    line-height: 1.6;
    transition: all 0.2s ease;
}

.citation-editor:focus {
    border-color: var(--color-brand);
    background: white;
    outline: none;
    box-shadow: 0 0 0 3px var(--color-brand-light);
}
```

**6. Hero Section Refinements**

```css
.hero {
    padding: var(--space-3xl) var(--space-xl);
}

.hero-title {
    font-size: 3rem;
    font-weight: 700;
    letter-spacing: -0.025em;
    color: var(--color-text-primary);
    margin-bottom: var(--space-md);
}

.hero-subtitle {
    font-size: 1.25rem;
    color: var(--color-text-secondary);
    font-weight: 400;
    line-height: 1.5;
}

/* Feature pills */
.feature-pill {
    background: var(--color-bg-primary);
    border: 1px solid var(--border-color);
    padding: var(--space-sm) var(--space-md);
    border-radius: 999px;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
}
```

**7. Header Refinements**

```css
.header {
    background: white;
    box-shadow: var(--shadow-sm);  /* Reduced from current */
    border-bottom: 1px solid var(--border-color-light);
}

.logo-icon {
    color: var(--color-brand);  /* Keep purple for brand identity */
}

.logo-text {
    color: var(--color-text-primary);
}
```

**8. Link Styling**

```css
a {
    font-weight: 500;
    color: var(--color-text-secondary);
    text-decoration: none;
    transition: color 0.2s ease;
}

a:hover {
    color: var(--color-brand);  /* Purple on hover only */
}

/* In-text links */
p a {
    color: var(--color-brand);
    text-decoration: underline;
    text-decoration-color: var(--color-brand-light);
}

p a:hover {
    text-decoration-color: var(--color-brand);
}
```

**9. Error Message Styling**

```css
.error {
    background: var(--color-error-bg);
    border: 1px solid var(--color-error-border);
    border-left: 3px solid var(--color-error);
    border-radius: 8px;
    padding: var(--space-lg);
    color: var(--color-error);
}
```

**10. Spacing Consistency**

Apply spacing system consistently:

```css
/* Sections */
.section {
    padding: var(--space-xl);
    margin-bottom: var(--space-xl);
}

/* Cards */
.card {
    padding: var(--space-lg);
    margin-bottom: var(--space-md);
}

/* Form elements */
.form-group {
    margin-bottom: var(--space-lg);
}

/* Inline spacing */
.inline-gap-sm { gap: var(--space-sm); }
.inline-gap-md { gap: var(--space-md); }
```

#### Design Philosophy Summary

**Academic Command Center aesthetic:**
- Refined, editorial feel (scholarly publication meets modern design)
- Sophisticated color palette (sage green, amber, navy)
- Strong typography hierarchy
- Generous whitespace and intentional spacing
- Purple brand color used sparingly for CTAs only
- Light shadows, clean borders
- Monospace font reserved for citations (creates technical/academic contrast)

**Key differentiators from generic SaaS:**
- Not purple-everywhere
- Amber for errors instead of bright red (less alarming, more editorial)
- Navy text instead of pure black (easier reading)
- Editorial-style left borders for emphasis
- Refined status indicators (circles with subtle borders)
- More sophisticated, less "startup-y"

### 5. Loading State Implementation

**Component: ValidationLoadingState.jsx**

Responsibilities:
- Receive submitted HTML from editor
- Split by `<p>` tags to get lines
- Progressive reveal logic:
  1. Render table skeleton with headers
  2. Loop through lines:
     - If line is blank (`<p></p>` or `<p><br></p>`): Wait 500-800ms, don't create row
     - If line has content: Create row with citation number, render HTML with `dangerouslySetInnerHTML`, show spinner + "Analyzing..."
     - Wait 200-300ms before next line
  3. After all lines revealed, start rotating status messages in Status column
- Status message rotation:
  - Array of messages: ["Checking format...", "Verifying authors...", "Analyzing structure...", "Reviewing punctuation...", "Cross-referencing APA 7..."]
  - Cycle every 4-6 seconds
  - Loop indefinitely until results arrive

**Technical considerations:**
- Use `setTimeout` or `setInterval` for timing
- Clean up timers on component unmount
- Preserve italics via `dangerouslySetInnerHTML`

### 5. Results State Implementation

**Component: ValidationTable.jsx**

Responsibilities:
- Receive validation results from API
- Render table with summary header
- Map results to table rows
- Handle expand/collapse state per row
- Apply truncation rules (valid citations only)

**Row-level state:**
- Track `expandedRows` as Set or object: `{ [citationNumber]: boolean }`
- Invalid citations: Initialize as expanded (`errors.length > 0 ? true : false`)
- Valid citations: Initialize as collapsed
- Toggle on row click or chevron click

**Component: ValidationTableRow.jsx**

Responsibilities:
- Render individual table row
- Props: `citationNumber`, `citation`, `sourceType`, `errors`, `isExpanded`, `onToggle`
- Handle truncation display vs full display based on `isExpanded` and error count
- Render error details in indented, styled section when expanded and errors exist

**Component: ValidationMobileSummary.jsx**

Responsibilities:
- Responsive alternative to table for mobile
- Render card-based layout
- Summary list → expandable detail view
- Same data as table, different presentation

### 6. State Transitions

**Loading → Results (success):**
1. API response received
2. Loading table fades out (300-500ms CSS transition: `opacity 1 → 0`)
3. Results table fades in (300-500ms CSS transition: `opacity 0 → 1`)
4. Clean component swap, no layout shift

**Loading → Error:**
1. API call fails (catch block)
2. Loading table fades out (same transition)
3. Error message appears (existing error display from App.jsx lines 339-343)
4. No table visible in error state

**Empty results (0 citations parsed):**
- Handled by error flow above
- Show user-friendly message: "Unable to parse citations. Please check formatting and try again."

### 7. PartialResults Integration

**When user has insufficient credits:**
- Use table format for shown results
- Render ValidationTable with available results
- Below table: Upgrade CTA banner/card
  - "5 more citations available - upgrade to see results"
  - Button: "Upgrade" → triggers upgrade modal
- Locked citations NOT shown in table (clean separation)

### 8. Component Structure

**New components:**
1. `ValidationLoadingState.jsx` - Progressive reveal + rotating messages
2. `ValidationTable.jsx` - Results table (desktop)
3. `ValidationTableRow.jsx` - Individual row with expand/collapse
4. `ValidationMobileSummary.jsx` - Mobile card layout

**Modified components:**
1. `App.jsx` - Replace results section (lines 345-426)
   - Add state: `submittedText` (capture HTML at submission)
   - Render `ValidationLoadingState` when `loading === true`, pass `submittedText`
   - Render `ValidationTable` (desktop) or `ValidationMobileSummary` (mobile) when `results` available
   - Keep existing error handling (lines 339-343)

2. `PartialResults.jsx` - Use ValidationTable, add upgrade CTA below

**Unchanged components:**
- `MiniChecker.jsx` - Out of scope, track as separate future task

### 9. State Management

**App.jsx state:**
- Existing: `loading`, `results`, `error`
- New: `submittedText` - Capture `editor.getHTML()` on form submission, pass to loading state

**ValidationTable state:**
- `expandedRows` - Track which rows are expanded (Set or object)
- Initialize based on error count per citation

**No global state changes needed** - Keep React component state

## Implementation Notes

### Text Handling
- **Capture HTML** from editor to preserve italics formatting
- **Split by `<p>` tags** - TipTap wraps each Enter-separated line in `<p>`
- **Visual wrapping** (CSS) does NOT create new `<p>` tags
- **Render with `dangerouslySetInnerHTML`** in both loading and results states
- **Blank lines** create pauses during reveal, not table rows

### Timing Values
- Line reveal delay: 200-300ms (use 250ms as default)
- Blank line pause: 500-800ms (use 650ms as default)
- Status message rotation: 4-6 seconds (use 5s as default)
- Fade transition: 300-500ms (use 400ms as default)

### Responsive Breakpoint
- Desktop table: > 768px
- Mobile cards: ≤ 768px

### Accessibility
- Table should have proper ARIA labels
- Expand/collapse should be keyboard accessible (Space/Enter)
- Loading state should have `aria-live="polite"` for status updates
- Focus management when expanding/collapsing rows

## Future Work

**Separate task: MiniChecker UX improvement**
- Apply same progressive loading + table design to MiniChecker component
- Apply refined design system (colors, typography, spacing)
- Consider credit integration for MiniChecker (currently unlimited/free)
- Maintain "Quick Check" positioning as PSEO page teaser
- **Note:** This should be tracked as a separate issue/task after main validation table redesign is complete

## Success Criteria

- Users see immediate feedback (loading state within 500ms)
- Progressive reveal creates perception of active processing
- Table layout is more scannable than current card layout
- Invalid citations immediately visible (expanded by default)
- Smooth transitions between states (no jarring shifts)
- Mobile experience maintains usability
- 45-60s wait feels less painful due to visual activity

## Technical Risks

**Low risk:**
- Splitting by `<p>` tags - straightforward DOM parsing
- Progressive reveal timing - standard setTimeout/setInterval patterns
- Table layout - well-established patterns

**Medium risk:**
- Line count mismatch - User's submitted lines may not match GPT-5-mini's parsed citation count
  - Mitigation: Loading shows submitted lines, results show parsed citations. Clear visual transition between states prevents confusion.

**Testing focus:**
- Various citation formats (single line, multi-line, mixed)
- Edge cases: Very long citations (>500 chars), many citations (20+), single citation
- Mobile responsive behavior
- Error states and transitions
- Timer cleanup (no memory leaks)
