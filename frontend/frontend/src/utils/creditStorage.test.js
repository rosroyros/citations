import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock localStorage for testing
const createLocalStorageMock = () => {
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
    store
  };
};

let localStorageMock;

// Import the functions we're going to test
import { saveToken, getToken, clearToken, getFreeUsage, incrementFreeUsage, resetFreeUsage, getFreeUserId, ensureFreeUserId, clearFreeUserId } from './creditStorage.js';

describe('Credit Storage Utilities', () => {
  beforeEach(() => {
    // Create fresh localStorage mock before each test
    localStorageMock = createLocalStorageMock();
    global.localStorage = localStorageMock;
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

  describe('Free User ID Management', () => {
    test('getFreeUserId returns null when no user ID exists', () => {
      localStorageMock.getItem.mockReturnValue(null);
      expect(getFreeUserId()).toBeNull();
    });

    test('getFreeUserId returns existing user ID', () => {
      const existingId = '550e8400-e29b-41d4-a716-446655440000';
      localStorageMock.getItem.mockReturnValue(existingId);
      expect(getFreeUserId()).toBe(existingId);
    });

    test('ensureFreeUserId generates UUID on first call', () => {
      const userId = ensureFreeUserId();

      // Should return a UUID string
      expect(typeof userId).toBe('string');
      expect(userId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);

      // Should store in localStorage
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'citation_checker_free_user_id',
        userId
      );
    });

    test('ensureFreeUserId returns same UUID on subsequent calls', () => {
      const existingId = '550e8400-e29b-41d4-a716-446655440000';

      // Mock localStorage to return existing ID
      localStorageMock.getItem.mockReturnValue(existingId);

      const userId1 = ensureFreeUserId();
      const userId2 = ensureFreeUserId();

      // Both calls should return the same ID
      expect(userId1).toBe(existingId);
      expect(userId2).toBe(existingId);
      expect(userId1).toBe(userId2);

      // Should not call setItem again
      expect(localStorageMock.setItem).toHaveBeenCalledTimes(0);
    });

    test('clearFreeUserId removes user ID from localStorage', () => {
      clearFreeUserId();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('citation_checker_free_user_id');
    });

    test('free user ID functions handle localStorage errors gracefully', () => {
      // Mock localStorage to throw errors for get/remove operations
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage access denied');
      });
      localStorageMock.removeItem.mockImplementation(() => {
        throw new Error('localStorage access denied');
      });

      // Should not throw errors
      expect(() => getFreeUserId()).not.toThrow();
      expect(() => ensureFreeUserId()).not.toThrow();
      expect(() => clearFreeUserId()).not.toThrow();

      // Should return null/error-safe values for get operations
      expect(getFreeUserId()).toBeNull();

      // ensureFreeUserId should still generate a UUID (setItem might still work)
      const userId = ensureFreeUserId();
      expect(typeof userId).toBe('string');
      if (userId !== null) {
        expect(userId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
      }
    });
  });
});