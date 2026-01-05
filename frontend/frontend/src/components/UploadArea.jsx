import React, { useState, useCallback } from 'react';
import styles from './UploadArea.module.css';
import { MAX_FILE_SIZE } from '../constants/fileValidation.js';

// DOCX MIME type
const DOCX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

export const UploadArea = ({ selectedStyle, onUploadStart, onUploadComplete, onUploadError }) => {
  const [dragState, setDragState] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  const validateFile = (file) => {
    // Check file extension
    if (!file.name.toLowerCase().endsWith('.docx')) {
      setError('Only .docx files are supported. Please upload a Word document.');
      return false;
    }

    // Check MIME type
    if (file.type !== DOCX_MIME_TYPE) {
      setError('Invalid file format. Please upload a .docx Word document.');
      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError('File too large. Maximum size is 10MB.');
      return false;
    }

    setError('');
    return true;
  };

  const handleFileSelect = useCallback(async (file) => {
    if (!validateFile(file)) {
      return;
    }

    setIsUploading(true);
    setError('');
    onUploadStart?.();

    try {
      // Create multipart form data
      const formData = new FormData();
      formData.append('file', file);
      formData.append('style', selectedStyle || 'apa7');

      // Send to backend
      const response = await fetch('/api/validate/async', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      onUploadComplete?.(data);
    } catch (err) {
      // Provide helpful error message
      const errorMessage = err.message || 'Upload failed. Please try again.';
      if (errorMessage.includes('parse') || errorMessage.includes('read') || errorMessage.includes('Could not parse')) {
        setError('Could not read file. Try pasting your text instead.');
      } else {
        setError(errorMessage);
      }
      onUploadError?.(errorMessage);
    } finally {
      setIsUploading(false);
    }
  }, [selectedStyle, onUploadStart, onUploadComplete, onUploadError]);

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

  // Show uploading state
  if (isUploading) {
    return (
      <div
        data-testid="uploading-indicator"
        className={`${styles.uploadArea} ${styles.uploading}`}
        role="progressbar"
        aria-label="Uploading document"
      >
        <div className={styles.content}>
          <div className={`${styles.icon} ${styles.spinningIcon}`}>⏳</div>
          <h3>Uploading your document...</h3>
          <p className={styles.uploadHint}>This may take a moment</p>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid="upload-area"
      className={`${styles.uploadArea} ${dragState ? styles.dragOver : ''} ${isUploading ? styles.uploading : ''}`}
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
          accept=".docx"
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
          id="file-input"
          disabled={isUploading}
        />
        <p className={styles.fileTypes}>.docx files accepted</p>
        {error && <div id="error-message" className={styles.error}>{error}</div>}
      </div>
    </div>
  );
};