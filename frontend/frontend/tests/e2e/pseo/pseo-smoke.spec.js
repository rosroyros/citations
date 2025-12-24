import { test, expect } from '@playwright/test';

/**
 * PSEO Smoke Tests
 * 
 * Tests for programmatic SEO pages to catch deployment regressions.
 * 
 * Note: PSEO page tests require production environment (nginx routing).
 * When running locally against dev server, PSEO page tests are skipped.
 * Sitemap tests work in all environments.
 * 
 * @tags smoke, pseo
 */

const isLocalDev = (process.env.BASE_URL || 'http://localhost:5173').includes('localhost');

test.describe('PSEO Smoke Tests', () => {

    // ═══════════════════════════════════════════════════════════════════
    // SITEMAP TESTS - Work in all environments
    // ═══════════════════════════════════════════════════════════════════

    test('sitemap is valid XML with expected URLs', async ({ request }) => {
        const response = await request.get('/sitemap.xml');
        expect(response.status()).toBe(200);

        const body = await response.text();

        // Valid XML structure
        expect(body).toContain('<?xml');
        expect(body).toContain('<urlset');

        // Contains PSEO pages (spot check)
        expect(body).toContain('/cite-youtube-apa/');
        expect(body).toContain('/cite-wikipedia-apa/');

        // URL count sanity check (currently ~195)
        const urlCount = (body.match(/<url>/g) || []).length;
        expect(urlCount).toBeGreaterThan(100);
    });

    // ═══════════════════════════════════════════════════════════════════
    // PSEO PAGE TESTS - Production only (require nginx routing)
    // ═══════════════════════════════════════════════════════════════════

    test('PSEO page loads with correct SEO elements', async ({ page }) => {
        test.skip(isLocalDev, 'PSEO pages require nginx routing (prod only)');

        await page.goto('/cite-youtube-apa/');

        // Single H1 (SEO requirement)
        const h1s = page.locator('h1');
        await expect(h1s).toHaveCount(1);
        await expect(h1s.first()).toContainText(/YouTube/i);

        // SEO meta tags
        await expect(page.locator('meta[name="description"]')).toBeAttached();
        await expect(page.locator('link[rel="canonical"]')).toBeAttached();
        await expect(page.locator('script[type="application/ld+json"]')).toBeAttached();

        // MiniChecker visible
        await expect(page.locator('.mini-checker').first()).toBeVisible();
    });

    test('PSEO page navigation and interaction', async ({ page }) => {
        test.skip(isLocalDev, 'PSEO pages require nginx routing (prod only)');

        await page.goto('/cite-youtube-apa/');

        // MiniChecker is interactive
        const textarea = page.locator('.mini-checker textarea').first();
        await expect(textarea).toBeEditable();
        await textarea.fill('Test citation');
        await expect(page.locator('.mini-checker button').first()).toBeEnabled();

        // Navigation links present
        await expect(page.locator('.logo[href="/"]')).toBeAttached();
        await expect(page.locator('a[href="/privacy"]')).toBeAttached();
    });

    test('sitemap URLs are accessible', async ({ request }) => {
        test.skip(isLocalDev, 'PSEO pages require nginx routing (prod only)');

        // Sample 3 PSEO URLs from sitemap
        const sitemapResponse = await request.get('/sitemap.xml');
        const sitemap = await sitemapResponse.text();

        const urlMatches = sitemap.match(/<loc>[^<]*cite-[^<]*<\/loc>/g) || [];
        const sampleUrls = urlMatches.slice(0, 3).map(m =>
            m.replace('<loc>', '').replace('</loc>', '')
                .replace('https://citationformatchecker.com', '')
        );

        for (const url of sampleUrls) {
            const response = await request.get(url);
            expect(response.status(), `${url} should return 200`).toBe(200);
        }
    });
});
