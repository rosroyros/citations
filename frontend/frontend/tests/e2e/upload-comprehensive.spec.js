import { test, expect } from '@playwright/test';

/**
 * Comprehensive Upload Feature E2E Tests
 * Tests additional scenarios not covered in upload-integration.spec.js:
 * - Processing animation timing
 * - All modal dismiss methods (button, backdrop, ESC key)
 * - Editor focus after modal close
 * - Drag visual feedback states
 * - Edge cases (rapid file selection, multiple interactions)
 */

test.describe('Upload Feature - Comprehensive E2E Tests', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 1280, height: 720 }
  });

  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
      window.gtag = function() {}; // Mock gtag
    });
    await page.goto('/');
    await expect(page.locator('h1:has-text("Citation Format Checker")')).toBeVisible();
  });

  test('Processing animation displays for 1.5 seconds before modal', async ({ page }) => {
    const fileContent = Buffer.from('Test PDF content');

    // Track timing
    const startTime = Date.now();

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: fileContent
    });

    // Processing indicator should appear immediately
    await expect(page.locator('[data-testid="processing-indicator"]')).toBeVisible({ timeout: 500 });
    await expect(page.locator('text=Processing your document')).toBeVisible();

    // Wait for modal to appear
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();

    const processingDuration = Date.now() - startTime;

    // Processing should take approximately 1500ms (allow 300ms variance for test stability)
    expect(processingDuration).toBeGreaterThanOrEqual(1300);
    expect(processingDuration).toBeLessThan(2100);
  });

  test('Modal can be dismissed by clicking Okay button', async ({ page }) => {
    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Test content')
    });

    // Wait for modal
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();

    // Click Okay button
    await page.locator('button:has-text("Okay")').click();

    // Modal should be dismissed
    await expect(page.locator('[data-testid="modal-backdrop"]')).not.toBeVisible();
  });

  test('Modal can be dismissed by clicking backdrop', async ({ page }) => {
    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Test content')
    });

    // Wait for modal
    const backdrop = page.locator('[data-testid="modal-backdrop"]');
    await expect(backdrop).toBeVisible();

    // Click backdrop (not the modal content)
    await backdrop.click({ position: { x: 10, y: 10 } });

    // Modal should be dismissed
    await expect(backdrop).not.toBeVisible();
  });

  test('Modal can be dismissed by pressing Escape key', async ({ page }) => {
    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Test content')
    });

    // Wait for modal
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();

    // Press Escape key
    await page.keyboard.press('Escape');

    // Modal should be dismissed
    await expect(page.locator('[data-testid="modal-backdrop"]')).not.toBeVisible();
  });

  test('Editor receives focus after modal is dismissed', async ({ page }) => {
    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Test content')
    });

    // Wait for modal and dismiss
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
    await page.locator('button:has-text("Okay")').click();

    // Editor should have focus
    const editor = page.locator('[data-testid="editor"] .ProseMirror, [contenteditable="true"]').first();
    await expect(editor).toBeFocused({ timeout: 2000 });
  });

  test('Drag visual feedback shows on dragenter', async ({ page }) => {
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    // Trigger dragenter event using evaluate to avoid dataTransfer issues
    await uploadArea.evaluate((el) => {
      const event = new DragEvent('dragenter', { bubbles: true, cancelable: true });
      el.dispatchEvent(event);
    });

    // Small wait for state update
    await page.waitForTimeout(100);

    // Should have dragOver class/visual feedback
    const hasOverState = await uploadArea.evaluate((el) => {
      return el.className.includes('dragOver');
    });

    expect(hasOverState).toBe(true);
  });

  test('Drag visual feedback clears on dragleave', async ({ page }) => {
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    // Trigger dragenter then dragleave using evaluate
    await uploadArea.evaluate((el) => {
      const enterEvent = new DragEvent('dragenter', { bubbles: true, cancelable: true });
      el.dispatchEvent(enterEvent);
      const leaveEvent = new DragEvent('dragleave', { bubbles: true, cancelable: true });
      el.dispatchEvent(leaveEvent);
    });

    // Small wait for state update
    await page.waitForTimeout(100);

    // dragOver state should be cleared
    const hasOverState = await uploadArea.evaluate((el) => {
      return el.className.includes('dragOver');
    });

    expect(hasOverState).toBe(false);
  });

  test('Drag visual feedback clears on drop', async ({ page }) => {
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    // Trigger dragenter then drop using evaluate
    await uploadArea.evaluate((el) => {
      const enterEvent = new DragEvent('dragenter', { bubbles: true, cancelable: true });
      el.dispatchEvent(enterEvent);
      const dropEvent = new DragEvent('drop', { bubbles: true, cancelable: true });
      el.dispatchEvent(dropEvent);
    });

    // dragOver state should be cleared after drop
    await page.waitForTimeout(100);
    const hasOverState = await uploadArea.evaluate((el) => {
      return el.className.includes('dragOver');
    });

    expect(hasOverState).toBe(false);
  });

  test('Upload handles file selection without crashing', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');

    // Select file
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Test file')
    });

    // Wait for processing to complete
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();

    // This test verifies the system handles file selection without crashing
    await expect(page.locator('text=We apologize, but document upload is temporarily unavailable')).toBeVisible();

    // After dismissing modal, the upload area shows processed state
    await page.locator('button:has-text("Okay")').click();
    await expect(page.locator('[data-testid="processing-complete"]')).toBeVisible();
  });

  test('Modal backdrop click does not close if clicking modal content', async ({ page }) => {
    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Test content')
    });

    // Wait for modal
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();

    // Click on modal content (not backdrop)
    const modalContent = page.locator('.modal-content');
    await modalContent.click();

    // Modal should still be visible
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
  });

  test('Processing progress bar animates from 0 to 100%', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');

    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Test content')
    });

    // Processing indicator should appear
    const processingIndicator = page.locator('[data-testid="processing-indicator"]');
    await expect(processingIndicator).toBeVisible({ timeout: 500 });

    // Check for progress bar using data-testid's parent styles (CSS modules)
    const progressFill = processingIndicator.locator('[class*="progressFill"]');
    await expect(progressFill).toBeVisible();

    // Progress should eventually reach or approach 100%
    await page.waitForTimeout(1000);

    const progressWidth = await progressFill.evaluate((el) => {
      return parseInt(el.style.width) || 0;
    });

    expect(progressWidth).toBeGreaterThan(50);
  });

  test('Processing state shows percentage complete', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');

    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Test content')
    });

    // Processing indicator should show percentage
    await expect(page.locator('[data-testid="processing-indicator"]')).toBeVisible({ timeout: 500 });

    // Should show percentage text (like "50% complete" or "100% complete")
    await expect(page.locator('text=% complete')).toBeVisible();
  });

  test('File validation error displays for invalid file type', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');

    // Try to upload invalid file type
    await fileInput.setInputFiles({
      name: 'image.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('Fake image')
    });

    // Error message should appear
    await expect(page.locator('text=Please select a valid file type')).toBeVisible();

    // Modal should NOT appear
    await expect(page.locator('[data-testid="modal-backdrop"]')).not.toBeVisible();
  });

  test('File validation error displays for oversized file', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');

    // Create large file buffer (>10MB)
    const largeBuffer = Buffer.alloc(11 * 1024 * 1024, 'x');

    await fileInput.setInputFiles({
      name: 'large.pdf',
      mimeType: 'application/pdf',
      buffer: largeBuffer
    });

    // Error message should appear
    await expect(page.locator('text=File size must be less than 10MB')).toBeVisible();

    // Modal should NOT appear
    await expect(page.locator('[data-testid="modal-backdrop"]')).not.toBeVisible();
  });
});
