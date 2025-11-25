import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ComingSoonModal } from './ComingSoonModal';

describe('ComingSoonModal', () => {
  const mockOnClose = vi.fn();
  const mockFile = new File(['x'.repeat(1024)], 'test-document.pdf', {
    type: 'application/pdf'
  });

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render modal with enhanced messaging when isOpen is true', () => {
    render(<ComingSoonModal isOpen={true} file={mockFile} onClose={mockOnClose} />);

    expect(screen.getByText(/File Upload Coming Soon/i)).toBeInTheDocument();
    expect(screen.getByText(/Great choice!/i)).toBeInTheDocument();
    expect(screen.getByText(/We detected your/i)).toBeInTheDocument();
    expect(screen.getByText(/saved it to help prioritize this feature./i)).toBeInTheDocument();
    expect(screen.getByText(/For now, you can paste the text from your document here:/i)).toBeInTheDocument();
  });

  it('should display file metadata correctly', () => {
    render(<ComingSoonModal isOpen={true} file={mockFile} onClose={mockOnClose} />);

    expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    expect(screen.getByText('1.0 KB')).toBeInTheDocument();
    // Use getAllByText since "PDF detected" appears in both messaging and file info
    expect(screen.getAllByText('PDF detected')).toHaveLength(2);
  });

  it('should track modal duration when closed', () => {
    const { unmount } = render(<ComingSoonModal isOpen={true} file={mockFile} onClose={mockOnClose} />);

    // Advance time by 5 seconds
    vi.advanceTimersByTime(5000);

    // Close modal by clicking close button
    const closeButton = screen.getByRole('button', { name: /close modal/i });
    fireEvent.click(closeButton);

    // Should track analytics event with duration
    expect(mockOnClose).toHaveBeenCalledWith({
      dismissMethod: 'close_button',
      duration: 5000
    });
  });

  it('should track dismiss method when backdrop is clicked', () => {
    render(<ComingSoonModal isOpen={true} file={mockFile} onClose={mockOnClose} />);

    // Click backdrop
    const backdrop = screen.getByTestId('modal-backdrop');
    fireEvent.click(backdrop);

    expect(mockOnClose).toHaveBeenCalledWith({
      dismissMethod: 'backdrop',
      duration: expect.any(Number)
    });
  });

  it('should track dismiss method when Escape key is pressed', () => {
    render(<ComingSoonModal isOpen={true} file={mockFile} onClose={mockOnClose} />);

    // Press Escape key
    fireEvent.keyDown(document, { key: 'Escape' });

    expect(mockOnClose).toHaveBeenCalledWith({
      dismissMethod: 'escape',
      duration: expect.any(Number)
    });
  });

  it('should not render when isOpen is false', () => {
    render(<ComingSoonModal isOpen={false} file={mockFile} onClose={mockOnClose} />);

    expect(screen.queryByText(/File Upload Coming Soon/i)).not.toBeInTheDocument();
  });

  it('should focus text input after modal close', () => {
    const textInputId = 'main-text-input';
    const mockTextInput = document.createElement('textarea');
    mockTextInput.id = textInputId;
    document.body.appendChild(mockTextInput);

    const { unmount } = render(<ComingSoonModal isOpen={true} file={mockFile} onClose={mockOnClose} />);

    // Close modal
    const closeButton = screen.getByRole('button', { name: /close modal/i });
    fireEvent.click(closeButton);

    // Should focus the text input
    expect(mockTextInput).toHaveFocus();

    // Cleanup
    document.body.removeChild(mockTextInput);
  });

  it('should handle different file types', () => {
    const docxFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });

    render(<ComingSoonModal isOpen={true} file={docxFile} onClose={mockOnClose} />);

    // Use getAllByText since "Document detected" appears in both messaging and file info
    expect(screen.getAllByText('Document detected')).toHaveLength(2);
  });

  it('should format file size correctly for different sizes', () => {
    const largeFile = new File(['x'.repeat(1024 * 1024)], 'large.pdf', {
      type: 'application/pdf',
      size: 1024 * 1024
    });

    render(<ComingSoonModal isOpen={true} file={largeFile} onClose={mockOnClose} />);

    expect(screen.getByText('1.0 MB')).toBeInTheDocument();
  });
});