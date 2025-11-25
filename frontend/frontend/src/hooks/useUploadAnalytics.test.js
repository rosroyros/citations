import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Mock analytics utility first
vi.mock('../utils/analytics', () => ({
  trackEvent: vi.fn(),
}));

import { useUploadAnalytics } from './useUploadAnalytics';
import { trackEvent } from '../utils/analytics';

describe('useUploadAnalytics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('should provide all upload analytics tracking functions', () => {
    const { result } = renderHook(() => useUploadAnalytics());

    expect(typeof result.current.trackUploadAreaClicked).toBe('function');
    expect(typeof result.current.trackFileSelected).toBe('function');
    expect(typeof result.current.trackProcessingShown).toBe('function');
    expect(typeof result.current.trackPreviewRendered).toBe('function');
    expect(typeof result.current.trackUploadCompletedDisabled).toBe('function');
    expect(typeof result.current.trackModalClosed).toBe('function');
    expect(typeof result.current.trackTextInputTransition).toBe('function');
    expect(typeof result.current.trackFormatSelection).toBe('function');
    expect(typeof result.current.trackRetryAttempt).toBe('function');
    expect(typeof result.current.trackSessionBehavior).toBe('function');
  });

  describe('Core Analytics Events', () => {
    it('should track upload area clicked', () => {
      const { result } = renderHook(() => useUploadAnalytics());

      act(() => {
        result.current.trackUploadAreaClicked();
      });

      expect(trackEvent).toHaveBeenCalledWith('upload_area_clicked', {
        page: expect.any(String),
        timestamp: expect.any(Number)
      });
    });

    it('should track file selected with metadata', () => {
      const { result } = renderHook(() => useUploadAnalytics());
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      Object.defineProperty(file, 'size', { value: 1024 });

      act(() => {
        result.current.trackFileSelected(file);
      });

      expect(trackEvent).toHaveBeenCalledWith('upload_file_selected', {
        file_name: 'test.pdf',
        file_size: 1024,
        file_type: 'application/pdf',
        file_extension: 'pdf',
        page: expect.any(String),
        timestamp: expect.any(Number)
      });
    });

    it('should track processing shown with file info', () => {
      const { result } = renderHook(() => useUploadAnalytics());
      const file = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });

      act(() => {
        result.current.trackProcessingShown(file);
      });

      expect(trackEvent).toHaveBeenCalledWith('upload_processing_shown', {
        file_name: 'test.docx',
        file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        file_extension: 'docx',
        page: expect.any(String),
        timestamp: expect.any(Number)
      });
    });

    it('should track preview rendered with timing', () => {
      const { result } = renderHook(() => useUploadAnalytics());
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });
      const processingTime = 1500;

      act(() => {
        result.current.trackPreviewRendered(file, processingTime);
      });

      expect(trackEvent).toHaveBeenCalledWith('upload_file_preview_rendered', {
        file_name: 'test.txt',
        file_type: 'text/plain',
        file_extension: 'txt',
        processing_time_ms: 1500,
        page: expect.any(String),
        timestamp: expect.any(Number)
      });
    });

    it('should track upload completed disabled modal', () => {
      const { result } = renderHook(() => useUploadAnalytics());
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      act(() => {
        result.current.trackUploadCompletedDisabled(file);
      });

      expect(trackEvent).toHaveBeenCalledWith('upload_completed_disabled', {
        file_name: 'test.pdf',
        file_type: 'application/pdf',
        file_extension: 'pdf',
        page: expect.any(String),
        timestamp: expect.any(Number)
      });
    });

    it('should track modal closed with dismiss method and duration', () => {
      const { result } = renderHook(() => useUploadAnalytics());
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      act(() => {
        result.current.trackUploadCompletedDisabled(file);
      });

      // Advance time by 5 seconds
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      act(() => {
        result.current.trackModalClosed('close_button');
      });

      // Check that the last call is the modal close event
      expect(trackEvent).toHaveBeenLastCalledWith('upload_modal_closed', {
        dismiss_method: 'close_button',
        modal_duration_ms: 5000,
        file_name: 'test.pdf',
        file_type: 'application/pdf',
        file_extension: 'pdf',
        page: expect.any(String),
        timestamp: expect.any(Number)
      });
    });

    it('should track text input transition with timing', () => {
      const { result } = renderHook(() => useUploadAnalytics());

      act(() => {
        result.current.trackUploadCompletedDisabled(new File(['test'], 'test.pdf', { type: 'application/pdf' }));
      });

      // Advance time by 3 seconds
      act(() => {
        vi.advanceTimersByTime(3000);
      });

      act(() => {
        result.current.trackTextInputTransition();
      });

      expect(trackEvent).toHaveBeenCalledWith('upload_text_input_transition', {
        modal_duration_ms: 3000,
        page: expect.any(String),
        timestamp: expect.any(Number)
      });
    });
  });

  describe('Enhanced Analytics Events', () => {
    it('should track format selection', () => {
      const { result } = renderHook(() => useUploadAnalytics());

      act(() => {
        result.current.trackFormatSelection('pdf');
      });

      expect(trackEvent).toHaveBeenCalledWith('upload_format_selection', {
        selected_format: 'pdf',
        page: expect.any(String),
        timestamp: expect.any(Number)
      });
    });

    it('should track retry attempt with attempt number', () => {
      const { result } = renderHook(() => useUploadAnalytics());
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      act(() => {
        result.current.trackRetryAttempt(file, 2);
      });

      expect(trackEvent).toHaveBeenCalledWith('upload_retry_attempt', {
        attempt_number: 2,
        file_name: 'test.pdf',
        file_type: 'application/pdf',
        file_extension: 'pdf',
        page: expect.any(String),
        timestamp: expect.any(Number)
      });
    });

    it('should track session behavior with upload and text input usage', () => {
      const { result } = renderHook(() => useUploadAnalytics());

      act(() => {
        result.current.trackFileSelected(new File(['test'], 'test.pdf', { type: 'application/pdf' }));
        result.current.trackTextInputTransition();
        result.current.trackSessionBehavior();
      });

      expect(trackEvent).toHaveBeenCalledWith('upload_session_behavior', {
        upload_attempts: 1,
        text_input_transitions: 1,
        session_duration_ms: expect.any(Number),
        page: expect.any(String),
        timestamp: expect.any(Number)
      });
    });
  });
});