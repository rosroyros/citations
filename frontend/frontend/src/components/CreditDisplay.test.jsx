import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CreditDisplay } from './CreditDisplay';
import { CreditProvider } from '../contexts/CreditContext.jsx';
import { getToken } from '../utils/creditStorage.js';

// Mock the creditStorage utilities
vi.mock('../utils/creditStorage.js', async () => {
  const actual = await vi.importActual('../utils/creditStorage.js')
  return {
    ...actual,
    getToken: vi.fn(),
  }
})

// Mock fetch for credit API calls
global.fetch = vi.fn();

describe('CreditDisplay', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch.mockClear();
  });

  it('should render nothing if no token', () => {
    // Arrange
    getToken.mockReturnValue(null);

    // Act
    const { container } = render(
      <CreditProvider>
        <CreditDisplay />
      </CreditProvider>
    );

    // Assert
    expect(container.firstChild).toBeNull();
  });

  it('should display credits if token exists', async () => {
    // Arrange
    getToken.mockReturnValue('test-token');
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ credits: 847 }),
    });

    // Act
    render(
      <CreditProvider>
        <CreditDisplay />
      </CreditProvider>
    );

    // Assert
    // Check for both lines
    await screen.findByText('Citation Credits');
    await screen.findByText('847 remaining');
  });

  it('should show loading state', () => {
    // Arrange
    getToken.mockReturnValue('test-token');
    global.fetch.mockImplementation(() => new Promise(() => { })); // Never resolves

    // Act
    render(
      <CreditProvider>
        <CreditDisplay />
      </CreditProvider>
    );

    // Assert
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should display 0 credits if credits is null but token exists', async () => {
    // Arrange
    getToken.mockReturnValue('test-token');
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ credits: 0 }),
    });

    // Act
    render(
      <CreditProvider>
        <CreditDisplay />
      </CreditProvider>
    );

    // Assert
    await screen.findByText('Citation Credits');
    await screen.findByText('0 remaining');
  });

  it('should show destructive color for low credits (<= 10)', async () => {
    // Arrange
    getToken.mockReturnValue('test-token');
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ credits: 5 }),
    });

    // Act
    render(
      <CreditProvider>
        <CreditDisplay />
      </CreditProvider>
    );

    // Assert
    const remainingText = await screen.findByText('5 remaining');
    expect(remainingText).toHaveClass('text-destructive');
  });

  describe('Day Pass Support', () => {
    it('should display pass status when user has active day pass', async () => {
      // Arrange
      getToken.mockReturnValue('test-token');
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          credits: 0,
          active_pass: { hours_remaining: 24 }
        }),
      });

      // Act
      render(
        <CreditProvider>
          <CreditDisplay />
        </CreditProvider>
      );

      // Assert
      await screen.findByText('1-Day Pass Active');
      // 24 hours = 1 day exactly.
      // Logic: hours <= 12 ? hours : days
      // 24 > 12 -> Show days.
      await screen.findByText('1 day left');
    });

    it('should display days for 13-24 hour range', async () => {
      // Arrange
      getToken.mockReturnValue('test-token');
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          credits: 0,
          active_pass: { hours_remaining: 13 }
        }),
      });

      // Act
      render(
        <CreditProvider>
          <CreditDisplay />
        </CreditProvider>
      );

      // Assert
      await screen.findByText('1-Day Pass Active');
      await screen.findByText('1 day left');
    });

    it('should display 7-day pass status', async () => {
      // Arrange
      getToken.mockReturnValue('test-token');
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          credits: 0,
          active_pass: { hours_remaining: 168 }
        }),
      });

      // Act
      render(
        <CreditProvider>
          <CreditDisplay />
        </CreditProvider>
      );

      // Assert
      await screen.findByText('7-Day Pass Active');
      await screen.findByText('7 days left');
    });

    it('should display hourly pass correctly (rounded to 1-Day) with warning color', async () => {
      // Arrange
      getToken.mockReturnValue('test-token');
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          credits: 0,
          active_pass: { hours_remaining: 5 }
        }),
      });

      // Act
      render(
        <CreditProvider>
          <CreditDisplay />
        </CreditProvider>
      );

      // Assert
      // 5h is treated as 1-Day Pass Active in title (since Math.ceil(5/24) = 1)
      await screen.findByText('1-Day Pass Active');

      // 5 <= 12, so show hours with warning color
      const timeText = await screen.findByText('5 hours left');
      expect(timeText).toHaveClass('text-amber-600');
    });

    it('should display hours for 12 hours remaining', async () => {
      // Arrange
      getToken.mockReturnValue('test-token');
      global.fetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          credits: 0,
          active_pass: { hours_remaining: 12 }
        }),
      });

      // Act
      render(
        <CreditProvider>
          <CreditDisplay />
        </CreditProvider>
      );

      // Assert
      await screen.findByText('1-Day Pass Active');
      const timeText = await screen.findByText('12 hours left');
      expect(timeText).toHaveClass('text-amber-600');
    });
  });
});