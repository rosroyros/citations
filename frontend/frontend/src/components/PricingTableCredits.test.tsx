import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { PricingTableCredits } from './PricingTableCredits'

describe('PricingTableCredits', () => {
  const mockOnSelectProduct = vi.fn()

  beforeEach(() => {
    mockOnSelectProduct.mockClear()
  })

  it('renders all 3 pricing tiers', () => {
    render(<PricingTableCredits onSelectProduct={mockOnSelectProduct} experimentVariant="1" />)

    // Check for all three credit amounts
    expect(screen.getByText('100 Credits')).toBeInTheDocument()
    expect(screen.getByText('500 Credits')).toBeInTheDocument()
    expect(screen.getByText('2,000 Credits')).toBeInTheDocument()
  })

  it('displays correct pricing for each tier', () => {
    render(<PricingTableCredits onSelectProduct={mockOnSelectProduct} experimentVariant="1" />)

    // Check prices
    expect(screen.getByText('$1.99')).toBeInTheDocument()
    expect(screen.getByText('$4.99')).toBeInTheDocument()
    expect(screen.getByText('$9.99')).toBeInTheDocument()
  })

  it('shows "Best Value" badge only on 500 credit tier', () => {
    render(<PricingTableCredits onSelectProduct={mockOnSelectProduct} experimentVariant="1" />)

    const badges = screen.getAllByText('Best Value')
    expect(badges).toHaveLength(1) // Only one badge should exist
  })

  it('displays price per citation correctly', () => {
    render(<PricingTableCredits onSelectProduct={mockOnSelectProduct} experimentVariant="1" />)

    expect(screen.getByText('$0.020 per citation')).toBeInTheDocument()
    expect(screen.getByText('$0.010 per citation')).toBeInTheDocument()
    expect(screen.getByText('$0.005 per citation')).toBeInTheDocument()
  })

  it('calls onSelectProduct with correct parameters when Buy button is clicked', () => {
    render(<PricingTableCredits onSelectProduct={mockOnSelectProduct} experimentVariant="1" />)

    // Find and click the 100 credits button
    const buy100Button = screen.getByText('Buy 100 Credits')
    fireEvent.click(buy100Button)

    expect(mockOnSelectProduct).toHaveBeenCalledWith('817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e', '1')
  })

  it('calls onSelectProduct for 500 credits button', () => {
    render(<PricingTableCredits onSelectProduct={mockOnSelectProduct} experimentVariant="1" />)

    const buy500Button = screen.getByText('Buy 500 Credits')
    fireEvent.click(buy500Button)

    expect(mockOnSelectProduct).toHaveBeenCalledWith('2a3c8913-2e82-4f12-9eb7-767e4bc98089', '1')
  })

  it('calls onSelectProduct for 2000 credits button', () => {
    render(<PricingTableCredits onSelectProduct={mockOnSelectProduct} experimentVariant="1" />)

    const buy2000Button = screen.getByRole('button', { name: 'Buy 2,000 Credits' })
    fireEvent.click(buy2000Button)

    expect(mockOnSelectProduct).toHaveBeenCalledWith('fe7b0260-e411-4f9a-87c8-0856bf1d8b95', '1')
  })

  it('displays all benefit items with checkmarks', () => {
    render(<PricingTableCredits onSelectProduct={mockOnSelectProduct} experimentVariant="1" />)

    // Check some key benefits
    expect(screen.getByText('100 citation validations')).toBeInTheDocument()
    expect(screen.getByText('Best value ($0.01/citation)')).toBeInTheDocument()
    expect(screen.getByText('2,000 citation validations')).toBeInTheDocument()
    expect(screen.getByText('Credits never expire')).toBeInTheDocument()
  })

  it('uses default variant when experimentVariant not provided', () => {
    render(<PricingTableCredits onSelectProduct={mockOnSelectProduct} />)

    const buy100Button = screen.getByText('Buy 100 Credits')
    fireEvent.click(buy100Button)

    expect(mockOnSelectProduct).toHaveBeenCalledWith('817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e', '1')
  })
})