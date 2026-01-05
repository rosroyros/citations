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

/**
 * Track inline citation validation completion.
 *
 * Called when a full_doc validation completes successfully.
 *
 * @param {string} jobId - Job identifier
 * @param {number} inlineCitationCount - Number of inline citations found
 * @param {number} orphanCount - Number of orphan citations
 * @param {string} validationType - "full_doc" or "ref_only"
 */
export const trackInlineValidation = (jobId, inlineCitationCount, orphanCount, validationType) => {
  trackEvent('inline_validation_completed', {
    job_id: jobId,
    inline_citation_count: inlineCitationCount,
    orphan_count: orphanCount,
    validation_type: validationType,
    has_orphans: orphanCount > 0
  });
};

/**
 * Track document upload.
 *
 * Called when user uploads a DOCX file.
 *
 * @param {string} fileName - Name of uploaded file
 * @param {number} fileSize - Size in bytes
 * @param {boolean} success - Whether upload succeeded
 */
export const trackDocumentUpload = (fileName, fileSize, success) => {
  trackEvent('document_upload', {
    file_name: fileName,
    file_size_kb: Math.round(fileSize / 1024),
    success: success
  });
};

/**
 * Track orphan citation click.
 *
 * Called when user clicks on an orphan citation for more info.
 *
 * @param {string} citationText - The orphan citation text
 */
export const trackOrphanClick = (citationText) => {
  trackEvent('orphan_citation_click', {
    citation_text: citationText
  });
};