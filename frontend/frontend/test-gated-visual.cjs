const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('Opening test server...');
    await page.goto('http://localhost:5174');

    // Wait for page to load
    await page.waitForTimeout(5000);

    console.log('Taking screenshot of current implementation...');
    await page.screenshot({
      path: 'test-screenshots/current-gated-results.png',
      fullPage: true
    });

    // Test overlay dimensions
    const overlay = await page.locator('[data-testid="gated-results"]').first();
    if (await overlay.isVisible()) {
      const overlayBox = await overlay.boundingBox();
      console.log('Overlay dimensions:', overlayBox);

      const backdrop = await page.locator('.gated-overlay-backdrop').first();
      const backdropBox = await backdrop.boundingBox();
      console.log('Backdrop dimensions:', backdropBox);

      const content = await page.locator('.gated-overlay-content').first();
      const contentBox = await content.boundingBox();
      console.log('Content dimensions:', contentBox);
    } else {
      console.log('Gated results overlay not found or not visible');
    }

    // Test with different viewport sizes
    console.log('Testing mobile viewport...');
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: 'test-screenshots/mobile-gated-results.png',
      fullPage: false
    });

    console.log('Testing tablet viewport...');
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(1000);
    await page.screenshot({
      path: 'test-screenshots/tablet-gated-results.png',
      fullPage: false
    });

    await page.setViewportSize({ width: 1200, height: 800 });
    await page.waitForTimeout(1000);

  } catch (error) {
    console.error('Error during testing:', error);
  } finally {
    await browser.close();
    console.log('Testing complete. Check test-screenshots/ directory.');
  }
})();