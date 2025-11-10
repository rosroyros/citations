import { test, expect } from '@playwright/test';

test.describe('Citation Checker Error Debug', () => {
  test('reproduce string pattern matching error', async ({ page }) => {
    // Enable console logging and request/response capturing
    const consoleMessages = [];
    const networkRequests = [];
    const networkResponses = [];

    // Capture console messages
    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      });
      console.log(`[${msg.type()}] ${msg.text()}`);
    });

    // Capture network requests
    page.on('request', request => {
      networkRequests.push({
        url: request.url(),
        method: request.method(),
        headers: request.headers(),
        postData: request.postData()
      });
    });

    // Capture network responses
    page.on('response', response => {
      response.text().then(body => {
        networkResponses.push({
          url: response.url(),
          status: response.status(),
          headers: response.headers(),
          body: body
        });
      });
    });

    // Navigate to a page with mini-checker
    await page.goto('https://citationformatchecker.com/guide/apa-citation-errors/');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Find the first mini-checker
    const miniChecker = page.locator('.mini-checker').first();
    await expect(miniChecker).toBeVisible();

    const textarea = miniChecker.locator('textarea');
    const button = miniChecker.locator('button');

    // Test case 1: Simple citation (control)
    console.log('\n=== Test 1: Simple APA citation ===');
    await textarea.fill('Smith, J. (2023). A simple article title. Journal Name, 10(2), 123-145.');
    await button.click();

    // Wait for response or error
    await page.waitForTimeout(15000);

    // Test case 2: Citation with potential problematic characters
    console.log('\n=== Test 2: Citation with special characters ===');

    // Clear previous results
    const existingResults = miniChecker.locator('.mini-checker-results');
    if (await existingResults.count() > 0) {
      await existingResults.first().remove();
    }

    // Test with various potentially problematic characters
    await textarea.fill(`Roedler, R. (2020). Assessment and management of patients with diabetes mellitus. In M. El Hussein, J. Osuji, J. L. Hinkle, & K. H. Cheever (Eds.), Brunner & Suddarth's textbook of medical-surgical nursing (14th ed., pp. 724–753). Wolters Kluwer.`);
    await button.click();

    // Wait longer for this test
    await page.waitForTimeout(20000);

    // Test case 3: Citation with unicode and potential control characters
    console.log('\n=== Test 3: Citation with unicode ===');

    // Clear results
    if (await existingResults.count() > 0) {
      await existingResults.first().remove();
    }

    await textarea.fill(`García, M. (2023). Café et santé: Une analyse comparative. Revue Médicale Internationale, 45(3), 234–246. https://doi.org/10.1016/j.revimed.2023.01.015`);
    await button.click();

    await page.waitForTimeout(20000);

    // Test case 4: Try with your exact citation that caused the error
    console.log('\n=== Test 4: Exact problematic citation ===');

    // Clear results
    if (await existingResults.count() > 0) {
      await existingResults.first().remove();
    }

    // Use the citation from your logs that showed the issue
    await textarea.fill(`Roedler, R. (2020). Assessment and management of patients with diabetes mellitus. In M. El Hussein, J. Osuji, J. L. Hinkle, & K. H. Cheever (Eds.), Brunner & Suddarth's textbook of medical-surgical nursing (14th ed., pp. 724–753). Wolters Kluwer.`);
    await button.click();

    // Wait and monitor for the error
    await page.waitForTimeout(30000);

    // Analyze results
    console.log('\n=== ANALYSIS ===');

    // Check for error messages
    const errorMessages = consoleMessages.filter(msg =>
      msg.type === 'error' &&
      (msg.text.includes('string did not match') ||
       msg.text.includes('expected pattern') ||
       msg.text.includes('JSON'))
    );

    console.log('\nError messages found:', errorMessages.length);
    errorMessages.forEach((msg, i) => {
      console.log(`${i + 1}. ${msg.text}`);
      console.log(`   Location: ${msg.location.url}:${msg.location.lineNumber}`);
    });

    // Check network requests to /api/validate
    const validateRequests = networkRequests.filter(req => req.url.includes('/api/validate'));
    console.log('\nAPI validate requests:', validateRequests.length);

    validateRequests.forEach((req, i) => {
      console.log(`Request ${i + 1}:`);
      console.log(`  URL: ${req.url}`);
      console.log(`  Method: ${req.method}`);
      console.log(`  Body: ${req.postData}`);
    });

    // Check network responses
    const validateResponses = networkResponses.filter(res => res.url.includes('/api/validate'));
    console.log('\nAPI validate responses:', validateResponses.length);

    validateResponses.forEach((res, i) => {
      console.log(`Response ${i + 1}:`);
      console.log(`  Status: ${res.status}`);
      console.log(`  Content-Type: ${res.headers['content-type']}`);
      console.log(`  Body length: ${res.body.length}`);
      console.log(`  Body preview: ${res.body.substring(0, 200)}...`);

      // Check for problematic characters
      const hasControlChars = /[\x00-\x1F\x7F]/.test(res.body);
      const hasLineSeparators = /[\u2028\u2029]/.test(res.body);
      const hasInvalidUnicode = /[\uFFFE\uFFFF]/.test(res.body);

      console.log(`  Has control characters: ${hasControlChars}`);
      console.log(`  Has line separators: ${hasLineSeparators}`);
      console.log(`  Has invalid unicode: ${hasInvalidUnicode}`);

      if (hasControlChars || hasLineSeparators || hasInvalidUnicode) {
        console.log(`  ⚠️  PROBLEMATIC CHARACTERS DETECTED!`);
        // Show the actual characters
        const problematic = res.body.match(/[\x00-\x1F\x7F\u2028\u2029\uFFFE\uFFFF]/g);
        if (problematic) {
          console.log(`  Characters: ${problematic.map(c => `\\u${c.charCodeAt(0).toString(16).padStart(4, '0')}`).join(', ')}`);
        }
      }
    });

    // Take screenshot if we have errors
    if (errorMessages.length > 0) {
      await page.screenshot({
        path: 'debug_checker_error.png',
        fullPage: true
      });
      console.log('\nScreenshot saved: debug_checker_error.png');
    }

    // Log final console message count
    console.log(`\nTotal console messages: ${consoleMessages.length}`);
    console.log(`Total network requests: ${networkRequests.length}`);
    console.log(`Total network responses: ${networkResponses.length}`);
  });
});