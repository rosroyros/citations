import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { PricingTablePasses } from './PricingTablePasses'
import { trackEvent } from '../utils/analytics'

// Mock analytics
vi.mock('../utils/analytics', () => ({
  trackEvent: vi.fn(),
  getToken: vi.fn()
}))
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock window.location.href to prevent actual navigation
Object.defineProperty(window, 'location', {
  value: { href: '' },
  writable: true,
})

// Mock console.log to avoid noise in tests
const mockConsoleLog = vi.fn()
global.console.log = mockConsoleLog

describe('PricingTablePasses', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    mockConsoleLog.mockClear()
    window.location.href = ''
    localStorage.clear()
  })

  it('renders all 3 pricing tiers', () => {
    render(<PricingTablePasses experimentVariant="2" />)

    // Check for all three pass types
    expect(screen.getByText('1-Day Pass')).toBeInTheDocument()
    expect(screen.getByText('7-Day Pass')).toBeInTheDocument()
    expect(screen.getByText('30-Day Pass')).toBeInTheDocument()
  })

  it('displays correct pricing for each tier', () => {
    render(<PricingTablePasses experimentVariant="2" />)

    // Check prices
    expect(screen.getByText('$1.99')).toBeInTheDocument()
    expect(screen.getByText('$4.99')).toBeInTheDocument()
    expect(screen.getByText('$9.99')).toBeInTheDocument()
  })

  it('shows "Best Value" badge only on 7-Day Pass tier', () => {
    render(<PricingTablePasses experimentVariant="2" />)

    const badges = screen.getAllByText('Best Value')
    expect(badges).toHaveLength(1) // Only one badge should exist
  })

  it('displays marketing descriptions', () => {
    render(<PricingTablePasses experimentVariant="2" />)

    expect(screen.getByText('Short-term access — great for quick checks.')).toBeInTheDocument()
    expect(screen.getByText('Best value for occasional writers.')).toBeInTheDocument()
    expect(screen.getByText('Unlimited access for heavy users.')).toBeInTheDocument()
  })

  it('calls checkout API and redirects when Buy button is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ checkout_url: 'https://checkout.polar.sh/example' })
    })

    render(<PricingTablePasses experimentVariant="2" />)

    // Find and click the 1-Day Pass button
    const buyButton = screen.getByText('Buy 1-Day Pass')
    fireEvent.click(buyButton)

    // Wait for the API call to complete
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productId: '1282bd9b-81b6-4f06-a1f2-29bb0be01f26',
          variantId: '2'
        })
      })
    })

    // Verify redirect happened
    await waitFor(() => {
      expect(window.location.href).toBe('https://checkout.polar.sh/example')
    })
  })

  it('calls checkout API for 7-Day Pass button', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ checkout_url: 'https://checkout.polar.sh/example' })
    })

    render(<PricingTablePasses experimentVariant="2" />)

    const buyButton = screen.getByText('Buy 7-Day Pass')
    fireEvent.click(buyButton)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productId: '5b311653-7127-41b5-aed6-496fb713149c',
          variantId: '2'
        })
      })
    })
  })

  it('shows loading state while checkout is being created', async () => {
    // Create a promise that we can control
    let resolveFetch
    const fetchPromise = new Promise(resolve => {
      resolveFetch = resolve
    })
    mockFetch.mockReturnValueOnce(fetchPromise)

    render(<PricingTablePasses experimentVariant="2" />)

    const buyButton = screen.getByText('Buy 1-Day Pass')
    fireEvent.click(buyButton)

    // Check for loading state
    expect(screen.getByText('Opening checkout...')).toBeInTheDocument()
    expect(buyButton).toBeDisabled()

    // Resolve the fetch promise
    resolveFetch({
      ok: true,
      json: async () => ({ checkout_url: 'https://checkout.polar.sh/example' })
    })

    // Button should be back to normal after loading
    await waitFor(() => {
      expect(screen.queryByText('Opening checkout...')).not.toBeInTheDocument()
      expect(buyButton).not.toBeDisabled()
    })
  })

  it('shows error message when checkout creation fails', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500
    })

    render(<PricingTablePasses experimentVariant="2" />)

    const buyButton = screen.getByText('Buy 1-Day Pass')
    fireEvent.click(buyButton)

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText('Failed to open checkout. Please try again.')).toBeInTheDocument()
    })

    // Verify button is not disabled after error
    expect(buyButton).not.toBeDisabled()
  })

  it('logs analytics events', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ checkout_url: 'https://checkout.polar.sh/example' })
    })

    render(<PricingTablePasses experimentVariant="2" />)

    // Check initial pricing table log
    expect(mockConsoleLog).toHaveBeenCalledWith('pricing_table_shown', { variant: '2' })

    const buyButton = screen.getByText('Buy 1-Day Pass')
    fireEvent.click(buyButton)

    await waitFor(() => {
      // Check product selection log
      expect(mockConsoleLog).toHaveBeenCalledWith('product_selected', {
        productId: '1282bd9b-81b6-4f06-a1f2-29bb0be01f26',
        variant: '2'
      })

      // Check checkout started log
      expect(trackEvent).toHaveBeenCalledWith('checkout_started', {
        productId: '1282bd9b-81b6-4f06-a1f2-29bb0be01f26',
        checkoutUrl: 'https://checkout.polar.sh/example'
      })
    })
  })

  it('displays benefits correctly', () => {
    render(<PricingTablePasses experimentVariant="2" />)

    expect(screen.getAllByText('Full APA 7 Compliance')).toHaveLength(3)
    expect(screen.getAllByText('Actionable error correction feedback')).toHaveLength(3)
    expect(screen.getAllByText('Risk-free with money-back guarantee')).toHaveLength(3)
  })

  it('displays fair use footer', () => {
    render(<PricingTablePasses experimentVariant="2" />)
    expect(screen.getByText(/Fair use: 1,000 citations per day/)).toBeInTheDocument()
  })

  // Tests for onCheckout prop (embedded checkout delegation to parent)
  describe('onCheckout prop (embedded checkout)', () => {
    it('calls onCheckout callback instead of internal checkout when provided', async () => {
      const mockOnCheckout = vi.fn()

      render(<PricingTablePasses onCheckout={mockOnCheckout} experimentVariant="2" />)

      const buyButton = screen.getByText('Buy 1-Day Pass')
      fireEvent.click(buyButton)

      await waitFor(() => {
        expect(mockOnCheckout).toHaveBeenCalledWith('1282bd9b-81b6-4f06-a1f2-29bb0be01f26')
      })

      // Verify internal fetch was NOT called (parent handles checkout)
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('shows loading state while onCheckout callback is pending', async () => {
      let resolveCheckout
      const checkoutPromise = new Promise(resolve => {
        resolveCheckout = resolve
      })
      const mockOnCheckout = vi.fn(() => checkoutPromise)

      render(<PricingTablePasses onCheckout={mockOnCheckout} experimentVariant="2" />)

      const buyButton = screen.getByText('Buy 1-Day Pass')
      fireEvent.click(buyButton)

      // Check for loading state
      expect(screen.getByText('Opening checkout...')).toBeInTheDocument()
      expect(buyButton).toBeDisabled()

      // Resolve the callback
      resolveCheckout()

      // Button should be back to normal after loading
      await waitFor(() => {
        expect(screen.queryByText('Opening checkout...')).not.toBeInTheDocument()
        expect(buyButton).not.toBeDisabled()
      })
    })

    it('shows error message when onCheckout callback throws', async () => {
      const mockOnCheckout = vi.fn(() => Promise.reject(new Error('Checkout failed')))

      render(<PricingTablePasses onCheckout={mockOnCheckout} experimentVariant="2" />)

      const buyButton = screen.getByText('Buy 1-Day Pass')
      fireEvent.click(buyButton)

      // Wait for error message to appear
      await waitFor(() => {
        expect(screen.getByText('Failed to open checkout. Please try again.')).toBeInTheDocument()
      })

      // Verify button is not disabled after error
      expect(buyButton).not.toBeDisabled()
    })

    it('passes correct productId for different pass tiers', async () => {
      const mockOnCheckout = vi.fn()

      render(<PricingTablePasses onCheckout={mockOnCheckout} experimentVariant="2" />)

      // Click 7-Day Pass
      const buy7DayButton = screen.getByText('Buy 7-Day Pass')
      fireEvent.click(buy7DayButton)

      await waitFor(() => {
        expect(mockOnCheckout).toHaveBeenCalledWith('5b311653-7127-41b5-aed6-496fb713149c')
      })
    })
  })
})
