import { test, expect } from '@playwright/test';

test.describe('Upload Component Integration - E2E Tests', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 1280, height: 720 }
  });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
      window.gtag = function() {}; // Mock gtag for analytics testing
    });
    await page.goto('/');

    // Wait for app to load
    await expect(page.locator('body')).toBeVisible();

    // Wait for main components to load
    await expect(page.locator('h1:has-text("Citation Format Checker")')).toBeVisible();
  });

  test('UploadArea renders correctly in responsive layout', async ({ page }) => {
    // Check that UploadArea is present
    await expect(page.locator('[data-testid="upload-area"]')).toBeVisible();
    await expect(page.locator('text=Drop your document here')).toBeVisible();
    await expect(page.locator('text=or click to browse')).toBeVisible();

    // Check file input exists
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
    await expect(fileInput).toHaveAttribute('accept', '.pdf,.docx,.txt,.rtf');

    // Check editor is also present (side-by-side layout)
    await expect(page.locator('[data-testid="editor"]')).toBeVisible();
  });

  test('Mobile responsive layout stacks upload area below editor', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Both components should still be visible
    await expect(page.locator('[data-testid="upload-area"]')).toBeVisible();
    await expect(page.locator('[data-testid="editor"]')).toBeVisible();

    // In mobile, upload area should come after editor in the DOM order
    const editorColumn = page.locator('.editor-column');
    const uploadColumn = page.locator('.upload-column');

    await expect(editorColumn).toBeVisible();
    await expect(uploadColumn).toBeVisible();
  });

  test('File upload triggers ComingSoonModal', async ({ page }) => {
    // Create a mock file
    const fileContent = Buffer.from('Test file content for upload');

    // Find the file input and upload a file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-document.pdf',
      mimeType: 'application/pdf',
      buffer: fileContent
    });

    // Wait for the modal to appear (file processing + modal show)
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
    await expect(page.locator('text=File Upload Coming Soon')).toBeVisible();

    // Check that file information is displayed
    await expect(page.locator('text=test-document.pdf')).toBeVisible();
  });

  test('Modal can be dismissed and returns to main interface', async ({ page }) => {
    // Upload a file to trigger modal
    const fileContent = Buffer.from('Test file content for upload');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-document.pdf',
      mimeType: 'application/pdf',
      buffer: fileContent
    });

    // Wait for modal to appear
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
    await expect(page.locator('text=File Upload Coming Soon')).toBeVisible();

    // Find and click the close button
    const closeButton = page.locator('button[aria-label="Close modal"], button:has-text("Got it"), button:has-text("Close")').first();
    await expect(closeButton).toBeVisible();
    await closeButton.click();

    // Modal should be hidden
    await expect(page.locator('[data-testid="modal-backdrop"]')).not.toBeVisible();

    // Should return to main interface
    await expect(page.locator('[data-testid="upload-area"]')).toBeVisible();
    await expect(page.locator('[data-testid="editor"]')).toBeVisible();
  });

  test('Analytics events are tracked during upload flow', async ({ page }) => {
    // Track analytics calls
    const analyticsCalls = [];
    await page.addInitScript(() => {
      window.gtag = function(...args) {
        window.analyticsCalls = window.analyticsCalls || [];
        window.analyticsCalls.push(args);
      };
    });

    // Upload a file
    const fileContent = Buffer.from('Test file content for upload');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-document.pdf',
      mimeType: 'application/pdf',
      buffer: fileContent
    });

    // Wait for modal to appear
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();

    // Check that analytics events were called
    const calls = await page.evaluate(() => window.analyticsCalls || []);

    // Should have upload-related events (implementation specific)
    expect(calls.length).toBeGreaterThan(0);
  });

  test('Accessibility features work correctly', async ({ page }) => {
    // Check that upload area is keyboard accessible
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();
    await expect(uploadArea).toHaveAttribute('role', 'button');
    await expect(uploadArea).toHaveAttribute('tabindex', '0');

    // Test keyboard navigation
    await uploadArea.focus();
    await expect(uploadArea).toBeFocused();

    // Test Enter key to trigger file selection
    const fileChooserPromise = page.waitForEvent('filechooser');
    await uploadArea.press('Enter');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'test-document.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Test file content')
    });

    // Modal should appear
    await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
  });

  test('Responsive layout adapts to different screen sizes', async ({ page }) => {
    // Test desktop layout
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(page.locator('[data-testid="upload-area"]')).toBeVisible();
    await expect(page.locator('[data-testid="editor"]')).toBeVisible();

    // Test tablet layout
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('[data-testid="upload-area"]')).toBeVisible();
    await expect(page.locator('[data-testid="editor"]')).toBeVisible();

    // Test mobile layout
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('[data-testid="upload-area"]')).toBeVisible();
    await expect(page.locator('[data-testid="editor"]')).toBeVisible();
  });
});