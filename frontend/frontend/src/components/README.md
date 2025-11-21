# Validation Components

Component documentation for the citation validation UX system.

## Overview

This directory contains components for displaying validation results and loading states during citation validation. These components were designed to handle GPT-5-mini's 45-60 second validation latency with progressive loading and scannable table results.

**Design Documentation:**
- Design spec: `docs/plans/2025-11-19-validation-latency-ux-design.md`
- Implementation plan: `docs/plans/2025-11-19-validation-latency-ux-implementation.md`
- Visual mockup: `docs/plans/validation-table-mockup.html`

## Components

### ValidationTable

Interactive table component for displaying validation results with expand/collapse functionality.

**File:** `ValidationTable.jsx` | `ValidationTable.css`

**Props:**
- `results` (object): Validation results from backend
  - `results.citations` (array): Array of citation validation objects
  - Each citation contains: `citation_number`, `status` (valid/invalid), `errors`, `formatted`, `corrections`

**Features:**
- Expandable/collapsible rows for detailed error information
- Invalid citations expanded by default
- Keyboard navigation (Tab, Enter, Space)
- ARIA labels for accessibility
- Mobile responsive layout
- Smooth expand/collapse animations
- Color-coded status badges (green for valid, red for invalid)

**Usage:**
```jsx
import ValidationTable from './components/ValidationTable'

<ValidationTable results={validationResults} />
```

**Keyboard Navigation:**
- `Tab` - Navigate between rows
- `Enter` or `Space` - Toggle row expand/collapse
- `Escape` - Collapse all rows

**Mobile Behavior:**
- Tables convert to card layout on small screens
- Each citation displays as a single card
- All information stacks vertically for readability

### ValidationLoadingState

Progressive loading component with text reveal and rotating status messages.

**File:** `ValidationLoadingState.jsx` | `ValidationLoadingState.css`

**Props:**
- `submittedText` (string): The citation text being validated
- `citationCount` (number): Number of citations being validated

**Features:**
- Progressive text reveal animation (0-10s)
- Rotating status messages during validation (10-60s)
- Smooth fade transitions between states
- Citation count badge
- Mobile responsive

**Status Messages:**
Status messages rotate every 3 seconds during validation:
- "Analyzing citation format..."
- "Checking APA 7th edition compliance..."
- "Verifying reference structure..."
- "Almost done..."

**Usage:**
```jsx
import ValidationLoadingState from './components/ValidationLoadingState'

<ValidationLoadingState
  submittedText={citations}
  citationCount={5}
/>
```

**Animation Timing:**
- 0-10s: Progressive text reveal (one citation at a time)
- 10s+: Rotating status messages
- Smooth fade transitions (600ms)

## Styling

Both components use CSS custom properties from the global design system:

**Colors:**
- `--color-primary` - Primary brand color
- `--color-success` - Valid citation badge
- `--color-error` - Invalid citation badge
- `--color-text-primary` - Main text
- `--color-text-secondary` - Secondary text
- `--color-bg-primary` - White backgrounds
- `--color-border` - Borders and dividers

**Spacing:**
- `--space-xs` through `--space-xl`
- Consistent spacing scale used throughout

**Shadows:**
- `--shadow-sm` - Subtle elevation
- `--shadow-md` - Card shadows

## Accessibility

All components follow WCAG 2.1 AA standards:

- Proper ARIA labels and roles
- Keyboard navigation support
- Focus indicators
- Color contrast ratios meet 4.5:1 minimum
- Screen reader announcements for state changes

## Testing

Component testing guidance:

**ValidationTable:**
- Test expand/collapse functionality
- Verify keyboard navigation
- Check mobile responsive layout
- Test with various citation counts (1, 10, 50+)

**ValidationLoadingState:**
- Test progressive reveal timing
- Verify status message rotation
- Check mobile layout
- Test with different citation counts

**E2E Testing:**
See `frontend/frontend/TESTING.md` for E2E test examples.

## Related Components

- **PartialResults** - Uses ValidationTable for partial credit results
- **Footer** - Site-wide footer component
- **CreditDisplay** - Credit balance display
- **UpgradeModal** - Upgrade prompt modal
