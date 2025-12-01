const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('🔍 Starting dimension analysis...');

    // Navigate to the test server
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // Find the citation input area and submit a single citation
    console.log('📝 Submitting single citation...');

    // Wait for the editor to be ready
    await page.waitForSelector('.ProseMirror', { timeout: 10000 });

    // Type a single citation
    await page.fill('.ProseMirror', 'Smith, J. (2023). Test citation for validation. Journal of Testing, 15(3), 123-145.');

    // Submit for validation
    await page.click('button[type="submit"]');

    // Wait for validation to complete and gated overlay to appear
    console.log('⏳ Waiting for validation results...');
    await page.waitForSelector('[data-testid="gated-results"]', { timeout: 30000 });
    await page.waitForTimeout(2000); // Ensure overlay is fully rendered

    // Get validation table dimensions
    const validationTable = await page.locator('.validation-table-container').first();
    const tableBox = await validationTable.boundingBox();
    console.log('\n📊 VALIDATION TABLE DIMENSIONS:');
    console.log(`Width: ${tableBox.width}px`);
    console.log(`Height: ${tableBox.height}px`);
    console.log(`Top: ${tableBox.y}px`);
    console.log(`Left: ${tableBox.x}px`);

    // Get validation table CSS properties
    const tableCSS = await validationTable.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        minHeight: styles.minHeight,
        maxHeight: styles.maxHeight,
        height: styles.height,
        width: styles.width,
        maxWidth: styles.maxWidth,
        position: styles.position,
        display: styles.display
      };
    });
    console.log('\n🎨 VALIDATION TABLE CSS:');
    console.log(`min-height: ${tableCSS.minHeight}`);
    console.log(`height: ${tableCSS.height}`);
    console.log(`width: ${tableCSS.width}`);
    console.log(`max-width: ${tableCSS.maxWidth}`);
    console.log(`position: ${tableCSS.position}`);

    // Get gated overlay dimensions
    const gatedOverlay = await page.locator('[data-testid="gated-results"]').first();
    const overlayBox = await gatedOverlay.boundingBox();
    console.log('\n🔒 GATED OVERLAY DIMENSIONS:');
    console.log(`Width: ${overlayBox.width}px`);
    console.log(`Height: ${overlayBox.height}px`);
    console.log(`Top: ${overlayBox.y}px`);
    console.log(`Left: ${overlayBox.x}px`);

    // Get overlay content dimensions
    const overlayContent = await page.locator('.gated-overlay-content').first();
    const contentBox = await overlayContent.boundingBox();
    console.log('\n💎 OVERLAY CONTENT DIMENSIONS:');
    console.log(`Width: ${contentBox.width}px`);
    console.log(`Height: ${contentBox.height}px`);

    // Get overlay content CSS properties
    const contentCSS = await overlayContent.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        width: styles.width,
        maxWidth: styles.maxWidth,
        minWidth: styles.minWidth,
        height: styles.height,
        maxHeight: styles.maxHeight,
        minHeight: styles.minHeight,
        padding: styles.padding,
        position: styles.position,
        display: styles.display
      };
    });
    console.log('\n🎨 OVERLAY CONTENT CSS:');
    console.log(`width: ${contentCSS.width}`);
    console.log(`max-width: ${contentCSS.maxWidth}`);
    console.log(`height: ${contentCSS.height}`);
    console.log(`padding: ${contentCSS.padding}`);

    // Compare dimensions
    console.log('\n📏 DIMENSION COMPARISON:');
    console.log(`Table height: ${tableBox.height}px`);
    console.log(`Overlay height: ${overlayBox.height}px`);
    console.log(`Content height: ${contentBox.height}px`);

    if (overlayBox.height > tableBox.height) {
      console.log(`❌ OVERLAY IS TALLER: ${overlayBox.height - tableBox.height}px difference`);
    } else {
      console.log(`✅ Overlay fits within table bounds`);
    }

    // Take a screenshot for visual reference
    await page.screenshot({
      path: 'dimension-analysis.png',
      fullPage: false,
      clip: {
        x: Math.min(tableBox.x, overlayBox.x) - 20,
        y: Math.min(tableBox.y, overlayBox.y) - 20,
        width: Math.max(tableBox.width, overlayBox.width) + 40,
        height: Math.max(tableBox.height, overlayBox.height) + 40
      }
    });
    console.log('\n📸 Screenshot saved as dimension-analysis.png');

  } catch (error) {
    console.error('❌ Error during analysis:', error);
  } finally {
    await browser.close();
  }
})();