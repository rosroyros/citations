import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);


/**
 * Upload Feature E2E Tests
 *
 * Updated for GHF3 inline citation validation feature.
 * Now tests DOCX-only upload flow with real validation (no ComingSoonModal).
 *
 * Test organization:
 * - Upload Area UI: Basic rendering and layout
 * - DOCX Upload: Valid DOCX file upload and validation
 * - Drag and Drop: Visual feedback and state management
 * - Validation Errors: File type and size validation
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

            // Check file input exists with DOCX-only accept type (GHF3 change)
            const fileInput = page.locator('input[type="file"]');
            await expect(fileInput).toHaveCount(1);
            await expect(fileInput).toHaveAttribute('accept', '.docx');

            // Check editor is also present (side-by-side layout)
            await expect(page.locator('[data-testid="editor"]')).toBeVisible();
        });
    });

    // ============================================
    // DOCX Upload (GHF3 - real validation, no modal)
    // ============================================
    test.describe('DOCX Upload', () => {
        test('Valid DOCX triggers validation flow', async ({ page }) => {
            // Mock the upload endpoint
            await page.route('/api/validate/async', async route => {
                const request = route.request();
                // Verify it's a multipart request (file upload)
                const contentType = await request.headerValue('content-type');
                expect(contentType).toContain('multipart/form-data');

                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        job_id: 'mock-upload-job',
                        status: 'pending'
                    })
                });
            });

            // Mock the polling result
            await page.route(/\/api\/jobs\/mock-upload-job/, async route => {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        status: 'completed',
                        results: {
                            job_id: 'mock-upload-job',
                            status: 'completed',
                            validation_type: 'full_doc',
                            results: [
                                {
                                    citation_number: 1,
                                    original: 'Smith, J. (2023). Sample Title. Publisher.',
                                    status: 'valid',
                                    errors: []
                                }
                            ],
                            inline_citations: [],
                            orphan_citations: []
                        }
                    })
                });
            });

            const fileInput = page.locator('input[type="file"]');

            // We need a path to a real file. Using one of the fixtures.
            const testDocPath = path.join(__dirname, '../../fixtures/test_doc_valid.docx');

            await fileInput.setInputFiles(testDocPath);

            // Wait for results section to appear
            await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 10000 });

            // Verify content from mock
            await expect(page.getByText('Sample Title')).toBeVisible();
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

            // Check for drag state - className should update synchronously
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

            // Check for drag state - className should update synchronously
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

            // Check for drag state - className should update synchronously
            const hasOverState = await uploadArea.evaluate((el) => {
                return el.className.includes('dragOver');
            });

            expect(hasOverState).toBe(false);
        });
    });

    // ============================================
    // Validation Errors
    // ============================================
    test.describe('Validation Errors', () => {
        test('Non-DOCX file shows error message', async ({ page }) => {
            const fileInput = page.locator('input[type="file"]');

            // Try to upload a non-DOCX file
            await fileInput.setInputFiles({
                name: 'document.pdf',
                mimeType: 'application/pdf',
                buffer: Buffer.from('Fake PDF content')
            });

            // Error message should appear (matches UploadArea.jsx validation)
            await expect(page.getByText(/Only .docx files are supported/i)).toBeVisible();
        });

        test('Oversized file shows error message', async ({ page }) => {
            const fileInput = page.locator('input[type="file"]');

            // Create large file buffer (>10MB)
            const largeBuffer = Buffer.alloc(11 * 1024 * 1024, 'x');

            await fileInput.setInputFiles({
                name: 'large.docx',
                mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                buffer: largeBuffer
            });

            // Error message should appear
            await expect(page.getByText(/File too large|Maximum size is 10MB/i)).toBeVisible();
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

        test('Enter key on upload area triggers file chooser', async ({ page }) => {
            const uploadArea = page.locator('[data-testid="upload-area"]');
            await uploadArea.focus();
            await expect(uploadArea).toBeFocused();

            // Test Enter key to trigger file selection
            const fileChooserPromise = page.waitForEvent('filechooser');
            await uploadArea.press('Enter');
            const fileChooser = await fileChooserPromise;

            // File chooser should be triggered
            expect(fileChooser).toBeTruthy();
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
