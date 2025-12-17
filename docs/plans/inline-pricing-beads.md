# Inline Pricing A/B Test - Execution Beads

**Context**: Implementing an A/B test to show pricing inline (removing the extra click on "Upgrade" button) to improve conversion from locked → purchase. The plan includes backend data schema updates, log parsing, frontend implementation, and robust testing.

**Global Goals**:
- Eliminate "active click" friction for 50% of users.
- Maintain accurate, truthful analytics (distinguishing "passive view" from "active click").
- ensure zero regressions in checkout usage.

---

## Bead 1: Data Infrastructure & Parsing
**Objective**: Prepare the database and log parser to handle the new `interaction_type` field, allowing us to distinguish between passive views (inline) and active clicks (button).

### Tasks
- [ ] **Create Migration Script**
    - Create `dashboard/migrations/add_interaction_type_column.py`
    - **Specs**:
        - Check if `validations` table exists
        - Check if `interaction_type` column exists
        - Add `interaction_type` column (TEXT) if missing
        - Add simple index on this column for future filtering
        - Follow pattern from `dashboard/migrations/add_user_id_columns.py`
    - **Verification**: Run script locally, check schema with `sqlite3`.

- [ ] **Update Log Parser Logic**
    - Modify `dashboard/log_parser.py`: `extract_upgrade_workflow_event`
    - **Logic**:
        - Update regex/json parsing to look for `interaction_type` in the event payload
        - Ensure it falls back to `None` gracefully if missing (backward compatibility)
        - Pass this field through to the job dictionary in `parse_job_events` or wherever upgrade events are processed
        - Ensure `add_upgrade_state` stores this metadata (may need to update `validations` table insertion logic in `log_parser.py` if it uses a fixed SQL insert - *Check this!*)

- [ ] **Add Tests for Log Parser**
    - **Gap Identified**: `extract_upgrade_workflow_event` is currently untested in `test_log_parser.py`.
    - Create new test file `dashboard/tests/test_upgrade_events.py`
    - **Test Cases**:
        - `test_extract_upgrade_event_basic`: Standard button click
        - `test_extract_upgrade_event_with_metadata`: Inline view with `interaction_type: 'auto'`
        - `test_extract_upgrade_event_malformed`: Invalid JSON
        - `test_integration`: Parse a dummy log file with these lines and verify DB/dict state

**Dependencies**: None
**Artifacts**: `migration script`, `updated log_parser.py`, `test_upgrade_events.py`

---

## Bead 2: Frontend Core & Utilities
**Objective**: Establish the shared infrastructure for managing 4 variants and robust checkout logic, decoupling it from the modal.

### Tasks
- [ ] **Refactor Experiment Utilities**
    - Update `frontend/frontend/src/utils/experimentVariant.js`
    - **Changes**:
        - Update `VALID_VARIANTS` to `['1.1', '1.2', '2.1', '2.2']`
        - Implement `getExperimentVariant()` with migration logic (if old/invalid, re-assign random new)
        - Add helpers: `isInlineVariant(id)`, `getPricingType(id)`
        - Update `forceVariant(id)` validation
    - **Tests**: Update `experimentVariant.test.js` to cover new 4-variant logic and migration cases.

- [ ] **Create Checkout Flow Utility**
    - Create `frontend/frontend/src/utils/checkoutFlow.js`
    - **Logic**:
        - Extract logic from `UpgradeModal.jsx`
        - Args: `{ productId, experimentVariant, jobId, onError }`
        - **Crucial**: Wrap fetch/redirect in `try/catch`. Call `onError(err)` on failure.
    - **Tracking**: ensure `product_selected` event is fired here.

- [ ] **Refactor UpgradeModal**
    - Modify `frontend/frontend/src/components/UpgradeModal.jsx`
    - **Changes**:
        - Remove internal `handleSelectProduct` logic
        - Import `createCheckout` from utils
        - Pass a simple validation/error handler to `onError` (e.g., set local state error)

**Dependencies**: None (can run parallel to Bead 1)
**Artifacts**: `experimentVariant.js`, `checkoutFlow.js`, `UpgradeModal.jsx`

---

## Bead 3: Inline Implementation
**Objective**: Implement the visible UI changes for the inline pricing variants (1.2 and 2.2).

### Tasks
- [ ] **Update PartialResults Component**
    - Modify `frontend/frontend/src/components/PartialResults.jsx`
    - **Logic**:
        - Get variant.
        - If `isInlineVariant` is true:
            - Render banner text (use existing text/icon) *without* the button.
            - Render `PricingTableCredits` or `PricingTablePasses` (based on `getPricingType`) directly below.
            - Wrap in `.inline-pricing-container`
        - If `isInlineVariant` is false:
            - Keep existing behavior (Banner + Button)
    - **Styles**: Add `.inline-pricing-container` to `PartialResults.css` (margin-top, 100% width).

- [ ] **Implement Truthful Analytics**
    - In `PartialResults.jsx`:
    - **Effect**: On mount (if inline):
        - `trackEvent('pricing_viewed', { variant, interaction_type: 'auto' })` -> **The Truth**
        - `trackEvent('clicked', { variant, interaction_type: 'auto', note: 'legacy' })` -> **The Compatibility Hack**

- [ ] **Unit Tests**
    - Update `PartialResults.test.jsx`
    - **Cases**:
        - Renders button for 1.1/2.1
        - Renders inline pricing for 1.2/2.2
        - Fires correct events on mount for inline
        - Does NOT fire active click events automatically for button variant

**Dependencies**: Bead 2 (needs shared variant/checkout utils)
**Artifacts**: `PartialResults.jsx`, `PartialResults.css`, `PartialResults.test.jsx`

---

## Bead 4: E2E Verification & Rollout
**Objective**: Verify the entire flow across all variants and deploy.

### Tasks
- [ ] **Update E2E Tests**
    - Modify `frontend/frontend/tests/e2e/pricing_variants.spec.cjs`
    - **New Tests**:
        - `Variant 1.2 (Credits Inline)`: Force 1.2, submit citations, verify pricing visible immediately, click buy, verify success.
        - `Variant 2.2 (Passes Inline)`: Force 2.2, submit citations, verify pricing visible immediately, click buy, verify success.
    - **Regression**: Ensure 1.1/2.1 still work as button->modal flows.

- [ ] **Manual Verification Plan (Pre-merge)**
    - Run migration script on dev DB.
    - Set `localStorage.setItem('experiment_v1', '1.2')`
    - Submit 6 citations.
    - Verify UI: Banner text present? Pricing table present? No button?
    - Verify Network: `pricing_viewed` event sent?
    - Click Buy -> Verify Polar redirect works.

- [ ] **Deployment Handoff**
    - Merge code.
    - Run migration script on Production (`ssh deploy@...`).
    - Deploy app.
    - Verify live.

**Dependencies**: Bead 1 (DB schema), Bead 3 (UI implementation)
**Artifacts**: `pricing_variants.spec.cjs`
