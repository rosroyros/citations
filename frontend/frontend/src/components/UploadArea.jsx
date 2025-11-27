import React, { useState, useCallback } from 'react';
import styles from './UploadArea.module.css';
import { VALID_FILE_TYPES, MAX_FILE_SIZE, ACCEPTED_FILE_EXTENSIONS } from '../constants/fileValidation.js';
import { useFileProcessing } from '../hooks/useFileProcessing.js';

export const UploadArea = ({ onFileSelected }) => {
  const [dragState, setDragState] = useState(false);
  const [error, setError] = useState('');
  const { processFile, isProcessing, progress, processedFile, reset } = useFileProcessing();

  const validateFile = (file) => {
    if (!VALID_FILE_TYPES.includes(file.type)) {
      setError('Please select a valid file type (PDF, DOCX, TXT, or RTF)');
      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError('File size must be less than 10MB');
      return false;
    }

    setError('');
    return true;
  };

  const handleFileSelect = useCallback((file) => {
    if (validateFile(file)) {
      // Use the file processing hook
      processFile(file);
    }
  }, [processFile]);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragState(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragState(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragState(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleFileInputChange = useCallback((e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  // Call onFileSelected when processing completes (only once)
  const hasCalledOnFileSelected = React.useRef(false);

  React.useEffect(() => {
    if (processedFile && onFileSelected && !hasCalledOnFileSelected.current) {
      hasCalledOnFileSelected.current = true;
      onFileSelected(processedFile);
    }
  }, [processedFile, onFileSelected]);

  // Show processing state
  if (isProcessing) {
    return (
      <div
        data-testid="processing-indicator"
        className={`${styles.uploadArea} ${styles.processing}`}
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Processing file: ${Math.round(progress)}% complete`}
      >
        <div className={styles.content}>
          <div className={styles.icon}>⏳</div>
          <h3>Processing your document...</h3>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${progress}%` }}
            />
          </div>
          <p>{Math.round(progress)}% complete</p>
        </div>
      </div>
    );
  }

  // Show completed state - but indicate processing is unavailable
  if (processedFile) {
    return (
      <div
        data-testid="processing-complete"
        className={`${styles.uploadArea} ${styles.unavailable}`}
      >
        <div className={styles.content}>
          <p className={styles.fileName}>{processedFile.name}</p>
          <p className={styles.fileInfo}>
            {processedFile.type} • {(processedFile.size / 1024 / 1024).toFixed(2)} MB
          </p>
          <p className={styles.unavailableMessage}>
            Document processing is temporarily unavailable
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid="upload-area"
      className={`${styles.uploadArea} ${dragState ? styles.dragOver : ''}`}
      onDragEnter={handleDragEnter}
      onDragOver={(e) => e.preventDefault()}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      aria-label={dragState ? "File drop zone - active" : "File drop zone"}
      aria-describedby={error ? "error-message" : undefined}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          document.getElementById('file-input')?.click();
        }
      }}
    >
      <div className={styles.content}>
        <div className={styles.icon}>📄</div>
        <p className={styles.mainText}>Drag and drop</p>
        <p className={styles.orText}>or <label htmlFor="file-input" role="button" tabIndex={-1}>browse files</label></p>
        <input
          type="file"
          accept={ACCEPTED_FILE_EXTENSIONS}
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
          id="file-input"
        />
        <p className={styles.fileTypes}>PDF, DOCX, TXT, or RTF files accepted</p>
        {error && <div id="error-message" className={styles.error}>{error}</div>}
      </div>
    </div>
  );
};