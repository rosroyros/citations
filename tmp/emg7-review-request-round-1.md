You are conducting a code review.

## Task Context

### Beads Issue ID: emg7

citations-emg7: P3.6: Write E2E test for tracking
Status: in_progress
Priority: P1
Type: task
Created: 2025-12-10 22:11
Updated: 2025-12-11 20:54

Description:
## Overview

Create Playwright E2E test verifying that UPGRADE_EVENT logs are generated correctly when users go through the upgrade funnel.

**File to create:** `frontend/frontend/tests/e2e/upgrade-tracking.spec.js`

**Why this is needed:** We need automated verification that P3.1, P3.2, and P3.3 are working correctly - that events are being logged when users see pricing, select products, and complete purchases. Without this test, we can't be confident the A/B test tracking is working in production.

**Oracle Feedback #5:** Every event must include `experiment_variant` - this test verifies that.

## Important Context

**What does this test verify?**

1. **Pricing table shown event** - When user hits free limit and sees pricing modal, `pricing_table_shown` event logged
2. **Experiment variant assignment** - User gets assigned variant 1 or 2, stored in localStorage
3. **Variant persistence** - Same variant used throughout session (sticky assignment)
4. **Event structure** - All required fields present (timestamp, event, token, experiment_variant)

**NOT tested here (future phases):**
- Product selection (Phase 4 - requires Polar integration)
- Checkout creation (Phase 4)
- Purchase completion (Phase 4 - requires webhook)

**Test approach:**

Cannot directly read app.log from browser, so we test:
1. Frontend behavior (localStorage variant assignment)
2. API calls made (network tab)
3. Backend verification via separate log check script

## Complete Implementation

Create `frontend/frontend/tests/e2e/upgrade-tracking.spec.js`:

```javascript
import { test, expect } from '@playwright/test';

test.describe('Upgrade Tracking - A/B Test Events', () => {
  test.use({ baseURL: 'http://localhost:5173' });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
    });
  });

  test('tracks pricing_table_shown event when user hits free limit', async ({ page }) => {
    console.log('🚀 Test: pricing_table_shown event');

    // Navigate to home page
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // Simulate user who has used 10 free validations (at limit)
    await page.evaluate(() => {
      localStorage.setItem('citation_checker_free_used', '10');
    });

    // Reload to apply localStorage
    await page.goto('/');

    // Submit a validation (should trigger upgrade flow)
    const editor = page.locator('.ProseMirror')
      .or(page.locator('[contenteditable="true"]'))
      .or(page.locator('textarea'));

    await expect(editor).toBeVisible();
    await editor.fill('Smith, J. (2023). Test citation. Journal, 1(1), 1-10.');

    // Track network requests to backend
    const apiCalls = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiCalls.push({
          url: request.url(),
          method: request.method()
        });
      }
    });

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for validation to complete
    await expect(
      page.locator('.results, .validation-results, .validation-table').first()
    ).toBeVisible({ timeout: 60000 });

    // Verify experiment variant was assigned
    const variant = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );

    console.log('📊 Assigned variant:', variant);

    // Variant should be '1' or '2'
    expect(['1', '2']).toContain(variant);
    expect(variant).not.toBeNull();

    // Verify variant persists
    const variantCheck = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );
    expect(variantCheck).toBe(variant);

    console.log('✅ Variant assignment verified');
  });

  test('variant assignment is sticky across multiple upgrade clicks', async ({ page }) => {
    console.log('🚀 Test: Sticky variant assignment');

    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // Pre-assign variant 1
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '1');
      localStorage.setItem('citation_checker_free_used', '10');
    });

    // Reload
    await page.goto('/');

    // First submission
    const editor = page.locator('.ProseMirror')
      .or(page.locator('[contenteditable="true"]'))
      .or(page.locator('textarea'));

    await editor.fill('Smith, J. (2023). Test citation 1. Journal, 1(1), 1-10.');
    await page.locator('button[type="submit"]').click();

    await expect(
      page.locator('.results, .validation-results, .validation-table').first()
    ).toBeVisible({ timeout: 60000 });

    const variant1 = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );

    // Clear results and submit again
    await page.reload();
    await editor.fill('Jones, M. (2023). Test citation 2. Journal, 2(2), 20-30.');
    await page.locator('button[type="submit"]').click();

    await expect(
      page.locator('.results, .validation-results, .validation-table').first()
    ).toBeVisible({ timeout: 60000 });

    const variant2 = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );

    // Variants should match (sticky)
    expect(variant1).toBe('1');
    expect(variant2).toBe('1');
    expect(variant1).toBe(variant2);

    console.log('✅ Sticky assignment verified');
  });

  test('different users get randomly assigned to different variants', async ({ context }) => {
    console.log('🚀 Test: Random variant assignment');

    // Simulate 10 different users
    const variants = [];

    for (let i = 0; i < 10; i++) {
      // Create new incognito context (fresh user)
      const page = await context.newPage();

      await page.goto('/');
      await expect(page.locator('body')).toBeVisible();

      // Set free limit
      await page.evaluate(() => {
        localStorage.setItem('citation_checker_free_used', '10');
      });

      await page.goto('/');

      // Submit validation
      const editor = page.locator('.ProseMirror')
        .or(page.locator('[contenteditable="true"]'))
        .or(page.locator('textarea'));

      await editor.fill('Test, A. (2023). Citation. Journal, 1(1), 1-10.');
      await page.locator('button[type="submit"]').click();

      await expect(
        page.locator('.results, .validation-results, .validation-table').first()
      ).toBeVisible({ timeout: 60000 });

      const variant = await page.evaluate(() =>
        localStorage.getItem('experiment_v1')
      );

      variants.push(variant);
      console.log(`User ${i + 1}: variant ${variant}`);

      await page.close();
    }

    // Statistical check: With 10 users, very unlikely all get same variant
    const variant1Count = variants.filter(v => v === '1').length;
    const variant2Count = variants.filter(v => v === '2').length;

    console.log(`📊 Distribution: Variant 1: ${variant1Count}, Variant 2: ${variant2Count}`);

    // At least 1 of each variant should be assigned (with 10 users)
    // Probability of all same = (0.5)^10 = 0.001 (very unlikely)
    expect(variant1Count).toBeGreaterThan(0);
    expect(variant2Count).toBeGreaterThan(0);

    console.log('✅ Random assignment verified');
  });

  test('variant assignment happens on first upgrade trigger', async ({ page }) => {
    console.log('🚀 Test: Variant assigned on first trigger');

    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // Verify no variant yet
    let variant = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );
    expect(variant).toBeNull();

    // Use up free tier
    await page.evaluate(() => {
      localStorage.setItem('citation_checker_free_used', '10');
    });

    await page.goto('/');

    // Submit validation (first upgrade trigger)
    const editor = page.locator('.ProseMirror')
      .or(page.locator('[contenteditable="true"]'))
      .or(page.locator('textarea'));

    await editor.fill('Smith, J. (2023). Test. Journal, 1(1), 1-10.');
    await page.locator('button[type="submit"]').click();

    await expect(
      page.locator('.results, .validation-results, .validation-table').first()
    ).toBeVisible({ timeout: 60000 });

    // Now variant should be assigned
    variant = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );

    expect(variant).not.toBeNull();
    expect(['1', '2']).toContain(variant);

    console.log('✅ First-trigger assignment verified');
  });
});
```

## Verification Script for Backend Logs

Create `backend/tests/verify_upgrade_events.py` to check app.log directly:

```python
#!/usr/bin/env python3
"""
Verify UPGRADE_EVENT logs are being generated correctly.

Usage:
    python3 verify_upgrade_events.py

Checks:
    1. UPGRADE_EVENT lines exist in app.log
    2. Events have required fields (timestamp, event, token, experiment_variant)
    3. Experiment variant is '1' or '2'
    4. JSON is valid
"""
import json
import re
import sys
from pathlib import Path

def verify_upgrade_events(log_path='/opt/citations/logs/app.log'):
    """Verify upgrade events in log file."""

    if not Path(log_path).exists():
        # Try alternative paths
        alt_paths = [
            '../logs/app.log',
            '../../logs/app.log',
            '/tmp/app.log',
            './app.log'
        ]

        for alt_path in alt_paths:
            if Path(alt_path).exists():
                log_path = alt_path
                break
        else:
            print(f"❌ Log file not found: {log_path}")
            print(f"Checked paths: {[log_path] + alt_paths}")
            return False

    events_found = 0
    errors = []

    with open(log_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if 'UPGRADE_EVENT:' not in line:
                continue

            events_found += 1

            # Extract JSON
            try:
                json_start = line.index('UPGRADE_EVENT:') + len('UPGRADE_EVENT:')
                json_str = line[json_start:].strip()
                event = json.loads(json_str)
            except (ValueError, json.JSONDecodeError) as e:
                errors.append(f"Line {line_num}: Invalid JSON - {e}")
                continue

            # Verify required fields
            required = ['timestamp', 'event', 'token', 'experiment_variant']
            missing = [f for f in required if f not in event]

            if missing:
                errors.append(f"Line {line_num}: Missing fields {missing}")

            # Verify variant is valid
            variant = event.get('experiment_variant')
            if variant not in ['1', '2', None]:
                errors.append(f"Line {line_num}: Invalid variant '{variant}' (must be '1' or '2')")

            # Oracle #5: variant should ALWAYS be present
            if variant is None:
                errors.append(f"Line {line_num}: Oracle #5 violation - variant is None")

    # Report results
    print(f"\n{'='*60}")
    print(f"UPGRADE_EVENT Log Verification")
    print(f"{'='*60}")
    print(f"\nLog file: {log_path}")
    print(f"Events found: {events_found}")
    print(f"Errors: {len(errors)}")

    if errors:
        print(f"\n❌ FAILED - Found {len(errors)} error(s):")
        for error in errors[:10]:  # Show first 10
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        return False

    if events_found == 0:
        print(f"\n⚠️  WARNING - No UPGRADE_EVENT logs found")
        print(f"This is expected if P3.1-P3.3 haven't been deployed yet.")
        return True

    print(f"\n✅ PASSED - All {events_found} events are valid")

    # Show sample event
    print(f"\nSample event:")
    with open(log_path, 'r') as f:
        for line in f:
            if 'UPGRADE_EVENT:' in line:
                json_start = line.index('UPGRADE_EVENT:') + len('UPGRADE_EVENT:')
                json_str = line[json_start:].strip()
                event = json.loads(json_str)
                print(json.dumps(event, indent=2))
                break

    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Verify UPGRADE_EVENT logs')
    parser.add_argument('--log-path', default='/opt/citations/logs/app.log',
                       help='Path to app.log file')

    args = parser.parse_args()

    success = verify_upgrade_events(args.log_path)
    sys.exit(0 if success else 1)
```

## Step-by-Step Implementation

### Step 1: Create E2E test file

```bash
cd frontend/frontend/tests/e2e
touch upgrade-tracking.spec.js
ls -la upgrade-tracking.spec.js
```

**Expected:** File created

### Step 2: Add test code

Copy the complete test from above into `upgrade-tracking.spec.js`.

### Step 3: Run tests locally

```bash
cd frontend/frontend

# Make sure backend is running
# In another terminal: cd backend && python3 -m uvicorn app:app --reload

# Run the specific test
npm run test:e2e -- upgrade-tracking.spec.js

# OR run with UI for debugging
npx playwright test upgrade-tracking.spec.js --ui
```

**Expected output:**
```
Running 4 tests using 1 worker

  ✓ tracks pricing_table_shown event when user hits free limit (15s)
  ✓ variant assignment is sticky across multiple upgrade clicks (25s)
  ✓ different users get randomly assigned to different variants (45s)
  ✓ variant assignment happens on first upgrade trigger (12s)

  4 passed (1m 37s)
```

### Step 4: Create log verification script

```bash
cd backend/tests
touch verify_upgrade_events.py
chmod +x verify_upgrade_events.py
```

Add the verification script code from above.

### Step 5: Test log verification

```bash
cd backend

# Run after E2E tests (so events exist in log)
python3 tests/verify_upgrade_events.py

# Try with custom log path
python3 tests/verify_upgrade_events.py /path/to/custom/app.log
```

**Expected output:**
```
============================================================
UPGRADE_EVENT Log Verification
============================================================

Log file: /opt/citations/logs/app.log
Events found: 8
Errors: 0

✅ PASSED - All 8 events are valid

Sample event:
{
  "timestamp": 1733916000,
  "event": "pricing_table_shown",
  "token": "abc12345",
  "experiment_variant": "1"
}
```

### Step 6: Run in CI (optional)

Add to `.github/workflows/test.yml` (if using GitHub Actions):

```yaml
- name: Run E2E upgrade tracking tests
  run: |
    cd frontend/frontend
    npm run test:e2e -- upgrade-tracking.spec.js
```

## Verification Checklist

- [ ] File `frontend/frontend/tests/e2e/upgrade-tracking.spec.js` created
- [ ] File `backend/tests/verify_upgrade_events.py` created
- [ ] Test 1: pricing_table_shown event test passes
- [ ] Test 2: sticky variant test passes
- [ ] Test 3: random assignment test passes
- [ ] Test 4: first trigger test passes
- [ ] Variant assignment stores '1' or '2' in localStorage
- [ ] Variant persists across page reloads
- [ ] Different users get different variants (randomization works)
- [ ] Verification script finds UPGRADE_EVENT logs
- [ ] Verification script validates JSON structure
- [ ] Verification script checks required fields
- [ ] Verification script enforces Oracle #5 (variant always present)
- [ ] No console errors during test execution
- [ ] Tests pass in both headless and headed mode

## Common Issues and Fixes

**Issue 1: Test fails - variant is null**
```
Expected ['1', '2'] to contain null
```
**Fix:** P3.2 not implemented yet. Variant assignment happens in validation endpoint. Ensure P3.2 deployed.

**Issue 2: Test times out waiting for results**
```
Timeout 60000ms exceeded while waiting for locator
```
**Fix:** Backend not running or validation failing. Check backend logs:
```bash
tail -f backend/logs/app.log
```

**Issue 3: Random assignment test fails (all same variant)**
```
Expected variant2Count to be greater than 0
```
**Fix:** Unlikely but possible with true randomness. Run test again. If fails repeatedly, check `Math.random()` in `experimentVariant.js`.

**Issue 4: Verification script finds no events**
```
⚠️  WARNING - No UPGRADE_EVENT logs found
```
**Fix:** Expected if P3.1-P3.3 not deployed. Run E2E tests first to generate events, or check log path:
```bash
ls -la /opt/citations/logs/app.log
grep UPGRADE_EVENT /opt/citations/logs/app.log
```

**Issue 5: Verification script shows Oracle #5 violations**
```
Oracle #5 violation - variant is None
```
**Fix:** `log_upgrade_event()` called without `experiment_variant` parameter. Review P3.1, P3.2, P3.3 implementations.

**Issue 6: Cannot read localStorage in test**
```
TypeError: localStorage is not defined
```
**Fix:** Use `page.evaluate()` to access browser localStorage:
```javascript
const variant = await page.evaluate(() => localStorage.getItem('experiment_v1'));
```

## What NOT to Do

❌ **Don't try to read app.log from browser** - Use verification script instead

❌ **Don't mock localStorage** - Test real variant assignment logic

❌ **Don't hardcode expected variant** - Accept either '1' or '2' (random)

❌ **Don't skip cleanup** - Always clear localStorage in beforeEach

❌ **Don't test Polar integration** - That's Phase 4, not Phase 3

❌ **Don't test purchase events** - webhook events tested in Phase 4

❌ **Don't assume log file exists** - Verification script should handle gracefully

## Success Criteria

- [ ] `upgrade-tracking.spec.js` created with 4 tests
- [ ] All 4 tests pass locally
- [ ] `verify_upgrade_events.py` created
- [ ] Verification script validates log structure
- [ ] Tests verify variant assignment ('1' or '2')
- [ ] Tests verify variant persistence (sticky)
- [ ] Tests verify randomization (different users get different variants)
- [ ] No console errors during test run
- [ ] Tests pass in CI (if configured)
- [ ] Verification script reports valid events
- [ ] Code committed with message: "test: Add E2E tests for upgrade event tracking (P3.6)"

## Time Estimate

**1.5 hours total:**
- Create test file: 15 min
- Write test code: 30 min
- Run and debug tests: 20 min
- Create verification script: 15 min
- Test verification script: 10 min
- Documentation: 10 min

## Dependencies

**Depends on:**
- P3.1 (citations-q2y5): `log_upgrade_event()` function exists
- P3.2 (citations-iixt): Validation endpoint logs pricing_table_shown
- `experimentVariant.js` utility (P2.4): Variant assignment logic

**Blocks:**
- Phase 4 deployment: Need confidence that tracking works before adding Polar

## Reference

**Design doc:** `docs/plans/2025-12-10-pricing-model-ab-test-design-FINAL.md`
- Lines 1980-2024: E2E test examples (shows test pattern)

**Existing tests:**
- `frontend/frontend/tests/e2e/async-polling-validation.spec.js`: Shows validation flow testing
- `frontend/frontend/tests/e2e/dashboard.spec.js`: Shows E2E test structure

**Playwright docs:**
- localStorage access: https://playwright.dev/docs/evaluating
- Multiple contexts: https://playwright.dev/docs/browser-contexts

## Parent Issue

citations-2amw (Phase 3: Tracking Infrastructure)

## Labels

`testing`, `e2e`, `playwright`, `tracking`, `ab-test`

Depends on (1):
  → citations-iixt: P3.2: Add tracking to validation endpoint [P1]

Blocks (1):
  ← citations-q0cu: Phase 4: Multi-Product Checkout [P1]

### What Was Implemented

Created E2E tests for upgrade event tracking with 4 comprehensive tests that verify variant assignment, persistence, and randomization. Also created a log verification script to validate UPGRADE_EVENT logs in the backend. The tests are currently failing (RED phase of TDD) because the variant assignment is not yet implemented in the frontend.

### Requirements/Plan

Key requirements from task description:
- Create `frontend/frontend/tests/e2e/upgrade-tracking.spec.js` with E2E tests
- Test that UPGRADE_EVENT logs are generated correctly for pricing_table_shown events
- Verify experiment variant assignment ('1' or '2') in localStorage
- Ensure variant persistence across sessions (sticky assignment)
- Test random variant assignment across different users
- Create verification script `backend/tests/verify_upgrade_events.py` to validate logs
- Enforce Oracle #5 requirement: experiment_variant must always be present

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 2e99dd62ed846271a9479da01f3dcbc191788300
- HEAD_SHA: 7fac9352b121ca5053dbdefac8f1cbeea7645924

Use git commands (git diff, git show, git log, etc.) to examine the changes.

## Review Criteria

Evaluate the implementation against these criteria:

**Adherence to Task:**
- Does implementation match task requirements?
- Were all requirements addressed?
- Any scope creep or missing functionality?

**Security:**
- SQL injection, XSS, command injection vulnerabilities
- Hardcoded secrets or credentials
- Input validation and sanitization

**Code Quality:**
- Follows project standards and patterns
- Clear naming and structure
- Appropriate error handling
- Edge cases covered

**Testing:**
- Tests written and passing
- Coverage adequate
- Tests verify actual behavior
- **Frontend visual/UX changes: Playwright tests REQUIRED for any visual or user interaction changes**

**Performance & Documentation:**
- No obvious performance issues
- Code is self-documenting or commented

## Required Output Format

Provide structured feedback in these categories:

1. **Critical**: Must fix immediately (security, broken functionality, data loss)
2. **Important**: Should fix before merge (bugs, missing requirements, poor patterns)
3. **Minor**: Nice to have (style, naming, optimization opportunities)
4. **Strengths**: What was done well

**IMPORTANT**: Verify implementation matches task requirements above.

Be specific with file:line references for all issues.