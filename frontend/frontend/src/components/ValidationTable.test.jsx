import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ValidationTable from './ValidationTable';

describe('ValidationTable', () => {
  const mockResults = [
    {
      citation_number: 1,
      original: 'Smith, J. (2023). Test citation. Journal of Testing.',
      source_type: 'journal_article',
      errors: [{ component: 'DOI', problem: 'Missing DOI' }]
    },
    {
      citation_number: 2,
      original: 'Brown, A. (2022). Perfect citation. Academic Press.',
      source_type: 'book',
      errors: []
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock querySelector for scroll behavior
    document.querySelector = vi.fn();
  });

  describe('Keyboard Accessibility', () => {
    it('handles Enter key on partial indicator', () => {
      const mockScrollIntoView = vi.fn();
      const mockUpgradeBanner = { scrollIntoView: mockScrollIntoView };
      document.querySelector = vi.fn().mockReturnValue(mockUpgradeBanner);

      const { container } = render(
        <ValidationTable
          results={mockResults}
          isPartial={true}
          citationsRemaining={3}
        />
      );

      const partialIndicator = container.querySelector('.partial-indicator.clickable');
      expect(partialIndicator).toBeTruthy();

      // Simulate Enter key press
      fireEvent.keyDown(partialIndicator, { key: 'Enter' });

      // Verify scroll behavior was triggered
      expect(document.querySelector).toHaveBeenCalledWith('.upgrade-banner');
      expect(mockScrollIntoView).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'nearest'
      });
    });

    it('handles Space key on partial indicator and triggers scroll', () => {
      const mockScrollIntoView = vi.fn();
      const mockUpgradeBanner = { scrollIntoView: mockScrollIntoView };
      document.querySelector = vi.fn().mockReturnValue(mockUpgradeBanner);

      const { container } = render(
        <ValidationTable
          results={mockResults}
          isPartial={true}
          citationsRemaining={3}
        />
      );

      const partialIndicator = container.querySelector('.partial-indicator.clickable');

      // Simulate Space key press
      fireEvent.keyDown(partialIndicator, { key: ' ' });

      // Verify scroll behavior was triggered
      // (preventDefault is called in implementation to prevent page scroll)
      expect(mockScrollIntoView).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'nearest'
      });
    });

    it('does not scroll when partial indicator not present', () => {
      const mockScrollIntoView = vi.fn();
      document.querySelector = vi.fn();

      const { container } = render(
        <ValidationTable
          results={mockResults}
          isPartial={false}
        />
      );

      // Partial indicator should not be rendered for full results
      const partialIndicator = container.querySelector('.partial-indicator.clickable');
      expect(partialIndicator).toBeFalsy();

      // querySelector should never be called
      expect(document.querySelector).not.toHaveBeenCalled();
    });

    it('has correct ARIA attributes for accessibility', () => {
      const { container } = render(
        <ValidationTable
          results={mockResults}
          isPartial={true}
          citationsRemaining={3}
        />
      );

      const partialIndicator = container.querySelector('.partial-indicator.clickable');

      // Verify accessibility attributes
      expect(partialIndicator.getAttribute('role')).toBe('button');
      expect(partialIndicator.getAttribute('tabIndex')).toBe('0');
      expect(partialIndicator.getAttribute('title')).toBe('Click to see upgrade options');
    });
  });

  describe('Display Logic', () => {
    it('displays full results header correctly', () => {
      const { container } = render(
        <ValidationTable
          results={mockResults}
          isPartial={false}
        />
      );

      // Should show "references" label
      const stats = container.querySelector('.table-stats');
      expect(stats.textContent).toContain('2');
      expect(stats.textContent).toContain('references');

      // Should show perfect and error counts
      expect(stats.textContent).toContain('perfect');
      expect(stats.textContent).toContain('need fixes');

      // Should NOT show partial indicator
      const partialIndicator = container.querySelector('.partial-indicator');
      expect(partialIndicator).toBeFalsy();
    });

    it('displays partial results header with remaining count', () => {
      const { container } = render(
        <ValidationTable
          results={mockResults}
          isPartial={true}
          citationsRemaining={5}
        />
      );

      // Should show "references" label (not "submitted")
      const stats = container.querySelector('.table-stats');
      expect(stats.textContent).toContain('2');
      expect(stats.textContent).toContain('references');
      expect(stats.textContent).not.toContain('submitted');

      // Should show remaining count with red styling
      expect(stats.textContent).toContain('5');
      expect(stats.textContent).toContain('remaining');

      const remainingBadge = container.querySelector('.stat-badge.remaining');
      expect(remainingBadge).toBeTruthy();

      // Should show partial indicator
      const partialIndicator = container.querySelector('.partial-indicator');
      expect(partialIndicator).toBeTruthy();
      expect(partialIndicator.textContent).toContain('⚠️ Partial');
    });

    it('does not show remaining stat when not partial', () => {
      const { container } = render(
        <ValidationTable
          results={mockResults}
          isPartial={false}
        />
      );

      // Should NOT show remaining count
      const remainingStat = container.querySelector('.stat-remaining');
      expect(remainingStat).toBeFalsy();
    });
  });

  describe('Corrected Citation Integration', () => {
    it('renders CorrectedCitationCard when corrected_citation is present in expanded row', () => {
      const resultsWithCorrection = [
        {
          citation_number: 1,
          original: 'Bad citation',
          source_type: 'journal',
          errors: [{ component: 'Title', problem: 'Bad title' }],
          corrected_citation: 'Good citation'
        }
      ]

      const { container } = render(
        <ValidationTable results={resultsWithCorrection} />
      )

      // Row is expanded by default for errors
      expect(screen.getByText('✓ CORRECTED')).toBeTruthy()
      expect(screen.getByText('Good citation')).toBeTruthy()
    })

    it('does not render CorrectedCitationCard when corrected_citation is missing', () => {
      const resultsWithoutCorrection = [
        {
          citation_number: 1,
          original: 'Bad citation',
          source_type: 'journal',
          errors: [{ component: 'Title', problem: 'Bad title' }],
          corrected_citation: null
        }
      ]

      const { container } = render(
        <ValidationTable results={resultsWithoutCorrection} />
      )

      expect(screen.queryByText('✓ CORRECTED')).toBeNull()
    })
  });
});
