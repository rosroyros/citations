import { test, expect } from '@playwright/test';

/**
 * Error Recovery E2E Tests
 * 
 * Tests for error scenarios that have zero existing coverage:
 * 1. API 500 error - user sees friendly message and can retry
 * 2. Job timeout - user sees timeout message and can retry
 */

test.describe('Error Recovery Scenarios', () => {
    test.beforeEach(async ({ page }) => {
        // Clear state
        await page.context().clearCookies();
        await page.addInitScript(() => {
            localStorage.clear();
        });
    });

    test('API 500 error displays user-friendly message and allows retry', async ({ page }) => {
        // Track request count to control behavior
        let requestCount = 0;

        // Mock /api/validate/async - return 500 on first call, success on second
        await page.route('**/api/validate/async', async route => {
            requestCount++;
            if (requestCount === 1) {
                console.log('Returning 500 error for validation request');
                await route.fulfill({
                    status: 500,
                    contentType: 'application/json',
                    body: JSON.stringify({ detail: 'Internal server error' })
                });
            } else {
                // Return a mocked success response (not real backend)
                console.log('Returning mocked success response');
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        job_id: 'mock-retry-job-' + Date.now(),
                        status: 'pending',
                        experiment_variant: 0
                    })
                });
            }
        });

        // Mock job polling to return completed immediately
        await page.route('**/api/jobs/*', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    status: 'completed',
                    results: {
                        results: [
                            { original: 'Brown, A. (2023). Second attempt citation. Academic Press.', source_type: 'book', errors: [] }
                        ],
                        user_status: { type: 'free', validations_used: 1, limit: 5 }
                    }
                })
            });
        });

        // Navigate to app
        await page.goto('http://localhost:5173');
        await page.locator('.ProseMirror').first().waitFor({ state: 'visible', timeout: 10000 });

        // Submit validation
        await page.fill('.ProseMirror', 'Smith, J. (2023). Test citation. Journal of Testing, 1(1), 1-10.');
        await page.click('button:has-text("Check My Citations")');

        // Wait for error message to appear
        await expect(page.locator('.error-message')).toBeVisible({ timeout: 10000 });

        // Verify error message is user-friendly (not raw "500" or technical jargon)
        const errorText = await page.locator('.error-message').textContent();
        console.log('Error message displayed:', errorText);

        // Should contain helpful language
        expect(errorText?.toLowerCase()).toMatch(/error|failed|try again|unable|server/i);

        // Should NOT show raw status code to user in a confusing way
        // (It's OK if it says "Server error (500)" but not raw JSON)
        expect(errorText).not.toContain('{"detail"');

        // Verify loading state cleared
        await expect(page.locator('button:has-text("Check My Citations")')).toBeEnabled({ timeout: 5000 });

        // Verify button text is back to normal (not "Validating...")
        await expect(page.locator('button:has-text("Check My Citations")')).toBeVisible();

        // Clear editor and resubmit - now the mock will return success
        await page.fill('.ProseMirror', 'Brown, A. (2023). Second attempt citation. Academic Press.');
        await page.click('button:has-text("Check My Citations")');

        // Wait for results - should succeed this time (using mocked response)
        await expect(page.locator('.validation-results-section').first()).toBeVisible({ timeout: 30000 });

        // Error message should be gone
        await expect(page.locator('.error-message')).not.toBeVisible();

        console.log('✅ Test 1 passed: API 500 error recovery works correctly');
    });

    test('Job timeout shows timeout message and allows new submission', async ({ page, browserName }, testInfo) => {
        // Run only on chromium - timeout behavior is browser-independent
        // This eliminates flakiness from running same test on multiple browsers
        test.skip(browserName !== 'chromium', 'Timeout behavior is browser-independent, test on chromium only');

        // Mock job creation endpoint
        await page.route('**/api/validate/async', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    job_id: 'mock-timeout-job-123',
                    status: 'pending',
                    experiment_variant: 0
                })
            });
        });

        // Track poll count to simulate timeout after a few polls
        let pollCount = 0;
        await page.route('**/api/jobs/*', async route => {
            pollCount++;
            console.log(`Returning pending status for job poll #${pollCount}`);

            // After 3 polls, return timeout error to simulate what happens when polling exhausts
            if (pollCount >= 3) {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        status: 'failed',
                        error: 'Validation timed out. Please try again.'
                    })
                });
            } else {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        status: 'pending',
                        progress: pollCount * 10
                    })
                });
            }
        });

        // Navigate to app
        await page.goto('http://localhost:5173');
        await page.locator('.ProseMirror').first().waitFor({ state: 'visible', timeout: 10000 });

        // Submit validation
        await page.fill('.ProseMirror', 'Johnson, M. (2023). Timeout test citation. Test Journal, 5(2), 50-60.');
        await page.click('button:has-text("Check My Citations")');

        // Wait for loading state
        await expect(page.locator('.validation-loading-container').first()).toBeVisible({ timeout: 5000 });

        // Wait for error message (should appear after ~3 polls, ~6 seconds)
        await expect(page.locator('.error-message')).toBeVisible({ timeout: 30000 });

        // Verify error message content
        const errorText = await page.locator('.error-message').textContent();
        console.log('Timeout error message:', errorText);
        expect(errorText?.toLowerCase()).toMatch(/timed out|timeout|failed/i);

        // Verify button re-enables for new submission
        await expect(page.locator('button:has-text("Check My Citations")')).toBeEnabled({ timeout: 5000 });

        console.log('✅ Test 2 passed: Job timeout recovery works correctly');
    });
});
