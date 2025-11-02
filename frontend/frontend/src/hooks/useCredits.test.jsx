import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCredits } from './useCredits';
import { getToken } from '../utils/creditStorage';

// Mock the creditStorage module
vi.mock('../utils/creditStorage', () => ({
  getToken: vi.fn(),
}));

// Mock fetch
global.fetch = vi.fn();

describe('useCredits', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch credits on mount if token exists', async () => {
    // Arrange
    const mockToken = 'test-token-123';
    getToken.mockReturnValue(mockToken);

    const mockResponse = {
      ok: true,
      json: async () => ({ credits: 847, token: mockToken }),
    };
    fetch.mockResolvedValue(mockResponse);

    // Act
    const { result } = renderHook(() => useCredits());

    // Assert - initial state
    expect(result.current.loading).toBe(true);
    expect(result.current.credits).toBe(null);
    expect(result.current.error).toBe(null);
    expect(result.current.hasToken).toBe(true);

    // Wait for async operation
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Assert - after fetch
    expect(fetch).toHaveBeenCalledWith(`/api/credits?token=${mockToken}`);
    expect(result.current.credits).toBe(847);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should return null if no token', async () => {
    // Arrange
    getToken.mockReturnValue(null);

    // Act
    const { result } = renderHook(() => useCredits());

    // Assert
    expect(result.current.credits).toBe(null);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.hasToken).toBe(false);
    expect(fetch).not.toHaveBeenCalled();
  });

  it('should refresh credits when refreshCredits is called', async () => {
    // Arrange
    const mockToken = 'test-token-456';
    getToken.mockReturnValue(mockToken);

    const mockResponse1 = {
      ok: true,
      json: async () => ({ credits: 100, token: mockToken }),
    };
    const mockResponse2 = {
      ok: true,
      json: async () => ({ credits: 95, token: mockToken }),
    };

    fetch
      .mockResolvedValueOnce(mockResponse1)
      .mockResolvedValueOnce(mockResponse2);

    // Act
    const { result } = renderHook(() => useCredits());

    // Wait for initial fetch
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Assert initial fetch
    expect(result.current.credits).toBe(100);

    // Act - refresh credits
    await act(async () => {
      await result.current.refreshCredits();
    });

    // Assert - refreshed credits
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(fetch).toHaveBeenLastCalledWith(`/api/credits?token=${mockToken}`);
    expect(result.current.credits).toBe(95);
  });

  it('should handle loading state correctly', async () => {
    // Arrange
    const mockToken = 'test-token-789';
    getToken.mockReturnValue(mockToken);

    let resolveFetch;
    const fetchPromise = new Promise(resolve => {
      resolveFetch = resolve;
    });
    fetch.mockReturnValue(fetchPromise);

    // Act
    const { result } = renderHook(() => useCredits());

    // Assert - loading state during fetch
    expect(result.current.loading).toBe(true);

    // Resolve fetch
    await act(async () => {
      resolveFetch({
        ok: true,
        json: async () => ({ credits: 500, token: mockToken }),
      });
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Assert - loading complete
    expect(result.current.loading).toBe(false);
    expect(result.current.credits).toBe(500);
  });

  it('should handle API errors gracefully', async () => {
    // Arrange
    const mockToken = 'test-token-error';
    getToken.mockReturnValue(mockToken);

    const mockError = new Error('Network error');
    fetch.mockRejectedValue(mockError);

    // Act
    const { result } = renderHook(() => useCredits());

    // Wait for async operation
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Assert
    expect(result.current.loading).toBe(false);
    expect(result.current.credits).toBe(null);
    expect(result.current.error).toBe('Network error');
    expect(result.current.hasToken).toBe(true);
  });

  it('should handle non-OK responses', async () => {
    // Arrange
    const mockToken = 'test-token-500';
    getToken.mockReturnValue(mockToken);

    const mockResponse = {
      ok: false,
      status: 500,
      json: async () => ({ error: 'Server error' }),
    };
    fetch.mockResolvedValue(mockResponse);

    // Act
    const { result } = renderHook(() => useCredits());

    // Wait for async operation
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Assert
    expect(result.current.loading).toBe(false);
    expect(result.current.credits).toBe(null);
    expect(result.current.error).toBeDefined();
    expect(result.current.hasToken).toBe(true);
  });
});