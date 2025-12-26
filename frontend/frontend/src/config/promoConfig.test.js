import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
    PROMO_CONFIG,
    isPromoEnabled,
    getPromoContent,
    getOriginalPrice,
    getButtonText
} from './promoConfig'

describe('promoConfig', () => {
    // Store original config values to restore after each test
    const originalConfig = { ...PROMO_CONFIG }

    beforeEach(() => {
        // Reset config to original values before each test
        Object.assign(PROMO_CONFIG, originalConfig)
    })

    describe('isPromoEnabled', () => {
        it('returns true when enabled and discount > 0', () => {
            PROMO_CONFIG.enabled = true
            PROMO_CONFIG.discountPercent = 50

            expect(isPromoEnabled()).toBe(true)
        })

        it('returns false when disabled', () => {
            PROMO_CONFIG.enabled = false
            PROMO_CONFIG.discountPercent = 50

            expect(isPromoEnabled()).toBe(false)
        })

        it('returns false when discount is 0', () => {
            PROMO_CONFIG.enabled = true
            PROMO_CONFIG.discountPercent = 0

            expect(isPromoEnabled()).toBe(false)
        })
    })

    describe('getPromoContent', () => {
        it('returns text and emoji when enabled', () => {
            PROMO_CONFIG.enabled = true
            PROMO_CONFIG.discountPercent = 50
            PROMO_CONFIG.text = "Test Promo"
            PROMO_CONFIG.emoji = { left: "🎁", right: "⏰" }

            expect(getPromoContent()).toEqual({
                text: "Test Promo",
                emoji: { left: "🎁", right: "⏰" }
            })
        })

        it('returns null when disabled', () => {
            PROMO_CONFIG.enabled = false

            expect(getPromoContent()).toBeNull()
        })
    })

    describe('getOriginalPrice', () => {
        it('calculates correct original price at 50% discount', () => {
            PROMO_CONFIG.enabled = true
            PROMO_CONFIG.discountPercent = 50

            // $4.99 at 50% off means original was ~$9.98, rounds to $9.99
            expect(getOriginalPrice(4.99)).toBe(9.99)
        })

        it('returns .99 ending', () => {
            PROMO_CONFIG.enabled = true
            PROMO_CONFIG.discountPercent = 50

            const result = getOriginalPrice(4.99)
            const cents = Math.round((result % 1) * 100)
            expect(cents).toBe(99)
        })

        it('returns null when promo disabled', () => {
            PROMO_CONFIG.enabled = false

            expect(getOriginalPrice(4.99)).toBeNull()
        })

        it('handles different discount percentages', () => {
            PROMO_CONFIG.enabled = true
            PROMO_CONFIG.discountPercent = 25

            // $4.99 at 25% off means original was ~$6.65, rounds to $6.99
            expect(getOriginalPrice(4.99)).toBe(6.99)
        })
    })

    describe('getButtonText', () => {
        it('returns dynamic promo text when enabled', () => {
            PROMO_CONFIG.enabled = true
            PROMO_CONFIG.discountPercent = 50

            expect(getButtonText('7-Day Pass')).toBe('Get 50% Off')
        })

        it('returns default buy text when disabled', () => {
            PROMO_CONFIG.enabled = false

            expect(getButtonText('7-Day Pass')).toBe('Buy 7-Day Pass')
        })

        it('includes correct discount percentage in text', () => {
            PROMO_CONFIG.enabled = true
            PROMO_CONFIG.discountPercent = 30

            expect(getButtonText('500 Credits')).toBe('Get 30% Off')
        })
    })
})
