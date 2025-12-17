# Upgrade Flow Tracking: Implementation Plan

> **Epic:** [citations-jk86](bd://citations-jk86)  
> **Priority:** Critical - Affects business analytics  
> **Status:** Planning (Approved pending final review)

---

## Executive Summary

This plan ensures robust, fully-tested tracking of the upgrade funnel (locked → clicked → modal → success). It addresses a critical bug (duplicate log parsers) and establishes comprehensive test coverage across 6 layers.

**Key Architectural Decision:** 
Production flow remains decoupled from monitoring. The API writes to logs; a separate process parses them. For E2E tests, we introduce a **Test-Mode Trigger** to force immediate log parsing, ensuring tests don't fail due to async latency.

---

## Part 1: Critical Bug - Duplicate Log Parsers

### What Happened

In commit `e88a3e2` (Dec 8, 2025), a "restore" action accidentally created a **copy** of `log_parser.py` in `backend/dashboard/` instead of restoring the original in `dashboard/`.

**Result:** Two divergent files. `dashboard/log_parser.py` (used by cron) has Gemini support. `backend/dashboard/log_parser.py` (used by API) has `purchase_completed` mapping.

### Fix (Phase 0)

**Goal:** Single source of truth.

1.  **Merge features** into `/dashboard/log_parser.py`:
    *   Keep: Gemini support, flexible regex, test job detection
    *   Add: `purchase_completed → success` mapping (from backend version)
2.  **Delete** `/backend/dashboard/log_parser.py`
3.  **Update import** in `backend/app.py` to point to the correct file.

---

## Part 2: Architecture & Data Flow

### Production Flow (Unchanged)
```
User Action → API → log_upgrade_event() → app.log
                                            ↓
                                (continue processing)
```
*   **Zero Latency Impact:** API doesn't wait for DB writes.
*   **Resilience:** If monitoring DB fails, user experience is unaffected.

### Monitoring Layer (Async)
```
Cron (5 min) → parse_logs_cron.py → log_parser.py → validations.db
                                                          ↓
                                              Dashboard API → UI
```

### E2E Test Flow (Synchronous)
*   **Problem:** Cron runs every 5 mins; tests run in seconds.
*   **Solution:** **Test-Mode Trigger**
*   Tests call `/test/get-validation`.
*   Helper endpoint **triggers parser immediately** on `app.log`.
*   Helper reads from DB and returns data.

---

## Part 3: Test Coverage Strategy

### The 6 Testing Layers

#### Layer 1: Event Emission
*   **Goal:** Ensure `app.log` receives correct data.
*   **Test:** `test_upgrade_event_emission.py` (Unit)
*   *Verify `checkout_started` logs include `product_id` and `variant`.*

#### Layer 2: Log Format Contract
*   **Goal:** Ensure log strings match parser regex.
*   **Test:** `test_log_format_contract.py` (Unit)

#### Layer 3: Log Parsing
*   **Goal:** Ensure parser extracts fields correctly.
*   **Test:** `test_log_parser_extraction.py` (Unit)

#### Layer 4: State Accumulation & User ID Continuity
*   **Goal:** Verify `upgrade_state` CSV build and ID linking.
*   **Test:** `test_state_accumulation.py` (Unit)
*   **Crucial Scenario (User ID Continuity):**
    *   Event 1: `locked` (User ID: None/Free)
    *   Event 2: `clicked` (User ID: Free)
    *   Event 3: `success` (User ID: Paid Token)
    *   *Verify parser links these into ONE job journey via `job_id`.*

#### Layer 5: Database Integration
*   **Goal:** Ensure data persists to SQLite correctly.
*   **Test:** `test_cron_parser_integration.py` (Integration)

#### Layer 6: Analytics Accuracy
*   **Goal:** Verify funnel metrics.
*   **Test:** `test_analytics_funnel.py` (Unit)

---

## Part 4: Implementation Phases

### Phase 0: Consolidate Log Parsers (Immediate)
**Priority:** CRITICAL
1.  Copy `event_to_state` mapping from `backend/dashboard/log_parser.py` to `dashboard/log_parser.py`.
2.  Delete `backend/dashboard/log_parser.py`.
3.  Fix imports in `backend/app.py`.

### Phase 1: Add Log Parser Unit Tests
**Priority:** HIGH
1.  Create `tests/test_log_parser_extraction.py`.
2.  Cover `extract_partial_results` (locked state).
3.  Cover `extract_upgrade_workflow` (rich data).

### Phase 2: Extend Schema & Parser
**Priority:** MEDIUM
1.  **Schema Migration:**
    *   Create script `scripts/migrate_validations_schema.py`.
    *   Run `ALTER TABLE validations ADD COLUMN experiment_variant TEXT;` (and other cols).
2.  **Parser Update:**
    *   Update regex to capture `variant`, `product_id`, `amount_cents`.
    *   Update `parse_job_events` to populate new fields.

### Phase 3: Migrate Test Helpers & Enable Test Trigger
**Priority:** HIGH (Unblocks E2E tests)
1.  **Update `backend/test_helpers.py`:**
    *   Implement `trigger_log_parse()`:
        ```python
        # Pseudo-code
        from dashboard.log_parser import CitationLogParser
        parser = CitationLogParser(db_path)
        parser.parse_logs(log_path) # Force flush
        ```
    *   Call `trigger_log_parse()` at start of `/test/get-validation`.
2.  **Update `pricing-integration.spec.js`:**
    *   Replace `/test/get-events` with `/test/get-validation?job_id=...`.
3.  **Cleanup:** Remove `UPGRADE_EVENT` table and legacy endpoints.

### Phase 4: Integration Tests
**Priority:** LOW
1.  Add `test_cron_parser_integration.py`.

---

## Part 5: Verification Checklist

- [ ] **Phase 0:** Backend tests pass. Cron job runs successfully.
- [ ] **Phase 1:** New unit tests pass.
- [ ] **Phase 2:** DB schema has new columns. Dashboard still loads.
- [ ] **Phase 3:** `npm run test:e2e` passes (especially `pricing-integration.spec.js`).
- [ ] **Manual:** Complete a purchase flow; check `validations.db` for `amount_cents`.
