/**
 * Tests for analytics utility functions
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trackEvent, trackResultsRevealed, validateTrackingData, trackResultsRevealedSafe } from './analytics.js';

describe('Analytics Utils', () => {
  beforeEach(() => {
    // Mock console methods
    vi.spyOn(console, 'debug').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('trackEvent', () => {
    it('should call gtag when available', () => {
      // Mock gtag function
      const mockGtag = vi.fn();
      global.window = {
        gtag: mockGtag
      };

      const eventName = 'test_event';
      const params = { param1: 'value1', param2: 'value2' };

      trackEvent(eventName, params);

      expect(mockGtag).toHaveBeenCalledWith('event', eventName, params);
    });

    it('should log to console when gtag is not available', () => {
      // Mock window without gtag and NODE_ENV as development
      global.window = {};
      vi.stubEnv('NODE_ENV', 'development');

      const eventName = 'test_event';
      const params = { param1: 'value1' };

      trackEvent(eventName, params);

      // Should log warning when gtag not available in development
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('⚠️ [Analytics] gtag not available, event not sent:'),
        eventName,
        params
      );
    });

    it('should handle missing params gracefully', () => {
      const mockGtag = vi.fn();
      global.window = {
        gtag: mockGtag
      };

      trackEvent('test_event');

      expect(mockGtag).toHaveBeenCalledWith('event', 'test_event', {});
    });

    it('should handle window being undefined (SSR)', () => {
      // Mock window as undefined and NODE_ENV as development
      delete global.window;
      vi.stubEnv('NODE_ENV', 'development');

      const eventName = 'test_event';
      const params = { param1: 'value1' };

      trackEvent(eventName, params);

      // Should log warning when gtag not available in development
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('⚠️ [Analytics] gtag not available, event not sent:'),
        eventName,
        params
      );
    });
  });

  describe('validateTrackingData', () => {
    it('should validate correct input data', () => {
      const result = validateTrackingData('job-123', 45);

      expect(result.isValid).toBe(true);
      expect(result.errors).toEqual([]);
    });

    it('should reject empty or null job ID', () => {
      const testCases = ['', null, undefined, '   '];

      testCases.forEach(jobId => {
        const result = validateTrackingData(jobId, 45);
        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('jobId must be a non-empty string');
      });
    });

    it('should reject non-string job ID', () => {
      const result = validateTrackingData(123, 45);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('jobId must be a non-empty string');
    });

    it('should reject negative time to reveal', () => {
      const result = validateTrackingData('job-123', -5);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('timeToReveal must be a non-negative number');
    });

    it('should reject non-number time to reveal', () => {
      const testCases = ['not-a-number', null, undefined, {}, []];

      testCases.forEach(timeToReveal => {
        const result = validateTrackingData('job-123', timeToReveal);
        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('timeToReveal must be a non-negative number');
      });
    });

    it('should reject time exceeding maximum duration', () => {
      const result = validateTrackingData('job-123', 7200); // 2 hours

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('timeToReveal exceeds maximum allowed duration (3600 seconds)');
    });

    it('should accept boundary values', () => {
      const testCases = [
        ['job-0', 0],        // Zero time
        ['job-3600', 3600],  // Maximum allowed time
      ];

      testCases.forEach(([jobId, timeToReveal]) => {
        const result = validateTrackingData(jobId, timeToReveal);
        expect(result.isValid).toBe(true);
        expect(result.errors).toEqual([]);
      });
    });
  });

  describe('trackResultsRevealed', () => {
    beforeEach(() => {
      // Mock process.env.NODE_ENV for development testing
      vi.stubEnv('NODE_ENV', 'development');
      // Mock console methods
      vi.spyOn(console, 'log').mockImplementation(() => {});
      vi.spyOn(console, 'warn').mockImplementation(() => {});
    });

    it('should call gtag with correct parameters', () => {
      const mockGtag = vi.fn();
      global.window = {
        gtag: mockGtag
      };

      const jobId = 'test-job-123';
      const timeToReveal = 45;
      const userType = 'free';

      trackResultsRevealed(jobId, timeToReveal, userType);

      expect(mockGtag).toHaveBeenCalledWith('event', 'results_revealed', {
        job_id: jobId,
        time_to_reveal_seconds: timeToReveal,
        user_type: userType,
        validation_type: 'gated'
      });
    });

    it('should log debug message in development', () => {
      const mockGtag = vi.fn();
      global.window = {
        gtag: mockGtag
      };

      const jobId = 'test-job-123';
      const timeToReveal = 45;
      const userType = 'free';

      trackResultsRevealed(jobId, timeToReveal, userType);

      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('🎯 [Analytics] Results revealed event tracked'),
        expect.objectContaining({
          job_id: jobId,
          time_to_reveal_seconds: timeToReveal,
          user_type: userType,
          validation_type: 'gated'
        })
      );
    });

    it('should handle missing gtag gracefully', () => {
      global.window = {};

      trackResultsRevealed('test-job-123', 45, 'free');

      // Should not throw error and should not call any gtag function
      expect(console.log).not.toHaveBeenCalledWith(
        expect.stringContaining('🎯 [Analytics] Results revealed event tracked'),
        expect.any(Object)
      );
    });

    it('should handle window being undefined (SSR)', () => {
      delete global.window;

      trackResultsRevealed('test-job-123', 45, 'free');

      // Should not throw error
      expect(console.log).not.toHaveBeenCalledWith(
        expect.stringContaining('🎯 [Analytics] Results revealed event tracked'),
        expect.any(Object)
      );
    });
  });

  describe('trackResultsRevealedSafe', () => {
    beforeEach(() => {
      vi.stubEnv('NODE_ENV', 'development');
      vi.spyOn(console, 'log').mockImplementation(() => {});
      vi.spyOn(console, 'warn').mockImplementation(() => {});
    });

    it('should return true for valid data and call trackResultsRevealed', () => {
      // Mock gtag for the real trackResultsRevealed function
      const mockGtag = vi.fn();
      global.window = {
        gtag: mockGtag
      };

      const jobId = 'test-job-123';
      const timeToReveal = 45;
      const userType = 'free';

      const result = trackResultsRevealedSafe(jobId, timeToReveal, userType);

      expect(result).toBe(true);
      // Verify that trackResultsRevealed was called by checking gtag was called
      expect(mockGtag).toHaveBeenCalledWith('event', 'results_revealed', {
        job_id: jobId,
        time_to_reveal_seconds: timeToReveal,
        user_type: userType,
        validation_type: 'gated'
      });
    });

    it('should return false for invalid data and not call trackResultsRevealed', () => {
      // Mock gtag to track if trackResultsRevealed is called
      const mockGtag = vi.fn();
      global.window = {
        gtag: mockGtag
      };

      const result = trackResultsRevealedSafe('', -5, 'invalid');

      expect(result).toBe(false);
      // trackResultsRevealed should not be called, so gtag should not be called
      expect(mockGtag).not.toHaveBeenCalled();
    });

    it('should log validation warnings in development', () => {
      trackResultsRevealedSafe('', -5, 'invalid');

      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('⚠️ [Analytics] Tracking data validation failed:'),
        expect.any(Array)
      );
    });

    it('should work with real trackResultsRevealed function', () => {
      const mockGtag = vi.fn();
      global.window = {
        gtag: mockGtag
      };

      const result = trackResultsRevealedSafe('test-job-123', 45, 'free');

      expect(result).toBe(true);
      expect(mockGtag).toHaveBeenCalledWith('event', 'results_revealed', {
        job_id: 'test-job-123',
        time_to_reveal_seconds: 45,
        user_type: 'free',
        validation_type: 'gated'
      });
    });
  });
});