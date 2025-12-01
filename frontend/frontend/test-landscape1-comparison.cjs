const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('🔍 Testing Landscape 1 Implementation - Final Verification');

    // Test the updated implementation
    console.log('\n📊 TESTING UPDATED LANDSCAPE 1 IMPLEMENTATION...');
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
        gap: styles.gap,

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

    // Check the completion indicator (left section)
    const leftSection = await page.locator('.completion-indicator').first().evaluate(el => {
      const styles = window.getComputedStyle(el);

      return {
        display: styles.display,
        flexDirection: styles.flexDirection,
        alignItems: styles.alignItems,
        gap: styles.gap,
        flex: styles.flex,
        borderRight: styles.borderRight,
        paddingRight: styles.paddingRight
      };
    });

    console.log('\n📋 COMPLETION INDICATOR PROPERTIES:');
    console.log(JSON.stringify(leftSection, null, 2));

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

    // Check the reveal button container
    const buttonContainer = await page.locator('.reveal-button-container').first().evaluate(el => {
      const styles = window.getComputedStyle(el);

      return {
        display: styles.display,
        justifyContent: styles.justifyContent
      };
    });

    console.log('\n📋 REVEAL BUTTON CONTAINER PROPERTIES:');
    console.log(JSON.stringify(buttonContainer, null, 2));

    // Check HTML structure
    const htmlStructure = await page.locator('[data-testid="gated-results"]').first().evaluate(el => {
      const directChildren = Array.from(el.children).map(child => ({
        tagName: child.tagName.toLowerCase(),
        className: child.className,
        children: child.children.length
      }));

      return {
        totalElements: el.querySelectorAll('*').length,
        directChildren
      };
    });

    console.log('\n📋 HTML STRUCTURE:');
    console.log(JSON.stringify(htmlStructure, null, 2));

    console.log('\n🎯 LANDSCAPE 1 COMPLIANCE CHECK:');

    // Check key Landscape 1 requirements
    const checks = {
      'Flex layout': containerProps.display === 'flex',
      'Row direction': containerProps.flexDirection === 'row',
      'Center alignment': containerProps.alignItems === 'center',
      '48px gap': containerProps.gap === '48px',
      '680px max-width': containerProps.maxWidth === '680px',
      '2 children': containerProps.childCount === 2,
      'Horizontal completion indicator': leftSection.flexDirection === 'row',
      'Indicator center aligned': leftSection.alignItems === 'center',
      '24px gap in indicator': leftSection.gap === '24px',
      'No divider': leftSection.borderRight === 'none',
      '64px icon': icon.width === '64px',
      '32px font in icon': icon.fontSize === '32px',
      'Button container flex': buttonContainer.display === 'flex',
      'slideInFromLeft animation': containerProps.animation.includes('slideInFromLeft')
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
      console.log('🎉 EXCELLENT! Implementation closely matches Landscape 1 design!');
    } else if (successRate >= 60) {
      console.log('✅ GOOD! Implementation mostly matches Landscape 1 design.');
    } else {
      console.log('⚠️  NEEDS WORK: Implementation differs significantly from Landscape 1.');
    }

    // Take a screenshot for visual verification
    await page.screenshot({
      path: 'landscape1-implementation-test.png',
      fullPage: false
    });
    console.log('\n📸 Screenshot saved: landscape1-implementation-test.png');

  } catch (error) {
    console.error('❌ Error during test:', error);
  } finally {
    await browser.close();
  }
})();