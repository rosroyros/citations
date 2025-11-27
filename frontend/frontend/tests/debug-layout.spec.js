import { test } from '@playwright/test';

test('Inspect layout CSS systematically', async ({ page }) => {
  await page.goto('http://localhost:5175/');
  await page.waitForLoadState('networkidle');

  console.log('\n========== EDITOR BOX ==========');
  const editorBox = page.locator('.citation-editor');
  const editorStyles = await editorBox.evaluate(el => {
    const computed = window.getComputedStyle(el);
    return {
      offsetHeight: el.offsetHeight,
      minHeight: computed.minHeight,
      maxHeight: computed.maxHeight,
      height: computed.height,
      padding: computed.padding,
      paddingTop: computed.paddingTop,
      paddingBottom: computed.paddingBottom,
      border: computed.border,
      borderTop: computed.borderTop,
      borderBottom: computed.borderBottom,
      boxSizing: computed.boxSizing,
      display: computed.display,
      scrollHeight: el.scrollHeight,
      clientHeight: el.clientHeight
    };
  });
  console.log(JSON.stringify(editorStyles, null, 2));

  console.log('\n========== UPLOAD BOX ==========');
  const uploadBox = page.locator('[data-testid="upload-area"]');
  const uploadStyles = await uploadBox.evaluate(el => {
    const computed = window.getComputedStyle(el);
    return {
      offsetHeight: el.offsetHeight,
      minHeight: computed.minHeight,
      maxHeight: computed.maxHeight,
      height: computed.height,
      padding: computed.padding,
      paddingTop: computed.paddingTop,
      paddingBottom: computed.paddingBottom,
      border: computed.border,
      borderTop: computed.borderTop,
      borderBottom: computed.borderBottom,
      boxSizing: computed.boxSizing,
      display: computed.display,
      scrollHeight: el.scrollHeight,
      clientHeight: el.clientHeight
    };
  });
  console.log(JSON.stringify(uploadStyles, null, 2));

  console.log('\n========== UPLOAD BOX CHILDREN (ONE BY ONE) ==========');
  const childSelectors = [
    '.content',
    '.mainText',
    '.orText',
    '.fileTypes',
    'label'
  ];

  for (const selector of childSelectors) {
    const child = uploadBox.locator(selector).first();
    const exists = await child.count() > 0;
    if (exists) {
      const info = await child.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          selector: el.className || el.tagName,
          offsetHeight: el.offsetHeight,
          margin: computed.margin,
          marginTop: computed.marginTop,
          marginBottom: computed.marginBottom,
          padding: computed.padding,
          paddingTop: computed.paddingTop,
          paddingBottom: computed.paddingBottom,
          display: computed.display,
          textContent: el.textContent?.trim().substring(0, 40)
        };
      });
      console.log(`\n${selector}:`, JSON.stringify(info, null, 2));
    } else {
      console.log(`\n${selector}: NOT FOUND`);
    }
  }

  console.log('\n========== HEIGHT COMPARISON ==========');
  console.log('Editor offsetHeight:', editorStyles.offsetHeight, 'px');
  console.log('Upload offsetHeight:', uploadStyles.offsetHeight, 'px');
  console.log('Difference:', editorStyles.offsetHeight - uploadStyles.offsetHeight, 'px');

  await page.screenshot({ path: '/tmp/layout-debug.png', fullPage: false });
  console.log('\nScreenshot saved to /tmp/layout-debug.png');

  await page.waitForTimeout(1000);
});
