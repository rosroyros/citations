YOLO mode is enabled. All tool calls will be automatically approved.
Loaded cached credentials.
The review has been completed.

**Summary**:
Critical integration bugs found between frontend and backend. The frontend components and tests are inconsistent regarding the API contract (`event` vs `event_type`), and the E2E tests are masking this issue.

**Critical Issues**:
1.  **API Contract Mismatch (Bug)**:
    -   File: `frontend/frontend/src/components/PartialResults.jsx` (implied by test) vs `backend/app.py`
    -   The backend endpoint `/api/upgrade-event` strictly requires an `event` field (see `backend/app.py`).
    -   `PartialResults.jsx` (verified via `read_file`) sends `event_type` instead of `event`.
    -   **Impact**: All upgrade clicks from Partial Results will fail with `400 Bad Request` ("event is required").

2.  **Broken Test Expectation**:
    -   File: `frontend/frontend/src/pages/Success.test.jsx` lines 144-150
    -   The test expects `event_type: 'success'`.
    -   However, `Success.jsx` correctly sends `event: 'success'`.
    -   **Impact**: This test should be failing. If it is passing, the test environment is not accurately reflecting the component behavior.

3.  **Incorrect Test Assertion**:
    -   File: `frontend/frontend/src/components/PartialResults.test.jsx` lines 242-248
    -   The test asserts that `event_type` is sent. While this matches the (buggy) component code, it enshrines the bug. It should assert `event` is sent, and the component should be fixed.

**Important Issues**:
1.  **E2E Test Masking Bugs**:
    -   File: `frontend/frontend/tests/e2e/upgrade-funnel.spec.js` line 44
    -   The mock handler accepts both: `event: eventData.event || eventData.event_type`.
    -   **Impact**: This allows the E2E test to pass despite the frontend sending the wrong field (`event_type`) which the real backend would reject. The mock should be strict (`eventData.event`) to catch such regressions.

**Strengths**:
-   Comprehensive test coverage across unit, integration, and E2E layers.
-   Good use of mocking in E2E tests (Polar, API).
-   Clear testing of edge cases (missing job_id, API failures).

**Recommendations**:
1.  Fix `PartialResults.jsx` to send `event` instead of `event_type`.
2.  Update `PartialResults.test.jsx` to expect `event`.
3.  Update `Success.test.jsx` to expect `event`.
4.  Update E2E mock to strictly use `eventData.event` to match backend behavior.

**File References**:
-   `backend/app.py`: Defines `upgrade_event` requiring `event`.
-   `frontend/frontend/src/components/PartialResults.jsx`: Sends `event_type`.
-   `frontend/frontend/src/pages/Success.test.jsx`: Expects `event_type`.
-   `frontend/frontend/tests/e2e/upgrade-funnel.spec.js`: Mocks leniently.
