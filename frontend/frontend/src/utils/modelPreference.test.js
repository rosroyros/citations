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
    it('should return a valid model preference', () => {
      localStorageMock.getItem.mockReturnValue(null)
      Math.random.mockReturnValue(0.3)

      const result = getModelPreference()

      expect(result).toBeOneOf(['model_a', 'model_b'])
      expect(localStorageMock.setItem).toHaveBeenCalledWith('model_preference', result)
    })

    it('should generate model_b when Math.random() < 0.5', () => {
      localStorageMock.getItem.mockReturnValue(null)
      Math.random.mockReturnValue(0.3)

      const result = getModelPreference()

      expect(result).toBe('model_b')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('model_preference', 'model_b')
    })

    it('should generate model_a when Math.random() >= 0.5', () => {
      localStorageMock.getItem.mockReturnValue(null)
      Math.random.mockReturnValue(0.7)

      const result = getModelPreference()

      expect(result).toBe('model_a')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('model_preference', 'model_a')
    })

    it('should return stored valid preference', () => {
      localStorageMock.getItem.mockReturnValue('model_b')

      const result = getModelPreference()

      expect(result).toBe('model_b')
      expect(localStorageMock.setItem).not.toHaveBeenCalled()
    })

    it('should clear invalid stored preference and generate new one', () => {
      localStorageMock.getItem.mockReturnValue('invalid_model')
      Math.random.mockReturnValue(0.2)

      const result = getModelPreference()

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('model_preference')
      expect(result).toBe('model_b')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('model_preference', 'model_b')
    })
  })

  describe('getModelName', () => {
    it('should return OpenAI for model_a', () => {
      expect(getModelName('model_a')).toBe('OpenAI')
    })

    it('should return Gemini for model_b', () => {
      expect(getModelName('model_b')).toBe('Gemini')
    })

    it('should return Unknown for invalid model', () => {
      expect(getModelName('invalid')).toBe('Unknown')
    })
  })
})