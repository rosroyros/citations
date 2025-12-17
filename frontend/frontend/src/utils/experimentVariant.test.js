/**
 * Unit tests for experimentVariant utility
 *
 * These verify:
 * - Random assignment works (25/25/25/25 split across 4 variants)
 * - Sticky assignment persists
 * - Migration from old 2-variant to new 4-variant scheme
 * - localStorage integration works
 * - Helper functions work correctly
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  getExperimentVariant,
  getVariantName,
  hasExperimentVariant,
  resetExperimentVariant,
  forceVariant,
  isInlineVariant,
  getPricingType
} from './experimentVariant'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}

  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = value.toString() },
    removeItem: (key) => { delete store[key] },
    clear: () => { store = {} }
  }
})()

// Setup and teardown
beforeEach(() => {
  // Clear localStorage before each test
  localStorageMock.clear()
  // Reset console mocks
  vi.spyOn(console, 'log').mockImplementation(() => {})
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
  // Override global localStorage
  global.localStorage = localStorageMock
})

describe('experimentVariant', () => {
  describe('getExperimentVariant', () => {
    it('assigns one of 4 variants on first call', () => {
      const variant = getExperimentVariant()
      expect(['1.1', '1.2', '2.1', '2.2']).toContain(variant)
    })

    it('stores variant in localStorage', () => {
      getExperimentVariant()
      const stored = localStorageMock.getItem('experiment_v1')
      expect(['1.1', '1.2', '2.1', '2.2']).toContain(stored)
    })

    it('returns same variant on subsequent calls (sticky)', () => {
      const first = getExperimentVariant()
      const second = getExperimentVariant()
      const third = getExperimentVariant()

      expect(second).toBe(first)
      expect(third).toBe(first)
    })

    it('respects existing valid localStorage value', () => {
      localStorageMock.setItem('experiment_v1', '1.2')
      const variant = getExperimentVariant()
      expect(variant).toBe('1.2')
    })

    it('migrates old "1"/"2" values to new 4-variant scheme', () => {
      localStorageMock.setItem('experiment_v1', '1')
      const variant = getExperimentVariant()
      expect(['1.1', '1.2', '2.1', '2.2']).toContain(variant)
    })

    it('migrates invalid values to new 4-variant scheme', () => {
      localStorageMock.setItem('experiment_v1', 'invalid')
      const variant = getExperimentVariant()
      expect(['1.1', '1.2', '2.1', '2.2']).toContain(variant)
    })

    it('returns variant 1.1 when localStorage is not available', () => {
      // Simulate SSR environment
      const originalLocalStorage = global.localStorage
      global.localStorage = undefined

      const variant = getExperimentVariant()
      expect(variant).toBe('1.1')
      expect(console.warn).toHaveBeenCalledWith('[A/B Test] localStorage not available, defaulting to variant 1.1')

      // Restore
      global.localStorage = originalLocalStorage
    })
  })

  describe('getVariantName', () => {
    it('returns correct names for all 4 variants', () => {
      expect(getVariantName('1.1')).toBe('Credits (Button)')
      expect(getVariantName('1.2')).toBe('Credits (Inline)')
      expect(getVariantName('2.1')).toBe('Passes (Button)')
      expect(getVariantName('2.2')).toBe('Passes (Inline)')
    })

    it('returns "Unknown" for invalid variant', () => {
      expect(getVariantName('99')).toBe('Unknown')
      expect(getVariantName('1')).toBe('Unknown')  // Old format
      expect(getVariantName(null)).toBe('Unknown')
      expect(getVariantName(undefined)).toBe('Unknown')
    })
  })

  describe('isInlineVariant', () => {
    it('returns true for inline variants', () => {
      expect(isInlineVariant('1.2')).toBe(true)
      expect(isInlineVariant('2.2')).toBe(true)
    })

    it('returns false for button variants', () => {
      expect(isInlineVariant('1.1')).toBe(false)
      expect(isInlineVariant('2.1')).toBe(false)
    })
  })

  describe('getPricingType', () => {
    it('returns "credits" for credits variants', () => {
      expect(getPricingType('1.1')).toBe('credits')
      expect(getPricingType('1.2')).toBe('credits')
    })

    it('returns "passes" for passes variants', () => {
      expect(getPricingType('2.1')).toBe('passes')
      expect(getPricingType('2.2')).toBe('passes')
    })
  })

  describe('hasExperimentVariant', () => {
    it('returns false when no variant assigned', () => {
      expect(hasExperimentVariant()).toBe(false)
    })

    it('returns true after variant assigned', () => {
      getExperimentVariant()
      expect(hasExperimentVariant()).toBe(true)
    })

    it('returns false when localStorage is not available', () => {
      const originalLocalStorage = global.localStorage
      global.localStorage = undefined

      expect(hasExperimentVariant()).toBe(false)

      // Restore
      global.localStorage = originalLocalStorage
    })
  })

  describe('resetExperimentVariant', () => {
    it('removes variant from localStorage', () => {
      getExperimentVariant()
      expect(hasExperimentVariant()).toBe(true)

      resetExperimentVariant()
      expect(hasExperimentVariant()).toBe(false)
    })

    it('allows new assignment after reset', () => {
      const first = getExperimentVariant()
      resetExperimentVariant()

      // Second assignment might be different (random)
      const second = getExperimentVariant()
      expect(['1.1', '1.2', '2.1', '2.2']).toContain(second)
    })

    it('handles localStorage not available', () => {
      const originalLocalStorage = global.localStorage
      global.localStorage = undefined

      resetExperimentVariant()
      expect(console.warn).toHaveBeenCalledWith('[A/B Test] localStorage not available')

      // Restore
      global.localStorage = originalLocalStorage
    })
  })

  describe('forceVariant', () => {
    it('sets specific variant', () => {
      forceVariant('1.1')
      expect(getExperimentVariant()).toBe('1.1')

      forceVariant('1.2')
      expect(getExperimentVariant()).toBe('1.2')

      forceVariant('2.1')
      expect(getExperimentVariant()).toBe('2.1')

      forceVariant('2.2')
      expect(getExperimentVariant()).toBe('2.2')
    })

    it('rejects invalid variant IDs', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      forceVariant('99')
      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Invalid variant ID: "99"'))

      forceVariant('1')  // Old format
      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Invalid variant ID: "1"'))

      consoleSpy.mockRestore()
    })

    it('handles localStorage not available', () => {
      const originalLocalStorage = global.localStorage
      global.localStorage = undefined

      forceVariant('1.1')
      expect(console.warn).toHaveBeenCalledWith('[A/B Test] localStorage not available')

      // Restore
      global.localStorage = originalLocalStorage
    })
  })

  describe('distribution test (statistical)', () => {
    it('should have roughly 25/25/25/25 distribution over 2000 trials', () => {
      const trials = 2000
      const counts = {
        '1.1': 0,
        '1.2': 0,
        '2.1': 0,
        '2.2': 0
      }

      for (let i = 0; i < trials; i++) {
        localStorageMock.clear()  // Reset for each trial
        const variant = getExperimentVariant()
        counts[variant]++
      }

      // Each variant should be roughly 25% (allow 8% variance)
      Object.entries(counts).forEach(([variant, count]) => {
        const ratio = count / trials
        expect(ratio).toBeGreaterThan(0.17)  // At least 17%
        expect(ratio).toBeLessThan(0.33)     // At most 33%
      })

      console.log(`Distribution: 1.1: ${counts['1.1']}, 1.2: ${counts['1.2']}, 2.1: ${counts['2.1']}, 2.2: ${counts['2.2']}`)
    })
  })
})