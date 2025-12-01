const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('🔍 Testing Landscape 1 variant...');

    // Navigate to the test server with landscape1 variant
    await page.goto('http://localhost:5175');
    await page.waitForLoadState('networkidle');

    // Find the citation input area and submit a single citation
    console.log('📝 Submitting single citation for Landscape 1 test...');

    // Wait for the editor to be ready
    await page.waitForSelector('.ProseMirror', { timeout: 10000 });

    // Type a single citation
    await page.fill('.ProseMirror', 'Smith, J. (2023). Test citation for validation. Journal of Testing, 15(3), 123-145.');

    // Submit for validation
    await page.click('button[type="submit"]');

    // Wait for validation to complete and gated overlay to appear
    console.log('⏳ Waiting for Landscape 1 validation results...');
    await page.waitForSelector('[data-testid="gated-results"]', { timeout: 30000 });
    await page.waitForTimeout(2000); // Ensure overlay is fully rendered

    // Check if landscape1 variant is applied
    const overlay = await page.locator('[data-testid="gated-results"]').first();
    const hasLandscapeClass = await overlay.evaluate(el => {
      return el.classList.contains('gated-variant-landscape1');
    });

    if (hasLandscapeClass) {
      console.log('✅ Landscape 1 variant class applied correctly');
    } else {
      console.log('❌ Landscape 1 variant class not found');
      const classes = await overlay.evaluate(el => Array.from(el.classList));
      console.log('Classes found:', classes);
    }

    // Get overlay content dimensions for landscape 1
    const overlayContent = await page.locator('.gated-overlay-content').first();
    const contentBox = await overlayContent.boundingBox();
    console.log('\n📊 LANDSCAPE 1 DIMENSIONS:');
    console.log(`Content Width: ${contentBox.width}px`);
    console.log(`Content Height: ${contentBox.height}px`);

    // Check for horizontal layout
    const contentDisplay = await overlayContent.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        display: styles.display,
        flexDirection: styles.flexDirection,
        gap: styles.gap
      };
    });
    console.log('\n🎨 LAYOUT PROPERTIES:');
    console.log(`Display: ${contentDisplay.display}`);
    console.log(`Flex Direction: ${contentDisplay.flexDirection}`);
    console.log(`Gap: ${contentDisplay.gap}`);

    // Check completion indicator layout
    const completionIndicator = await page.locator('.completion-indicator').first();
    const indicatorLayout = await completionIndicator.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        display: styles.display,
        flexDirection: styles.flexDirection,
        alignItems: styles.alignItems
      };
    });
    console.log('\n🏗️ COMPLETION INDICATOR:');
    console.log(`Layout: ${indicatorLayout.display}`);
    console.log(`Direction: ${indicatorLayout.flexDirection}`);
    console.log(`Align: ${indicatorLayout.alignItems}`);

    // Verify button is on the right side
    const revealButton = await page.locator('.reveal-button').first();
    const buttonPosition = await revealButton.evaluate(el => {
      const rect = el.getBoundingClientRect();
      const containerRect = el.closest('.gated-overlay-content').getBoundingClientRect();
      return {
        buttonRight: rect.right,
        containerRight: containerRect.right,
        isOnRight: rect.right > (containerRect.left + containerRect.width * 0.7)
      };
    });
    console.log('\n🎯 BUTTON POSITION:');
    console.log(`Button positioned on right side: ${buttonPosition.isOnRight}`);

    // Take a screenshot for visual verification
    await page.screenshot({
      path: 'landscape1-test.png',
      fullPage: false,
      clip: {
        x: contentBox.x - 20,
        y: contentBox.y - 20,
        width: contentBox.width + 40,
        height: contentBox.height + 40
      }
    });
    console.log('\n📸 Screenshot saved as landscape1-test.png');

    console.log('\n✅ Landscape 1 variant test complete!');
    console.log('🌐 View at: http://localhost:5175/');

  } catch (error) {
    console.error('❌ Error during Landscape 1 test:', error);
  } finally {
    await browser.close();
  }
})();