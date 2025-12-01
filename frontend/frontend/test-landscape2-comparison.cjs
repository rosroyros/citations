const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('🔍 Testing Landscape 2 Implementation - Final Verification');

    // Test the updated implementation
    console.log('\n📊 TESTING UPDATED IMPLEMENTATION...');
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // Submit a citation to trigger the gated overlay
    await page.waitForSelector('.ProseMirror', { timeout: 10000 });
    await page.fill('.ProseMirror', 'Smith, J. (2023). Test citation for validation. Journal of Testing, 15(3), 123-145.');
    await page.click('button[type="submit"]');

    // Wait for gated overlay to appear
    await page.waitForSelector('[data-testid="gated-results"]', { timeout: 30000 });
    await page.waitForTimeout(2000);

    // Get the main container properties
    const containerProps = await page.locator('.gated-overlay-content').first().evaluate(el => {
      const styles = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();

      return {
        // Layout properties
        display: styles.display,
        flexDirection: styles.flexDirection,
        alignItems: styles.alignItems,
        justifyContent: styles.justifyContent,

        // Dimensions
        width: styles.width,
        maxWidth: styles.maxWidth,
        actualWidth: rect.width + 'px',
        actualHeight: rect.height + 'px',

        // Spacing
        padding: styles.padding,

        // Visual
        background: styles.background,
        backdropFilter: styles.backdropFilter,
        borderRadius: styles.borderRadius,
        animation: styles.animation,

        // Structure
        childCount: el.children.length
      };
    });

    console.log('\n📋 CONTAINER PROPERTIES:');
    console.log(JSON.stringify(containerProps, null, 2));

    // Check the left section (completion indicator)
    const leftSection = await page.locator('.completion-indicator').first().evaluate(el => {
      const styles = window.getComputedStyle(el);

      return {
        display: styles.display,
        flexDirection: styles.flexDirection,
        alignItems: styles.alignItems,
        textAlign: styles.textAlign,
        gap: styles.gap,
        borderRight: styles.borderRight,
        paddingRight: styles.paddingRight
      };
    });

    console.log('\n📋 LEFT SECTION PROPERTIES:');
    console.log(JSON.stringify(leftSection, null, 2));

    // Check the right section (summary)
    const rightSection = await page.locator('.completion-summary').first().evaluate(el => {
      const styles = window.getComputedStyle(el);

      return {
        display: styles.display,
        flexDirection: styles.flexDirection,
        alignItems: styles.alignItems,
        textAlign: styles.textAlign,
        gap: styles.gap,
        paddingLeft: styles.paddingLeft
      };
    });

    console.log('\n📋 RIGHT SECTION PROPERTIES:');
    console.log(JSON.stringify(rightSection, null, 2));

    // Check the icon
    const icon = await page.locator('.completion-icon').first().evaluate(el => {
      const styles = window.getComputedStyle(el);

      return {
        width: styles.width,
        height: styles.height,
        fontSize: styles.fontSize,
        borderRadius: styles.borderRadius
      };
    });

    console.log('\n📋 ICON PROPERTIES:');
    console.log(JSON.stringify(icon, null, 2));

    // Check the title
    const title = await page.locator('.completion-title').first().evaluate(el => {
      const styles = window.getComputedStyle(el);

      return {
        fontSize: styles.fontSize,
        fontWeight: styles.fontWeight,
        fontFamily: styles.fontFamily
      };
    });

    console.log('\n📋 TITLE PROPERTIES:');
    console.log(JSON.stringify(title, null, 2));

    console.log('\n🎯 LANDSCAPE 2 COMPLIANCE CHECK:');

    // Check key Landscape 2 requirements
    const checks = {
      'Flex layout': containerProps.display === 'flex',
      'Row direction': containerProps.flexDirection === 'row',
      'Center alignment': containerProps.alignItems === 'center',
      'Space between': containerProps.justifyContent === 'space-between',
      '720px max-width': containerProps.maxWidth === '720px',
      '2 children': containerProps.childCount === 2,
      'Left column layout': leftSection.flexDirection === 'column',
      'Left center aligned': leftSection.alignItems === 'center',
      'Right column layout': rightSection.flexDirection === 'column',
      'Right right aligned': rightSection.alignItems === 'flex-end',
      'Divider present': leftSection.borderRight !== 'none',
      '72px icon': icon.width === '72px',
      '1.5rem title': title.fontSize === '1.5rem',
      'slideInFromRight animation': containerProps.animation.includes('slideInFromRight')
    };

    let passedChecks = 0;
    const totalChecks = Object.keys(checks).length;

    console.log('\n┌─────────────────────────────────────┬──────────────┐');
    console.log('│ Check                               │ Status       │');
    console.log('├─────────────────────────────────────┼──────────────┤');

    for (const [check, passed] of Object.entries(checks)) {
      const status = passed ? '✅ PASS' : '❌ FAIL';
      console.log(`│ ${check.padEnd(35)} │ ${status.padEnd(12)} │`);
      if (passed) passedChecks++;
    }

    console.log('└─────────────────────────────────────┴──────────────┘');

    const successRate = Math.round((passedChecks / totalChecks) * 100);
    console.log(`\n📈 OVERALL: ${passedChecks}/${totalChecks} checks passed (${successRate}%)`);

    if (successRate >= 80) {
      console.log('🎉 EXCELLENT! Implementation closely matches Landscape 2 design!');
    } else if (successRate >= 60) {
      console.log('✅ GOOD! Implementation mostly matches Landscape 2 design.');
    } else {
      console.log('⚠️  NEEDS WORK: Implementation differs significantly from Landscape 2.');
    }

    // Take a screenshot for visual verification
    await page.screenshot({
      path: 'landscape2-implementation-test.png',
      fullPage: false
    });
    console.log('\n📸 Screenshot saved: landscape2-implementation-test.png');

  } catch (error) {
    console.error('❌ Error during test:', error);
  } finally {
    await browser.close();
  }
})();