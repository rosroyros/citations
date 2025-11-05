import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UpgradeModal } from './UpgradeModal';
import { getToken } from '../utils/creditStorage.js';

// Mock the getToken function
vi.mock('../utils/creditStorage.js', () => ({
  getToken: vi.fn(),
}));

// Mock window.location.href
delete window.location;
window.location = { href: '' };

describe('UpgradeModal', () => {
  let mockGetToken;

  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken = vi.fn();
    window.location.href = '';
  });

  it('should not render when isOpen is false', () => {
    // Arrange
    mockGetToken.mockReturnValue('test-token');
    vi.mocked(getToken).mockImplementation(mockGetToken);

    // Act
    const { container } = render(<UpgradeModal isOpen={false} onClose={() => {}} />);

    // Assert
    expect(container.firstChild).toBeNull();
  });

  it('should render modal when isOpen is true', () => {
    // Arrange
    mockGetToken.mockReturnValue('test-token');
    vi.mocked(getToken).mockImplementation(mockGetToken);

    // Act
    render(<UpgradeModal isOpen={true} onClose={() => {}} />);

    // Assert
    expect(screen.getByText('Get 1,000 Citation Credits')).toBeInTheDocument();
    expect(screen.getByText('$8.99')).toBeInTheDocument();
    expect(screen.getByText('Credits never expire')).toBeInTheDocument();
    expect(screen.getByText('Continue to Checkout')).toBeInTheDocument();
  });

  it('should display all benefits', () => {
    // Arrange
    mockGetToken.mockReturnValue('test-token');
    vi.mocked(getToken).mockImplementation(mockGetToken);

    // Act
    render(<UpgradeModal isOpen={true} onClose={() => {}} />);

    // Assert
    expect(screen.getByText('Check citations for 50+ research papers')).toBeInTheDocument();
    expect(screen.getByText('Credits never expire - use anytime')).toBeInTheDocument();
    expect(screen.getByText('Risk-free with money-back guarantee')).toBeInTheDocument();

    // Also check for checkmarks
    const checkmarks = screen.getAllByText('✓');
    expect(checkmarks).toHaveLength(3);
  });

  it('should call onClose when close button is clicked', () => {
    // Arrange
    mockGetToken.mockReturnValue('test-token');
    vi.mocked(getToken).mockImplementation(mockGetToken);
    const mockOnClose = vi.fn();

    // Act
    render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    // Assert
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should call checkout API when Continue to Checkout is clicked', async () => {
    // Arrange
    mockGetToken.mockReturnValue('test-token');
    vi.mocked(getToken).mockImplementation(mockGetToken);

    const mockResponse = { checkout_url: 'https://polar.sh/checkout/123' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const mockOnClose = vi.fn();

    // Act
    render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);
    const checkoutButton = screen.getByText('Continue to Checkout');
    fireEvent.click(checkoutButton);

    // Assert - loading state
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    expect(checkoutButton).toBeDisabled();

    // Assert - API call
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: 'test-token' }),
      });
    });

    // Assert - redirect
    await waitFor(() => {
      expect(window.location.href).toBe('https://polar.sh/checkout/123');
    });
  });

  it('should show error message when checkout API fails', async () => {
    // Arrange
    mockGetToken.mockReturnValue('test-token');
    vi.mocked(getToken).mockImplementation(mockGetToken);

    const errorMessage = 'Checkout failed';
    global.fetch = vi.fn().mockRejectedValue(new Error(errorMessage));

    // Act
    render(<UpgradeModal isOpen={true} onClose={() => {}} />);
    const checkoutButton = screen.getByText('Continue to Checkout');
    fireEvent.click(checkoutButton);

    // Assert - error message appears
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    // Assert - button is re-enabled
    await waitFor(() => {
      expect(checkoutButton).not.toBeDisabled();
      expect(screen.getByText('Continue to Checkout')).toBeInTheDocument();
    });
  });

  it('should show loading state during API call', async () => {
    // Arrange
    mockGetToken.mockReturnValue('test-token');
    vi.mocked(getToken).mockImplementation(mockGetToken);

    let resolvePromise;
    global.fetch = vi.fn().mockImplementation(() => new Promise(resolve => {
      resolvePromise = resolve;
    }));

    // Act
    render(<UpgradeModal isOpen={true} onClose={() => {}} />);
    const checkoutButton = screen.getByText('Continue to Checkout');
    fireEvent.click(checkoutButton);

    // Assert - loading state
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    expect(checkoutButton).toBeDisabled();

    // Resolve the promise
    resolvePromise({
      ok: true,
      json: () => Promise.resolve({ checkout_url: 'https://example.com' })
    });

    // Assert - loading state cleared
    await waitFor(() => {
      expect(screen.queryByText('Processing...')).not.toBeInTheDocument();
    });
  });

  it('should call onClose when overlay is clicked', () => {
    // Arrange
    mockGetToken.mockReturnValue('test-token');
    vi.mocked(getToken).mockImplementation(mockGetToken);
    const mockOnClose = vi.fn();

    // Act
    render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);
    const overlay = screen.getByTestId('modal-overlay');
    fireEvent.click(overlay);

    // Assert
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should not call onClose when modal content is clicked', () => {
    // Arrange
    mockGetToken.mockReturnValue('test-token');
    vi.mocked(getToken).mockImplementation(mockGetToken);
    const mockOnClose = vi.fn();

    // Act
    render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);
    const modalContent = screen.getByTestId('modal-content');
    fireEvent.click(modalContent);

    // Assert
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('should handle missing token gracefully', async () => {
    // Arrange
    mockGetToken.mockReturnValue(null);
    vi.mocked(getToken).mockImplementation(mockGetToken);

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ checkout_url: 'https://polar.sh/checkout/123' }),
    });

    // Act
    render(<UpgradeModal isOpen={true} onClose={() => {}} />);
    const checkoutButton = screen.getByText('Continue to Checkout');
    fireEvent.click(checkoutButton);

    // Assert - should still call API with null token
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: null }),
      });
    });
  });
});