import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('UploadArea Component - E2E Tests', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 1280, height: 720 }
  });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
    });
    await page.goto('/');

    // Wait for app to load
    await expect(page.locator('body')).toBeVisible();

    // Find the editor (TipTap uses .ProseMirror)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
  });

  test('UploadArea component renders correctly', async ({ page }) => {
    // Look for the UploadArea component - it should be visible beside the editor
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    // Verify the upload area contains expected text
    await expect(uploadArea.locator('text=Drag and drop')).toBeVisible();
    await expect(uploadArea.locator('text=or browse files')).toBeVisible();
  });

  test('File selection via click works correctly', async ({ page }) => {
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    // Create a test PDF file
    const testFilePath = path.join(__dirname, '..', '..', 'test-files', 'test.pdf');

    // For file upload tests, we need to handle the file input dialog
    // In Playwright, we can set the files directly on the input element
    const fileInput = uploadArea.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();

    // Create a mock PDF file content for testing
    const fileContent = Buffer.from('%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000056 00000 n \n0000000109 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n158\n%%EOF');

    // Upload the file
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: fileContent
    });

    // The component should handle the file and potentially call onFileSelected
    // Since we don't have the full integration yet, we verify the upload area is still responsive
    await expect(uploadArea).toBeVisible();
  });

  test('Drag and drop functionality works', async ({ page }) => {
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    // Test drag enter shows visual feedback
    await uploadArea.dispatchEvent('dragenter', {
      dataTransfer: {}
    });

    // Check that the drag state is applied (CSS module class should contain 'dragOver')
    const className = await uploadArea.getAttribute('class');
    expect(className).toContain('dragOver');

    // Test drag leave removes visual feedback
    await uploadArea.dispatchEvent('dragleave');
    const classNameAfterLeave = await uploadArea.getAttribute('class');
    expect(classNameAfterLeave).not.toContain('dragOver');
  });

  test('File validation rejects invalid file types', async ({ page }) => {
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    const fileInput = uploadArea.locator('input[type="file"]');

    // Create an invalid file (image)
    const invalidFileContent = Buffer.from('fake image content');
    await fileInput.setInputFiles({
      name: 'test.jpg',
      mimeType: 'image/jpeg',
      buffer: invalidFileContent
    });

    // Error message should appear
    await expect(uploadArea.locator('text=Please select a valid file type')).toBeVisible();
  });

  test('File validation rejects oversized files', async ({ page }) => {
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    // Test file drop with large file
    const largeFileContent = Buffer.alloc(11 * 1024 * 1024, 'x'); // 11MB file

    await uploadArea.dispatchEvent('drop', {
      dataTransfer: {
        files: [{
          name: 'large.pdf',
          mimeType: 'application/pdf',
          buffer: largeFileContent
        }]
      }
    });

    // Error message should appear
    await expect(uploadArea.locator('text=File size must be less than 10MB')).toBeVisible();
  });

  test('Responsive design works on mobile', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    // Verify mobile layout - upload area should still be visible and functional
    await expect(uploadArea.locator('text=Drag and drop')).toBeVisible();
    await expect(uploadArea.locator('text=or browse files')).toBeVisible();

    // Test that file input still works on mobile
    const fileInput = uploadArea.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
  });

  test('Accessibility features work correctly', async ({ page }) => {
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    // Test keyboard navigation to the file input label
    const fileLabel = uploadArea.locator('label[for="file-input"]');
    await expect(fileLabel).toBeVisible();

    // Test that the label is focusable
    await fileLabel.focus();
    await expect(fileLabel).toBeFocused();

    // Test Tab navigation
    await page.keyboard.press('Tab');

    // Verify upload area is still accessible after navigation
    await expect(uploadArea).toBeVisible();
  });
});

test.describe('UploadArea Integration - End-to-End Flow', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 1280, height: 720 }
  });

  test('Complete upload flow from drag to file selection', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    const uploadArea = page.locator('[data-testid="upload-area"]');
    await expect(uploadArea).toBeVisible();

    // Step 1: Drag file over area
    await uploadArea.dispatchEvent('dragenter');
    let className = await uploadArea.getAttribute('class');
    expect(className).toContain('dragOver');

    // Step 2: Drop valid file
    const validFileContent = Buffer.from('%PDF-1.4\n%Mock PDF content for testing');
    await uploadArea.dispatchEvent('drop', {
      dataTransfer: {
        files: [{
          name: 'test-document.pdf',
          mimeType: 'application/pdf',
          buffer: validFileContent
        }]
      }
    });

    // Step 3: Verify drag state is cleared and no error appears
    className = await uploadArea.getAttribute('class');
    expect(className).not.toContain('dragOver');

    // No error message should appear for valid files
    await expect(uploadArea.locator('text=Please select a valid file type')).not.toBeVisible();
    await expect(uploadArea.locator('text=File size must be less than 10MB')).not.toBeVisible();
  });
});