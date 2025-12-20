import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UpgradeModal } from './UpgradeModal';

// Create mock functions at module level
const mockRefreshCredits = vi.fn().mockResolvedValue(undefined);
const mockInitiateCheckout = vi.fn();

// Mock CreditContext at module level
vi.mock('../contexts/CreditContext', () => ({
  useCredits: () => ({
    credits: 100,
    hasCredits: true,
    creditsLoading: false,
    refreshCredits: mockRefreshCredits,
    decrementCredits: vi.fn(),
  }),
  CreditProvider: ({ children }) => children,
}));

// Mock checkoutFlow
vi.mock('../utils/checkoutFlow', () => ({
  initiateCheckout: (...args) => mockInitiateCheckout(...args),
}));

// Mock analytics
vi.mock('../utils/analytics', () => ({
  trackEvent: vi.fn(),
}));

// Mock experiment variant
vi.mock('../utils/experimentVariant', () => ({
  getExperimentVariant: vi.fn(() => '1.1'),
  getPricingType: vi.fn((variant) => variant?.startsWith('1') ? 'credits' : 'passes'),
}));

describe('UpgradeModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockInitiateCheckout.mockImplementation(async () => { });
    mockRefreshCredits.mockResolvedValue(undefined);
  });

  it('should not render when isOpen is false', () => {
    // Arrange & Act
    const { container } = render(
      <UpgradeModal isOpen={false} onClose={() => { }} limitType="free_limit" />
    );

    // Assert
    expect(container.firstChild).toBeNull();
  });

  it('should render modal when isOpen is true', async () => {
    // Arrange & Act
    render(
      <UpgradeModal isOpen={true} onClose={() => { }} limitType="free_limit" />
    );

    // Assert - should show the upgrade modal with title
    await waitFor(() => {
      expect(screen.getByText('Upgrade for More Access')).toBeInTheDocument();
    });
  });

  it('should call onClose when close button is clicked', async () => {
    // Arrange
    const mockOnClose = vi.fn();

    // Act
    render(
      <UpgradeModal isOpen={true} onClose={mockOnClose} limitType="free_limit" />
    );

    await waitFor(() => {
      expect(screen.getByTestId('close-modal')).toBeInTheDocument();
    });

    const closeButton = screen.getByTestId('close-modal');
    fireEvent.click(closeButton);

    // Assert
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should show success state when checkout completes', async () => {
    // Arrange - mock initiateCheckout to call onSuccess immediately
    mockInitiateCheckout.mockImplementation(async ({ onSuccess }) => {
      if (onSuccess) {
        await onSuccess();
      }
    });

    const mockOnClose = vi.fn();

    // Act
    render(
      <UpgradeModal isOpen={true} onClose={mockOnClose} limitType="free_limit" />
    );

    // Wait for the modal to render and find a Buy button
    await waitFor(() => {
      expect(screen.getByText('Upgrade for More Access')).toBeInTheDocument();
    });

    // Find and click a Buy button (from PricingTableCredits)
    const buyButtons = screen.getAllByRole('button', { name: /buy/i });
    expect(buyButtons.length).toBeGreaterThan(0);
    fireEvent.click(buyButtons[0]);

    // Assert - should show success state
    await waitFor(() => {
      expect(screen.getByTestId('checkout-success')).toBeInTheDocument();
      expect(screen.getByText('Payment Successful!')).toBeInTheDocument();
      expect(screen.getByTestId('continue-button')).toBeInTheDocument();
    });
  });

  it('should refresh credits on successful checkout', async () => {
    // Arrange - mock initiateCheckout to call onSuccess
    mockInitiateCheckout.mockImplementation(async ({ onSuccess }) => {
      if (onSuccess) {
        await onSuccess();
      }
    });

    // Act
    render(
      <UpgradeModal isOpen={true} onClose={() => { }} limitType="free_limit" />
    );

    await waitFor(() => {
      expect(screen.getByText('Upgrade for More Access')).toBeInTheDocument();
    });

    // Click Buy button
    const buyButtons = screen.getAllByRole('button', { name: /buy/i });
    expect(buyButtons.length).toBeGreaterThan(0);
    fireEvent.click(buyButtons[0]);

    // Assert - refreshCredits should be called
    await waitFor(() => {
      expect(mockRefreshCredits).toHaveBeenCalled();
    });
  });

  it('should close modal when Continue button is clicked after success', async () => {
    // Arrange
    mockInitiateCheckout.mockImplementation(async ({ onSuccess }) => {
      if (onSuccess) {
        await onSuccess();
      }
    });

    const mockOnClose = vi.fn();

    // Act
    render(
      <UpgradeModal isOpen={true} onClose={mockOnClose} limitType="free_limit" />
    );

    await waitFor(() => {
      expect(screen.getByText('Upgrade for More Access')).toBeInTheDocument();
    });

    // Click Buy button to trigger success
    const buyButtons = screen.getAllByRole('button', { name: /buy/i });
    expect(buyButtons.length).toBeGreaterThan(0);
    fireEvent.click(buyButtons[0]);

    // Wait for success state
    await waitFor(() => {
      expect(screen.getByTestId('continue-button')).toBeInTheDocument();
    });

    // Click Continue button
    fireEvent.click(screen.getByTestId('continue-button'));

    // Assert - onClose should be called
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should show error message when checkout fails', async () => {
    // Arrange - mock initiateCheckout to call onError
    const errorMessage = 'Checkout failed';
    mockInitiateCheckout.mockImplementation(async ({ onError }) => {
      if (onError) {
        onError(new Error(errorMessage));
      }
    });

    // Act
    render(
      <UpgradeModal isOpen={true} onClose={() => { }} limitType="free_limit" />
    );

    await waitFor(() => {
      expect(screen.getByText('Upgrade for More Access')).toBeInTheDocument();
    });

    // Click Buy button
    const buyButtons = screen.getAllByRole('button', { name: /buy/i });
    expect(buyButtons.length).toBeGreaterThan(0);
    fireEvent.click(buyButtons[0]);

    // Assert - error message should appear
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('should reset loading state when user closes checkout', async () => {
    // Arrange - mock initiateCheckout to call onClose
    mockInitiateCheckout.mockImplementation(async ({ onClose }) => {
      if (onClose) {
        onClose();
      }
    });

    // Act
    render(
      <UpgradeModal isOpen={true} onClose={() => { }} limitType="free_limit" />
    );

    await waitFor(() => {
      expect(screen.getByText('Upgrade for More Access')).toBeInTheDocument();
    });

    // Click Buy button
    const buyButtons = screen.getAllByRole('button', { name: /buy/i });
    expect(buyButtons.length).toBeGreaterThan(0);
    fireEvent.click(buyButtons[0]);

    // Assert - should still show pricing (not success state)
    await waitFor(() => {
      expect(screen.queryByTestId('checkout-success')).not.toBeInTheDocument();
      expect(screen.getByText('Upgrade for More Access')).toBeInTheDocument();
    });
  });

  it('should show daily limit message for daily_limit type', async () => {
    // Arrange
    const resetTimestamp = Date.now() + 3600000; // 1 hour from now

    // Act
    render(
      <UpgradeModal
        isOpen={true}
        onClose={() => { }}
        limitType="daily_limit"
        resetTimestamp={resetTimestamp}
      />
    );

    // Assert
    await waitFor(() => {
      expect(screen.getByText('Daily Limit Reached')).toBeInTheDocument();
    });
  });

  it('should show credits exhausted message for credits_exhausted type', async () => {
    // Act
    render(
      <UpgradeModal
        isOpen={true}
        onClose={() => { }}
        limitType="credits_exhausted"
      />
    );

    // Assert
    await waitFor(() => {
      expect(screen.getByText('Out of Credits')).toBeInTheDocument();
    });
  });

  it('should call onClose when overlay is clicked', async () => {
    // Arrange
    const mockOnClose = vi.fn();

    // Act
    render(
      <UpgradeModal isOpen={true} onClose={mockOnClose} limitType="free_limit" />
    );

    await waitFor(() => {
      expect(screen.getByText('Upgrade for More Access')).toBeInTheDocument();
    });

    // Click the overlay (the outer div)
    const overlay = document.querySelector('.upgrade-modal-overlay');
    expect(overlay).not.toBeNull();
    fireEvent.click(overlay);

    expect(mockOnClose).toHaveBeenCalled();
  });
});