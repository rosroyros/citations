import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UploadArea } from './UploadArea';
import { MAX_FILE_SIZE } from '../constants/fileValidation.js';

// Mock fetch globally
global.fetch = vi.fn();

describe('UploadArea', () => {
  const mockOnUploadStart = vi.fn();
  const mockOnUploadComplete = vi.fn();
  const mockOnUploadError = vi.fn();
  const defaultProps = {
    selectedStyle: 'apa7',
    onUploadStart: mockOnUploadStart,
    onUploadComplete: mockOnUploadComplete,
    onUploadError: mockOnUploadError
  };

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch.mockReset();
  });

  it('should render upload area with correct text', () => {
    render(<UploadArea {...defaultProps} />);

    expect(screen.getByText(/Drag and drop/i)).toBeInTheDocument();
    expect(screen.getByText(/or/i)).toBeInTheDocument();
    expect(screen.getByText(/browse files/i)).toBeInTheDocument();
  });

  it('should accept only .docx files via drag and drop', async () => {
    const docxFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });

    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ job_id: 'test-job-id' })
    });

    render(<UploadArea {...defaultProps} />);

    const uploadArea = screen.getByTestId('upload-area');
    fireEvent.drop(uploadArea, {
      dataTransfer: { files: [docxFile] }
    });

    // Check that uploading state appears
    await waitFor(() => {
      expect(screen.getByText(/Uploading your document/i)).toBeInTheDocument();
    });
    expect(mockOnUploadStart).toHaveBeenCalled();
  });

  it('should reject non-docx files via drag and drop', () => {
    const pdfFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    render(<UploadArea {...defaultProps} />);

    const uploadArea = screen.getByTestId('upload-area');
    fireEvent.drop(uploadArea, {
      dataTransfer: { files: [pdfFile] }
    });

    expect(mockOnUploadStart).not.toHaveBeenCalled();
    expect(screen.getByText(/Only .docx files are supported/i)).toBeInTheDocument();
  });

  it('should validate file size', () => {
    const largeFile = new File(['x'.repeat(MAX_FILE_SIZE + 1024)], 'large.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });

    render(<UploadArea {...defaultProps} />);

    const uploadArea = screen.getByTestId('upload-area');
    fireEvent.drop(uploadArea, {
      dataTransfer: { files: [largeFile] }
    });

    expect(mockOnUploadStart).not.toHaveBeenCalled();
    expect(screen.getByText(/File too large/i)).toBeInTheDocument();
  });

  it('should show drag state when file is dragged over', () => {
    render(<UploadArea {...defaultProps} />);

    const uploadArea = screen.getByTestId('upload-area');

    fireEvent.dragEnter(uploadArea);
    expect(uploadArea.className).toContain('dragOver');

    fireEvent.dragLeave(uploadArea);
    expect(uploadArea.className).not.toContain('dragOver');
  });

  it('should handle successful file upload', async () => {
    const docxFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });

    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ job_id: 'test-job-123' })
    });

    render(<UploadArea {...defaultProps} />);

    const uploadArea = screen.getByTestId('upload-area');
    fireEvent.drop(uploadArea, {
      dataTransfer: { files: [docxFile] }
    });

    await waitFor(() => {
      expect(mockOnUploadStart).toHaveBeenCalled();
      expect(mockOnUploadComplete).toHaveBeenCalledWith({ job_id: 'test-job-123' });
    });

    expect(global.fetch).toHaveBeenCalledWith('/api/validate/async', expect.objectContaining({
      method: 'POST',
      body: expect.any(FormData)
    }));
  });

  it('should handle upload error', async () => {
    const docxFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });

    global.fetch.mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Upload failed' })
    });

    render(<UploadArea {...defaultProps} />);

    const uploadArea = screen.getByTestId('upload-area');
    fireEvent.drop(uploadArea, {
      dataTransfer: { files: [docxFile] }
    });

    await waitFor(() => {
      expect(mockOnUploadError).toHaveBeenCalledWith('Upload failed');
    });

    expect(screen.getByText(/Upload failed/i)).toBeInTheDocument();
  });

  it('should show "try pasting" message for parse errors', async () => {
    const docxFile = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });

    global.fetch.mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Could not parse file' })
    });

    render(<UploadArea {...defaultProps} />);

    const uploadArea = screen.getByTestId('upload-area');
    fireEvent.drop(uploadArea, {
      dataTransfer: { files: [docxFile] }
    });

    await waitFor(() => {
      expect(screen.getByText(/Could not read file. Try pasting/i)).toBeInTheDocument();
    });
  });
});
