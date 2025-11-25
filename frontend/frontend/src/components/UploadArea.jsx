import React, { useState, useCallback } from 'react';
import styles from './UploadArea.module.css';

const VALID_FILE_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'application/rtf',
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const UploadArea = ({ onFileSelected }) => {
  const [dragState, setDragState] = useState(false);
  const [error, setError] = useState('');

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
      onFileSelected(file);
    }
  }, [onFileSelected]);

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

  return (
    <div
      data-testid="upload-area"
      className={`${styles.uploadArea} ${dragState ? styles.dragOver : ''}`}
      onDragEnter={handleDragEnter}
      onDragOver={(e) => e.preventDefault()}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className={styles.content}>
        <div className={styles.icon}>📄</div>
        <h3>Drop your document here</h3>
        <p>or click to browse</p>
        <input
          type="file"
          accept=".pdf,.docx,.txt,.rtf"
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
          id="file-input"
        />
        <label htmlFor="file-input" role="button" tabIndex={0}>
          Choose File
        </label>
        {error && <div className={styles.error}>{error}</div>}
      </div>
    </div>
  );
};