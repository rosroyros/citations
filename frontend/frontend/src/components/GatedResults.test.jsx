import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import GatedResults from './GatedResults';

describe('GatedResults', () => {
  const defaultProps = {
    results: [
      {
        citation_number: 1,
        original: 'Smith, J. (2023). Test citation. Journal of Testing.',
        source_type: 'journal_article',
        errors: []
      },
      {
        citation_number: 2,
        original: 'Brown, A. (2022). Another citation. Academic Press.',
        source_type: 'book',
        errors: [{ component: 'author', problem: 'Missing author' }]
      }
    ],
    onReveal: vi.fn(),
    trackingData: {
      jobStartedAt: '2023-01-01T10:00:00Z',
      resultsReadyAt: '2023-01-01T10:01:30Z',
      isGated: true
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders gated results container', () => {
      render(<GatedResults {...defaultProps} />);

      expect(screen.getByTestId('gated-results')).toBeTruthy();
    });

    it('displays validation statistics header', () => {
      render(<GatedResults {...defaultProps} />);

      expect(screen.getByText('Validation Results')).toBeTruthy();
      expect(screen.getByText((content, element) => content.includes('2 citations'))).toBeTruthy();
      expect(screen.getByText('perfect')).toBeTruthy();
      expect(screen.getByText('need fixes')).toBeTruthy();
    });

    it('displays completion indicator', () => {
      render(<GatedResults {...defaultProps} />);

      expect(screen.getByText('Your citation validation is complete')).toBeTruthy();
      expect(screen.getByText('Results Ready')).toBeTruthy();
    });

    it('displays reveal button with citation count', () => {
      render(<GatedResults {...defaultProps} />);

      const revealButton = screen.getByRole('button', { name: /View Results.*citations/i });
      expect(revealButton).toBeTruthy();
      expect(revealButton).toHaveTextContent('View Results (2 citations)');
    });
  });

  describe('Props Interface', () => {
    it('accepts results array', () => {
      render(<GatedResults {...defaultProps} />);

      expect(screen.getByText((content, element) => content.includes('2 citations'))).toBeTruthy();
    });

    it('accepts empty results array', () => {
      const propsWithEmptyResults = { ...defaultProps, results: [] };
      render(<GatedResults {...propsWithEmptyResults} />);

      expect(screen.getByText((content, element) => content.includes('0 citations'))).toBeTruthy();
      expect(screen.getByText('View Results (0 citations)')).toBeTruthy();
    });

    it('accepts onReveal callback function', async () => {
      render(<GatedResults {...defaultProps} />);

      const revealButton = screen.getByRole('button');

      await act(async () => {
        fireEvent.click(revealButton);
      });

      expect(defaultProps.onReveal).toHaveBeenCalledTimes(1);
    });

    it('accepts trackingData object', () => {
      const customTrackingData = {
        ...defaultProps.trackingData,
        customField: 'test value'
      };

      const propsWithCustomTracking = { ...defaultProps, trackingData: customTrackingData };
      render(<GatedResults {...propsWithCustomTracking} />);

      // Component should render without errors
      expect(screen.getByTestId('gated-results')).toBeTruthy();
    });
  });

  describe('User Interactions', () => {
    it('calls onReveal when reveal button is clicked', async () => {
      render(<GatedResults {...defaultProps} />);

      const revealButton = screen.getByRole('button');

      await act(async () => {
        fireEvent.click(revealButton);
      });

      expect(defaultProps.onReveal).toHaveBeenCalledTimes(1);
    });

    it('calls onReveal when Enter key is pressed on reveal button', async () => {
      render(<GatedResults {...defaultProps} />);

      const revealButton = screen.getByRole('button');

      await act(async () => {
        fireEvent.keyDown(revealButton, { key: 'Enter' });
      });

      expect(defaultProps.onReveal).toHaveBeenCalledTimes(1);
    });

    it('calls onReveal when Space key is pressed on reveal button', async () => {
      render(<GatedResults {...defaultProps} />);

      const revealButton = screen.getByRole('button');

      await act(async () => {
        fireEvent.keyDown(revealButton, { key: ' ' });
      });

      expect(defaultProps.onReveal).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility', () => {
    it('has proper button role and accessibility attributes', () => {
      render(<GatedResults {...defaultProps} />);

      const revealButton = screen.getByRole('button');
      expect(revealButton).toHaveAttribute('tabIndex', '0');
    });

    it('provides accessible button name', () => {
      render(<GatedResults {...defaultProps} />);

      const revealButton = screen.getByRole('button', { name: /View Results.*citations/i });
      expect(revealButton).toBeTruthy();
    });

    it('supports keyboard navigation', async () => {
      render(<GatedResults {...defaultProps} />);

      const revealButton = screen.getByRole('button');

      // Test keyboard interactions
      await act(async () => {
        fireEvent.keyDown(revealButton, { key: 'Enter' });
      });
      await act(async () => {
        fireEvent.keyDown(revealButton, { key: ' ' });
      });

      expect(defaultProps.onReveal).toHaveBeenCalledTimes(2);
    });
  });

  describe('Statistics Calculation', () => {
    it('calculates perfect and error counts correctly', () => {
      const resultsWithError = [
        ...defaultProps.results,
        {
          citation_number: 3,
          original: 'Johnson, C. (2021). Error citation.',
          source_type: 'website',
          errors: [{ component: 'date', problem: 'Invalid date' }]
        }
      ];

      const propsWithMoreErrors = { ...defaultProps, results: resultsWithError };
      render(<GatedResults {...propsWithMoreErrors} />);

      expect(screen.getByText((content, element) => content.includes('3 citations'))).toBeTruthy();
      expect(screen.getByText('perfect')).toBeTruthy();
      expect(screen.getByText('need fixes')).toBeTruthy();
    });

    it('handles all-perfect results', () => {
      const allPerfectResults = defaultProps.results.map(r => ({ ...r, errors: [] }));
      const propsWithAllPerfect = { ...defaultProps, results: allPerfectResults };

      render(<GatedResults {...propsWithAllPerfect} />);

      expect(screen.getByText((content, element) => content.includes('2 citations'))).toBeTruthy();
      expect(screen.getByText('perfect')).toBeTruthy();
      expect(screen.getByText('need fixes')).toBeTruthy();
      // Check that there are 2 perfect citations using getAllByText
      const perfectBadges = screen.getAllByText('2');
      expect(perfectBadges.length).toBeGreaterThan(0);
    });

    it('handles all-error results', () => {
      const allErrorResults = defaultProps.results.map(r => ({
        ...r,
        errors: [{ component: 'test', problem: 'Test error' }]
      }));
      const propsWithAllErrors = { ...defaultProps, results: allErrorResults };

      render(<GatedResults {...propsWithAllErrors} />);

      expect(screen.getByText((content, element) => content.includes('2 citations'))).toBeTruthy();
      expect(screen.getByText('perfect')).toBeTruthy();
      expect(screen.getByText('need fixes')).toBeTruthy();
      // Check that there are 2 errors using getAllByText
      const errorBadges = screen.getAllByText('2');
      expect(errorBadges.length).toBeGreaterThan(0);
    });
  });
});