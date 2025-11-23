const { chromium } = require('playwright');

async function testScenario1() {
    console.log('🚀 Starting Scenario 1: Free user - Small batch (5 citations)');

    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Enable console logging
    page.on('console', msg => {
        console.log('📝 Console:', msg.type(), msg.text());
    });

    // Enable network logging
    page.on('request', request => {
        if (request.url().includes('/api/')) {
            console.log('🌐 API Request:', request.method(), request.url());
        }
    });

    page.on('response', response => {
        if (response.url().includes('/api/')) {
            console.log('📡 API Response:', response.status(), response.url());
        }
    });

    try {
        // Navigate to the app with wait until networkidle
        console.log('📍 Opening http://localhost:5173/');
        await page.goto('http://localhost:5173/', {
            waitUntil: 'networkidle',
            timeout: 30000
        });

        // Wait a bit more for React to mount
        await page.waitForTimeout(2000);

        // Wait for page to load (TipTap editor)
        await page.waitForSelector('.ProseMirror', { timeout: 15000 });
        console.log('✅ Page loaded successfully');

        // Clear localStorage
        console.log('🧹 Clearing localStorage...');
        await page.evaluate(() => localStorage.clear());

        // Sample test citations (5 simple ones)
        const testCitations = `Smith, J. (2023). The impact of artificial intelligence on modern society. Journal of Technology Studies, 45(2), 123-145.
Johnson, M. K. (2023). Climate change and renewable energy: A comprehensive review. Environmental Science Quarterly, 78(4), 567-589.
Williams, R. A. (2023). Educational psychology in the digital age. Learning and Instruction, 67, 101-115.
Brown, T. L. (2023). Global supply chain management: Challenges and opportunities. Business Logistics Review, 12(3), 234-251.
Davis, S. M. (2023). Public health in post-pandemic era. Health Policy Journal, 23(1), 45-67.`;

        console.log('📝 Filling TipTap editor...');
        await page.fill('.ProseMirror', testCitations);

        // Submit the form
        console.log('🚀 Clicking submit button...');
        await page.click('button[type="submit"]');

        // Monitor for loading state
        console.log('⏳ Waiting for loading state...');

        // Wait for either results or loading indicator
        await page.waitForTimeout(2000); // Give it time to start processing

        // Check for loading state or results within reasonable time (should be ~20 seconds for 5 citations)
        console.log('👀 Monitoring for completion...');

        let foundResults = false;
        let foundLoading = false;

        // Check for loading state first
        try {
            await page.waitForSelector('.loading, .spinner, [data-loading="true"], .progress', { timeout: 5000 });
            foundLoading = true;
            console.log('✅ Loading state detected');
        } catch (e) {
            console.log('⚠️  No explicit loading state found, checking for results...');
        }

        // Wait up to 60 seconds for results (5 citations may take ~35 seconds with OpenAI)
        try {
            await page.waitForSelector('.results, .validation-results, .citations-output', { timeout: 60000 });
            foundResults = true;
            console.log('✅ Results displayed successfully');
        } catch (e) {
            console.log('❌ Results not found within 60 seconds');

            // Check final job status manually
            try {
                const finalJobStatus = await page.evaluate(() => {
                    const jobId = localStorage.getItem('current_job_id');
                    return jobId ? { jobId, hasJobId: true } : { hasJobId: false };
                });
                console.log('📊 Final job status check:', finalJobStatus);
            } catch (jobCheckError) {
                console.log('⚠️ Could not check final job status:', jobCheckError.message);
            }
        }

        // Check localStorage for current_job_id
        const jobId = await page.evaluate(() => localStorage.getItem('current_job_id'));
        if (jobId) {
            console.log('❌ ERROR: current_job_id still in localStorage after completion:', jobId);
        } else {
            console.log('✅ current_job_id correctly removed from localStorage');
        }

        // Check for any errors
        const errors = await page.$$eval('.error, .alert-danger', els => els.map(el => el.textContent));
        if (errors.length > 0) {
            console.log('❌ Errors found:', errors);
        }

        // Get final status
        console.log('\n📊 Test Results:');
        console.log('- Loading state found:', foundLoading);
        console.log('- Results found:', foundResults);
        console.log('- Job ID cleanup:', !jobId);
        console.log('- Errors on page:', errors.length);

        if (foundResults && !jobId && errors.length === 0) {
            console.log('\n✅ SCENARIO 1 PASSED!');
        } else {
            console.log('\n❌ SCENARIO 1 FAILED!');
        }

        // Take screenshot for verification
        await page.screenshot({ path: 'scenario1-results.png', fullPage: true });
        console.log('📸 Screenshot saved as scenario1-results.png');

    } catch (error) {
        console.error('❌ Test failed with error:', error);
        await page.screenshot({ path: 'scenario1-error.png', fullPage: true });
    } finally {
        await browser.close();
    }
}

testScenario1();