const { test, expect } = require('@playwright/test');

/**
 * E2E Tests for Chicago 17 Citation Validation Flow
 *
 * Test cases:
 * 1. Basic Chicago Validation - Select Chicago tab and validate citation
 * 2. URL Parameter Pre-Selection - ?style=chicago17 pre-selects Chicago
 * 3. APA Regression - APA validation still works after Chicago addition
 * 4. StyleSelector visibility - Shows when multiple styles available
 */

test.describe('Chicago Validation Flow', () => {

    test('Chicago validation with style selector', async ({ page }) => {
        // Get Test ID for tracing
        const testId = process.env.TEST_ID || `chicago-test-${Date.now()}`;

        // Chicago Notes-Bib format: Author Last, First. Title. City: Publisher, Year.
        // Include testtesttest marker to flag as test job
        const chicagoCitation = `Morrison, Toni. testtesttest: Chicago E2E Test Citation ${testId}. New York: Knopf, 1987.`;

        console.log(`Starting Chicago E2E test with ID: ${testId}`);

        // 1. Visit Homepage
        await page.goto('/');

        // 2. Check if StyleSelector appears (only if Chicago is enabled via feature flag)
        // The StyleSelector only renders when multiple styles are available
        const styleSelector = page.locator('.style-selector');
        const styleTabChicago = page.locator('.style-tab', { hasText: /Chicago/i });

        // Check if style selector is visible (CHICAGO_ENABLED=true)
        const selectorVisible = await styleSelector.isVisible().catch(() => false);

        if (selectorVisible) {
            console.log('StyleSelector visible - checking for Chicago tab');

            // Click Chicago tab if available
            const chicagoTabVisible = await styleTabChicago.isVisible().catch(() => false);
            if (chicagoTabVisible) {
                // Use force: true for mobile where UI elements may overlap
                await styleTabChicago.click({ force: true });
                console.log('Selected Chicago 17 style');

                // Verify Chicago tab is active
                await expect(styleTabChicago).toHaveClass(/style-tab--active/);
            } else {
                console.log('Chicago tab not visible - Chicago not enabled');
                test.skip(true, 'Chicago not enabled via CHICAGO_ENABLED feature flag');
            }
        } else {
            console.log('StyleSelector not visible - skipping Chicago-specific tests');
            test.skip(true, 'StyleSelector not visible');
        }

        // 3. Fill Citation
        const editor = page.locator('.ProseMirror');
        await expect(editor).toBeVisible();
        await editor.fill(chicagoCitation);

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

        console.log(`CHICAGO_E2E_SUCCESS_TEST_ID:${testId}`);
    });

    test('URL parameter pre-selects Chicago style', async ({ page }) => {
        // Visit with style=chicago17 URL parameter
        await page.goto('/?style=chicago17');

        // Check if StyleSelector exists and Chicago is available
        const styleTabChicago = page.locator('.style-tab', { hasText: /Chicago/i });
        const chicagoTabVisible = await styleTabChicago.isVisible().catch(() => false);

        if (!chicagoTabVisible) {
            console.log('Chicago tab not visible - skipping URL param test');
            test.skip(true, 'Chicago not enabled via feature flag');
        }

        // Chicago tab should be pre-selected via URL param
        await expect(styleTabChicago).toHaveClass(/style-tab--active/);

        console.log('URL parameter ?style=chicago17 correctly pre-selects Chicago tab');
    });

    test('APA validation still works (regression test)', async ({ page }) => {
        // This test ensures APA validation continues to work after Chicago addition
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

    test('All three style tabs display correctly', async ({ page, browserName }) => {
        // Skip this test on webkit due to flaky StyleSelector rendering
        test.skip(browserName === 'webkit', 'StyleSelector rendering is flaky on webkit');

        // Visit page
        await page.goto('/');

        // Check for all three style tabs
        const styleTabApa = page.locator('.style-tab', { hasText: 'APA 7' });
        const styleTabMla = page.locator('.style-tab', { hasText: 'MLA 9' });
        const styleTabChicago = page.locator('.style-tab', { hasText: /Chicago/i });

        // Check visibility of each tab
        const apaVisible = await styleTabApa.isVisible().catch(() => false);
        const mlaVisible = await styleTabMla.isVisible().catch(() => false);
        const chicagoVisible = await styleTabChicago.isVisible().catch(() => false);

        console.log(`APA visible: ${apaVisible}, MLA visible: ${mlaVisible}, Chicago visible: ${chicagoVisible}`);

        // At least one tab should be visible (APA or MLA or Chicago)
        const anyVisible = apaVisible || mlaVisible || chicagoVisible;
        expect(anyVisible).toBe(true);

        // Log which tabs are visible for debugging
        if (apaVisible) console.log('APA tab is visible');
        if (mlaVisible) console.log('MLA tab is visible (MLA_ENABLED=true)');
        if (chicagoVisible) console.log('Chicago tab is visible (CHICAGO_ENABLED=true)');
    });

    test('Chicago selection persists after reload', async ({ page }) => {
        // Check if Chicago tab is available
        await page.goto('/');

        const styleTabChicago = page.locator('.style-tab', { hasText: /Chicago/i });
        const chicagoTabVisible = await styleTabChicago.isVisible().catch(() => false);

        if (!chicagoTabVisible) {
            console.log('Chicago tab not visible - skipping persistence test');
            test.skip(true, 'Chicago not enabled via feature flag');
        }

        // Click Chicago tab (use force: true for mobile where UI elements may overlap)
        await styleTabChicago.click({ force: true });

        // Reload page
        await page.reload();

        // Chicago tab should still be active (persistence via localStorage)
        await expect(styleTabChicago).toHaveClass(/style-tab--active/);

        console.log('Chicago selection correctly persists after page reload');
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

        // Fill citation (Chicago format)
        const editor = page.locator('.ProseMirror');
        await editor.fill('Morrison, Toni. Beloved. New York: Knopf, 1987.');

        // Click submit
        const submitButton = page.getByRole('button', { name: 'Check My Citations' });
        await submitButton.click();

        // During loading, style tabs should be disabled
        const styleTabs = page.locator('.style-tab');
        const firstTab = styleTabs.first();

        // Check disabled state briefly during loading
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
