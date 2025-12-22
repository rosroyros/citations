/**
 * Analytics testing helper functions for Google Analytics 4 network request parsing
 */

// Test configuration
export const TEST_CONFIG = {
  baseUrl: 'https://citationformatchecker.com',
  trackingId: 'G-RZWHZQP8N9',
  utmParams: {
    utm_source: 'analytics_test',
    utm_medium: 'playwright',
    utm_campaign: 'analytics_validation'
  }
};

/**
 * Parse event name from Google Analytics URL
 * @param {string} url - GA request URL
 * @returns {string|null} Event name or null if not found
 */
export function getEventName(url) {
  try {
    const urlObj = new URL(url);
    return urlObj.searchParams.get('en') || null;
  } catch (e) {
    return null;
  }
}

/**
 * Parse event parameter from Google Analytics URL
 * @param {string} url - GA request URL
 * @param {string} paramName - Parameter name (without 'ep.' prefix)
 * @returns {string|null} Parameter value or null if not found
 */
export function getEventParam(url, paramName) {
  try {
    const urlObj = new URL(url);
    return urlObj.searchParams.get(`ep.${paramName}`) || null;
  } catch (e) {
    return null;
  }
}

/**
 * Get tracking ID from Google Analytics URL
 * @param {string} url - GA request URL
 * @returns {string|null} Tracking ID or null if not found
 */
export function getTrackingId(url) {
  try {
    const urlObj = new URL(url);
    return urlObj.searchParams.get('tid') || null;
  } catch (e) {
    return null;
  }
}

/**
 * Filter requests by event name
 * @param {Array} requests - Array of request objects
 * @param {string} eventName - Event name to filter by
 * @returns {Array} Filtered requests matching the event name
 */
export function getEventsByName(requests, eventName) {
  return requests.filter(request => getEventName(request.url()) === eventName);
}

/**
 * Print summary of captured analytics events
 * @param {Array} requests - Array of request objects
 */
export function printEventSummary(requests) {
  console.log(`\n=== Analytics Event Summary ===`);
  console.log(`Total events captured: ${requests.length}`);

  const eventCounts = {};
  requests.forEach(request => {
    const eventName = getEventName(request.url());
    eventCounts[eventName] = (eventCounts[eventName] || 0) + 1;
  });

  Object.entries(eventCounts).forEach(([eventName, count]) => {
    console.log(`  ${eventName}: ${count}`);
  });
  console.log(`===============================\n`);
}

/**
 * Setup request interception for Google Analytics requests
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @returns {Array} Array to store captured requests
 */
export function setupAnalyticsCapture(page) {
  const capturedRequests = [];

  // Intercept Google Analytics requests
  page.on('request', request => {
    const url = request.url();

    // Check if this is a Google Analytics request
    if (url.includes('/g/collect') && (url.includes('google-analytics.com') || url.includes('analytics.google.com'))) {
      capturedRequests.push(request);
      console.log(`🎯 GA Event Captured: ${getEventName(url) || 'unknown'}`);
    }
  });

  return capturedRequests;
}

/**
 * Build test URL with UTM parameters
 * @param {string} path - Page path (e.g., '/', '/citate-apa')
 * @returns {string} Complete URL with UTM parameters
 */
export function buildTestUrl(path) {
  const url = new URL(path, TEST_CONFIG.baseUrl);

  Object.entries(TEST_CONFIG.utmParams).forEach(([key, value]) => {
    url.searchParams.set(key, value);
  });

  return url.toString();
}

/**
 * Wait for specific analytics event to be captured
 * Polls the live array reference for new events
 * @param {Array} capturedRequests - Array of captured requests (live reference)
 * @param {string} eventName - Event name to wait for
 * @param {number|object} timeoutOrOptions - Timeout in ms, or options object { timeout, minCount }
 * @returns {Promise<boolean>} True if event was captured
 */
export async function waitForEvent(capturedRequests, eventName, timeoutOrOptions = 10000) {
  // Support both old API (timeout number) and new API (options object)
  const options = typeof timeoutOrOptions === 'number'
    ? { timeout: timeoutOrOptions, minCount: 1 }
    : { timeout: 10000, minCount: 1, ...timeoutOrOptions };

  const { timeout, minCount } = options;
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const events = getEventsByName(capturedRequests, eventName);
    if (events.length >= minCount) {
      return true;
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  return false;
}