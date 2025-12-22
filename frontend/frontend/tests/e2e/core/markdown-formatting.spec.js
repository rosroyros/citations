import { test, expect } from '@playwright/test';

test.describe('Markdown Formatting in Validation Table', () => {
  test('should display **bold** and _italic_ formatting correctly in validation results', async ({ page }) => {
    // Navigate to the citation checker
    await page.goto('http://localhost:5173');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Fill in citations with markdown formatting
    await page.fill('textarea', `Smith, J. (2020). **Journal of Testing**, 15(2), 123-145.
Brown, A. (2021). _Academic Press_, New York.
Wilson, K. (2019). Mixed **bold** and _italic_ formatting.`);

    // Submit the form
    await page.click('button[type="submit"]');

    // Wait for validation results to load
    await page.waitForSelector('.validation-table, .results-container, .result-row', { timeout: 15000 });

    // Check that markdown formatting is converted to HTML
    const content = await page.content();

    // Verify bold formatting is converted to <strong>
    expect(content).toContain('<strong>Journal of Testing</strong>');
    expect(content).toContain('<strong>bold</strong>');

    // Verify italic formatting is converted to <em>
    expect(content).toContain('<em>Academic Press</em>');
    expect(content).toContain('<em>italic</em>');

    // Verify raw markdown markers are NOT present
    expect(content).not.toContain('**Journal of Testing**');
    expect(content).not.toContain('_Academic Press_');
    expect(content).not.toContain('**bold**');
    expect(content).not.toContain('_italic_');

    // Test specific validation table content
    const tableContent = await page.locator('.validation-table').textContent();
    console.log('Table content:', tableContent);

    // The table should show properly formatted text, not markdown
    expect(tableContent).toContain('Journal of Testing'); // Should be there, formatted
    expect(tableContent).toContain('Academic Press');   // Should be there, formatted
  });

  test('should handle complex nested markdown formatting', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Test complex nested formatting
    await page.fill('textarea', `Davis, M. (2022). **_Complex nested formatting_** in citation.`);

    await page.click('button[type="submit"]');
    await page.waitForSelector('.validation-table, .results-container', { timeout: 15000 });

    const content = await page.content();

    // Nested formatting should be properly converted
    expect(content).toContain('<strong><em>Complex nested formatting</em></strong>');
    expect(content).not.toContain('**_Complex nested formatting_**');
  });
});