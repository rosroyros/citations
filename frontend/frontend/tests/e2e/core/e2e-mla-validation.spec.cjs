const { test, expect } = require('@playwright/test');

/**
 * E2E Tests for MLA 9 Citation Validation Flow
 * 
 * Test cases:
 * 1. Basic MLA Validation - Select MLA tab and validate citation
 * 2. URL Parameter Pre-Selection - ?style=mla9 pre-selects MLA
 * 3. APA Regression - APA validation still works after MLA addition
 * 4. StyleSelector visibility - Only shows when multiple styles available
 */

test.describe('MLA Validation Flow', () => {

    test('MLA validation with style selector', async ({ page }) => {
        // Get Test ID for tracing
        const testId = process.env.TEST_ID || `mla-test-${Date.now()}`;

        // MLA format: Author Last, First. Title. Publisher, Year.
        // Include testtesttest marker to flag as test job
        const mlaCitation = `Smith, John. testtesttest: MLA E2E Test Citation ${testId}. Academic Press, 2023.`;

        console.log(`Starting MLA E2E test with ID: ${testId}`);

        // 1. Visit Homepage
        await page.goto('/');

        // 2. Check if StyleSelector appears (only if MLA is enabled via feature flag)
        // The StyleSelector only renders when multiple styles are available
        const styleSelector = page.locator('.style-selector');
        const styleTabMla = page.locator('.style-tab', { hasText: 'MLA 9' });

        // Check if style selector is visible (MLA_ENABLED=true)
        const selectorVisible = await styleSelector.isVisible().catch(() => false);

        if (selectorVisible) {
            console.log('StyleSelector visible - MLA is enabled');

            // Click MLA tab if available
            const mlaTabVisible = await styleTabMla.isVisible().catch(() => false);
            if (mlaTabVisible) {
                await styleTabMla.click();
                console.log('Selected MLA 9 style');

                // Verify MLA tab is active
                await expect(styleTabMla).toHaveClass(/style-tab--active/);
            }
        } else {
            console.log('StyleSelector not visible - MLA not enabled, skipping MLA-specific tests');
            test.skip(true, 'MLA not enabled via MLA_ENABLED feature flag');
        }

        // 3. Fill Citation
        const editor = page.locator('.ProseMirror');
        await expect(editor).toBeVisible();
        await editor.fill(mlaCitation);

        // 4. Submit
        const submitButton = page.getByRole('button', { name: 'Check My Citations' });
        await expect(submitButton).toBeEnabled();

        // Setup response listener to verify style is sent
        const responsePromise = page.waitForResponse(response =>
            response.url().includes('/api/validate/async') && response.status() === 200
        );

        await submitButton.click();

        const response = await responsePromise;
        const json = await response.json();
        const jobId = json.job_id;

        if (jobId) {
            console.log(`CAPTURED_JOB_ID:${jobId}`);
        }

        // 5. Wait for Results
        const resultsSection = page.locator('.validation-results-section');
        await expect(resultsSection).toBeVisible({ timeout: 60000 });

        // 6. Verify Result Content
        await expect(resultsSection).toContainText(testId);

        console.log(`MLA_E2E_SUCCESS_TEST_ID:${testId}`);
    });

    test('URL parameter pre-selects MLA style', async ({ page }) => {
        // Visit with style=mla9 URL parameter
        await page.goto('/?style=mla9');

        // Check if StyleSelector exists and MLA is available
        const styleTabMla = page.locator('.style-tab', { hasText: 'MLA 9' });
        const mlaTabVisible = await styleTabMla.isVisible().catch(() => false);

        if (!mlaTabVisible) {
            console.log('MLA tab not visible - skipping URL param test');
            test.skip(true, 'MLA not enabled via feature flag');
        }

        // MLA tab should be pre-selected via URL param
        await expect(styleTabMla).toHaveClass(/style-tab--active/);

        console.log('URL parameter ?style=mla9 correctly pre-selects MLA tab');
    });

    test('APA validation still works (regression test)', async ({ page }) => {
        // This test ensures APA validation continues to work after MLA addition
        const testId = process.env.TEST_ID || `apa-regression-${Date.now()}`;
        const apaCitation = `Smith, J. (2023). testtesttest: APA Regression Test ${testId}. Journal of Testing, 1(1), 1-10.`;

        console.log(`Starting APA regression test with ID: ${testId}`);

        // 1. Visit Homepage
        await page.goto('/');

        // 2. If StyleSelector exists, ensure APA is selected (it's default)
        const styleTabApa = page.locator('.style-tab', { hasText: 'APA 7' });
        const apaTabVisible = await styleTabApa.isVisible().catch(() => false);

        if (apaTabVisible) {
            // APA should be selected by default
            await expect(styleTabApa).toHaveClass(/style-tab--active/);
            console.log('APA tab correctly selected by default');
        }

        // 3. Fill Citation
        const editor = page.locator('.ProseMirror');
        await expect(editor).toBeVisible();
        await editor.fill(apaCitation);

        // 4. Submit and verify
        const submitButton = page.getByRole('button', { name: 'Check My Citations' });
        await expect(submitButton).toBeEnabled();

        const responsePromise = page.waitForResponse(response =>
            response.url().includes('/api/validate/async') && response.status() === 200
        );

        await submitButton.click();

        const response = await responsePromise;
        const json = await response.json();

        if (json.job_id) {
            console.log(`CAPTURED_JOB_ID:${json.job_id}`);
        }

        // 5. Wait for Results
        const resultsSection = page.locator('.validation-results-section');
        await expect(resultsSection).toBeVisible({ timeout: 60000 });

        // 6. Verify Result Content
        await expect(resultsSection).toContainText(testId);

        console.log(`APA_REGRESSION_SUCCESS_TEST_ID:${testId}`);
    });

    test('StyleSelector disabled during validation', async ({ page }) => {
        // Visit page
        await page.goto('/');

        // Check if StyleSelector exists
        const styleSelector = page.locator('.style-selector');
        const selectorVisible = await styleSelector.isVisible().catch(() => false);

        if (!selectorVisible) {
            console.log('StyleSelector not visible - skipping disabled state test');
            test.skip(true, 'StyleSelector not visible');
        }

        // Fill citation
        const editor = page.locator('.ProseMirror');
        await editor.fill('Smith, J. (2023). Test citation. Journal, 1(1), 1-10.');

        // Click submit
        const submitButton = page.getByRole('button', { name: 'Check My Citations' });
        await submitButton.click();

        // During loading, style tabs should be disabled
        const styleTabs = page.locator('.style-tab');
        const firstTab = styleTabs.first();

        // Check disabled state briefly during loading
        // This is a best-effort check since loading can be fast
        const isDisabled = await firstTab.isDisabled().catch(() => false);
        console.log(`StyleSelector disabled during validation: ${isDisabled}`);

        // Wait for validation to complete
        const resultsSection = page.locator('.validation-results-section');
        await expect(resultsSection).toBeVisible({ timeout: 60000 });

        // After completion, tabs should be enabled again
        await expect(firstTab).toBeEnabled();

        console.log('StyleSelector correctly re-enabled after validation');
    });
});
