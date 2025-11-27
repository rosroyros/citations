import { test } from '@playwright/test';

test('Check actual rendered classes', async ({ page }) => {
  await page.goto('http://localhost:5175/');
  await page.waitForLoadState('networkidle');

  const uploadBox = page.locator('[data-testid="upload-area"]');
  const html = await uploadBox.innerHTML();

  console.log('\n========== UPLOAD BOX HTML ==========');
  console.log(html);

  console.log('\n========== ALL P ELEMENTS ==========');
  const pElements = await uploadBox.locator('p').all();
  for (let i = 0; i < pElements.length; i++) {
    const el = pElements[i];
    const info = await el.evaluate(e => ({
      class: e.className,
      text: e.textContent.trim(),
      styles: {
        marginTop: window.getComputedStyle(e).marginTop,
        marginBottom: window.getComputedStyle(e).marginBottom
      }
    }));
    console.log(`P element ${i}:`, JSON.stringify(info, null, 2));
  }
});
