import { useState, useRef, useCallback } from 'react';
import { trackEvent } from '../utils/analytics';

// Constants for file processing
const PROCESSING_DURATION_MS = 1500; // 1.5 seconds
const PROGRESS_UPDATE_INTERVAL_MS = 50; // Update every 50ms for smooth animation

export const useFileProcessing = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [processedFile, setProcessedFile] = useState(null);
  const processingStartTime = useRef(null);
  const progressInterval = useRef(null);
  const fileReader = useRef(null);
  const fileContent = useRef(null);

  const processFile = useCallback((file) => {
    if (!file) {
      console.error('No file provided to processFile');
      // Don't start processing if no file
      return;
    }

    // Validate file object
    if (!(file instanceof File)) {
      console.error('Invalid file object provided');
      return;
    }

    // Start processing
    setIsProcessing(true);
    setProgress(0);
    setProcessedFile(null);
    processingStartTime.current = Date.now();
    fileContent.current = null;

    // Track processing started
    trackEvent('upload_processing_shown', {
      file_type: file.type || 'unknown',
      file_size: file.size || 0,
    });

    // Start file content extraction using FileReader
    fileReader.current = new FileReader();

    fileReader.current.onload = (event) => {
      fileContent.current = event.target.result;
    };

    fileReader.current.onerror = () => {
      console.error('Error reading file:', fileReader.current.error);
      fileContent.current = null;
    };

    // Choose appropriate reading method based on file type
    const fileType = file.type || '';
    if (fileType.startsWith('text/')) {
      fileReader.current.readAsText(file);
    } else if (fileType.startsWith('image/')) {
      fileReader.current.readAsDataURL(file);
    } else {
      // For binary files, read as array buffer
      fileReader.current.readAsArrayBuffer(file);
    }

    // Set up progress animation over 1.5 seconds
    const totalSteps = PROCESSING_DURATION_MS / PROGRESS_UPDATE_INTERVAL_MS;
    const progressIncrement = 100 / totalSteps;
    let currentStep = 0;

    progressInterval.current = setInterval(() => {
      currentStep++;
      const newProgress = Math.min(currentStep * progressIncrement, 100);
      setProgress(newProgress);

      if (newProgress >= 100) {
        clearInterval(progressInterval.current);
        completeProcessing(file);
      }
    }, PROGRESS_UPDATE_INTERVAL_MS);
  }, []);

  const completeProcessing = useCallback((file) => {
    const processingTime = Date.now() - processingStartTime.current;

    // Track file preview rendered
    trackEvent('upload_file_preview_rendered', {
      processing_time_ms: processingTime,
      file_type: file.type,
      file_size: file.size,
    });

    // Set processed file metadata with content
    const processedFileData = {
      file,
      name: file.name,
      type: file.type,
      size: file.size,
      lastModified: file.lastModified,
    };

    // Add content if successfully extracted
    if (fileContent.current !== null) {
      processedFileData.content = fileContent.current;
    }

    setProcessedFile(processedFileData);

    // Complete processing
    setIsProcessing(false);
    setProgress(100);
  }, []);

  const reset = useCallback(() => {
    if (progressInterval.current) {
      clearInterval(progressInterval.current);
    }
    if (fileReader.current &&
        fileReader.current.readyState !== undefined &&
        fileReader.current.readyState !== FileReader.DONE) {
      fileReader.current.abort();
    }
    setIsProcessing(false);
    setProgress(0);
    setProcessedFile(null);
    processingStartTime.current = null;
    fileContent.current = null;
    fileReader.current = null;
  }, []);

  return {
    isProcessing,
    progress,
    processedFile,
    processFile,
    reset,
  };
};