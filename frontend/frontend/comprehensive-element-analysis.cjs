const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('🔍 Comprehensive HTML Element & CSS Analysis');

    // Helper function to analyze elements with their CSS
    const analyzeElements = async (selector, context) => {
      const elements = await page.locator(selector).evaluateAll(elements => {
        return elements.map((el, index) => {
          const styles = window.getComputedStyle(el);
          const cssRules = {};

          // Get key CSS properties
          const importantProps = [
            'display', 'position', 'width', 'height', 'max-width', 'min-width',
            'padding', 'margin', 'flex-direction', 'align-items', 'justify-content',
            'text-align', 'font-size', 'font-weight', 'color', 'background',
            'border', 'border-radius', 'box-shadow', 'backdrop-filter',
            'animation', 'transform', 'gap', 'grid-template-columns', 'grid-gap'
          ];

          importantProps.forEach(prop => {
            cssRules[prop] = styles.getPropertyValue(prop);
          });

          return {
            index,
            tagName: el.tagName.toLowerCase(),
            className: el.className,
            id: el.id,
            textContent: el.textContent?.trim().substring(0, 60),
            children: el.children.length,
            cssRules,
            computedWidth: el.getBoundingClientRect().width + 'px',
            computedHeight: el.getBoundingClientRect().height + 'px'
          };
        });
      });

      return elements;
    };

    // Analyze current implementation
    console.log('\n📊 ANALYZING CURRENT IMPLEMENTATION...');
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // Submit a citation to trigger the gated overlay
    await page.waitForSelector('.ProseMirror', { timeout: 10000 });
    await page.fill('.ProseMirror', 'Smith, J. (2023). Test citation for validation. Journal of Testing, 15(3), 123-145.');
    await page.click('button[type="submit"]');

    // Wait for gated overlay to appear
    await page.waitForSelector('[data-testid="gated-results"]', { timeout: 30000 });
    await page.waitForTimeout(2000);

    const currentElements = await analyzeElements('[data-testid="gated-results"] *', 'Current');

    // Analyze Landscape 2 reference
    console.log('\n📊 ANALYZING LANDSCAPE 2 REFERENCE...');
    const path = require('path');
    const demoPath = 'file://' + path.resolve(__dirname, 'test-landscape-variants.html');
    await page.goto(demoPath);
    await page.waitForLoadState('networkidle');

    const landscape2Elements = await analyzeElements('.variant-landscape2 .gated-results-overlay *', 'Landscape 2');

    console.log('\n📋 COMPREHENSIVE ELEMENT ANALYSIS:');
    console.log('='.repeat(120));

    // Create element map for easy comparison
    const createElementKey = (el) => `${el.tagName}.${el.className || 'no-class'}`;

    const currentMap = new Map();
    currentElements.forEach(el => {
      const key = createElementKey(el);
      if (!currentMap.has(key)) {
        currentMap.set(key, []);
      }
      currentMap.get(key).push(el);
    });

    const landscape2Map = new Map();
    landscape2Elements.forEach(el => {
      const key = createElementKey(el);
      if (!landscape2Map.has(key)) {
        landscape2Map.set(key, []);
      }
      landscape2Map.get(key).push(el);
    });

    // Get all unique element keys
    const allKeys = new Set([...currentMap.keys(), ...landscape2Map.keys()]);
    const sortedKeys = Array.from(allKeys).sort();

    console.log(`\n📊 ELEMENT COMPARISON TABLE (${sortedKeys.length} unique element types):`);
    console.log('┌─────────────────────────────────────┬─────────────────┬─────────────────┬─────────────────────────────────────────┐');
    console.log('│ Element (Tag.Class)                 │ Current (Test)  │ Landscape 2     │ Key CSS Differences                      │');
    console.log('├─────────────────────────────────────┼─────────────────┼─────────────────┼─────────────────────────────────────────┤');

    sortedKeys.forEach(key => {
      const currentEls = currentMap.get(key) || [];
      const landscape2Els = landscape2Map.get(key) || [];

      const currentCount = currentEls.length;
      const landscape2Count = landscape2Els.length;

      let status = '';
      if (currentCount === landscape2Count && currentCount > 0) {
        status = '✅ MATCH';
      } else if (currentCount === 0 && landscape2Count > 0) {
        status = '❌ MISSING';
      } else if (currentCount > 0 && landscape2Count === 0) {
        status = '➕ EXTRA';
      } else {
        status = '⚠️  DIFF';
      }

      const currentStr = currentCount > 0 ? `${currentCount}×` : '—';
      const landscape2Str = landscape2Count > 0 ? `${landscape2Count}×` : '—';

      // Compare CSS if both exist
      let cssDiff = 'N/A';
      if (currentCount > 0 && landscape2Count > 0) {
        const currentEl = currentEls[0];
        const landscape2El = landscape2Els[0];

        const diffKeys = [];
        const importantCssKeys = ['display', 'flex-direction', 'align-items', 'justify-content', 'width', 'max-width', 'padding', 'text-align'];

        importantCssKeys.forEach(cssKey => {
          const currentVal = currentEl.cssRules[cssKey] || 'auto';
          const landscape2Val = landscape2El.cssRules[cssKey] || 'auto';

          if (currentVal !== landscape2Val) {
            diffKeys.push(`${cssKey}: ${currentVal} vs ${landscape2Val}`);
          }
        });

        cssDiff = diffKeys.length > 0 ? diffKeys.slice(0, 2).join('; ') : '✅ Identical';
      }

      const elementName = key.length > 35 ? key.substring(0, 32) + '...' : key;

      console.log(`│ ${elementName.padEnd(35)} │ ${currentStr.padEnd(15)} │ ${landscape2Str.padEnd(15)} │ ${(cssDiff.length > 40 ? cssDiff.substring(0, 37) + '...' : cssDiff).padEnd(39)} │`);
    });

    console.log('└─────────────────────────────────────┴─────────────────┴─────────────────┴─────────────────────────────────────────┘');

    // Detailed breakdown for each implementation
    console.log('\n📋 DETAILED ELEMENT BREAKDOWN:');
    console.log('\n🔹 CURRENT IMPLEMENTATION ELEMENTS:');
    currentElements.forEach((el, index) => {
      console.log(`\n${index + 1}. <${el.tagName}> class="${el.className}"`);
      console.log(`   Text: "${el.textContent}"`);
      console.log(`   Children: ${el.children} | Size: ${el.computedWidth} × ${el.computedHeight}`);
      console.log(`   Key CSS: display=${el.cssRules.display}, width=${el.cssRules.width || el.cssRules['max-width']}, text-align=${el.cssRules['text-align']}`);
    });

    console.log('\n🔹 LANDSCAPE 2 REFERENCE ELEMENTS:');
    landscape2Elements.forEach((el, index) => {
      console.log(`\n${index + 1}. <${el.tagName}> class="${el.className}"`);
      console.log(`   Text: "${el.textContent}"`);
      console.log(`   Children: ${el.children} | Size: ${el.computedWidth} × ${el.computedHeight}`);
      console.log(`   Key CSS: display=${el.cssRules.display}, width=${el.cssRules.width || el.cssRules['max-width']}, text-align=${el.cssRules['text-align']}`);
    });

    // Summary statistics
    const currentTotal = currentElements.length;
    const landscape2Total = landscape2Elements.length;
    const matchingTypes = sortedKeys.filter(key => {
      const currentCount = (currentMap.get(key) || []).length;
      const landscape2Count = (landscape2Map.get(key) || []).length;
      return currentCount === landscape2Count && currentCount > 0;
    }).length;

    console.log('\n📈 SUMMARY STATISTICS:');
    console.log(`Current Implementation: ${currentTotal} total elements, ${currentMap.size} unique types`);
    console.log(`Landscape 2 Reference: ${landscape2Total} total elements, ${landscape2Map.size} unique types`);
    console.log(`Matching Element Types: ${matchingTypes}/${sortedKeys.length} (${Math.round(matchingTypes/sortedKeys.length*100)}%)`);
    console.log(`Element Count Match: ${currentTotal === landscape2Total ? '✅' : '❌'} (${currentTotal} vs ${landscape2Total})`);

    console.log('\n✅ Comprehensive element analysis complete!');

  } catch (error) {
    console.error('❌ Error during analysis:', error);
  } finally {
    await browser.close();
  }
})();