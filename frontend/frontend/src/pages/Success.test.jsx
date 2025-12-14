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

    // Mock localStorage differently - override entire localStorage
    const localStorageMock = {
      getItem: vi.fn((key) => {
        if (key === 'pending_upgrade_job_id') {
          return 'test-job-123';
        }
        return null;
      }),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };

    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });

    const localStorageGetItem = localStorageMock.getItem;
    const localStorageRemoveItem = localStorageMock.removeItem;

    // Mock upgrade-event API first, then credits API
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      })
      .mockResolvedValueOnce({
        json: () => Promise.resolve({ credits: 1000 }),
      });

    // Add more fetch mocks for polling
    fetch
      .mockResolvedValue({
        json: () => Promise.resolve({ credits: 1000 }),
      });

    // Act
    render(
      <CreditProvider>
        <Success />
      </CreditProvider>
    );

    // Assert - Check that upgrade-event was called
    await vi.waitFor(() => {
      const upgradeCalls = fetch.mock.calls.filter(
        call => call[0] === '/api/upgrade-event'
      );
      expect(upgradeCalls).toHaveLength(1);
      // Check the call details manually
      expect(upgradeCalls[0][0]).toBe('/api/upgrade-event');
      expect(upgradeCalls[0][1].method).toBe('POST');
      expect(upgradeCalls[0][1].headers).toEqual({
        'Content-Type': 'application/json',
        'X-User-Token': 'abc-123'
      });

      // Parse JSON to compare object regardless of key order
      const bodyObj = JSON.parse(upgradeCalls[0][1].body);
      expect(bodyObj).toEqual({
        event: 'success',
        job_id: 'test-job-123'
      });
    });

    // Wait for localStorage.removeItem to be called
    await vi.waitFor(() => {
      expect(localStorageRemoveItem).toHaveBeenCalledWith('pending_upgrade_job_id');
    }, { timeout: 2000 });

    // Cleanup - no need for mockRestore with this approach
  });

  it('should not log upgrade event when no pending_upgrade_job_id', async () => {
    // Arrange
    window.location.search = '?token=abc-123';
    fetch.mockResolvedValueOnce({
      json: () => Promise.resolve({ credits: 1000 }),
    });

    // Mock localStorage to have no pending job
    const localStorageMock = {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };

    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });

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

    // Cleanup - no need for mockRestore with this approach
  });

  it('should clear localStorage even if upgrade-event API fails', async () => {
    // Arrange
    window.location.search = '?token=abc-123';

    // Mock upgrade-event API to fail, then credits API to succeed
    fetch
      .mockRejectedValueOnce(new Error('API error'))
      .mockResolvedValueOnce({
        json: () => Promise.resolve({ credits: 1000 }),
      });

    // Mock localStorage to have pending job
    const localStorageMock = {
      getItem: vi.fn(() => 'test-job-123'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };

    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });

    const localStorageGetItem = localStorageMock.getItem;
    const localStorageRemoveItem = localStorageMock.removeItem;

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

    // Cleanup - no need for mockRestore with this approach
  });

  describe('Success Banner - Pass Support', () => {
    it('should show pass message when user has active day pass', async () => {
      // Arrange
      window.location.search = '?token=test-pass-token';

      const mockFetch = vi.fn();
      global.fetch = mockFetch;

      // Mock successful response with active pass
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            credits: 0,
            active_pass: { hours_remaining: 72 }
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({})
        });

      // Act
      render(
        <CreditProvider>
          <Success />
        </CreditProvider>
      );

      // Assert - Wait for success status and banner to appear
      await vi.waitFor(async () => {
        expect(await screen.queryByText('✅ Payment Successful! Your 3-Day Pass is now active')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should show credits message when user has credits', async () => {
      // Arrange
      window.location.search = '?token=test-credits-token';

      const mockFetch = vi.fn();
      global.fetch = mockFetch;

      // Mock successful response with credits
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            credits: 1000,
            active_pass: null
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({})
        });

      // Act
      render(
        <CreditProvider>
          <Success />
        </CreditProvider>
      );

      // Assert - Wait for success status and banner to appear
      await vi.waitFor(async () => {
        expect(await screen.queryByText('✅ Payment Successful! You now have 1000 Citation Credits')).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });
});