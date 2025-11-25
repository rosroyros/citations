import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useFileProcessing } from './useFileProcessing';
import { trackEvent } from '../utils/analytics';

// Mock analytics
vi.mock('../utils/analytics', () => ({
  trackEvent: vi.fn(),
}));

describe('useFileProcessing - RED PHASE', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should process file for exactly 1.5 seconds with progress tracking', async () => {
    // Arrange - Create a test file
    const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    // Act - Start processing
    const { result } = renderHook(() => useFileProcessing());

    act(() => {
      result.current.processFile(testFile);
    });

    // Assert - Initial state should show processing started
    expect(result.current.isProcessing).toBe(true);
    expect(result.current.progress).toBe(0);
    expect(trackEvent).toHaveBeenCalledWith('upload_processing_shown', expect.objectContaining({
      file_type: 'application/pdf',
      file_size: testFile.size
    }));

    // Assert - Progress should update during processing
    act(() => {
      vi.advanceTimersByTime(750); // Halfway through 1.5s
    });

    expect(result.current.progress).toBeGreaterThan(0);
    expect(result.current.progress).toBeLessThan(100);

    // Assert - Processing should complete after exactly 1.5s
    act(() => {
      vi.advanceTimersByTime(750); // Complete the 1.5s
    });

    expect(result.current.isProcessing).toBe(false);
    expect(result.current.progress).toBe(100);
    expect(trackEvent).toHaveBeenCalledWith('upload_file_preview_rendered', expect.objectContaining({
      processing_time_ms: 1500,
      file_type: 'application/pdf',
      file_size: testFile.size
    }));
  });

  it('should extract and return file metadata after processing', async () => {
    // Arrange
    const testFile = new File(['test content'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });

    // Act
    const { result } = renderHook(() => useFileProcessing());

    act(() => {
      result.current.processFile(testFile);
    });

    // Complete processing
    act(() => {
      vi.advanceTimersByTime(1500);
    });

    // Assert - check that basic metadata is present and content is included
    const processedFile = result.current.processedFile;
    expect(processedFile).toMatchObject({
      file: testFile,
      name: 'test.docx',
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      size: testFile.size,
      lastModified: testFile.lastModified
    });
    expect(processedFile).toHaveProperty('content');
  });

  it('should extract file content using FileReader API', async () => {
    // Arrange - Mock FileReader
    const mockFileReader = {
      readAsText: vi.fn(),
      readAsDataURL: vi.fn(),
      readAsArrayBuffer: vi.fn(),
      result: 'test file content',
      onload: null,
      onerror: null,
    };

    global.FileReader = vi.fn(() => mockFileReader);

    const testFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

    // Act
    const { result } = renderHook(() => useFileProcessing());

    act(() => {
      result.current.processFile(testFile);
    });

    // Simulate FileReader completion
    act(() => {
      if (typeof mockFileReader.onload === 'function') {
        mockFileReader.onload({ target: { result: 'test file content' } });
      }
      vi.advanceTimersByTime(1500);
    });

    // Assert
    expect(mockFileReader.readAsText).toHaveBeenCalledWith(testFile);
    expect(result.current.processedFile.content).toBe('test file content');
  });

  it('should handle FileReader errors gracefully', async () => {
    // Arrange - Mock FileReader with error
    const mockFileReader = {
      readAsText: vi.fn(),
      readAsDataURL: vi.fn(),
      readAsArrayBuffer: vi.fn(),
      result: null,
      onload: null,
      onerror: null,
    };

    global.FileReader = vi.fn(() => mockFileReader);

    const testFile = new File(['test content'], 'test.txt', { type: 'text/plain' });

    // Act
    const { result } = renderHook(() => useFileProcessing());

    act(() => {
      result.current.processFile(testFile);
    });

    // Simulate FileReader error
    act(() => {
      if (typeof mockFileReader.onerror === 'function') {
        mockFileReader.onerror();
      }
      vi.advanceTimersByTime(1500);
    });

    // Assert - should still complete processing but without content
    expect(result.current.isProcessing).toBe(false);
    expect(result.current.processedFile).toMatchObject({
      name: 'test.txt',
      type: 'text/plain',
      size: testFile.size,
      lastModified: testFile.lastModified
    });
    expect(result.current.processedFile.content).toBeUndefined();
  });

  it('should handle null/undefined file input', async () => {
    // Act
    const { result } = renderHook(() => useFileProcessing());

    // Should not throw error
    act(() => {
      result.current.processFile(null);
    });

    act(() => {
      vi.advanceTimersByTime(1500);
    });

    // Assert - should remain in non-processing state
    expect(result.current.isProcessing).toBe(false);
    expect(result.current.processedFile).toBeNull();
  });

  it('should handle empty file', async () => {
    // Arrange
    const emptyFile = new File([], 'empty.txt', { type: 'text/plain' });

    // Act
    const { result } = renderHook(() => useFileProcessing());

    act(() => {
      result.current.processFile(emptyFile);
    });

    act(() => {
      vi.advanceTimersByTime(1500);
    });

    // Assert - should complete successfully even with empty file
    expect(result.current.isProcessing).toBe(false);
    expect(result.current.processedFile).toMatchObject({
      name: 'empty.txt',
      type: 'text/plain',
      size: 0
    });
  });

  it('should reset properly', async () => {
    // Arrange
    const testFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const { result } = renderHook(() => useFileProcessing());

    // Act - Start processing
    act(() => {
      result.current.processFile(testFile);
    });

    expect(result.current.isProcessing).toBe(true);

    // Advance time to get some progress
    act(() => {
      vi.advanceTimersByTime(100);
    });

    // Reset
    act(() => {
      result.current.reset();
    });

    // Assert
    expect(result.current.isProcessing).toBe(false);
    expect(result.current.progress).toBe(0);
    expect(result.current.processedFile).toBeNull();
  });
});