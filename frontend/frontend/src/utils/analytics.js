/**
 * Analytics utility functions for Google Analytics tracking
 */

/**
 * Safely tracks an event using gtag, checking if gtag exists first
 * @param {string} eventName - The name of the event to track
 * @param {Object} params - Additional parameters to send with the event
 */
export const trackEvent = (eventName, params = {}) => {
  if (typeof window !== 'undefined' && typeof window.gtag === 'function') {
    window.gtag('event', eventName, params);
  } else {
    // In development or when gtag is not available, log to console for debugging
    console.debug('Analytics Event:', eventName, params);
  }
};