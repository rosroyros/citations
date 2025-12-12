import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { PricingTableCredits } from './PricingTableCredits'

// Mock fetch to control API calls
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

describe('PricingTableCredits', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    mockConsoleLog.mockClear()
    window.location.href = ''
  })

  it('renders all 3 pricing tiers', () => {
    render(<PricingTableCredits experimentVariant="1" />)

    // Check for all three credit amounts
    expect(screen.getByText('100 Credits')).toBeInTheDocument()
    expect(screen.getByText('500 Credits')).toBeInTheDocument()
    expect(screen.getByText('2,000 Credits')).toBeInTheDocument()
  })

  it('displays correct pricing for each tier', () => {
    render(<PricingTableCredits experimentVariant="1" />)

    // Check prices
    expect(screen.getByText('$1.99')).toBeInTheDocument()
    expect(screen.getByText('$4.99')).toBeInTheDocument()
    expect(screen.getByText('$9.99')).toBeInTheDocument()
  })

  it('shows "Best Value" badge only on 500 credit tier', () => {
    render(<PricingTableCredits experimentVariant="1" />)

    const badges = screen.getAllByText('Best Value')
    expect(badges).toHaveLength(1) // Only one badge should exist
  })

  it('displays price per citation correctly', () => {
    render(<PricingTableCredits experimentVariant="1" />)

    expect(screen.getByText('$0.020 per citation')).toBeInTheDocument()
    expect(screen.getByText('$0.010 per citation')).toBeInTheDocument()
    expect(screen.getByText('$0.005 per citation')).toBeInTheDocument()
  })

  it('calls checkout API and redirects when Buy button is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ checkout_url: 'https://checkout.polar.sh/example' })
    })

    render(<PricingTableCredits experimentVariant="1" />)

    // Find and click the 100 credits button
    const buy100Button = screen.getByText('Buy 100 Credits')
    fireEvent.click(buy100Button)

    // Wait for the API call to complete
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productId: '817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e',
          variantId: '1'
        })
      })
    })

    // Verify redirect happened
    await waitFor(() => {
      expect(window.location.href).toBe('https://checkout.polar.sh/example')
    })
  })

  it('calls checkout API for 500 credits button', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ checkout_url: 'https://checkout.polar.sh/example' })
    })

    render(<PricingTableCredits experimentVariant="1" />)

    const buy500Button = screen.getByText('Buy 500 Credits')
    fireEvent.click(buy500Button)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productId: '2a3c8913-2e82-4f12-9eb7-767e4bc98089',
          variantId: '1'
        })
      })
    })
  })

  it('shows loading state while checkout is being created', async () => {
    // Create a promise that we can control
    let resolveFetch: (value: any) => void
    const fetchPromise = new Promise(resolve => {
      resolveFetch = resolve
    })
    mockFetch.mockReturnValueOnce(fetchPromise)

    render(<PricingTableCredits experimentVariant="1" />)

    const buy100Button = screen.getByText('Buy 100 Credits')
    fireEvent.click(buy100Button)

    // Check for loading state
    expect(screen.getByText('Opening checkout...')).toBeInTheDocument()
    expect(buy100Button).toBeDisabled()

    // Resolve the fetch promise
    resolveFetch({
      ok: true,
      json: async () => ({ checkout_url: 'https://checkout.polar.sh/example' })
    })

    // Button should be back to normal after loading
    await waitFor(() => {
      expect(screen.queryByText('Opening checkout...')).not.toBeInTheDocument()
      expect(buy100Button).not.toBeDisabled()
    })
  })

  it('shows error message when checkout creation fails', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500
    })

    render(<PricingTableCredits experimentVariant="1" />)

    const buy100Button = screen.getByText('Buy 100 Credits')
    fireEvent.click(buy100Button)

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText('Failed to open checkout. Please try again.')).toBeInTheDocument()
    })

    // Verify button is not disabled after error
    expect(buy100Button).not.toBeDisabled()
  })

  it('logs analytics events', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ checkout_url: 'https://checkout.polar.sh/example' })
    })

    render(<PricingTableCredits experimentVariant="2" />)

    // Check initial pricing table log
    expect(mockConsoleLog).toHaveBeenCalledWith('pricing_table_shown', { variant: '2' })

    const buy100Button = screen.getByText('Buy 100 Credits')
    fireEvent.click(buy100Button)

    await waitFor(() => {
      // Check product selection log
      expect(mockConsoleLog).toHaveBeenCalledWith('product_selected', {
        productId: '817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e',
        variant: '2'
      })

      // Check checkout started log
      expect(mockConsoleLog).toHaveBeenCalledWith('checkout_started', {
        productId: '817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e',
        checkoutUrl: 'https://checkout.polar.sh/example'
      })
    })
  })

  it('displays all benefit items with checkmarks', () => {
    render(<PricingTableCredits experimentVariant="1" />)

    // Check some key benefits
    expect(screen.getByText('100 citation validations')).toBeInTheDocument()
    expect(screen.getByText('Best value ($0.01/citation)')).toBeInTheDocument()
    expect(screen.getByText('2,000 citation validations')).toBeInTheDocument()
    expect(screen.getByText('Credits never expire')).toBeInTheDocument()
  })

  it('uses default variant when experimentVariant not provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ checkout_url: 'https://checkout.polar.sh/example' })
    })

    render(<PricingTableCredits />)

    // Check initial pricing table log with default variant
    expect(mockConsoleLog).toHaveBeenCalledWith('pricing_table_shown', { variant: '1' })

    const buy100Button = screen.getByText('Buy 100 Credits')
    fireEvent.click(buy100Button)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productId: '817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e',
          variantId: '1'
        })
      })
    })
  })
})