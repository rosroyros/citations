const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('🔍 Visual comparison test...');

    // Navigate to test server with glassmorphism variant
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // Submit a single citation for validation
    console.log('📝 Submitting citation...');
    await page.waitForSelector('.ProseMirror', { timeout: 10000 });
    await page.fill('.ProseMirror', 'Smith, J. (2023). Test citation for validation. Journal of Testing, 15(3), 123-145.');
    await page.click('button[type="submit"]');

    // Wait for validation and overlay
    console.log('⏳ Waiting for gated overlay...');
    await page.waitForSelector('[data-testid="gated-results"]', { timeout: 30000 });
    await page.waitForTimeout(2000);

    // Get visual properties of the overlay content
    const overlayContent = await page.locator('.gated-overlay-content').first();
    const contentStyles = await overlayContent.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        background: styles.background,
        backdropFilter: styles.backdropFilter,
        WebkitBackdropFilter: styles.webkitBackdropFilter,
        border: styles.border,
        borderRadius: styles.borderRadius,
        boxShadow: styles.boxShadow,
        padding: styles.padding,
        width: styles.width,
        maxWidth: styles.maxWidth,
        height: styles.height,
        maxHeight: styles.maxHeight,
        display: styles.display,
        flexDirection: styles.flexDirection,
        gap: styles.gap
      };
    });

    console.log('\n🎨 OVERLAY CONTENT VISUAL PROPERTIES:');
    console.log(`Background: ${contentStyles.background}`);
    console.log(`Backdrop Filter: ${contentStyles.backdropFilter}`);
    console.log(`Border: ${contentStyles.border}`);
    console.log(`Border Radius: ${contentStyles.borderRadius}`);
    console.log(`Box Shadow: ${contentStyles.boxShadow}`);
    console.log(`Padding: ${contentStyles.padding}`);
    console.log(`Width: ${contentStyles.width}`);
    console.log(`Max Width: ${contentStyles.maxWidth}`);
    console.log(`Display: ${contentStyles.display}`);
    console.log(`Flex Direction: ${contentStyles.flexDirection}`);
    console.log(`Gap: ${contentStyles.gap}`);

    // Get completion title styles
    const completionTitle = await page.locator('.completion-title').first();
    const titleStyles = await completionTitle.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        color: styles.color,
        fontFamily: styles.fontFamily,
        fontSize: styles.fontSize,
        fontWeight: styles.fontWeight,
        lineHeight: styles.lineHeight,
        margin: styles.margin,
        textAlign: styles.textAlign
      };
    });

    console.log('\n📝 COMPLETION TITLE STYLES:');
    console.log(`Color: ${titleStyles.color}`);
    console.log(`Font Family: ${titleStyles.fontFamily}`);
    console.log(`Font Size: ${titleStyles.fontSize}`);
    console.log(`Font Weight: ${titleStyles.fontWeight}`);
    console.log(`Line Height: ${titleStyles.lineHeight}`);
    console.log(`Margin: ${titleStyles.margin}`);
    console.log(`Text Align: ${titleStyles.textAlign}`);

    // Get completion summary styles
    const resultsSummary = await page.locator('.results-summary').first();
    const summaryStyles = await resultsSummary.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        color: styles.color,
        fontSize: styles.fontSize,
        fontFamily: styles.fontFamily,
        marginBottom: styles.marginBottom
      };
    });

    console.log('\n📊 RESULTS SUMMARY STYLES:');
    console.log(`Color: ${summaryStyles.color}`);
    console.log(`Font Size: ${summaryStyles.fontSize}`);
    console.log(`Font Family: ${summaryStyles.fontFamily}`);
    console.log(`Margin Bottom: ${summaryStyles.marginBottom}`);

    // Get reveal button styles
    const revealButton = await page.locator('.reveal-button').first();
    const buttonStyles = await revealButton.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        background: styles.background,
        color: styles.color,
        padding: styles.padding,
        borderRadius: styles.borderRadius,
        fontSize: styles.fontSize,
        fontWeight: styles.fontWeight,
        fontFamily: styles.fontFamily,
        minHeight: styles.minHeight,
        boxShadow: styles.boxShadow,
        border: styles.border
      };
    });

    console.log('\n🎯 REVEAL BUTTON STYLES:');
    console.log(`Background: ${buttonStyles.background}`);
    console.log(`Color: ${buttonStyles.color}`);
    console.log(`Padding: ${buttonStyles.padding}`);
    console.log(`Border Radius: ${buttonStyles.borderRadius}`);
    console.log(`Font Size: ${buttonStyles.fontSize}`);
    console.log(`Font Weight: ${buttonStyles.fontWeight}`);
    console.log(`Font Family: ${buttonStyles.fontFamily}`);
    console.log(`Min Height: ${buttonStyles.minHeight}`);
    console.log(`Box Shadow: ${buttonStyles.boxShadow}`);
    console.log(`Border: ${buttonStyles.border}`);

    // Get completion icon styles
    const completionIcon = await page.locator('.completion-icon').first();
    const iconStyles = await completionIcon.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        background: styles.background,
        color: styles.color,
        width: styles.width,
        height: styles.height,
        borderRadius: styles.borderRadius,
        boxShadow: styles.boxShadow
      };
    });

    console.log('\n✅ COMPLETION ICON STYLES:');
    console.log(`Background: ${iconStyles.background}`);
    console.log(`Color: ${iconStyles.color}`);
    console.log(`Width: ${iconStyles.width}`);
    console.log(`Height: ${iconStyles.height}`);
    console.log(`Border Radius: ${iconStyles.borderRadius}`);
    console.log(`Box Shadow: ${iconStyles.boxShadow}`);

    console.log('\n✅ Visual comparison complete!');

  } catch (error) {
    console.error('❌ Error during visual comparison:', error);
  } finally {
    await browser.close();
  }
})();