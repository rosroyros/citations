import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PartialResults } from './PartialResults';

// Mock analytics
vi.mock('../utils/analytics', () => ({
  trackEvent: vi.fn(),
}));

// Mock useAnalyticsTracking hook
vi.mock('../hooks/useAnalyticsTracking', () => ({
  useAnalyticsTracking: () => ({
    trackSourceTypeView: vi.fn(),
  }),
}));

describe('PartialResults', () => {
  const mockOnUpgrade = vi.fn();
  const mockResults = [
    {
      citation_number: 1,
      original: 'Smith, J. (2023). <em>Understanding research</em>. Journal of Studies.',
      source_type: 'journal_article',
      errors: [
        {
          component: 'DOI',
          problem: 'Missing DOI',
          correction: 'Add DOI: https://doi.org/10.1234/example'
        }
      ]
    },
    {
      citation_number: 2,
      original: 'Brown, A. (2022). <em>Perfect citation</em>. Academic Press. https://doi.org/10.1234/perfect',
      source_type: 'book',
      errors: []
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display validated citations with full error details', () => {
    // Arrange
    const props = {
      results: mockResults,
      partial: true,
      citations_checked: 3,
      citations_remaining: 7,
      job_id: 'test-job-123',
      onUpgrade: mockOnUpgrade
    };

    // Act
    render(<PartialResults {...props} />);

    // Assert
    expect(screen.getByText('Validation Results')).toBeInTheDocument();
    expect(screen.getByText('1 issue')).toBeInTheDocument();
    expect(screen.getByText('Perfect')).toBeInTheDocument();
    expect(screen.getAllByText('Original:')).toHaveLength(2);
    expect(screen.getByText('Source type: journal_article')).toBeInTheDocument();
    expect(screen.getByText('Source type: book')).toBeInTheDocument();
    expect(screen.getByText('Errors found:')).toBeInTheDocument();
    expect(screen.getByText('✗')).toBeInTheDocument();
    expect(screen.getByText('DOI:')).toBeInTheDocument();
    expect(screen.getByText('Missing DOI')).toBeInTheDocument();
    expect(screen.getByText('Should be:')).toBeInTheDocument();
    expect(screen.getByText('Add DOI: https://doi.org/10.1234/example')).toBeInTheDocument();
  });

  it('should show locked citations count', () => {
    // Arrange
    const props = {
      results: mockResults,
      partial: true,
      citations_checked: 3,
      citations_remaining: 7,
      job_id: 'test-job-123',
      onUpgrade: mockOnUpgrade
    };

    // Act
    render(<PartialResults {...props} />);

    // Assert
    expect(screen.getByText('7 more citations available')).toBeInTheDocument();
    expect(screen.getByText('Upgrade to see validation results for all your citations')).toBeInTheDocument();
  });

  it('should show singular form for 1 remaining citation', () => {
    // Arrange
    const props = {
      results: mockResults,
      partial: true,
      citations_checked: 9,
      citations_remaining: 1,
      onUpgrade: mockOnUpgrade
    };

    // Act
    render(<PartialResults {...props} />);

    // Assert
    expect(screen.getByText('1 more citation checked')).toBeInTheDocument();
  });

  it('"Upgrade" button calls onUpgrade callback', () => {
    // Arrange
    const props = {
      results: mockResults,
      partial: true,
      citations_checked: 3,
      citations_remaining: 7,
      job_id: 'test-job-123',
      onUpgrade: mockOnUpgrade
    };

    // Act
    render(<PartialResults {...props} />);
    const upgradeButton = screen.getByText('Upgrade Now');
    fireEvent.click(upgradeButton);

    // Assert
    expect(mockOnUpgrade).toHaveBeenCalledTimes(1);
  });

  it('should display correct summary stats', () => {
    // Arrange
    const props = {
      results: mockResults,
      partial: true,
      citations_checked: 3,
      citations_remaining: 7,
      job_id: 'test-job-123',
      onUpgrade: mockOnUpgrade
    };

    // Act
    render(<PartialResults {...props} />);

    // Assert
    const statNumbers = screen.getAllByText('1');
    expect(screen.getByText('3')).toBeInTheDocument(); // Citations Checked
    expect(statNumbers).toHaveLength(2); // Perfect and Need Fixes both show "1"
  });

  it('should render lock icon and locked section styling', () => {
    // Arrange
    const props = {
      results: mockResults,
      partial: true,
      citations_checked: 3,
      citations_remaining: 7,
      job_id: 'test-job-123',
      onUpgrade: mockOnUpgrade
    };

    // Act
    render(<PartialResults {...props} />);

    // Assert
    const lockIcon = document.querySelector('.lock-icon');
    expect(lockIcon).toBeInTheDocument();
    expect(lockIcon.textContent).toBe('🔒');

    const lockedSection = document.querySelector('.locked-results');
    expect(lockedSection).toBeInTheDocument();
  });

  // localStorage tracking tests
  it('should store job_id in localStorage when upgrade button is clicked', () => {
    // Arrange
    const props = {
      results: mockResults,
      partial: true,
      citations_checked: 3,
      citations_remaining: 7,
      job_id: 'test-job-456',
      onUpgrade: mockOnUpgrade
    };

    // Mock localStorage directly
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });

    // Mock fetch for upgrade-event API
    const mockFetch = vi.fn().mockResolvedValue({ ok: true });
    global.fetch = mockFetch;

    // Act
    render(<PartialResults {...props} />);

    // Debug: Check what buttons are in the document
    const allButtons = screen.getAllByRole('button');
    console.log('All buttons found:', allButtons.map(b => b.textContent));

    const upgradeButton = screen.getByText('Upgrade Now');
    console.log('Upgrade button found:', upgradeButton);
    fireEvent.click(upgradeButton);

    console.log('localStorage calls after click:', localStorageMock.setItem.mock.calls);

    // Assert
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'pending_upgrade_job_id',
      'test-job-456'
    );
  });

  it('should call upgrade-event API when upgrade button is clicked', () => {
    // Arrange
    const props = {
      results: mockResults,
      partial: true,
      citations_checked: 3,
      citations_remaining: 7,
      job_id: 'test-job-789',
      onUpgrade: mockOnUpgrade
    };

    // Mock fetch
    const mockFetch = vi.fn().mockResolvedValue({ ok: true });
    global.fetch = mockFetch;

    // Act
    render(<PartialResults {...props} />);
    const upgradeButton = screen.getByText('Upgrade Now');
    fireEvent.click(upgradeButton);

    // Assert
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/upgrade-event',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: 'clicked_upgrade',
          job_id: 'test-job-789',
          trigger_location: 'partial_results',
          citations_locked: 7
        })
      }
    );

    // Cleanup
    mockFetch.mockRestore();
  });

  it('should not store job_id in localStorage when no job_id provided', () => {
    // Arrange
    const props = {
      results: mockResults,
      partial: true,
      citations_checked: 3,
      citations_remaining: 7,
      job_id: null,
      onUpgrade: mockOnUpgrade
    };

    // Mock localStorage directly
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });

    const mockFetch = vi.fn().mockResolvedValue({ ok: true });
    global.fetch = mockFetch;

    // Act
    render(<PartialResults {...props} />);
    const upgradeButton = screen.getByText('Upgrade Now');
    fireEvent.click(upgradeButton);

    // Assert
    expect(localStorageMock.setItem).not.toHaveBeenCalledWith(
      'pending_upgrade_job_id',
      null
    );
  });
});