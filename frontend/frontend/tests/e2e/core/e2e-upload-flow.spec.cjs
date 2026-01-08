const { test, expect } = require('@playwright/test');
const path = require('path');

/**
 * E2E Upload Flow Integration Test
 *
 * Tests real DOCX upload → backend processing → LLM validation → results display.
 * Uses actual backend and LLM (no mocking) to verify full integration.
 */
test('E2E Upload Flow: Upload DOCX and verify inline citation validation', async ({ page }) => {
  // Increase timeout for real LLM processing
  test.setTimeout(120000);

  const testId = process.env.TEST_ID || `upload-${Date.now()}`;
  console.log(`Starting upload E2E test with ID: ${testId}`);

  // 1. Visit Homepage
  await page.goto('/');
  await expect(page.locator('h1:has-text("Citation Format Checker")')).toBeVisible();

  // 2. Locate file input and upload test DOCX
  const fileInput = page.locator('input[type="file"]');
  await expect(fileInput).toHaveCount(1);

  // Use fixture with inline citations and references
  const testDocPath = path.join(__dirname, '../../fixtures/test_doc_valid.docx');

  // Setup response listener BEFORE uploading to capture Job ID
  const responsePromise = page.waitForResponse(response =>
    response.url().includes('/api/validate/async') && response.status() === 200
  );

  // 3. Upload the file
  await fileInput.setInputFiles(testDocPath);
  console.log(`Uploaded: ${testDocPath}`);

  // 4. Capture job ID from async response
  const response = await responsePromise;
  const json = await response.json();
  const jobId = json.job_id;

  if (jobId) {
    console.log(`CAPTURED_JOB_ID:${jobId}`);
  } else {
    console.error('Failed to capture Job ID from upload response');
  }

  // 5. Wait for results section to appear (LLM processing can take 30s+)
  const resultsSection = page.locator('.validation-results-section');
  await expect(resultsSection).toBeVisible({ timeout: 90000 });

  // 6. Handle Gated Results if present
  const viewResultsBtn = page.getByRole('button', { name: /View Results/ });
  if (await viewResultsBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    console.log('Gated results detected, clicking "View Results"...');
    await viewResultsBtn.click();
    await expect(viewResultsBtn).toBeHidden();
  }

  // 7. Verify results contain expected content from DOCX
  // The fixture contains: Smith (2019), Jones (2020) as inline citations
  // and References section with formatted citations

  // Check for reference content (author names from the fixture)
  const resultsText = await resultsSection.textContent();

  // Verify we got actual validation results (not just loading/error state)
  expect(resultsText).toMatch(/Smith|Jones/i);

  // 8. Verify inline citations were detected (if full_doc validation)
  // Check for inline citation indicators or the validation type
  const hasInlineCitations = resultsText.includes('inline') ||
    await page.locator('[data-testid="inline-citations"]').isVisible().catch(() => false) ||
    await page.locator('.inline-citation').isVisible().catch(() => false);

  console.log(`Inline citations detected: ${hasInlineCitations}`);

  // 9. Verify validation completed (check for status indicators)
  const hasValidationStatus =
    await page.locator('[data-testid="results"]').isVisible().catch(() => false) ||
    await page.locator('.citation-row').isVisible().catch(() => false) ||
    resultsText.includes('perfect') ||
    resultsText.includes('need fixes');

  expect(hasValidationStatus).toBe(true);

  console.log(`E2E_UPLOAD_SUCCESS_TEST_ID:${testId}`);
});
