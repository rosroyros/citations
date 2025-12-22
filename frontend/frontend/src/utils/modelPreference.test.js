import { describe, it, beforeEach, afterEach, expect, vi } from 'vitest'
import { getModelPreference, getModelName } from './modelPreference'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  get length() { return 0 },
  key: vi.fn()
}

beforeEach(() => {
  // Reset all mocks before each test
  Object.keys(localStorageMock).forEach(key => {
    if (typeof localStorageMock[key] === 'function') {
      localStorageMock[key].mockClear()
    }
  })

  // Replace global localStorage with mock
  vi.stubGlobal('localStorage', localStorageMock)

  // Mock Math.random
  vi.spyOn(Math, 'random')
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('modelPreference', () => {
  describe('getModelPreference', () => {
    it('should always return model_c (Gemini 3 Flash)', () => {
      // Currently all users get model_c
      const result = getModelPreference()
      expect(result).toBe('model_c')
    })

    it('should not use localStorage (single model mode)', () => {
      const result = getModelPreference()
      expect(result).toBe('model_c')
      // localStorage should not be accessed in single model mode
      expect(localStorageMock.setItem).not.toHaveBeenCalled()
    })

    it('should return model_c regardless of Math.random value', () => {
      // Even if random assignment was enabled, we should get model_c
      Math.random.mockReturnValue(0.3)
      expect(getModelPreference()).toBe('model_c')

      Math.random.mockReturnValue(0.7)
      expect(getModelPreference()).toBe('model_c')
    })

    // Commented test preserved for future A/B re-enablement
    // it('should generate random assignment when A/B testing enabled', () => {
    //   localStorageMock.getItem.mockReturnValue(null)
    //   Math.random.mockReturnValue(0.3)
    //   const result = getModelPreference()
    //   expect(result).toBeOneOf(['model_a', 'model_b', 'model_c'])
    //   expect(localStorageMock.setItem).toHaveBeenCalled()
    // })
  })

  describe('getModelName', () => {
    it('should return OpenAI for model_a', () => {
      expect(getModelName('model_a')).toBe('OpenAI')
    })

    it('should return Gemini for model_b', () => {
      expect(getModelName('model_b')).toBe('Gemini')
    })

    it('should return Gemini 3 for model_c', () => {
      expect(getModelName('model_c')).toBe('Gemini 3')
    })

    it('should return Unknown for invalid model', () => {
      expect(getModelName('invalid')).toBe('Unknown')
    })
  })
})