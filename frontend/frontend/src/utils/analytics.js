/**
 * Analytics utility functions for Google Analytics tracking
 */

/**
 * Safely tracks an event using gtag, checking if gtag exists first
 * @param {string} eventName - The name of the event to track
 * @param {Object} params - Additional parameters to send with the event
 */
export const trackEvent = (eventName, params = {}) => {
  // DEBUG: Log all tracking attempts
  console.log('🔍 [Analytics] trackEvent called:', eventName, params);
  console.log('🔍 [Analytics] window.gtag exists?', typeof window !== 'undefined' && typeof window.gtag === 'function');

  if (typeof window !== 'undefined' && typeof window.gtag === 'function') {
    console.log('✅ [Analytics] Firing gtag event:', eventName);
    window.gtag('event', eventName, params);
  } else {
    // In development or when gtag is not available, log to console for debugging
    console.warn('⚠️ [Analytics] gtag not available, event not sent:', eventName, params);
  }
};