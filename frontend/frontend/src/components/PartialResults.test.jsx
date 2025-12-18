import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PartialResults } from './PartialResults';
import * as experimentUtils from '../utils/experimentVariant';
import { trackEvent } from '../utils/analytics';

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

// Mock experiment variant utils
vi.mock('../utils/experimentVariant', () => ({
  getExperimentVariant: vi.fn(),
  isInlineVariant: vi.fn(),
  getPricingType: vi.fn(),
}));

// Mock child components to simplify testing
vi.mock('./PricingTableCredits', () => ({
  PricingTableCredits: () => <div data-testid="pricing-table-credits">Credits Pricing Table</div>
}));

vi.mock('./PricingTablePasses', () => ({
  PricingTablePasses: () => <div data-testid="pricing-table-passes">Passes Pricing Table</div>
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
    // Default to button variant (1.1)
    vi.mocked(experimentUtils.getExperimentVariant).mockReturnValue('1.1');
    vi.mocked(experimentUtils.isInlineVariant).mockReturnValue(false);
    vi.mocked(experimentUtils.getPricingType).mockReturnValue('credits');
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
  });

  it('renders upgrade button for button variants (1.1)', () => {
    // Arrange
    vi.mocked(experimentUtils.getExperimentVariant).mockReturnValue('1.1');
    vi.mocked(experimentUtils.isInlineVariant).mockReturnValue(false);

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
    expect(screen.getByText('Upgrade to Unlock Now')).toBeInTheDocument();
    expect(screen.queryByTestId('pricing-table-credits')).not.toBeInTheDocument();
    expect(screen.queryByTestId('pricing-table-passes')).not.toBeInTheDocument();
  });

  it('renders inline pricing for inline variants (1.2)', () => {
    // Arrange
    vi.mocked(experimentUtils.getExperimentVariant).mockReturnValue('1.2');
    vi.mocked(experimentUtils.isInlineVariant).mockReturnValue(true);
    vi.mocked(experimentUtils.getPricingType).mockReturnValue('credits');

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
    expect(screen.queryByText('Upgrade to Unlock Now')).not.toBeInTheDocument();
    expect(screen.getByTestId('pricing-table-credits')).toBeInTheDocument();
  });

  it('fires pricing_viewed event for inline variants', () => {
    // Arrange
    vi.mocked(experimentUtils.getExperimentVariant).mockReturnValue('1.2');
    vi.mocked(experimentUtils.isInlineVariant).mockReturnValue(true);

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
    expect(trackEvent).toHaveBeenCalledWith('pricing_viewed', {
      variant: '1.2',
      interaction_type: 'auto'
    });
  });

  it('does NOT fire auto events for button variants', () => {
    // Arrange
    vi.mocked(experimentUtils.getExperimentVariant).mockReturnValue('1.1');
    vi.mocked(experimentUtils.isInlineVariant).mockReturnValue(false);

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
    // Check all calls to verify none are pricing_viewed with auto
    const pricingViewedCalls = vi.mocked(trackEvent).mock.calls.filter(call => call[0] === 'pricing_viewed');
    expect(pricingViewedCalls).toHaveLength(0);
  });

  it('shows correct pricing table based on variant type (Credits)', () => {
    // Arrange
    vi.mocked(experimentUtils.getExperimentVariant).mockReturnValue('1.2');
    vi.mocked(experimentUtils.isInlineVariant).mockReturnValue(true);
    vi.mocked(experimentUtils.getPricingType).mockReturnValue('credits');

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
    expect(screen.getByTestId('pricing-table-credits')).toBeInTheDocument();
    expect(screen.queryByTestId('pricing-table-passes')).not.toBeInTheDocument();
  });

  it('shows correct pricing table based on variant type (Passes)', () => {
    // Arrange
    vi.mocked(experimentUtils.getExperimentVariant).mockReturnValue('2.2');
    vi.mocked(experimentUtils.isInlineVariant).mockReturnValue(true);
    vi.mocked(experimentUtils.getPricingType).mockReturnValue('passes');

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
    expect(screen.getByTestId('pricing-table-passes')).toBeInTheDocument();
    expect(screen.queryByTestId('pricing-table-credits')).not.toBeInTheDocument();
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
    expect(screen.getByText('Upgrade to unlock validation results & more usage')).toBeInTheDocument();
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
    expect(screen.getByText('1 more citation available')).toBeInTheDocument();
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
    const upgradeButton = screen.getByText('Upgrade to Unlock Now');
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
    // Lucide icon renders as svg, not emoji. Checking presence is enough.
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

    const upgradeButton = screen.getByText('Upgrade to Unlock Now');
    fireEvent.click(upgradeButton);

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
    const upgradeButton = screen.getByText('Upgrade to Unlock Now');
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
          event: 'clicked_upgrade',
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
    const upgradeButton = screen.getByText('Upgrade to Unlock Now');
    fireEvent.click(upgradeButton);

    // Assert
    expect(localStorageMock.setItem).not.toHaveBeenCalledWith(
      'pending_upgrade_job_id',
      null
    );
  });
});