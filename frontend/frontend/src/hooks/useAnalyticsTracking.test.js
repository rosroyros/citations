import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Mock analytics utility first
vi.mock('../utils/analytics', () => ({
  trackEvent: vi.fn(),
}));

// Mock window object for scroll tracking
Object.defineProperty(window, 'scrollY', { writable: true, value: 0 });
Object.defineProperty(window, 'innerHeight', { writable: true, value: 800 });
Object.defineProperty(document.documentElement, 'scrollHeight', { writable: true, value: 2000 });

import { useAnalyticsTracking } from './useAnalyticsTracking';
import { trackEvent } from '../utils/analytics';

describe('useAnalyticsTracking', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset window scroll position
    window.scrollY = 0;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should track page view on mount', () => {
    Object.defineProperty(document, 'title', { value: 'Test Page' });

    renderHook(() => useAnalyticsTracking());

    expect(trackEvent).toHaveBeenCalledWith('page_view', {
      page: '/',
      page_title: 'Test Page'
    });
  });

  it('should provide tracking functions', () => {
    const { result } = renderHook(() => useAnalyticsTracking());

    expect(typeof result.current.trackNavigationClick).toBe('function');
    expect(typeof result.current.trackCTAClick).toBe('function');
    expect(typeof result.current.trackSourceTypeView).toBe('function');
    expect(typeof result.current.getMaxScrollDepth).toBe('function');
  });

  it('should track navigation clicks correctly', () => {
    const { result } = renderHook(() => useAnalyticsTracking());

    act(() => {
      result.current.trackNavigationClick('footer_link', '/privacy');
    });

    expect(trackEvent).toHaveBeenCalledWith('navigation_click', {
      element_type: 'footer_link',
      destination_url: '/privacy',
      page: '/'
    });
  });

  it('should track CTA clicks correctly', () => {
    const { result } = renderHook(() => useAnalyticsTracking());

    act(() => {
      result.current.trackCTAClick('Check My Citations', 'main_form');
    });

    expect(trackEvent).toHaveBeenCalledWith('cta_click', {
      cta_text: 'Check My Citations',
      cta_location: 'main_form',
      page: '/'
    });
  });

  it('should track source type views correctly', () => {
    const { result } = renderHook(() => useAnalyticsTracking());

    act(() => {
      result.current.trackSourceTypeView('journal_article', 1);
    });

    expect(trackEvent).toHaveBeenCalledWith('source_type_guide_view', {
      source_type: 'journal_article',
      citation_number: 1,
      page: '/'
    });
  });

  it('should not track duplicate source type views', () => {
    const { result } = renderHook(() => useAnalyticsTracking());

    act(() => {
      result.current.trackSourceTypeView('journal_article', 1);
      result.current.trackSourceTypeView('journal_article', 1); // Duplicate
    });

    expect(trackEvent).toHaveBeenCalledTimes(2); // page_view + one source_type_guide_view
    expect(trackEvent).toHaveBeenCalledWith('source_type_guide_view', {
      source_type: 'journal_article',
      citation_number: 1,
      page: '/'
    });
  });

  it('should track different source types separately', () => {
    const { result } = renderHook(() => useAnalyticsTracking());

    act(() => {
      result.current.trackSourceTypeView('journal_article', 1);
      result.current.trackSourceTypeView('book', 1);
    });

    expect(trackEvent).toHaveBeenCalledTimes(3); // page_view + two source_type_guide_view calls
    expect(trackEvent).toHaveBeenCalledWith('source_type_guide_view', {
      source_type: 'journal_article',
      citation_number: 1,
      page: '/'
    });
    expect(trackEvent).toHaveBeenCalledWith('source_type_guide_view', {
      source_type: 'book',
      citation_number: 1,
      page: '/'
    });
  });

  it('should provide getMaxScrollDepth function', () => {
    const { result } = renderHook(() => useAnalyticsTracking());

    expect(typeof result.current.getMaxScrollDepth).toBe('function');
    expect(result.current.getMaxScrollDepth()).toBe(0);
  });
});