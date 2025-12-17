# Remove Deprecated Sync Validation Endpoint (Revised)

## Context

The synchronous validation endpoint (`/api/validate`) has been replaced by the asynchronous validation endpoint (`/api/validate/async`). The main application (`App.jsx` and `Success.jsx`) already uses the async endpoint. The sync endpoint is no longer needed for the primary user flow and should be removed to:

1. **Reduce code complexity** - Eliminate ~240 lines of duplicated logic in `app.py`
2. **Reduce maintenance overhead** - Stop maintaining two parallel code paths
3. **Reduce test burden** - Stop maintaining tests for deprecated functionality
4. **Clarify architecture** - Single validation path makes codebase easier to understand

## Decisions Made

Based on user feedback:

| Decision Point | Choice |
|----------------|--------|
| **MiniChecker** | ✅ Preserve - Migrate to async endpoint |
| **Debug Components** | 🗑️ Delete both (`DebugHTMLTest.jsx`, `DebugValidationTable.jsx`) |
| **Backend Tests** | 🗑️ Delete obsolete tests (coverage exists in async tests) |

---

## Proposed Changes

### Backend (`/backend`)

#### [MODIFY] [app.py](file:///Users/roy/Documents/Projects/citations/backend/app.py)

**Lines to remove: ~917-1157** (approximately 240 lines)

Remove the synchronous validation endpoint:

```python
@app.post("/api/validate", response_model=ValidationResponse)
async def validate_citations(http_request: Request, request: ValidationRequest):
    # ... entire function (~240 lines)
```

> [!NOTE]
> **Tracking Impact**: The sync endpoint creates job IDs with prefix `sync_` (line 966: `job_id = f"sync_{int(time.time())}_{uuid.uuid4().hex[:8]}"`). After removal, all job IDs will be UUIDs from the async endpoint. This is purely cosmetic for log parsing.

---

#### [DELETE] [tests/test_free_tier.py](file:///Users/roy/Documents/Projects/citations/backend/tests/test_free_tier.py)

**Entire file (276 lines)** - All 7 tests use sync endpoint. Equivalent coverage exists in:
- `test_async_jobs.py` (lines 160-237, 269-317)
- `test_async_jobs_integration.py` (lines 214+)

---

#### [DELETE] [tests/test_credit_enforcement.py](file:///Users/roy/Documents/Projects/citations/backend/tests/test_credit_enforcement.py)

**Entire file (227 lines)** - All 6 tests use sync endpoint. Equivalent coverage exists in:
- `test_async_jobs.py` (lines 122-157)
- `test_async_jobs_integration.py` (lines 183-210)

---

#### [MODIFY] [tests/test_gemini_routing_integration.py](file:///Users/roy/Documents/Projects/citations/backend/tests/test_gemini_routing_integration.py)

Delete one test method (lines 197-229):
```python
async def test_direct_validate_endpoint_model_routing(...)
```

---

#### [DELETE] [tests/load_test_p5_7.py](file:///Users/roy/Documents/Projects/citations/backend/tests/load_test_p5_7.py)

**Entire file** - Uses sync endpoint for load testing. If load testing is still needed, create a new script that uses async endpoint.

---

### Frontend (`/frontend/frontend/src`)

#### [MODIFY] [components/MiniChecker.jsx](file:///Users/roy/Documents/Projects/citations/frontend/frontend/src/components/MiniChecker.jsx)

**Migration to async endpoint** - The key change:

```diff
  const handleValidate = async () => {
    if (!citation.trim()) return

    setIsValidating(true)
    setError(null)
    setResult(null)

    try {
-     const response = await fetch('/api/validate', {
+     // Start async job
+     const createResponse = await fetch('/api/validate/async', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Experiment-Variant': getExperimentVariant()
        },
        body: JSON.stringify({
          citations: citation,
          style: 'apa7',
        }),
      })

-     if (!response.ok) {
+     if (!createResponse.ok) {
        // ... error handling
      }

-     const data = await response.json()
+     const { job_id } = await createResponse.json()
+
+     // Poll for results (simple 1-second interval)
+     let data
+     const maxAttempts = 60 // 60 seconds timeout
+     for (let i = 0; i < maxAttempts; i++) {
+       const statusResponse = await fetch(`/api/jobs/${job_id}`)
+       const jobData = await statusResponse.json()
+       
+       if (jobData.status === 'completed') {
+         data = jobData.results
+         break
+       }
+       if (jobData.status === 'failed') {
+         throw new Error(jobData.error || 'Validation failed')
+       }
+       await new Promise(r => setTimeout(r, 1000))
+     }
+     
+     if (!data) {
+       throw new Error('Validation timed out')
+     }

      // Extract first result (single citation)
      if (data.results && data.results.length > 0) {
        setResult(data.results[0])
        // ... rest of success handling
      }
```

**Estimated effort**: ~1-2 hours

---

#### [DELETE] [components/DebugHTMLTest.jsx](file:///Users/roy/Documents/Projects/citations/frontend/frontend/src/components/DebugHTMLTest.jsx)

**Entire file (236 lines)** - Debug component not used in production.

---

#### [DELETE] [components/DebugValidationTable.jsx](file:///Users/roy/Documents/Projects/citations/frontend/frontend/src/components/DebugValidationTable.jsx)

**Entire file (87 lines)** - Debug component not used in production.

---

#### [MODIFY] [App.jsx](file:///Users/roy/Documents/Projects/citations/frontend/frontend/src/App.jsx)

> [!IMPORTANT]
> **New finding from deep review**: `DebugHTMLTest` is imported and used in `App.jsx`!

**Remove import (line 25)**:
```diff
-import DebugHTMLTest from './components/DebugHTMLTest'
```

**Remove route handler (lines 1089-1091)**:
```diff
-  if (pathname === '/debug-html') {
-    return <DebugHTMLTest />
-  }
```

---

#### [MODIFY] [components/MiniChecker.test.jsx](file:///Users/roy/Documents/Projects/citations/frontend/frontend/src/components/MiniChecker.test.jsx)

Update all tests to:
1. Expect calls to `/api/validate/async` instead of `/api/validate`
2. Mock the polling flow (job creation → status polling → completion)

**Example test update**:
```diff
  it('validates citation when button clicked', async () => {
-   global.fetch = vi.fn(() =>
-     Promise.resolve({
-       ok: true,
-       json: () => Promise.resolve(mockResponse),
-     })
-   )
+   global.fetch = vi.fn()
+     .mockResolvedValueOnce({  // Job creation
+       ok: true,
+       json: () => Promise.resolve({ job_id: 'test-job-123' })
+     })
+     .mockResolvedValueOnce({  // Job status
+       ok: true,
+       json: () => Promise.resolve({
+         status: 'completed',
+         results: mockResponse
+       })
+     })

    // ... rest of test
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
-       '/api/validate',
+       '/api/validate/async',
        expect.objectContaining({
          method: 'POST',
```

---

#### [MODIFY] [App.test.jsx](file:///Users/roy/Documents/Projects/citations/frontend/frontend/src/App.test.jsx)

> [!WARNING]
> **Investigation finding**: Lines 66 and 248 expect `/api/validate` but `App.jsx` actually uses `/api/validate/async`. These tests may be broken/passing coincidentally due to mocking. Review and fix.

Either:
- Update to expect `/api/validate/async` + mock polling
- Or verify tests are actually testing the real behavior

---

### E2E Tests (`/frontend/frontend/tests`)

#### [DELETE or UPDATE] [debug_checker_error.spec.js](file:///Users/roy/Documents/Projects/citations/frontend/frontend/tests/debug_checker_error.spec.js)

> [!IMPORTANT]
> **New finding from deep review**: This E2E test navigates to **production PSEO pages** and tests MiniChecker!

The test (line 43) goes to:
```javascript
await page.goto('https://citationformatchecker.com/guide/apa-citation-errors/');
```

**Options**:
1. **Keep test** - It will continue to work after MiniChecker is migrated to async
2. **Update test** - Update the network request assertions (lines 124-136) if needed

The test filters for `/api/validate` which will match both sync and async endpoints. After migration, the requests will go to `/api/validate/async` instead. The test logic should still work but may need assertion updates.

---

## Critical Step: PSEO Asset Rebuild

> [!WARNING]
> `MiniChecker` is bundled into `mini-checker.js` for PSEO pages.

**After modifying `MiniChecker.jsx`, you MUST run**:
```bash
cd frontend/frontend
npm run build:mini-checker
```
This updates `/backend/pseo/builder/assets/js/mini-checker.js`. If you skip this, PSEO pages will still try to use the old Sync endpoint and will break when we remove it!

---

### Documentation

#### [MODIFY] [README.md](file:///Users/roy/Documents/Projects/citations/README.md)

The README already documents async architecture (line 33). No changes needed.

---

## Complete File Change Summary

| Category | File | Action | Lines Changed |
|----------|------|--------|---------------|
| **Backend** | `app.py` | Remove sync endpoint | -240 |
| **Backend** | `tests/test_free_tier.py` | Delete file | -276 |
| **Backend** | `tests/test_credit_enforcement.py` | Delete file | -227 |
| **Backend** | `tests/test_gemini_routing_integration.py` | Remove 1 test | -33 |
| **Backend** | `tests/load_test_p5_7.py` | Delete file | -120 |
| **Frontend** | `App.jsx` | Remove import + route | -4 |
| **Frontend** | `MiniChecker.jsx` | Migrate to async | +35/-15 |
| **Frontend** | `DebugHTMLTest.jsx` | Delete file | -236 |
| **Frontend** | `DebugValidationTable.jsx` | Delete file | -87 |
| **Frontend** | `MiniChecker.test.jsx` | Update for async | ±100 |
| **Frontend** | `App.test.jsx` | Review/fix | ±10 |
| **E2E** | `debug_checker_error.spec.js` | Review (may work as-is) | 0 |

**Total estimated reduction**: ~900-1100 lines of code

---

## Verification Plan

### Automated Tests

1. **Backend tests**:
   ```bash
   cd backend && python3 -m pytest tests/ -v
   ```

2. **Frontend unit tests**:
   ```bash
   cd frontend/frontend && npm test
   ```

3. **E2E tests**:
   ```bash
   cd frontend/frontend && npm run test:e2e
   ```

### Manual Verification

1. **Main app flow**: Validate citations work end-to-end
2. **PSEO pages with MiniChecker**: Test on a PSEO page (e.g., `/cite-youtube-apa`)
3. **Sync endpoint returns 404**:
   ```bash
   curl -X POST http://localhost:8000/api/validate \
     -H "Content-Type: application/json" \
     -d '{"citations": "Test", "style": "apa7"}'
   # Expected: 404 Not Found
   ```

---

## Implementation Order

### Phase 1: MiniChecker Migration (Frontend)
1. Update `MiniChecker.jsx` to use async endpoint
2. Update `MiniChecker.test.jsx` 
3. **Run `npm run build:mini-checker`** (Updates PSEO assets)
4. Run frontend tests
5. Test on local PSEO pages

### Phase 2: Debug Component Cleanup (Frontend)
1. Delete `DebugHTMLTest.jsx`
2. Delete `DebugValidationTable.jsx`
3. Remove import and route from `App.jsx`
4. Run frontend tests

### Phase 3: Backend Cleanup
1. Remove sync endpoint from `app.py`
2. Delete `test_free_tier.py`
3. Delete `test_credit_enforcement.py`
4. Update `test_gemini_routing_integration.py`
5. Delete `load_test_p5_7.py`
6. Run backend tests

### Phase 4: Full Verification
1. Run full E2E test suite
2. Manual testing of main flow
3. Manual testing of MiniChecker on PSEO
4. Verify sync endpoint returns 404

### Phase 5: Deploy
1. Commit all changes
2. Deploy to production
3. Monitor for errors

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| MiniChecker polling complexity | Low | Medium | Use simple polling (already proven in App.jsx) |
| E2E test `debug_checker_error.spec.js` breaks | Low | Low | Test uses generic `/api/validate` filter, should work |
| External integrations using sync endpoint | Low | High | Check access logs before deployment |
| Test coverage gaps | Low | Low | Async endpoint already has comprehensive tests |

---

## Questions for Implementation

None - all decision points resolved. Ready for implementation upon approval.
