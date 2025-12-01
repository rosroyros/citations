const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('🔍 Comparing Updated Implementation vs Landscape 2 Reference');

    // First, let's check the updated implementation on localhost:5174
    console.log('\n📊 ANALYZING UPDATED IMPLEMENTATION (localhost:5174)...');
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // Submit a citation to trigger the gated overlay
    await page.waitForSelector('.ProseMirror', { timeout: 10000 });
    await page.fill('.ProseMirror', 'Smith, J. (2023). Test citation for validation. Journal of Testing, 15(3), 123-145.');
    await page.click('button[type="submit"]');

    // Wait for gated overlay to appear
    await page.waitForSelector('[data-testid="gated-results"]', { timeout: 30000 });
    await page.waitForTimeout(2000);

    // Get CSS rules for updated implementation
    const updatedOverlay = await page.locator('.gated-overlay-content').first();
    const updatedCSS = await updatedOverlay.evaluate(el => {
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

      // Check flex layout specifically
      const flexChildren = el.children;
      computedStyles['childCount'] = flexChildren.length;

      return computedStyles;
    });

    console.log('\n📋 UPDATED IMPLEMENTATION CSS RULES:');
    console.log(JSON.stringify(updatedCSS, null, 2));

    // Now check the demo HTML file for Landscape 2 reference
    console.log('\n📊 ANALYZING LANDSCAPE 2 REFERENCE...');
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

      // Check flex layout specifically
      const flexChildren = el.children;
      computedStyles['childCount'] = flexChildren.length;

      return computedStyles;
    });

    console.log('\n📋 LANDSCAPE 2 REFERENCE CSS RULES:');
    console.log(JSON.stringify(landscape2CSS, null, 2));

    // Create comparison table
    console.log('\n📊 COMPARISON TABLE:');
    console.log('┌─────────────────────────────────────┬─────────────────────────────┬─────────────────────────────┬─────────────────────────────┐');
    console.log('│ CSS Property                        │ Updated Implementation       │ Landscape 2 Reference        │ Match Status                │');
    console.log('├─────────────────────────────────────┼─────────────────────────────┼─────────────────────────────┼─────────────────────────────┤');

    // Get all unique properties from both implementations
    const allProps = new Set([...Object.keys(updatedCSS), ...Object.keys(landscape2CSS)]);
    const sortedProps = Array.from(allProps).sort();

    let matchCount = 0;
    let totalChecked = 0;

    for (const prop of sortedProps) {
      const updatedVal = updatedCSS[prop] || 'N/A';
      const landscape2Val = landscape2CSS[prop] || 'N/A';
      const isMatch = updatedVal === landscape2Val;

      if (isMatch) matchCount++;
      totalChecked++;

      console.log(`│ ${prop.padEnd(35)} │ ${(updatedVal.length > 25 ? updatedVal.substring(0, 22) + '...' : updatedVal).padEnd(25)} │ ${(landscape2Val.length > 25 ? landscape2Val.substring(0, 22) + '...' : landscape2Val).padEnd(25)} │ ${(isMatch ? '✓ MATCH' : '✗ DIFFERENT').padEnd(25)} │`);
    }

    console.log('└─────────────────────────────────────┴─────────────────────────────┴─────────────────────────────┴─────────────────────────────┘');

    // Match percentage
    const matchPercentage = totalChecked > 0 ? Math.round((matchCount / totalChecked) * 100) : 0;
    console.log(`\n📈 MATCH ANALYSIS: ${matchCount}/${totalChecked} properties match (${matchPercentage}%)`);

    // Key differences summary
    console.log('\n🔍 KEY DIFFERENCES:');
    const keyDifferences = sortedProps.filter(prop => updatedCSS[prop] !== landscape2CSS[prop]);
    if (keyDifferences.length > 0) {
      console.log(`Found ${keyDifferences.length} different properties:`);
      keyDifferences.forEach(prop => {
        console.log(`  • ${prop}:`);
        console.log(`    Updated: "${updatedCSS[prop]}"`);
        console.log(`    Landscape 2: "${landscape2CSS[prop]}"`);
      });
    } else {
      console.log('🎉 Perfect match! All CSS properties are identical.');
    }

    // Layout analysis
    console.log('\n🎨 LAYOUT ANALYSIS:');
    console.log(`Updated - Display: ${updatedCSS.display}, Flex Direction: ${updatedCSS['flex-direction'] || 'N/A'}, Children: ${updatedCSS.childCount}`);
    console.log(`Landscape 2 - Display: ${landscape2CSS.display}, Flex Direction: ${landscape2CSS['flex-direction'] || 'N/A'}, Children: ${landscape2CSS.childCount}`);

    console.log(`Updated - Width: ${updatedCSS.actualWidth}, Height: ${updatedCSS.actualHeight}`);
    console.log(`Landscape 2 - Width: ${landscape2CSS.actualWidth}, Height: ${landscape2CSS.actualHeight}`);

    console.log('\n✅ Comparison complete!');

  } catch (error) {
    console.error('❌ Error during comparison:', error);
  } finally {
    await browser.close();
  }
})();