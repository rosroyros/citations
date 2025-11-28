/**
 * Analytics utility functions for Google Analytics tracking
 */

/**
 * Safely tracks an event using gtag, checking if gtag exists first
 * @param {string} eventName - The name of the event to track
 * @param {Object} params - Additional parameters to send with the event
 */
export const trackEvent = (eventName, params = {}) => {
  // DEBUG: Log only in development
  if (process.env.NODE_ENV === 'development') {
    console.log('🔍 [Analytics] trackEvent called:', eventName, params);
    console.log('🔍 [Analytics] window.gtag exists?', typeof window !== 'undefined' && typeof window.gtag === 'function');
  }

  if (typeof window !== 'undefined' && typeof window.gtag === 'function') {
    if (process.env.NODE_ENV === 'development') {
      console.log('✅ [Analytics] Firing gtag event:', eventName);
    }
    window.gtag('event', eventName, params);
  } else {
    // In development or when gtag is not available, log to console for debugging
    if (process.env.NODE_ENV === 'development') {
      console.warn('⚠️ [Analytics] gtag not available, event not sent:', eventName, params);
    }
  }
};

/**
 * Track results revealed event for gated validation engagement
 * @param {string} jobId - Unique identifier for the validation job
 * @param {number} timeToReveal - Time in seconds between results ready and reveal
 * @param {string} userType - Type of user ('paid', 'free', 'anonymous')
 */
export const trackResultsRevealed = (jobId, timeToReveal, userType) => {
  if (typeof window !== 'undefined' && typeof window.gtag === 'function') {
    window.gtag('event', 'results_revealed', {
      job_id: jobId,
      time_to_reveal_seconds: timeToReveal,
      user_type: userType,
      validation_type: 'gated'
    });

    // DEBUG: Log only in development
    if (process.env.NODE_ENV === 'development') {
      console.log('🎯 [Analytics] Results revealed event tracked:', {
        job_id: jobId,
        time_to_reveal_seconds: timeToReveal,
        user_type: userType,
        validation_type: 'gated'
      });
    }
  }
};

/**
 * Validate tracking data before transmission
 * @param {string} jobId - Unique identifier for the validation job
 * @param {number} timeToReveal - Time in seconds between results ready and reveal
 * @returns {Object} Validation result with isValid flag and errors array
 */
export const validateTrackingData = (jobId, timeToReveal) => {
  const errors = [];

  if (!jobId || typeof jobId !== 'string' || jobId.trim() === '') {
    errors.push('jobId must be a non-empty string');
  }

  if (typeof timeToReveal !== 'number' || timeToReveal < 0) {
    errors.push('timeToReveal must be a non-negative number');
  }

  if (timeToReveal > 3600) { // 1 hour max
    errors.push('timeToReveal exceeds maximum allowed duration (3600 seconds)');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Safely track results revealed with validation
 * @param {string} jobId - Unique identifier for the validation job
 * @param {number} timeToReveal - Time in seconds between results ready and reveal
 * @param {string} userType - Type of user ('paid', 'free', 'anonymous')
 */
export const trackResultsRevealedSafe = (jobId, timeToReveal, userType) => {
  const validation = validateTrackingData(jobId, timeToReveal);

  if (!validation.isValid) {
    if (process.env.NODE_ENV === 'development') {
      console.warn('⚠️ [Analytics] Tracking data validation failed:', validation.errors);
    }
    return false;
  }

  try {
    trackResultsRevealed(jobId, timeToReveal, userType);
    return true;
  } catch (error) {
    if (process.env.NODE_ENV === 'development') {
      console.warn('⚠️ [Analytics] Failed to track results revealed:', error);
    }
    return false;
  }
};