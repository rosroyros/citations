# MLA 9th Edition Citation Support - Design Document

**Date**: 2025-12-28  
**Version**: 6.0 (Complete)  
**Goal**: Add MLA 9th edition to expand traffic by capturing humanities/literature students.

---

## Phase 1: Research & Prompt Development

### 1.1 Research MLA 9 Rules
- Research MLA 9 "containers" model from Purdue OWL and authoritative sources
- Create `docs/mla9-research.md`
- Create `docs/mla9-rules.md` (source of truth)
- **Signoff**: Review rules

### 1.2 Golden Test Set
- Collect ~60 verified MLA 9 citations (valid/invalid/ambiguous)
- Create `mla9_test_set.jsonl`
- **Signoff**: Review sample

### 1.3 Draft Prompt
- Clone APA prompt structure
- Replace with MLA 9 rules
- Keep text output format (no JSON)
- Create `validator_prompt_mla9.txt`
- **Signoff**: Review prompt

### 1.4 Measure & Optimize
- Run `test_mla9_prompt_batched.py`
- Target: ≥80% accuracy
- Iterate until passing

---

## Phase 2: Backend Integration

### 2.1 Styles Module
Create `backend/styles.py`:
```python
SUPPORTED_STYLES = {
    "apa7": {"prompt": "validator_prompt_v3_no_hallucination.txt", "label": "APA 7th Edition"},
    "mla9": {"prompt": "validator_prompt_mla9.txt", "label": "MLA 9th Edition"}
}
```

### 2.2 Update Components
- Update `PromptManager` to load from styles module
- Update parser to check style-specific success messages
- Add `MLA_ENABLED` feature flag
- Create `/api/styles` endpoint

---

## Phase 3: Frontend & UX

### 3.1 Style Selector (Tabs UI)
- Create tab/toggle component (visible, not dropdown)
- Persist to `localStorage`
- Support `?style=mla9` URL parameter

### 3.2 Complete Text Audit & Updates

**Dynamic Updates (based on selected style)**:
| Element | APA 7 | MLA 9 |
|---------|-------|-------|
| Browser Title | "APA Citation Checker" | "MLA Citation Checker" |
| H1 | "Free APA Citation Checker" | "Free MLA Citation Checker" |
| Subheading/Description | Check for "APA" mentions | Update to "MLA" |
| Editor Placeholder | "(APA 7th edition)" | "(MLA 9th edition)" |
| Loading messages | "Validating against APA 7 rules..." | "Validating against MLA 9 rules..." |

**Static Updates (mention both styles)**:
| Element | Current | Updated |
|---------|---------|---------|
| Homepage FAQ | "We support APA 7th edition" | "We support APA 7th and MLA 9th edition" |
| Any "APA-only" copy | Audit and revise | Make style-agnostic or mention both |

### 3.3 SEO Meta Tags (Dynamic)
Update `<Helmet>` or equivalent:
```jsx
<meta name="description" content={`Free ${styleName} citation checker...`} />
<meta property="og:title" content={`${styleName} Citation Checker`} />
<meta property="og:description" content={`Validate ${styleName} citations...`} />
```

### 3.4 Mini-Checker Behavior
**Clarification**: Mini-checker uses the same React app (embedded via iframe on PSEO pages).

**Implementation**:
- When we add `?style=mla9` URL param support to `App.jsx`, mini-checker automatically supports it
- **Zero additional code changes needed**
- PSEO pages can use `<iframe src="/?style=mla9">` for MLA mini-checkers

---

## Phase 4: Analytics & Monitoring

### 4.1 Backend Logging
Already included in existing logging:
- `PROVIDER_SELECTION: job_id=X style=mla9`
- Dashboard extracts and displays style

### 4.2 Client-Side Events (NEW)
Add analytics events:
```javascript
// When user switches style
analytics.track('style_selected', { style: 'mla9', source: 'tab_click' });

// When validation starts
analytics.track('validation_started', { style: 'mla9', citation_count: 5 });
```

Purpose: Understand MLA adoption rate and user behavior

---

## Phase 5: Testing

### 5.1 Backend Tests
- Styles module configuration
- Prompt loading per style
- Parser handles both success messages

### 5.2 Frontend Tests
- Tab switching updates state
- URL param sets initial style
- Dynamic text updates (Title, H1)
- localStorage persistence

### 5.3 E2E Tests
- Select MLA → submit → verify results
- Verify `?style=mla9` works
- Verify mini-checker receives style from URL
- Rollback: `MLA_ENABLED=false` hides tabs

---

## Phase 6: Documentation

- Update `README.md`, `CLAUDE.md`, `GEMINI.md`
- Update homepage FAQ

---

## Summary Checklist

### Text Updates
- [ ] Browser title (dynamic)
- [ ] H1 (dynamic)  
- [ ] Subheading/description (dynamic)
- [ ] Editor placeholder (dynamic)
- [ ] Loading messages (dynamic)
- [ ] Meta tags (dynamic)
- [ ] FAQ (static - mentions both)

### Mini-Checker
- [ ] Confirm: Uses same `App.jsx` component
- [ ] Confirm: URL param support = mini-checker support
- [ ] Test: Mini-checker iframe with `?style=mla9`

### Analytics
- [ ] Backend: style in logs
- [ ] Frontend: style selection event
- [ ] Frontend: validation started event

---

## Signoff Checkpoints

| Phase | Deliverable | Signoff |
|-------|-------------|---------|
| 1 | Rules & Test Set | ✅ |
| 1 | Baseline accuracy | ✅ |
| 2-6 | Implementation | ✅ |
