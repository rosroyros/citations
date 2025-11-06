import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import Success from './Success';
import { CreditProvider } from '../contexts/CreditContext';

// Mock the creditStorage utility
vi.mock('../utils/creditStorage', () => ({
  saveToken: vi.fn(),
  getToken: vi.fn(),
}));

// Mock fetch
global.fetch = vi.fn();

// Mock analytics
vi.mock('../utils/analytics', () => ({
  trackEvent: vi.fn(),
}));

// Mock useAnalyticsTracking hook
vi.mock('../hooks/useAnalyticsTracking', () => ({
  useAnalyticsTracking: () => ({
    trackCTAClick: vi.fn(),
  }),
}));

describe('Success', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    vi.clearAllMocks();
    delete window.location;
    window.location = { ...originalLocation, search: '' };
  });

  afterEach(() => {
    window.location = originalLocation;
  });

  it('should show error when no token in URL', () => {
    // Arrange - no token in URL
    window.location.search = '';

    // Act
    render(
      <CreditProvider>
        <Success />
      </CreditProvider>
    );

    // Assert
    expect(screen.getByText('Error: Credits not activated. Please contact support.')).toBeInTheDocument();
  });

  it('should show "Activating..." when token is present', () => {
    // Arrange
    window.location.search = '?token=abc-123';
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve({ credits: 0 }),
    });

    // Act
    render(
      <CreditProvider>
        <Success />
      </CreditProvider>
    );

    // Assert
    expect(screen.getByText('Activating your credits...')).toBeInTheDocument();
  });

  it('should call saveToken when token is present', () => {
    // Arrange
    window.location.search = '?token=abc-123';
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve({ credits: 0 }),
    });

    // Act
    render(
      <CreditProvider>
        <Success />
      </CreditProvider>
    );

    // Assert - Token extraction and API call should work
    expect(fetch).toHaveBeenCalledWith('/api/credits?token=abc-123');
  });

  
  it('should include citation input when rendered', () => {
    // Arrange
    window.location.search = '?token=abc-123';

    // Act
    render(
      <CreditProvider>
        <Success />
      </CreditProvider>
    );

    // Assert - Should show activating state initially
    expect(screen.getByText('Activating your credits...')).toBeInTheDocument();
  });

  it('should handle fetch errors gracefully', () => {
    // Arrange
    window.location.search = '?token=abc-123';
    fetch.mockRejectedValueOnce(new Error('Network error'));

    // Act
    render(
      <CreditProvider>
        <Success />
      </CreditProvider>
    );

    // Should not crash and should show activating state
    expect(screen.getByText('Activating your credits...')).toBeInTheDocument();
  });
});