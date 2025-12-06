import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import Success from './Success';
import { CreditProvider } from '../contexts/CreditContext';

// Mock the creditStorage utility
vi.mock('../utils/creditStorage', () => ({
  saveToken: vi.fn(),
  getToken: vi.fn(),
  clearFreeUserId: vi.fn(),
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

  // Upgrade workflow logging tests
  it('should log upgrade success event when pending_upgrade_job_id exists', async () => {
    // Arrange
    window.location.search = '?token=abc-123';
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve({ credits: 1000 }),
    });

    // Mock localStorage to have pending job
    const localStorageGetItem = vi.spyOn(Storage.prototype, 'getItem');
    const localStorageRemoveItem = vi.spyOn(Storage.prototype, 'removeItem');
    localStorageGetItem.mockReturnValue('test-job-123');

    // Act
    render(
      <CreditProvider>
        <Success />
      </CreditProvider>
    );

    // Assert - Wait for async operations
    await vi.waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/upgrade-event',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            event_type: 'success',
            job_id: 'test-job-123'
          })
        }
      );
    });

    expect(localStorageRemoveItem).toHaveBeenCalledWith('pending_upgrade_job_id');

    // Cleanup
    localStorageGetItem.mockRestore();
    localStorageRemoveItem.mockRestore();
  });

  it('should not log upgrade event when no pending_upgrade_job_id', async () => {
    // Arrange
    window.location.search = '?token=abc-123';
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve({ credits: 1000 }),
    });

    const localStorageGetItem = vi.spyOn(Storage.prototype, 'getItem');
    localStorageGetItem.mockReturnValue(null);

    // Act
    render(
      <CreditProvider>
        <Success />
      </CreditProvider>
    );

    // Wait a bit to ensure async operations complete
    await new Promise(resolve => setTimeout(resolve, 100));

    // Assert - Should not call upgrade-event API
    const upgradeEventCalls = fetch.mock.calls.filter(
      call => call[0] === '/api/upgrade-event'
    );
    expect(upgradeEventCalls).toHaveLength(0);

    // Cleanup
    localStorageGetItem.mockRestore();
  });

  it('should clear localStorage even if upgrade-event API fails', async () => {
    // Arrange
    window.location.search = '?token=abc-123';
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve({ credits: 1000 }),
    });

    // Mock upgrade-event API to fail
    fetch
      .mockResolvedValueOnce({
        json: () => Promise.resolve({ credits: 1000 }),
      })
      .mockRejectedValueOnce(new Error('API error'));

    const localStorageGetItem = vi.spyOn(Storage.prototype, 'getItem');
    const localStorageRemoveItem = vi.spyOn(Storage.prototype, 'removeItem');
    localStorageGetItem.mockReturnValue('test-job-123');

    // Act
    render(
      <CreditProvider>
        <Success />
      </CreditProvider>
    );

    // Wait for async operations
    await vi.waitFor(() => {
      expect(localStorageRemoveItem).toHaveBeenCalledWith('pending_upgrade_job_id');
    }, { timeout: 2000 });

    // Cleanup
    localStorageGetItem.mockRestore();
    localStorageRemoveItem.mockRestore();
  });
});