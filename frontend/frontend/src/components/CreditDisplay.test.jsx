import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CreditDisplay } from './CreditDisplay';
import { useCredits } from '../hooks/useCredits.js';

// Mock the useCredits hook
vi.mock('../hooks/useCredits.js', () => ({
  useCredits: vi.fn(),
}));

describe('CreditDisplay', () => {
  let mockUseCredits;

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseCredits = vi.fn();
  });

  it('should render nothing if no token', () => {
    // Arrange
    mockUseCredits.mockReturnValue({
      credits: null,
      loading: false,
      error: null,
      hasToken: false,
    });

    vi.mocked(useCredits).mockImplementation(mockUseCredits);

    // Act
    const { container } = render(<CreditDisplay />);

    // Assert
    expect(container.firstChild).toBeNull();
  });

  it('should display credits if token exists', () => {
    // Arrange
    mockUseCredits.mockReturnValue({
      credits: 847,
      loading: false,
      error: null,
      hasToken: true,
    });

    vi.mocked(useCredits).mockImplementation(mockUseCredits);

    // Act
    render(<CreditDisplay />);

    // Assert
    expect(screen.getByText('Citation Credits: 847')).toBeInTheDocument();
  });

  it('should show loading state', () => {
    // Arrange
    mockUseCredits.mockReturnValue({
      credits: null,
      loading: true,
      error: null,
      hasToken: true,
    });

    vi.mocked(useCredits).mockImplementation(mockUseCredits);

    // Act
    render(<CreditDisplay />);

    // Assert
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should display 0 credits if credits is null but token exists', () => {
    // Arrange
    mockUseCredits.mockReturnValue({
      credits: null,
      loading: false,
      error: null,
      hasToken: true,
    });

    vi.mocked(useCredits).mockImplementation(mockUseCredits);

    // Act
    render(<CreditDisplay />);

    // Assert
    expect(screen.getByText('Citation Credits: 0')).toBeInTheDocument();
  });

  it('should update when credits prop changes', () => {
    // Arrange
    mockUseCredits.mockReturnValueOnce({
      credits: 100,
      loading: false,
      error: null,
      hasToken: true,
    });

    vi.mocked(useCredits).mockImplementation(mockUseCredits);

    // Act
    const { rerender } = render(<CreditDisplay />);

    // Assert initial
    expect(screen.getByText('Citation Credits: 100')).toBeInTheDocument();

    // Arrange updated credits
    mockUseCredits.mockReturnValue({
      credits: 95,
      loading: false,
      error: null,
      hasToken: true,
    });

    // Act - rerender
    rerender(<CreditDisplay />);

    // Assert updated
    expect(screen.getByText('Citation Credits: 95')).toBeInTheDocument();
  });
});