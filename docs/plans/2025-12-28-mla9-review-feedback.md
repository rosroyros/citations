# MLA 9 Design Review & Suggestions

**Date**: 2025-12-28
**Reviewed Document**: `docs/plans/2025-12-28-mla9-support-design.md`

## Executive Summary
The proposed design is robust, effectively leveraging the existing architecture (LLM providers, parsers) while introducing necessary abstractions (styles module, feature flags). However, to maximize reliability, user ergonomics, and traffic growth, the following enhancements are recommended.

---

## 1. Reliability & Architecture

### Recommendation 1.1: Structured "Valid" Flag in LLM Response
**Change**: Instead of relying on exact string matching for success messages ("No MLA 9 formatted errors..."), require the LLM to output a structured JSON boolean field (e.g., `"is_valid": true`) or a specific status code.
**Rationale**:
- **Fragility Reduction**: String matching is brittle. If the LLM output shifts slightly (e.g., adds a period, changes capitalization, or "hallucinates" a slightly different confirmation phrase), validation fails.
- **Simpler Parsing**: Checking a boolean is O(1) and unambiguous compared to regex/string searching.
- **Future-Proofing**: Allows for "Warnings" vs "Errors" distinction later (e.g., `status: "valid_with_warnings"`).

### Recommendation 1.2: Unified Error Code System
**Change**: Define a static list of error codes (e.g., `MLA_ERR_001` for "Missing Date") in `mla9-rules.md` and instruct the LLM to return these codes alongside the human-readable message.
**Rationale**:
- **Localization/Copy Editing**: Allows frontend to update wording without re-prompting/re-deploying the backend.
- **Analytics**: "Error Code 001" is easier to aggregate and track than free-text error descriptions, flagging which rules users struggle with most (content opportunity).

---

## 2. User Experience (UX) & Ergonomics

### Recommendation 2.1: Account-Level Preference Sync
**Change**: In addition to `localStorage`, persist the `preferred_style` in the Postgres `users` table for logged-in users.
**Rationale**:
- **Cross-Device Continuity**: Students often switch between library computers, laptops, and phones. Losing their preference (defaulting back to APA) causes friction and potential errors.
- **Sticky Experience**: "It just remembers me" is a subtle but powerful retention driver.

### Recommendation 2.2: "Smart" Style Heuristics (Stretch Goal)
**Change**: Implement a lightweight client-side regex check on paste. If a user pastes a citation that looks strongly like MLA (e.g., dates at the end, no parentheses around dates) but has "APA" selected, show a toast: *"Looks like you pasted an MLA citation. Switch to MLA mode?"*
**Rationale**:
- **Error Prevention**: Prevents the frustration of receiving 50 red error flags because the wrong parser was active.
- **Delight Factor**: Anticipating user intent feels "smart" and premium.

### Recommendation 2.3: Mobile-First Style Selector
**Change**: Instead of a standard `<select>`, use a custom UI component that renders as a bottom-sheet drawer on mobile.
**Rationale**:
- **Ergonomics**: Standard dropdowns on mobile can be finicky or unstyled (iOS default). A bottom sheet is thumb-friendly and allows for richer content (e.g., "MLA 9th Edition (Latest)" vs just "MLA 9").

---

## 3. Growth & Traffic (SEO)

### Recommendation 3.1: Front-Run PSEO Routes
**Change**: Do not defer the *creation* of PSEO routes. Implement the URLs `cite-website-mla`, `cite-book-mla` immediately, even if they render the same React app with `?style=mla9` pre-selected.
**Rationale**:
- **Indexing Latency**: SEO takes weeks/months. By publishing the URLs now (with proper `<title>` and `<h1>` tags dynamically updated based on the URL/style), you start building domain age for these keywords immediately.
- **Zero Eng Effort**: It's effectively free if using a router; just map the route to the existing component with a prop.

### Recommendation 3.2: "Visual" Citation Examples on Landing Page
**Change**: Add a "Live Preview" of MLA vs APA on the homepage/landing page.
**Rationale**:
- **Conversion**: Users searching for "MLA checker" want to verify visually that the tool knows the difference. A side-by-side or togglable example (before they even paste) builds instant trust.

---

## 4. Testing & QA

### Recommendation 4.1: A/B Testing Slot in Architecture
**Change**: Structure `backend/styles.py` to support variants, e.g., `mla9-b` mapping to `validator_prompt_mla9_v2_experimental.txt`.
**Rationale**:
- **Optimization Velocity**: You *will* want to test new prompts. Baking the ability to route traffic to a shadow prompt or A/B variant into the architecture now prevents "spaghetti code" routing later.

### Recommendation 4.2: "Regression" Golden Set
**Change**: Explicitly include "Ambiguous" citations in the test set (citations that look like APA but are valid MLA, or vice versa) to ensure the model doesn't drift into validating the *wrong* style just because it looks valid in another.
**Rationale**:
- **Model Confusion**: LLMs can be "too helpful" and validate an APA citation as "Correct" even in MLA mode if the prompt isn't strict. Specific negative tests ("This is perfect APA, therefore it is terrible MLA") are crucial.
