import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PromoPill } from './PromoPill'
import * as promoConfig from '../config/promoConfig'

describe('PromoPill', () => {
    // Store original config values
    const originalConfig = { ...promoConfig.PROMO_CONFIG }

    beforeEach(() => {
        // Reset to enabled state with default values
        Object.assign(promoConfig.PROMO_CONFIG, {
            enabled: true,
            text: "New Year's Deal — 50% Off",
            emoji: { left: "🎉", right: "⏰" },
            discountPercent: 50
        })
    })

    afterEach(() => {
        // Restore original config
        Object.assign(promoConfig.PROMO_CONFIG, originalConfig)
    })

    describe('when promo is enabled', () => {
        it('renders the promo text', () => {
            render(<PromoPill />)

            expect(screen.getByText("New Year's Deal — 50% Off")).toBeInTheDocument()
        })

        it('renders both emojis', () => {
            render(<PromoPill />)

            expect(screen.getByText("🎉")).toBeInTheDocument()
            expect(screen.getByText("⏰")).toBeInTheDocument()
        })

        it('applies custom className to outer container', () => {
            const { container } = render(<PromoPill className="mt-4" />)

            expect(container.firstChild).toHaveClass('mt-4')
        })

        it('has correct styling classes', () => {
            const { container } = render(<PromoPill />)
            const pill = container.querySelector('.bg-gradient-to-r')

            expect(pill).toBeInTheDocument()
            expect(pill).toHaveClass('from-amber-200')
            expect(pill).toHaveClass('border-amber-400')
            expect(pill).toHaveClass('rounded-full')
        })
    })

    describe('when promo is disabled', () => {
        it('returns null and renders nothing', () => {
            promoConfig.PROMO_CONFIG.enabled = false

            const { container } = render(<PromoPill />)

            expect(container.firstChild).toBeNull()
        })
    })

    describe('responsive behavior', () => {
        it('has mobile-first responsive classes', () => {
            const { container } = render(<PromoPill />)
            const pill = container.querySelector('.bg-gradient-to-r')

            // Mobile-first classes (smaller on mobile, larger on sm+)
            expect(pill).toHaveClass('gap-2')
            expect(pill).toHaveClass('sm:gap-3')
            expect(pill).toHaveClass('px-4')
            expect(pill).toHaveClass('sm:px-6')
            expect(pill).toHaveClass('py-2')
            expect(pill).toHaveClass('sm:py-3')
            expect(pill).toHaveClass('text-sm')
            expect(pill).toHaveClass('sm:text-base')
        })
    })
})
