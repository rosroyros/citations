import { useRef, useCallback } from 'react';
import { trackEvent } from '../utils/analytics';

/**
 * Hook for comprehensive upload analytics tracking
 * Tracks all upload-related events including user behavior, timing, and file metadata
 */
export const useUploadAnalytics = () => {
  const sessionStartTime = useRef(Date.now());
  const modalStartTime = useRef(null);
  const uploadAttempts = useRef(0);
  const textInputTransitions = useRef(0);
  const lastFileInfo = useRef(null);

  // Core Analytics Events

  const trackUploadAreaClicked = useCallback(() => {
    trackEvent('upload_area_clicked', {
      page: window.location.pathname,
      timestamp: Date.now()
    });
  }, []);

  const trackFileSelected = useCallback((file) => {
    uploadAttempts.current++;
    lastFileInfo.current = {
      name: file.name,
      type: file.type,
      size: file.size
    };

    const fileExtension = file.name.split('.').pop().toLowerCase();

    trackEvent('upload_file_selected', {
      file_name: file.name,
      file_size: file.size,
      file_type: file.type,
      file_extension: fileExtension,
      page: window.location.pathname,
      timestamp: Date.now()
    });
  }, []);

  const trackProcessingShown = useCallback((file) => {
    trackEvent('upload_processing_shown', {
      file_name: file.name,
      file_type: file.type,
      file_extension: file.name.split('.').pop().toLowerCase(),
      page: window.location.pathname,
      timestamp: Date.now()
    });
  }, []);

  const trackPreviewRendered = useCallback((file, processingTime) => {
    trackEvent('upload_file_preview_rendered', {
      file_name: file.name,
      file_type: file.type,
      file_extension: file.name.split('.').pop().toLowerCase(),
      processing_time_ms: processingTime,
      page: window.location.pathname,
      timestamp: Date.now()
    });
  }, []);

  const trackUploadCompletedDisabled = useCallback((file) => {
    modalStartTime.current = Date.now();

    // Store file info for modal close tracking
    lastFileInfo.current = {
      name: file.name,
      type: file.type,
      size: file.size
    };

    trackEvent('upload_completed_disabled', {
      file_name: file.name,
      file_type: file.type,
      file_extension: file.name.split('.').pop().toLowerCase(),
      page: window.location.pathname,
      timestamp: Date.now()
    });
  }, []);

  const trackModalClosed = useCallback((dismissMethod) => {
    const modalDuration = modalStartTime.current ? Date.now() - modalStartTime.current : 0;
    modalStartTime.current = null;

    // Preserve file info during modal close
    const fileInfo = { ...lastFileInfo.current };

    trackEvent('upload_modal_closed', {
      dismiss_method: dismissMethod,
      modal_duration_ms: modalDuration,
      file_name: fileInfo?.name || '',
      file_type: fileInfo?.type || '',
      file_extension: fileInfo?.name?.split('.').pop()?.toLowerCase() || '',
      page: window.location.pathname,
      timestamp: Date.now()
    });
  }, []);

  const trackTextInputTransition = useCallback(() => {
    textInputTransitions.current++;
    const modalDuration = modalStartTime.current ? Date.now() - modalStartTime.current : 0;
    modalStartTime.current = null;

    trackEvent('upload_text_input_transition', {
      modal_duration_ms: modalDuration,
      page: window.location.pathname,
      timestamp: Date.now()
    });
  }, []);

  // Enhanced Analytics Events

  const trackFormatSelection = useCallback((format) => {
    trackEvent('upload_format_selection', {
      selected_format: format,
      page: window.location.pathname,
      timestamp: Date.now()
    });
  }, []);

  const trackRetryAttempt = useCallback((file, attemptNumber) => {
    trackEvent('upload_retry_attempt', {
      attempt_number: attemptNumber,
      file_name: file.name,
      file_type: file.type,
      file_extension: file.name.split('.').pop().toLowerCase(),
      page: window.location.pathname,
      timestamp: Date.now()
    });
  }, []);

  const trackSessionBehavior = useCallback(() => {
    const sessionDuration = Date.now() - sessionStartTime.current;

    trackEvent('upload_session_behavior', {
      upload_attempts: uploadAttempts.current,
      text_input_transitions: textInputTransitions.current,
      session_duration_ms: sessionDuration,
      page: window.location.pathname,
      timestamp: Date.now()
    });
  }, []);

  return {
    // Core events
    trackUploadAreaClicked,
    trackFileSelected,
    trackProcessingShown,
    trackPreviewRendered,
    trackUploadCompletedDisabled,
    trackModalClosed,
    trackTextInputTransition,

    // Enhanced events
    trackFormatSelection,
    trackRetryAttempt,
    trackSessionBehavior
  };
};