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
        // Track if we should fail the request
        let shouldFail = true;

        // Mock /api/validate/async to return 500 on first call
        await page.route('**/api/validate/async', async route => {
            if (shouldFail) {
                console.log('Returning 500 error for validation request');
                await route.fulfill({
                    status: 500,
                    contentType: 'application/json',
                    body: JSON.stringify({ detail: 'Internal server error' })
                });
            } else {
                // Let the real API handle subsequent requests
                await route.continue();
            }
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

        // Now allow the request to succeed
        shouldFail = false;

        // Clear editor and resubmit
        await page.fill('.ProseMirror', 'Brown, A. (2023). Second attempt citation. Academic Press.');
        await page.click('button:has-text("Check My Citations")');

        // Wait for results - should succeed this time
        await expect(page.locator('.validation-results-section').first()).toBeVisible({ timeout: 30000 });

        // Error message should be gone
        await expect(page.locator('.error-message')).not.toBeVisible();

        console.log('✅ Test 1 passed: API 500 error recovery works correctly');
    });

    test('Job timeout shows timeout message and allows new submission', async ({ page, browserName }, testInfo) => {
        // Skip on mobile browsers - this tests network timeout behavior which is identical
        // across viewports, and the 3+ minute runtime makes it impractical to run on all browsers
        const isMobile = testInfo.project.name.toLowerCase().includes('mobile');
        test.skip(isMobile, 'Timeout behavior is viewport-independent, skip on mobile for efficiency');

        // This test requires extended timeout to wait for polling to timeout
        // App polls for 90 attempts at 2s = ~3 minutes
        test.setTimeout(240000); // 4 minutes

        // Navigate to app
        await page.goto('http://localhost:5173');
        await page.locator('.ProseMirror').first().waitFor({ state: 'visible', timeout: 10000 });

        // Intercept job status to always return 'pending' (simulating a stuck job)
        // Note: endpoint is /api/jobs/{id} (plural 'jobs')
        await page.route('**/api/jobs/*', async route => {
            console.log('Returning pending status for job poll');
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    status: 'pending',
                    progress: 0
                })
            });
        });

        // Submit validation to get a real job created
        await page.fill('.ProseMirror', 'Johnson, M. (2023). Timeout test citation. Test Journal, 5(2), 50-60.');
        await page.click('button:has-text("Check My Citations")');

        // Wait for loading state
        await expect(page.locator('.validation-loading-container').first()).toBeVisible({ timeout: 5000 });

        // Wait for timeout error message (takes ~3 minutes with real polling config)
        await expect(page.locator('.error-message')).toBeVisible({ timeout: 200000 });

        // Verify timeout message content
        const errorText = await page.locator('.error-message').textContent();
        console.log('Timeout error message:', errorText);
        expect(errorText?.toLowerCase()).toContain('timed out');

        // Verify localStorage is cleaned up (job_id removed)
        const jobId = await page.evaluate(() => localStorage.getItem('current_job_id'));
        expect(jobId).toBeNull();

        // Verify button re-enables for new submission
        await expect(page.locator('button:has-text("Check My Citations")')).toBeEnabled({ timeout: 5000 });

        console.log('✅ Test 2 passed: Job timeout recovery works correctly');
    });
});
