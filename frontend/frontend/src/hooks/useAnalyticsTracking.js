import { useEffect, useRef, useCallback } from 'react';
import { trackEvent } from '../utils/analytics';

/**
 * Hook for comprehensive analytics tracking
 * Tracks scroll depth, navigation clicks, CTA clicks, and source type guide content
 */
export const useAnalyticsTracking = () => {
  // DEBUG: Log hook mount
  console.log('🎯 [Analytics] useAnalyticsTracking hook mounted');

  const scrollDepthTracked = useRef(new Set());
  const lastScrollDepth = useRef(0);
  const contentInteractionTracked = useRef(new Set());

  // Track scroll depth
  const trackScrollDepth = useCallback(() => {
    const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPosition = window.scrollY;
    const scrollPercentage = Math.round((scrollPosition / scrollHeight) * 100);

    // Track at 25%, 50%, 75%, and 100%
    const milestones = [25, 50, 75, 100];

    milestones.forEach(milestone => {
      if (scrollPercentage >= milestone && !scrollDepthTracked.current.has(milestone)) {
        console.log('📜 [Analytics] Scroll milestone reached:', milestone, '%');
        scrollDepthTracked.current.add(milestone);
        trackEvent('scroll_depth', {
          depth_percentage: milestone,
          page: window.location.pathname
        });
      }
    });

    lastScrollDepth.current = Math.max(lastScrollDepth.current, scrollPercentage);
  }, []);

  // Track navigation and CTA clicks
  const trackNavigationClick = useCallback((element, url) => {
    console.log('🔗 [Analytics] trackNavigationClick called:', element, url);
    trackEvent('nav_link_clicked', {
      element_type: element,
      destination_url: url,
      page: window.location.pathname
    });
  }, []);

  // Track CTA clicks
  const trackCTAClick = useCallback((ctaText, ctaLocation) => {
    trackEvent('cta_clicked', {
      cta_text: ctaText,
      cta_location: ctaLocation,
      page: window.location.pathname
    });
  }, []);

  // Track source type guide content interaction
  const trackSourceTypeView = useCallback((sourceType, citationNumber) => {
    const trackKey = `${sourceType}-${citationNumber}`;

    if (!contentInteractionTracked.current.has(trackKey)) {
      contentInteractionTracked.current.add(trackKey);
      trackEvent('guide_viewed', {
        source_type: sourceType,
        citation_number: citationNumber,
        page: window.location.pathname
      });
    }
  }, []);

  // Set up scroll tracking
  useEffect(() => {
    let timeoutId;

    const handleScroll = () => {
      // Debounce scroll events
      clearTimeout(timeoutId);
      timeoutId = setTimeout(trackScrollDepth, 100);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(timeoutId);
    };
  }, [trackScrollDepth]);

  // Track page view on mount
  useEffect(() => {
    console.log('📄 [Analytics] Page view tracking on mount');
    trackEvent('page_view', {
      page: window.location.pathname,
      page_title: document.title
    });
  }, []);

  return {
    trackNavigationClick,
    trackCTAClick,
    trackSourceTypeView,
    getMaxScrollDepth: () => lastScrollDepth.current
  };
};