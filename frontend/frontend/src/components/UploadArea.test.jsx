import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UploadArea } from './UploadArea';
import { MAX_FILE_SIZE } from '../constants/fileValidation.js';

describe('UploadArea', () => {
  const mockOnFileSelected = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render upload area with correct text', () => {
    render(<UploadArea onFileSelected={mockOnFileSelected} />);

    expect(screen.getByText(/drop your document here/i)).toBeInTheDocument();
    expect(screen.getByText(/or click to browse/i)).toBeInTheDocument();
  });

  it('should handle file selection via click', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    render(<UploadArea onFileSelected={mockOnFileSelected} />);

    const fileInput = screen.getByLabelText(/Choose File/i);
    await userEvent.upload(fileInput, file);

    expect(mockOnFileSelected).toHaveBeenCalledWith(file);
  });

  it('should validate file types via programmatic file selection', () => {
    const invalidFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' });

    render(<UploadArea onFileSelected={mockOnFileSelected} />);

    // Simulate direct file validation by calling the component's internal logic
    const uploadArea = screen.getByTestId('upload-area');

    // Test via drag drop to bypass file input filtering
    fireEvent.drop(uploadArea, {
      dataTransfer: {
        files: [invalidFile],
      },
    });

    expect(mockOnFileSelected).not.toHaveBeenCalled();
    expect(screen.getByText(/please select a valid file type/i)).toBeInTheDocument();
  });

  it('should validate file size', () => {
    const largeFile = new File(['x'.repeat(MAX_FILE_SIZE + 1024)], 'large.pdf', { type: 'application/pdf' });

    render(<UploadArea onFileSelected={mockOnFileSelected} />);

    const uploadArea = screen.getByTestId('upload-area');

    fireEvent.drop(uploadArea, {
      dataTransfer: {
        files: [largeFile],
      },
    });

    expect(mockOnFileSelected).not.toHaveBeenCalled();
    expect(screen.getByText(/file size must be less than 10mb/i)).toBeInTheDocument();
  });

  it('should show drag state when file is dragged over', () => {
    render(<UploadArea onFileSelected={mockOnFileSelected} />);

    const uploadArea = screen.getByTestId('upload-area');

    // Check that dragOver class is applied (CSS modules use different naming)
    fireEvent.dragEnter(uploadArea);
    expect(uploadArea.className).toContain('dragOver');

    fireEvent.dragLeave(uploadArea);
    expect(uploadArea.className).not.toContain('dragOver');
  });

  it('should handle file drop', () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    render(<UploadArea onFileSelected={mockOnFileSelected} />);

    const uploadArea = screen.getByTestId('upload-area');

    fireEvent.drop(uploadArea, {
      dataTransfer: {
        files: [file],
      },
    });

    expect(mockOnFileSelected).toHaveBeenCalledWith(file);
  });
});