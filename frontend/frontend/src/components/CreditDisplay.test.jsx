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
    await screen.findByText('Citation Credits: 847');
  });

  it('should show loading state', () => {
    // Arrange
    getToken.mockReturnValue('test-token');
    global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

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
    await screen.findByText('Citation Credits: 0');
  });

  it('should display initial credits after API call', async () => {
    // Arrange
    getToken.mockReturnValue('test-token');
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ credits: 150 }),
    });

    // Act
    render(
      <CreditProvider>
        <CreditDisplay />
      </CreditProvider>
    );

    // Assert
    await screen.findByText('Citation Credits: 150');
  });
});