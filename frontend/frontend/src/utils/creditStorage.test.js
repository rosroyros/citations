import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock localStorage for testing
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = String(value);
    }),
    removeItem: vi.fn((key) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

global.localStorage = localStorageMock;

// Import the functions we're going to test
import { saveToken, getToken, clearToken, getFreeUsage, incrementFreeUsage, resetFreeUsage } from './creditStorage.js';

describe('Credit Storage Utilities', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  describe('Token management', () => {
    test('saveToken stores token in localStorage under correct key', () => {
      const testToken = 'test-token-123';
      saveToken(testToken);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'citation_checker_token',
        testToken
      );
    });

    test('getToken retrieves token or returns null', () => {
      // Test when token exists
      localStorageMock.getItem.mockReturnValue('existing-token');
      expect(getToken()).toBe('existing-token');

      // Test when no token exists
      localStorageMock.getItem.mockReturnValue(null);
      expect(getToken()).toBeNull();
    });

    test('clearToken removes token from localStorage', () => {
      clearToken();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('citation_checker_token');
    });
  });

  describe('Free tier tracking', () => {
    test('getFreeUsage returns 0 for new users', () => {
      localStorageMock.getItem.mockReturnValue(null);
      expect(getFreeUsage()).toBe(0);
    });

    test('getFreeUsage returns existing usage count', () => {
      localStorageMock.getItem.mockReturnValue('5');
      expect(getFreeUsage()).toBe(5);
    });

    test('incrementFreeUsage increments counter correctly', () => {
      // Mock existing usage of 3
      localStorageMock.getItem.mockReturnValue('3');
      incrementFreeUsage(2);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'citation_checker_free_used',
        '5'
      );
    });

    test('resetFreeUsage clears counter', () => {
      resetFreeUsage();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('citation_checker_free_used');
    });
  });

  describe('Error handling', () => {
    test('handles localStorage quota exceeded gracefully', () => {
      // Mock localStorage to throw quota exceeded error
      localStorageMock.setItem.mockImplementation(() => {
        const error = new Error('QuotaExceededError');
        error.name = 'QuotaExceededError';
        throw error;
      });

      // Should not throw error
      expect(() => saveToken('test-token')).not.toThrow();
    });

    test('handles localStorage access errors gracefully', () => {
      // Mock localStorage to throw generic error
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage access denied');
      });

      // Should return null on error
      expect(getToken()).toBeNull();
      expect(getFreeUsage()).toBe(0);
    });
  });
});