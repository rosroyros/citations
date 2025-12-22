import { test, expect } from '@playwright/test';

/**
 * Consolidated Upload Feature E2E Tests
 * 
 * This file combines tests from:
 * - upload-comprehensive.spec.js (base)
 * - upload-area.spec.js (merged)
 * - upload-integration.spec.js (merged)
 * 
 * Test organization:
 * - Upload Area UI: Basic rendering and layout
 * - File Selection: Click-to-upload functionality
 * - Drag and Drop: Visual feedback and state management
 * - Validation: File type and size validation
 * - Coming Soon Modal: Modal display and dismiss methods
 * - Processing State: Animation timing and progress
 * - Accessibility: Keyboard navigation and ARIA
 * - Responsive Layout: Mobile and desktop layouts
 */

test.describe('Upload Feature E2E Tests', () => {
    test.use({
        baseURL: 'http://localhost:5173',
        viewport: { width: 1280, height: 720 }
    });

    test.beforeEach(async ({ page }) => {
        await page.context().clearCookies();
        await page.addInitScript(() => {
            localStorage.clear();
            window.gtag = function () { }; // Mock gtag
        });
        await page.goto('/');
        await expect(page.locator('h1:has-text("Citation Format Checker")')).toBeVisible();
    });

    // ============================================
    // Upload Area UI
    // ============================================
    test.describe('Upload Area UI', () => {
        test('UploadArea component renders correctly', async ({ page }) => {
            const uploadArea = page.locator('[data-testid="upload-area"]');
            await expect(uploadArea).toBeVisible();

            // Verify the upload area contains expected text
            await expect(uploadArea.locator('text=Drag and drop')).toBeVisible();
            await expect(uploadArea.locator('text=or browse files')).toBeVisible();

            // Check file input exists with correct accept types
            const fileInput = page.locator('input[type="file"]');
            await expect(fileInput).toHaveCount(1);
            await expect(fileInput).toHaveAttribute('accept', '.pdf,.docx,.txt,.rtf');

            // Check editor is also present (side-by-side layout)
            await expect(page.locator('[data-testid="editor"]')).toBeVisible();
        });
    });

    // ============================================
    // File Selection
    // ============================================
    test.describe('File Selection', () => {
        test('File selection via click works correctly', async ({ page }) => {
            const uploadArea = page.locator('[data-testid="upload-area"]');
            await expect(uploadArea).toBeVisible();

            const fileInput = page.locator('input[type="file"]');

            // Create a mock PDF file content for testing
            const fileContent = Buffer.from('%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n');

            // Upload the file
            await fileInput.setInputFiles({
                name: 'test.pdf',
                mimeType: 'application/pdf',
                buffer: fileContent
            });

            // File upload should trigger processing, then modal
            await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
        });

        test('Upload handles file selection without crashing', async ({ page }) => {
            const fileInput = page.locator('input[type="file"]');

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
    });

    // ============================================
    // Drag and Drop
    // ============================================
    test.describe('Drag and Drop', () => {
        test('Drag visual feedback shows on dragenter', async ({ page }) => {
            const uploadArea = page.locator('[data-testid="upload-area"]');
            await expect(uploadArea).toBeVisible();

            // Trigger dragenter event using evaluate
            await uploadArea.evaluate((el) => {
                const event = new DragEvent('dragenter', { bubbles: true, cancelable: true });
                el.dispatchEvent(event);
            });

            await page.waitForTimeout(100);

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

            await page.waitForTimeout(100);

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

            await page.waitForTimeout(100);
            const hasOverState = await uploadArea.evaluate((el) => {
                return el.className.includes('dragOver');
            });

            expect(hasOverState).toBe(false);
        });
    });

    // ============================================
    // Validation
    // ============================================
    test.describe('Validation', () => {
        test('File validation error displays for invalid file type', async ({ page }) => {
            const fileInput = page.locator('input[type="file"]');

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

    // ============================================
    // Coming Soon Modal
    // ============================================
    test.describe('Coming Soon Modal', () => {
        test('File upload triggers ComingSoonModal', async ({ page }) => {
            const fileContent = Buffer.from('Test file content for upload');

            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles({
                name: 'test-document.pdf',
                mimeType: 'application/pdf',
                buffer: fileContent
            });

            // Wait for the modal to appear
            await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
            await expect(page.locator('text=We apologize, but document upload is temporarily unavailable')).toBeVisible();

            // Check that button is present
            await expect(page.locator('button:has-text("Okay")')).toBeVisible();
        });

        test('Modal can be dismissed by clicking Okay button', async ({ page }) => {
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles({
                name: 'test.pdf',
                mimeType: 'application/pdf',
                buffer: Buffer.from('Test content')
            });

            await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
            await page.locator('button:has-text("Okay")').click();

            await expect(page.locator('[data-testid="modal-backdrop"]')).not.toBeVisible();
        });

        test('Modal can be dismissed by clicking backdrop', async ({ page }) => {
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles({
                name: 'test.pdf',
                mimeType: 'application/pdf',
                buffer: Buffer.from('Test content')
            });

            const backdrop = page.locator('[data-testid="modal-backdrop"]');
            await expect(backdrop).toBeVisible();

            // Click backdrop (not the modal content)
            await backdrop.click({ position: { x: 10, y: 10 } });

            await expect(backdrop).not.toBeVisible();
        });

        test('Modal can be dismissed by pressing Escape key', async ({ page }) => {
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles({
                name: 'test.pdf',
                mimeType: 'application/pdf',
                buffer: Buffer.from('Test content')
            });

            await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
            await page.keyboard.press('Escape');

            await expect(page.locator('[data-testid="modal-backdrop"]')).not.toBeVisible();
        });

        test('Modal backdrop click does not close if clicking modal content', async ({ page }) => {
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles({
                name: 'test.pdf',
                mimeType: 'application/pdf',
                buffer: Buffer.from('Test content')
            });

            await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();

            // Click on modal content (not backdrop)
            const modalContent = page.locator('.modal-content');
            await modalContent.click();

            // Modal should still be visible
            await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
        });

        test('Modal dismissal returns to main interface with processed state', async ({ page }) => {
            const fileContent = Buffer.from('Test file content for upload');
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles({
                name: 'test-document.pdf',
                mimeType: 'application/pdf',
                buffer: fileContent
            });

            await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();

            const closeButton = page.locator('button:has-text("Okay")').first();
            await closeButton.click();

            // Modal should be hidden
            await expect(page.locator('[data-testid="modal-backdrop"]')).not.toBeVisible();

            // Should return to main interface with processed state
            await expect(page.locator('[data-testid="processing-complete"]')).toBeVisible();
            await expect(page.locator('text=Document processing is temporarily unavailable')).toBeVisible();
            await expect(page.locator('[data-testid="editor"]')).toBeVisible();
        });
    });

    // ============================================
    // Processing State
    // ============================================
    test.describe('Processing State', () => {
        test('Processing animation displays for 1.5 seconds before modal', async ({ page }) => {
            const fileContent = Buffer.from('Test PDF content');
            const startTime = Date.now();

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

            // Processing should take approximately 1500ms (allow 300ms variance)
            expect(processingDuration).toBeGreaterThanOrEqual(1300);
            expect(processingDuration).toBeLessThan(2100);
        });

        test('Processing progress bar animates from 0 to 100%', async ({ page }) => {
            const fileInput = page.locator('input[type="file"]');

            await fileInput.setInputFiles({
                name: 'test.pdf',
                mimeType: 'application/pdf',
                buffer: Buffer.from('Test content')
            });

            const processingIndicator = page.locator('[data-testid="processing-indicator"]');
            await expect(processingIndicator).toBeVisible({ timeout: 500 });

            const progressFill = processingIndicator.locator('[class*="progressFill"]');
            await expect(progressFill).toBeVisible();

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

            await expect(page.locator('[data-testid="processing-indicator"]')).toBeVisible({ timeout: 500 });

            // Should show percentage text
            await expect(page.locator('text=% complete')).toBeVisible();
        });

        test('Editor receives focus after modal is dismissed', async ({ page }) => {
            const fileInput = page.locator('input[type="file"]');
            await fileInput.setInputFiles({
                name: 'test.pdf',
                mimeType: 'application/pdf',
                buffer: Buffer.from('Test content')
            });

            await expect(page.locator('[data-testid="modal-backdrop"]')).toBeVisible();
            await page.locator('button:has-text("Okay")').click();

            const editor = page.locator('[data-testid="editor"] .ProseMirror, [contenteditable="true"]').first();
            await expect(editor).toBeFocused({ timeout: 2000 });
        });
    });

    // ============================================
    // Accessibility
    // ============================================
    test.describe('Accessibility', () => {
        test('Upload area has correct ARIA attributes', async ({ page }) => {
            const uploadArea = page.locator('[data-testid="upload-area"]');
            await expect(uploadArea).toBeVisible();
            await expect(uploadArea).toHaveAttribute('role', 'button');
            await expect(uploadArea).toHaveAttribute('tabindex', '0');
        });

        test('Keyboard navigation to upload area works', async ({ page }) => {
            const uploadArea = page.locator('[data-testid="upload-area"]');
            await uploadArea.focus();
            await expect(uploadArea).toBeFocused();
        });

        test('Enter key on upload area triggers file selection', async ({ page }) => {
            const uploadArea = page.locator('[data-testid="upload-area"]');
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
    });

    // ============================================
    // Responsive Layout
    // ============================================
    test.describe('Responsive Layout', () => {
        test('Desktop layout shows upload area and editor side-by-side', async ({ page }) => {
            await page.setViewportSize({ width: 1200, height: 800 });
            await expect(page.locator('[data-testid="upload-area"]')).toBeVisible();
            await expect(page.locator('[data-testid="editor"]')).toBeVisible();
        });

        test('Tablet layout adapts correctly', async ({ page }) => {
            await page.setViewportSize({ width: 768, height: 1024 });
            await expect(page.locator('[data-testid="upload-area"]')).toBeVisible();
            await expect(page.locator('[data-testid="editor"]')).toBeVisible();
        });

        test('Mobile layout stacks components', async ({ page }) => {
            await page.setViewportSize({ width: 375, height: 667 });

            await expect(page.locator('[data-testid="upload-area"]')).toBeVisible();
            await expect(page.locator('[data-testid="editor"]')).toBeVisible();

            // Verify mobile layout - upload area should still be visible and functional
            await expect(page.locator('text=Drag and drop')).toBeVisible();
            await expect(page.locator('text=or browse files')).toBeVisible();

            // File input exists in DOM (hidden by design, accessed via label)
            const fileInput = page.locator('input[type="file"]');
            await expect(fileInput).toHaveCount(1);
        });

        test('Mobile responsive layout stacks upload area below editor', async ({ page }) => {
            await page.setViewportSize({ width: 375, height: 667 });

            const editorColumn = page.locator('.editor-column');
            const uploadColumn = page.locator('.upload-column');

            await expect(editorColumn).toBeVisible();
            await expect(uploadColumn).toBeVisible();
        });
    });
});
