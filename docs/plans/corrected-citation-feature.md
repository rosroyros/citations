# Corrected Citation Feature - Implementation Plan

Add a copyable "corrected citation" to validation results for citations with errors.

---

## Overview

When a citation has formatting errors, the LLM will generate a complete corrected version. Users can copy this with one click (preserving formatting like italics) and paste directly into their document.

**Key Design Decisions:**
- Corrected citation shown prominently above error details in expanded rows
- Both copy button click AND citation text click trigger copy + analytics
- Rich text copy (HTML) with plain text fallback for mobile/older browsers
- Dashboard tracks corrections copied per job

---

## Phase 1: Backend (Prompt + Parsing)

### [MODIFY] validator_prompt_optimized.txt

Add `CORRECTED:` section to OUTPUT FORMAT. Place it after error list, with explicit instruction to OMIT when no errors:

```diff
 ❌ [Component]: [What's wrong]
    Should be: [Correct format using markdown: _text_ for italics, **text** for bold]
+
+CORRECTED: [Complete corrected citation with all fixes applied]
+
+[IMPORTANT: Only include CORRECTED line when there are errors. Omit entirely for perfect citations.]
```

> **Token Impact**: Adds ~30-50 tokens per citation with errors. With 10000 max output tokens, no issue for typical batch sizes.

### [MODIFY] gemini_provider.py

Update `_parse_citation_block()`:
- Parse `CORRECTED:` line after validation results  
- Store as `corrected_citation` field
- Apply same markdown→HTML conversion as corrections
- **Defensive check**: Discard `corrected_citation` if errors list is empty (belt + suspenders)

### [MODIFY] openai_provider.py

Same parsing changes for fallback consistency.

### [MODIFY] app.py

Add to `CitationResult` Pydantic model:
```python
corrected_citation: str = None
```

---

## Phase 2: Frontend (ValidationTable)

### [MODIFY] ValidationTable.jsx

1. Add `jobId` prop for analytics
2. Add corrected citation card inside expanded error rows:
   - Render above `error-details` when `corrected_citation` exists
   - Copy button (ghost style) + click handler on citation text
3. **Rich text copy** using ClipboardItem API:
   ```javascript
   try {
     await navigator.clipboard.write([
       new ClipboardItem({
         'text/html': new Blob([html], { type: 'text/html' }),
         'text/plain': new Blob([plainText], { type: 'text/plain' })
       })
     ])
   } catch {
     // Fallback to plain text (mobile, older browsers)
     await navigator.clipboard.writeText(plainText)
   }
   ```
4. **Visual feedback**: Checkmark icon + "Copied" text for 2 seconds
5. Track `correction_copied` event on copy

### [MODIFY] ValidationTable.css

Add `.corrected-citation-card` styles:
- Background: `var(--color-success-bg)` (#ecfdf5)
- Border: `1px solid var(--color-success-border)` (#a7f3d0)
- Left accent: `3px solid var(--color-success)` (#047857)

---

## Phase 3: Integration Points

### [MODIFY] App.jsx

Pass `jobId` prop to ValidationTable:
```jsx
<ValidationTable results={results.results} jobId={results.job_id} />
```

### [MODIFY] PartialResults.jsx

Pass `jobId` prop to ValidationTable:
```jsx
<ValidationTable results={results} jobId={job_id} />
```

> **Sales driver**: Partial results show the "Corrected Citation" feature for visible rows - "Show, Don't Tell" value demo.

---

## Phase 4: Analytics + Dashboard

### [MODIFY] analytics.js

Track correction usage:
```javascript
trackEvent('correction_copied', {
  job_id,
  citation_number,
  source_type
})
```

### [MODIFY] dashboard/static/index.html

Add `📋` column showing `corrections_copied` count per job.

### [MODIFY] dashboard/log_parser.py

Parse `correction_copied` events for dashboard aggregation.

---

## Verification Plan

### Backend Tests
`cd backend && python -m pytest tests/test_gemini_provider.py -v`
- Add `CORRECTED:` to test fixtures
- Test extraction works correctly
- Test defensive check: correction discarded when errors empty

### Frontend Tests
`cd frontend/frontend && npm test`
- Test copy functionality (mock clipboard API)
- Test fallback to plain text
- Test visual feedback state
- Test null handling when no correction

### E2E Tests
`cd frontend/frontend && npx playwright test validation`
- Verify corrected citation appears for citations with errors
- Verify copy and copied state

### Manual Verification
1. **Rich text copy**: Paste into Word/Google Docs, verify italics preserved
2. **Mobile test**: Try on iOS Safari - should fallback to plain text
3. **Dashboard**: Submit job, copy correction, verify count
4. **Prompt quality**: Test 5-10 diverse citations

---

## Out of Scope

- **MiniChecker**: PSEO widget unchanged. Corrected citations exclusive to main app (value hook).
- **"Copy All" button**: Individual copy is better UX - each correction replaces one specific citation.
- **Valid/Invalid dashboard column**: Defer to separate task (unrelated to this feature).
