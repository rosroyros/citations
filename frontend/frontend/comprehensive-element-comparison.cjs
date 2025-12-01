const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    console.log('📊 COMPREHENSIVE HTML ELEMENT & CSS COMPARISON');
    console.log('='.repeat(100));

    // Test site analysis
    console.log('\n🔍 ANALYZING TEST SITE...');
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // Trigger gated overlay
    await page.waitForSelector('.ProseMirror', { timeout: 10000 });
    await page.fill('.ProseMirror', 'Smith, J. (2023). Test citation. Journal of Testing, 15(3), 123-145.');
    await page.click('button[type="submit"]');
    await page.waitForSelector('[data-testid="gated-results"]', { timeout: 30000 });
    await page.waitForTimeout(2000);

    // Get all elements in test site
    const testElements = await page.locator('.gated-overlay-content').first().evaluate(el => {
      const elements = [];

      function getElementInfo(element, depth = 0) {
        const computedStyles = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();

        const info = {
          tag: element.tagName.toLowerCase(),
          className: element.className,
          id: element.id || '',
          textContent: element.textContent?.trim().substring(0, 50) || '',
          depth: depth,
          children: Array.from(element.children).map(child => getElementInfo(child, depth + 1)),
          css: {
            display: computedStyles.display,
            flexDirection: computedStyles.flexDirection,
            alignItems: computedStyles.alignItems,
            justifyContent: computedStyles.justifyContent,
            gap: computedStyles.gap,
            padding: computedStyles.padding,
            margin: computedStyles.margin,
            width: computedStyles.width,
            maxWidth: computedStyles.maxWidth,
            height: computedStyles.height,
            fontSize: computedStyles.fontSize,
            fontWeight: computedStyles.fontWeight,
            color: computedStyles.color,
            background: computedStyles.background,
            borderRadius: computedStyles.borderRadius,
            animation: computedStyles.animation,
            position: computedStyles.position,
            top: computedStyles.top,
            left: computedStyles.left,
            right: computedStyles.right,
            bottom: computedStyles.bottom,
            zIndex: computedStyles.zIndex
          },
          dimensions: {
            width: rect.width + 'px',
            height: rect.height + 'px',
            x: rect.x + 'px',
            y: rect.y + 'px'
          }
        };
        return info;
      }

      return getElementInfo(el);
    });

    // Read the Landscape 1 mock HTML and manually parse it
    const fs = require('fs');
    const mockHtml = fs.readFileSync('./test-landscape-variants.html', 'utf8');

    // Find the Landscape 1 variant section manually
    const landscape1Match = mockHtml.match(/<div class="variant-landscape1"[^>]*>[\s\S]*?<div class="gated-overlay-content">([\s\S]*?)<\/div>[\s\S]*?<\/div>/);

    let mockElements = null;
    if (landscape1Match) {
      const mockContent = landscape1Match[1];

      // Manual parsing of the mock HTML structure
      mockElements = {
        tag: 'div',
        className: 'gated-overlay-content',
        id: '',
        textContent: '✓ Your citation validation is complete 2 valid • 2 errors found View Results (4 citations)',
        depth: 0,
        children: [
          {
            tag: 'div',
            className: 'completion-indicator',
            id: '',
            textContent: '✓ Your citation validation is complete 2 valid • 2 errors found',
            depth: 1,
            children: [
              {
                tag: 'div',
                className: 'completion-icon',
                id: '',
                textContent: '✓',
                depth: 2,
                children: []
              },
              {
                tag: 'div',
                className: 'completion-text',
                id: '',
                textContent: 'Your citation validation is complete 2 valid • 2 errors found',
                depth: 2,
                children: [
                  {
                    tag: 'h3',
                    className: 'completion-title',
                    id: '',
                    textContent: 'Your citation validation is complete',
                    depth: 3,
                    children: []
                  },
                  {
                    tag: 'p',
                    className: 'completion-summary',
                    id: '',
                    textContent: '2 valid • 2 errors found',
                    depth: 3,
                    children: []
                  }
                ]
              }
            ]
          },
          {
            tag: 'div',
            className: 'reveal-button-container',
            id: '',
            textContent: 'View Results (4 citations)',
            depth: 1,
            children: [
              {
                tag: 'button',
                className: 'reveal-button',
                id: '',
                textContent: 'View Results (4 citations)',
                depth: 2,
                children: []
              }
            ]
          }
        ]
      };
    }

    // mockElements is already defined above

    // Create comparison table
    console.log('\n📋 ELEMENT COMPARISON TABLE');
    console.log('='.repeat(200));

    function printComparison(testEl, mockEl, path = '') {
      const currentPath = path ? `${path} > ${testEl.tag}` : testEl.tag;

      console.log('\n┌' + '─'.repeat(198) + '┐');
      console.log(`│ ${currentPath.padEnd(80)} │ TEST SITE ${''.padEnd(45)} │ LANDSCAPE1 MOCK ${''.padEnd(45)} │`);
      console.log('├' + '─'.repeat(198) + '┤');

      // Element existence
      const testExists = testEl ? '✅ YES' : '❌ NO';
      const mockExists = mockEl ? '✅ YES' : '❌ NO';
      console.log(`│ ${'Exists:'.padEnd(80)} │ ${testExists.padEnd(57)} │ ${mockExists.padEnd(57)} │`);

      if (testEl && mockEl) {
        // Class name
        console.log(`│ ${'Class:'.padEnd(80)} │ ${(testEl.className || 'none').padEnd(57)} │ ${(mockEl.className || 'none').padEnd(57)} │`);

        // Text content
        console.log(`│ ${'Text:'.padEnd(80)} │ ${(testEl.textContent || 'none').padEnd(57)} │ ${(mockEl.textContent || 'none').padEnd(57)} │`);

        // Key CSS properties for test
        if (testEl.css) {
          console.log(`│ ${'CSS Display:'.padEnd(80)} │ ${testEl.css.display.padEnd(57)} │ ${'N/A'.padEnd(57)} │`);
          console.log(`│ ${'CSS Flex Direction:'.padEnd(80)} │ ${testEl.css.flexDirection.padEnd(57)} │ ${'N/A'.padEnd(57)} │`);
          console.log(`│ ${'CSS Gap:'.padEnd(80)} │ ${testEl.css.gap.padEnd(57)} │ ${'N/A'.padEnd(57)} │`);
          console.log(`│ ${'CSS Max Width:'.padEnd(80)} │ ${testEl.css.maxWidth.padEnd(57)} │ ${'N/A'.padEnd(57)} │`);
          console.log(`│ ${'CSS Padding:'.padEnd(80)} │ ${testEl.css.padding.padEnd(57)} │ ${'N/A'.padEnd(57)} │`);
          console.log(`│ ${'CSS Font Size:'.padEnd(80)} │ ${testEl.css.fontSize.padEnd(57)} │ ${'N/A'.padEnd(57)} │`);
          console.log(`│ ${'CSS Animation:'.padEnd(80)} │ ${testEl.css.animation.padEnd(57)} │ ${'N/A'.padEnd(57)} │`);
        }
      }

      console.log('└' + '─'.repeat(198) + '┘');

      // Recursively compare children
      if (testEl && testEl.children && mockEl && mockEl.children) {
        const maxChildren = Math.max(testEl.children.length, mockEl.children.length);
        for (let i = 0; i < maxChildren; i++) {
          printComparison(
            testEl.children[i] || null,
            mockEl.children[i] || null,
            currentPath
          );
        }
      }
    }

    printComparison(testElements, mockElements);

    // Summary statistics
    console.log('\n📊 SUMMARY STATISTICS');
    console.log('='.repeat(100));

    function countElements(el) {
      if (!el) return 0;
      return 1 + el.children.reduce((sum, child) => sum + countElements(child), 0);
    }

    const testCount = countElements(testElements);
    const mockCount = countElements(mockElements);

    console.log(`\nTotal Elements:`);
    console.log(`  Test Site:     ${testCount}`);
    console.log(`  Landscape1:    ${mockCount}`);
    console.log(`  Difference:    ${Math.abs(testCount - mockCount)}`);

  } catch (error) {
    console.error('❌ Error during analysis:', error);
  } finally {
    await browser.close();
  }
})();