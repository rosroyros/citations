const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('🔍 Comparing Gated Overlay CSS Rules: Current vs Landscape 2');

    // First, let's check what's running on localhost:5174 (current glassmorphism)
    console.log('\n📊 ANALYZING CURRENT IMPLEMENTATION (localhost:5174)...');
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // Submit a citation to trigger the gated overlay
    await page.waitForSelector('.ProseMirror', { timeout: 10000 });
    await page.fill('.ProseMirror', 'Smith, J. (2023). Test citation for validation. Journal of Testing, 15(3), 123-145.');
    await page.click('button[type="submit"]');

    // Wait for gated overlay to appear
    await page.waitForSelector('[data-testid="gated-results"]', { timeout: 30000 });
    await page.waitForTimeout(2000);

    // Get CSS rules for current implementation
    const currentOverlay = await page.locator('.gated-overlay-content').first();
    const currentCSS = await currentOverlay.evaluate(el => {
      const styles = window.getComputedStyle(el);
      const computedStyles = {};

      // Get all CSS properties we care about
      for (let i = 0; i < styles.length; i++) {
        const prop = styles[i];
        if (prop.includes('width') || prop.includes('height') || prop.includes('padding') ||
            prop.includes('margin') || prop.includes('display') || prop.includes('flex') ||
            prop.includes('position') || prop.includes('background') || prop.includes('border') ||
            prop.includes('border-radius') || prop.includes('box-shadow') || prop.includes('backdrop') ||
            prop.includes('transform') || prop.includes('animation') || prop.includes('transition') ||
            prop.includes('gap') || prop.includes('align') || prop.includes('justify') ||
            prop.includes('grid') || prop.includes('max') || prop.includes('min')) {
          computedStyles[prop] = styles.getPropertyValue(prop);
        }
      }

      // Also get computed dimensions
      const rect = el.getBoundingClientRect();
      computedStyles['actualWidth'] = rect.width + 'px';
      computedStyles['actualHeight'] = rect.height + 'px';

      return computedStyles;
    });

    console.log('\n📋 CURRENT IMPLEMENTATION CSS RULES:');
    console.log(JSON.stringify(currentCSS, null, 2));

    // Now check the demo HTML file for Landscape 2
    console.log('\n📊 ANALYZING LANDSCAPE 2 DEMO...');
    const path = require('path');
    const demoPath = 'file://' + path.resolve(__dirname, 'test-landscape-variants.html');
    await page.goto(demoPath);
    await page.waitForLoadState('networkidle');

    // Get CSS rules for Landscape 2
    const landscape2Overlay = await page.locator('.variant-landscape2 .gated-overlay-content').first();
    const landscape2CSS = await landscape2Overlay.evaluate(el => {
      const styles = window.getComputedStyle(el);
      const computedStyles = {};

      // Get all CSS properties we care about (same as above)
      for (let i = 0; i < styles.length; i++) {
        const prop = styles[i];
        if (prop.includes('width') || prop.includes('height') || prop.includes('padding') ||
            prop.includes('margin') || prop.includes('display') || prop.includes('flex') ||
            prop.includes('position') || prop.includes('background') || prop.includes('border') ||
            prop.includes('border-radius') || prop.includes('box-shadow') || prop.includes('backdrop') ||
            prop.includes('transform') || prop.includes('animation') || prop.includes('transition') ||
            prop.includes('gap') || prop.includes('align') || prop.includes('justify') ||
            prop.includes('grid') || prop.includes('max') || prop.includes('min')) {
          computedStyles[prop] = styles.getPropertyValue(prop);
        }
      }

      // Also get computed dimensions
      const rect = el.getBoundingClientRect();
      computedStyles['actualWidth'] = rect.width + 'px';
      computedStyles['actualHeight'] = rect.height + 'px';

      return computedStyles;
    });

    console.log('\n📋 LANDSCAPE 2 CSS RULES:');
    console.log(JSON.stringify(landscape2CSS, null, 2));

    // Create comparison table
    console.log('\n📊 COMPARISON TABLE:');
    console.log('┌─────────────────────────────────────┬─────────────────────────────┬─────────────────────────────┬─────────────────────────────┐');
    console.log('│ CSS Property                        │ Current (Glassmorphism)     │ Landscape 2 (Split Layout)   │ Difference                 │');
    console.log('├─────────────────────────────────────┼─────────────────────────────┼─────────────────────────────┼─────────────────────────────┤');

    // Get all unique properties from both implementations
    const allProps = new Set([...Object.keys(currentCSS), ...Object.keys(landscape2CSS)]);
    const sortedProps = Array.from(allProps).sort();

    for (const prop of sortedProps) {
      const currentVal = currentCSS[prop] || 'N/A';
      const landscape2Val = landscape2CSS[prop] || 'N/A';
      const isDifferent = currentVal !== landscape2Val;

      console.log(`│ ${prop.padEnd(35)} │ ${(currentVal.length > 25 ? currentVal.substring(0, 22) + '...' : currentVal).padEnd(25)} │ ${(landscape2Val.length > 25 ? landscape2Val.substring(0, 22) + '...' : landscape2Val).padEnd(25)} │ ${(isDifferent ? '✓ DIFFERENT' : 'same').padEnd(25)} │`);
    }

    console.log('└─────────────────────────────────────┴─────────────────────────────┴─────────────────────────────┴─────────────────────────────┘');

    // Key differences summary
    console.log('\n🔍 KEY DIFFERENCES SUMMARY:');

    const keyDifferences = sortedProps.filter(prop => currentCSS[prop] !== landscape2CSS[prop]);
    if (keyDifferences.length > 0) {
      console.log(`Found ${keyDifferences.length} different properties:`);
      keyDifferences.forEach(prop => {
        console.log(`  • ${prop}:`);
        console.log(`    Current: "${currentCSS[prop]}"`);
        console.log(`    Landscape 2: "${landscape2CSS[prop]}"`);
      });
    } else {
      console.log('No significant differences found in CSS properties.');
    }

    // Layout analysis
    console.log('\n🎨 LAYOUT ANALYSIS:');
    console.log(`Current - Display: ${currentCSS.display}, Flex Direction: ${currentCSS['flex-direction'] || 'N/A'}`);
    console.log(`Landscape 2 - Display: ${landscape2CSS.display}, Flex Direction: ${landscape2CSS['flex-direction'] || 'N/A'}`);

    console.log(`Current - Width: ${currentCSS.actualWidth}, Height: ${currentCSS.actualHeight}`);
    console.log(`Landscape 2 - Width: ${landscape2CSS.actualWidth}, Height: ${landscape2CSS.actualHeight}`);

    console.log('\n✅ Comparison complete!');

  } catch (error) {
    console.error('❌ Error during comparison:', error);
  } finally {
    await browser.close();
  }
})();