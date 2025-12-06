const { test, expect } = require('@playwright/test');

test('E2E Full Flow: Submit unique citation and verify completion', async ({ page }) => {
  // 1. Get Test ID from env
  const testId = process.env.TEST_ID || `test-${Date.now()}`;
  // We use a unique pattern that the backend verifier can easily search for
  const uniqueCitation = `Smith, J. (2023). E2E Test Citation ${testId}. Journal of Testing, 1(1), 1-10.`;

  console.log(`Starting E2E test with ID: ${testId}`);

  // 2. Visit Homepage
  await page.goto('/');

  // 3. Fill Citation
  // Tiptap editor usually uses .ProseMirror class
  const editor = page.locator('.ProseMirror');
  await expect(editor).toBeVisible();
  await editor.fill(uniqueCitation);

  // 4. Submit
  // Wait for button to be enabled (in case there's initial loading)
  const submitButton = page.getByRole('button', { name: 'Check My Citations' });
  await expect(submitButton).toBeEnabled();

  // Setup response listener BEFORE clicking submit to capture Job ID
  // We listen for either sync or async endpoint
  const responsePromise = page.waitForResponse(response => 
    (response.url().includes('/api/validate') || response.url().includes('/api/validate/async')) 
    && response.status() === 200
  );

  await submitButton.click();

  const response = await responsePromise;
  const json = await response.json();
  // Extract Job ID from response (supports both sync and async patterns)
  const jobId = json.job_id;
  
  if (jobId) {
      console.log(`CAPTURED_JOB_ID:${jobId}`);
  } else {
      console.error('Failed to capture Job ID from API response');
  }

  // 5. Wait for Results
  // The processing might take 10-20s, so we increase the timeout
  // We wait for the results section to appear
  const resultsSection = page.locator('.validation-results-section');
  await expect(resultsSection).toBeVisible({ timeout: 60000 });

  // 6. Verify Result Content
  // Check if the unique text is present in the results table (original citation column)
  // We check for the testId specifically
  await expect(resultsSection).toContainText(testId);
  
  console.log(`E2E_SUCCESS_TEST_ID:${testId}`);
});
