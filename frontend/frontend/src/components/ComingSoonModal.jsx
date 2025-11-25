import { useEffect, useRef } from 'react';
import { trackEvent } from '../utils/analytics.js';
import './ComingSoonModal.css';

export const ComingSoonModal = ({ isOpen, file, onClose, textInputId = 'main-text-input' }) => {
  const modalStartTime = useRef(null);

  useEffect(() => {
    if (isOpen) {
      modalStartTime.current = Date.now();
      // Track modal open event
      trackEvent('modal_open', {
        modal_type: 'file_upload_coming_soon',
        file_type: file?.type,
        file_size: file?.size
      });
    }
  }, [isOpen, file]);

  const handleDismiss = (dismissMethod) => {
    const duration = modalStartTime.current ? Date.now() - modalStartTime.current : 0;

    // Track analytics
    trackEvent('modal_close', {
      modal_type: 'file_upload_coming_soon',
      dismiss_method: dismissMethod,
      duration: duration,
      file_type: file?.type,
      file_size: file?.size
    });

    // Focus text input after closing
    const textInput = document.getElementById(textInputId);
    if (textInput) {
      textInput.focus();
    }

    onClose({ dismissMethod, duration });
  };

  const getFileTypeLabel = () => {
    if (!file) return '';

    if (file.type === 'application/pdf') {
      return 'PDF detected';
    } else if (file.type.includes('document') || file.type.includes('word') || file.name.endsWith('.docx')) {
      return 'Document detected';
    }
    return 'File detected';
  };

  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';

    // For very small files (< 1KB), show exact bytes
    if (bytes < 1024) {
      return `${bytes} B`;
    }

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      handleDismiss('backdrop');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      handleDismiss('escape');
    }
  };

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isOpen]);

  if (!isOpen || !file) {
    return null;
  }

  return (
    <div
      className="modal-backdrop"
      data-testid="modal-backdrop"
      onClick={handleBackdropClick}
    >
      <div className="modal-content" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <button
          className="close-button"
          onClick={() => handleDismiss('close_button')}
          aria-label="Close modal"
        >
          ×
        </button>

        <div className="modal-header">
          <h2 id="modal-title">📄 File Upload Coming Soon</h2>
        </div>

        <div className="modal-body">
          <div className="messaging">
            <p className="highlight-text">Great choice!</p>
            <p>We detected your <strong>{getFileTypeLabel()}</strong> and saved it to help prioritize this feature.</p>
          </div>

          <div className="file-info">
            <h4>File Information:</h4>
            <ul>
              <li><strong>Name:</strong> {file.name}</li>
              <li><strong>Size:</strong> {formatFileSize(file.size)}</li>
              <li><strong>Type:</strong> {getFileTypeLabel()}</li>
            </ul>
          </div>

          <div className="alternative-action">
            <p>For now, you can paste the text from your document here:</p>
            <div className="text-input-placeholder">
              <span className="arrow-indicator">↓</span>
              <span className="placeholder-text">[Text input area highlighted]</span>
            </div>
          </div>

          <div className="feedback-text">
            <p>✨ Your feedback helps us build this faster!</p>
          </div>
        </div>

        <div className="modal-footer">
          <button
            className="action-button"
            onClick={() => handleDismiss('got_it')}
          >
            Got it, I'll use text input
          </button>
        </div>
      </div>
    </div>
  );
};