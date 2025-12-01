const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('🔍 Comparing HTML Structure: Current vs Landscape 2 Reference');

    // First, get the current implementation structure
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

    // Get HTML structure from current implementation
    const currentStructure = await page.locator('[data-testid="gated-results"]').first().evaluate(el => {
      return {
        html: el.innerHTML,
        elementCount: el.querySelectorAll('*').length,
        directChildren: Array.from(el.children).map(child => ({
          tagName: child.tagName.toLowerCase(),
          className: child.className,
          textContent: child.textContent?.trim().substring(0, 50),
          children: child.children.length
        }))
      };
    });

    console.log('\n📋 CURRENT IMPLEMENTATION HTML:');
    console.log('Total elements:', currentStructure.elementCount);
    console.log('Direct children:', currentStructure.directChildren.length);
    console.log('\n📄 HTML Structure:');
    console.log(currentStructure.html);

    console.log('\n📋 DIRECT CHILDREN BREAKDOWN:');
    currentStructure.directChildren.forEach((child, index) => {
      console.log(`${index + 1}. <${child.tagName} class="${child.className}">`);
      console.log(`   Text: "${child.textContent}"`);
      console.log(`   Children: ${child.children}`);
      console.log('');
    });

    // Now check the Landscape 2 reference
    console.log('\n📊 ANALYZING LANDSCAPE 2 REFERENCE...');
    const path = require('path');
    const demoPath = 'file://' + path.resolve(__dirname, 'test-landscape-variants.html');
    await page.goto(demoPath);
    await page.waitForLoadState('networkidle');

    // Get HTML structure from Landscape 2 reference
    const landscape2Structure = await page.locator('.variant-landscape2 .gated-results-overlay').first().evaluate(el => {
      return {
        html: el.innerHTML,
        elementCount: el.querySelectorAll('*').length,
        directChildren: Array.from(el.children).map(child => ({
          tagName: child.tagName.toLowerCase(),
          className: child.className,
          textContent: child.textContent?.trim().substring(0, 50),
          children: child.children.length
        }))
      };
    });

    console.log('\n📋 LANDSCAPE 2 REFERENCE HTML:');
    console.log('Total elements:', landscape2Structure.elementCount);
    console.log('Direct children:', landscape2Structure.directChildren.length);
    console.log('\n📄 HTML Structure:');
    console.log(landscape2Structure.html);

    console.log('\n📋 DIRECT CHILDREN BREAKDOWN:');
    landscape2Structure.directChildren.forEach((child, index) => {
      console.log(`${index + 1}. <${child.tagName} class="${child.className}">`);
      console.log(`   Text: "${child.textContent}"`);
      console.log(`   Children: ${child.children}`);
      console.log('');
    });

    // Create comparison table
    console.log('\n📊 STRUCTURE COMPARISON:');
    console.log('┌─────────────────────────────────────┬─────────────────────────────┬─────────────────────────────┬─────────────────────────────┐');
    console.log('│ Aspect                              │ Current Implementation      │ Landscape 2 Reference        │ Match Status                │');
    console.log('├─────────────────────────────────────┼─────────────────────────────┼─────────────────────────────┼─────────────────────────────┤');

    const comparisons = [
      {
        aspect: 'Total elements',
        current: currentStructure.elementCount,
        reference: landscape2Structure.elementCount
      },
      {
        aspect: 'Direct children count',
        current: currentStructure.directChildren.length,
        reference: landscape2Structure.directChildren.length
      }
    ];

    comparisons.forEach(comp => {
      const match = comp.current === comp.reference;
      console.log(`│ ${comp.aspect.padEnd(35)} │ ${comp.current.toString().padEnd(25)} │ ${comp.reference.toString().padEnd(25)} │ ${(match ? '✓ MATCH' : '✗ DIFFERENT').padEnd(25)} │`);
    });

    console.log('└─────────────────────────────────────┴─────────────────────────────┴─────────────────────────────┴─────────────────────────────┘');

    // Detailed element comparison
    console.log('\n🔍 DETAILED ELEMENT COMPARISON:');
    console.log('\nCURRENT IMPLEMENTATION:');
    currentStructure.directChildren.forEach((child, index) => {
      console.log(`${index + 1}. ${child.tagName}.${child.className}`);
    });

    console.log('\nLANDSCAPE 2 REFERENCE:');
    landscape2Structure.directChildren.forEach((child, index) => {
      console.log(`${index + 1}. ${child.tagName}.${child.className}`);
    });

    // Check for differences in structure
    const currentTagClasses = currentStructure.directChildren.map(c => `${c.tagName}.${c.className}`);
    const referenceTagClasses = landscape2Structure.directChildren.map(c => `${c.tagName}.${c.className}`);

    console.log('\n📈 STRUCTURE ANALYSIS:');
    if (JSON.stringify(currentTagClasses) === JSON.stringify(referenceTagClasses)) {
      console.log('✅ Perfect structure match!');
    } else {
      console.log('⚠️  Structure differences detected:');
      console.log('Current elements:', currentTagClasses);
      console.log('Reference elements:', referenceTagClasses);

      const missing = referenceTagClasses.filter(tag => !currentTagClasses.includes(tag));
      const extra = currentTagClasses.filter(tag => !referenceTagClasses.includes(tag));

      if (missing.length > 0) {
        console.log('Missing elements:', missing);
      }
      if (extra.length > 0) {
        console.log('Extra elements:', extra);
      }
    }

    console.log('\n✅ HTML structure comparison complete!');

  } catch (error) {
    console.error('❌ Error during comparison:', error);
  } finally {
    await browser.close();
  }
})();