const { chromium } = require('playwright');

async function debugPage() {
    console.log('🔍 Debugging the page content...');

    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    try {
        console.log('📍 Opening http://localhost:5173/');
        await page.goto('http://localhost:5173/', {
            waitUntil: 'networkidle',
            timeout: 30000
        });

        // Wait for page to load
        await page.waitForTimeout(5000);

        // Get page title
        const title = await page.title();
        console.log('📄 Page title:', title);

        // Check for all interactive elements
        const textareas = await page.$$eval('textarea', els => els.length);
        const buttons = await page.$$eval('button', els => els.length);
        const inputs = await page.$$eval('input', els => els.length);
        const forms = await page.$$eval('form', els => els.length);

        console.log('📊 Found elements:');
        console.log('- Textareas:', textareas);
        console.log('- Buttons:', buttons);
        console.log('- Inputs:', inputs);
        console.log('- Forms:', forms);

        // Look for any elements with common selectors
        const selectors = [
            'textarea',
            'button[type="submit"]',
            'button',
            'form',
            '[data-testid]',
            '.citation-input',
            '#citations',
            'input[type="text"]'
        ];

        for (const selector of selectors) {
            try {
                const count = await page.$$eval(selector, els => els.length);
                if (count > 0) {
                    console.log(`✅ Found ${count} elements with selector: ${selector}`);
                }
            } catch (e) {
                // Selector not found, continue
            }
        }

        // Take a screenshot
        await page.screenshot({ path: 'debug-page.png', fullPage: true });
        console.log('📸 Screenshot saved as debug-page.png');

        // Get page content
        const content = await page.content();
        console.log('📄 Page content length:', content.length, 'characters');

    } catch (error) {
        console.error('❌ Debug failed with error:', error);
    } finally {
        // Keep browser open for manual inspection
        console.log('🔄 Keeping browser open for 30 seconds for manual inspection...');
        await page.waitForTimeout(30000);
        await browser.close();
    }
}

debugPage();