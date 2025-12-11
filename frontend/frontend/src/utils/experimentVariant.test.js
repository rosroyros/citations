/**
 * Unit tests for experimentVariant utility
 *
 * These verify:
 * - Random assignment works (50/50 split)
 * - Sticky assignment persists
 * - localStorage integration works
 * - Helper functions work correctly
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  getExperimentVariant,
  getVariantName,
  hasExperimentVariant,
  resetExperimentVariant,
  forceVariant
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
    it('assigns variant 1 or 2 on first call', () => {
      const variant = getExperimentVariant()
      expect(['1', '2']).toContain(variant)
    })

    it('stores variant in localStorage', () => {
      getExperimentVariant()
      const stored = localStorageMock.getItem('experiment_v1')
      expect(['1', '2']).toContain(stored)
    })

    it('returns same variant on subsequent calls (sticky)', () => {
      const first = getExperimentVariant()
      const second = getExperimentVariant()
      const third = getExperimentVariant()

      expect(second).toBe(first)
      expect(third).toBe(first)
    })

    it('respects existing localStorage value', () => {
      localStorageMock.setItem('experiment_v1', '2')
      const variant = getExperimentVariant()
      expect(variant).toBe('2')
    })

    it('returns variant 1 when localStorage is not available', () => {
      // Simulate SSR environment
      const originalLocalStorage = global.localStorage
      global.localStorage = undefined

      const variant = getExperimentVariant()
      expect(variant).toBe('1')
      expect(console.warn).toHaveBeenCalledWith('[A/B Test] localStorage not available, defaulting to variant 1')

      // Restore
      global.localStorage = originalLocalStorage
    })
  })

  describe('getVariantName', () => {
    it('returns "Credits" for variant 1', () => {
      expect(getVariantName('1')).toBe('Credits')
    })

    it('returns "Passes" for variant 2', () => {
      expect(getVariantName('2')).toBe('Passes')
    })

    it('returns "Unknown" for invalid variant', () => {
      expect(getVariantName('99')).toBe('Unknown')
      expect(getVariantName(null)).toBe('Unknown')
      expect(getVariantName(undefined)).toBe('Unknown')
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
      expect(['1', '2']).toContain(second)
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
      forceVariant('1')
      expect(getExperimentVariant()).toBe('1')

      forceVariant('2')
      expect(getExperimentVariant()).toBe('2')
    })

    it('rejects invalid variant IDs', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      forceVariant('99')
      expect(consoleSpy).toHaveBeenCalledWith('[A/B Test] Invalid variant ID. Must be "1" or "2"')
    })

    it('handles localStorage not available', () => {
      const originalLocalStorage = global.localStorage
      global.localStorage = undefined

      forceVariant('1')
      expect(console.warn).toHaveBeenCalledWith('[A/B Test] localStorage not available')

      // Restore
      global.localStorage = originalLocalStorage
    })
  })

  describe('distribution test (statistical)', () => {
    it('should have roughly 50/50 distribution over 1000 trials', () => {
      const trials = 1000
      let countVariant1 = 0
      let countVariant2 = 0

      for (let i = 0; i < trials; i++) {
        localStorageMock.clear()  // Reset for each trial
        const variant = getExperimentVariant()

        if (variant === '1') countVariant1++
        else if (variant === '2') countVariant2++
      }

      // Should be roughly 50/50 (allow 10% variance)
      const ratio = countVariant1 / trials
      expect(ratio).toBeGreaterThan(0.40)  // At least 40%
      expect(ratio).toBeLessThan(0.60)     // At most 60%

      console.log(`Distribution: Variant 1: ${countVariant1}, Variant 2: ${countVariant2}`)
    })
  })
})