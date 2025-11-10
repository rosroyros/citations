import { test, expect } from '@playwright/test';

test('Debug citation checker error', async ({ page }) => {
  // Capture console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
      console.log('ERROR:', msg.text());
    }
  });

  // Handle uncaught errors
  page.on('pageerror', error => {
    console.log('PAGE ERROR:', error.message);
    console.log('STACK:', error.stack);
  });

  // Navigate to page with mini-checker
  await page.goto('https://citationformatchecker.com/guide/apa-citation-errors/');

  // Wait for mini-checker to load
  await page.waitForSelector('.mini-checker', { timeout: 10000 });

  // Find the first mini-checker
  const miniChecker = page.locator('.mini-checker').first();
  await expect(miniChecker).toBeVisible();

  const textarea = miniChecker.locator('textarea');
  const submitButton = miniChecker.locator('button');
  await expect(textarea).toBeVisible();
  await expect(submitButton).toBeVisible();

  // Test with the problematic citation
  const problematicCitation = `Roedler, R. (2020). Assessment and management of patients with diabetes mellitus. In M. El Hussein, J. Osuji, J. L. Hinkle, & K. H. Cheever (Eds.), Brunner & Suddarth's textbook of medical-surgical nursing (14th ed., pp. 724–753). Wolters Kluwer.`;

  console.log('\n=== Testing with problematic citation ===');
  console.log('Citation:', problematicCitation);

  // Fill the citation
  await textarea.fill(problematicCitation);

  // Click submit and monitor for errors
  const submitPromise = submitButton.click();

  // Wait for either success or error
  try {
    await Promise.race([
      submitPromise,
      page.waitForSelector('.mini-checker-results', { timeout: 30000 }),
      page.waitForTimeout(30000) // Timeout after 30 seconds
    ]);
  } catch (error) {
    console.log('Wait completed or timed out');
  }

  // Check for any JavaScript errors
  console.log('\n=== CONSOLE ERRORS FOUND ===');
  consoleErrors.forEach((error, i) => {
    console.log(`${i + 1}. ${error}`);
    if (error.includes('string did not match') || error.includes('expected pattern')) {
      console.log('🎯 FOUND THE TARGET ERROR!');
    }
  });

  // Look for error dialogs
  const errorDialogs = await page.locator('dialog:visible').count();
  if (errorDialogs > 0) {
    console.log('\n=== ERROR DIALOGS FOUND ===');
    for (let i = 0; i < errorDialogs; i++) {
      const dialog = page.locator('dialog').nth(i);
      const text = await dialog.textContent();
      console.log(`Dialog ${i + 1}:`, text);
    }
  }

  // Look for alert messages
  page.on('dialog', async dialog => {
    console.log('\n=== ALERT DIALOG ===');
    console.log('Message:', dialog.message());
    console.log('Type:', dialog.type());
    await dialog.dismiss();
  });

  // Wait a bit more to catch delayed errors
  await page.waitForTimeout(5000);

  // Take screenshot if we found the target error
  const hasTargetError = consoleErrors.some(error =>
    error.includes('string did not match') || error.includes('expected pattern')
  );

  if (hasTargetError) {
    await page.screenshot({
      path: 'found_string_pattern_error.png',
      fullPage: true
    });
    console.log('\n📸 Screenshot saved: found_string_pattern_error.png');
  }

  console.log('\n=== FINAL ANALYSIS ===');
  console.log(`Total console errors: ${consoleErrors.length}`);
  console.log(`Found target error: ${hasTargetError}`);
});