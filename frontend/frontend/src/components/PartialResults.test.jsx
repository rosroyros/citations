import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PartialResults } from './PartialResults';

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
      onUpgrade: mockOnUpgrade
    };

    // Act
    render(<PartialResults {...props} />);

    // Assert
    expect(screen.getByText('Validation Results')).toBeInTheDocument();
    expect(screen.getByText('Citation #1 ❌')).toBeInTheDocument();
    expect(screen.getByText('Citation #2 ✅')).toBeInTheDocument();
    expect(screen.getAllByText('Original:')).toHaveLength(2);
    expect(screen.getByText('Source type: journal_article')).toBeInTheDocument();
    expect(screen.getByText('Source type: book')).toBeInTheDocument();
    expect(screen.getByText('Errors found:')).toBeInTheDocument();
    expect(screen.getByText('❌ DOI:')).toBeInTheDocument();
    expect(screen.getByText('Problem:')).toBeInTheDocument();
    expect(screen.getByText('Missing DOI')).toBeInTheDocument();
    expect(screen.getByText('Correction:')).toBeInTheDocument();
    expect(screen.getByText('Add DOI: https://doi.org/10.1234/example')).toBeInTheDocument();
    expect(screen.getByText(/No errors found/)).toBeInTheDocument();
  });

  it('should show locked citations count', () => {
    // Arrange
    const props = {
      results: mockResults,
      partial: true,
      citations_checked: 3,
      citations_remaining: 7,
      onUpgrade: mockOnUpgrade
    };

    // Act
    render(<PartialResults {...props} />);

    // Assert
    expect(screen.getByText('7 more citations checked')).toBeInTheDocument();
    expect(screen.getByText('Upgrade to see all results')).toBeInTheDocument();
    expect(screen.getByText('Get 1,000 Citation Credits for $8.99')).toBeInTheDocument();
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
      onUpgrade: mockOnUpgrade
    };

    // Act
    render(<PartialResults {...props} />);
    const upgradeButton = screen.getByText('Get 1,000 Citation Credits for $8.99');
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
});