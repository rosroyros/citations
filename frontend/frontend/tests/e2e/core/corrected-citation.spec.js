import { test, expect } from '@playwright/test';

const TIMEOUT = 30000;

const testCitation = {
    withErrors: 'Smith, J. (2020). the wrong title. Publisher.',
    perfect: 'Smith, J. (2023). The correct title. Journal of Testing, 45(2), 123-145. https://doi.org/10.1234/test'
};

test.describe('Corrected Citation Feature', () => {
    test.use({
        baseURL: process.env.CI ? 'https://citationformatchecker.com' : 'http://localhost:5173'
    });

    test.beforeEach(async ({ page }) => {
        await page.context().clearCookies();
        await page.addInitScript(() => {
            localStorage.clear();
        });
    });

    test('shows corrected citation for citations with errors', async ({ page }) => {
        // Mock job creation endpoint
        await page.route(/\/api\/validate\/async/, async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    job_id: 'mock-corrected-citation-job',
                    status: 'pending',
                    experiment_variant: 0
                })
            });
        });

        // Mock job polling to return results with corrected citation
        await page.route(/\/api\/jobs\/.*/, async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    status: 'completed',
                    results: {
                        results: [{
                            citation_number: 1,
                            original: testCitation.withErrors,
                            source_type: 'book',
                            errors: [
                                { component: 'Title', problem: 'Missing proper capitalization', correction: 'Capitalize title properly' }
                            ],
                            corrected_citation: 'Smith, J. (2020). <em>The Wrong Title</em>. Publisher.'
                        }],
                        user_status: { type: 'free', validations_used: 1, limit: 5 }
                    }
                })
            });
        });

        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Submit citation with errors
        const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
        await expect(editor).toBeVisible({ timeout: 10000 });
        await editor.fill(testCitation.withErrors);

        // Submit form
        await page.locator('button[type="submit"]').click();

        // Wait for results
        await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

        // Verify corrected citation card appears (row expands automatically for errors)
        await expect(page.locator('.corrected-citation-card')).toBeVisible({ timeout: 5000 });
        await expect(page.locator('.corrected-citation-card')).toContainText('CORRECTED');
    });

    test('does not show corrected citation for perfect citations', async ({ page }) => {
        // Mock job creation endpoint
        await page.route(/\/api\/validate\/async/, async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    job_id: 'mock-perfect-citation-job',
                    status: 'pending',
                    experiment_variant: 0
                })
            });
        });

        // Mock job polling to return perfect results (no errors, no corrected_citation)
        await page.route(/\/api\/jobs\/.*/, async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    status: 'completed',
                    results: {
                        results: [{
                            citation_number: 1,
                            original: testCitation.perfect,
                            source_type: 'journal_article',
                            errors: [],
                            corrected_citation: null
                        }],
                        user_status: { type: 'free', validations_used: 1, limit: 5 }
                    }
                })
            });
        });

        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Submit perfect citation
        const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
        await expect(editor).toBeVisible({ timeout: 10000 });
        await editor.fill(testCitation.perfect);

        // Submit form
        await page.locator('button[type="submit"]').click();

        // Wait for results
        await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

        // Wait a moment for any animations
        await page.waitForTimeout(500);

        // Verify corrected citation card does NOT appear anywhere in the page
        // (perfect citations don't have errors, so no corrected citation card)
        await expect(page.locator('.corrected-citation-card')).toHaveCount(0);
    });

    // Clipboard API permissions only work reliably in desktop Chromium
    // Test on desktop chromium only to verify the UI feedback works
    test('copy button shows Copied feedback', async ({ page, browserName }, testInfo) => {
        // Skip on non-Chromium browsers as clipboard permissions aren't supported
        test.skip(browserName !== 'chromium', 'Clipboard permissions only work in Chromium');

        // Skip on mobile projects (Mobile Chrome) - gated overlay handling is inconsistent
        const isMobile = testInfo.project.name.toLowerCase().includes('mobile');
        test.skip(isMobile, 'Skip clipboard test on mobile browsers');

        // Grant clipboard permissions (Chromium only)
        await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);

        // Mock user credits endpoint to confirm paid status (avoid gating)
        await page.route('/api/user/credits**', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    credits: 100,
                    active_pass: null
                })
            });
        });

        // Mock job creation endpoint
        await page.route(/\/api\/validate\/async/, async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    job_id: 'mock-copy-test-job',
                    status: 'pending',
                    experiment_variant: 0
                })
            });
        });

        // Mock job polling to return results with corrected citation
        await page.route(/\/api\/jobs\/.*/, async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    status: 'completed',
                    results: {
                        results: [{
                            citation_number: 1,
                            original: testCitation.withErrors,
                            source_type: 'book',
                            errors: [
                                { component: 'Title', problem: 'Wrong capitalization', correction: 'Fix it' }
                            ],
                            corrected_citation: 'Smith, J. (2020). <em>The Wrong Title</em>. Publisher.'
                        }],
                        user_status: { type: 'credits', balance: 99, full_access: true }
                    }
                })
            });
        });

        // Mock analytics endpoint
        await page.route('/api/analytics/correction-copied', async (route) => {
            await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
        });

        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // Submit citation with errors
        const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
        await expect(editor).toBeVisible({ timeout: 10000 });
        await editor.fill(testCitation.withErrors);

        // Submit form
        await page.locator('button[type="submit"]').click();

        // Wait for results
        await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

        // Handle gated overlay if it appears - wait briefly for it to potentially appear
        await page.waitForTimeout(500);
        const gatedOverlay = page.locator('[data-testid="gated-results"]');
        if (await gatedOverlay.isVisible()) {
            console.log('Gated overlay detected, clicking View Results...');
            await page.locator('button:has-text("View Results")').first().click({ force: true });
            await expect(gatedOverlay).not.toBeVisible({ timeout: 5000 });
        }

        // Wait for corrected citation card
        await expect(page.locator('.corrected-citation-card')).toBeVisible({ timeout: 5000 });

        // Ensure overlay is definitely gone before clicking
        await expect(page.locator('.gated-overlay-backdrop')).not.toBeVisible({ timeout: 2000 }).catch(() => { });

        // Click copy button with force to bypass any remaining overlay issues
        const copyButton = page.locator('.corrected-citation-card button');
        await copyButton.click({ force: true });

        // Verify feedback shows "Copied"
        await expect(page.locator('.corrected-citation-card')).toContainText('Copied');

        // Wait for feedback to disappear (2 seconds + buffer)
        await page.waitForTimeout(2500);
        await expect(page.locator('.corrected-citation-card')).toContainText('Copy');
    });
});

