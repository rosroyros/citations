/**
 * Tests for analytics utility functions
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trackEvent } from './analytics.js';

describe('Analytics Utils', () => {
  beforeEach(() => {
    // Mock console.debug
    vi.spyOn(console, 'debug').mockImplementation(() => {});
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
      // Mock window without gtag
      global.window = {};

      const eventName = 'test_event';
      const params = { param1: 'value1' };

      trackEvent(eventName, params);

      expect(console.debug).toHaveBeenCalledWith('Analytics Event:', eventName, params);
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
      // Mock window as undefined
      delete global.window;

      const eventName = 'test_event';
      const params = { param1: 'value1' };

      trackEvent(eventName, params);

      expect(console.debug).toHaveBeenCalledWith('Analytics Event:', eventName, params);
    });
  });
});