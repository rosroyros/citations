import { describe, it, expect } from 'vitest';
import { convertBackendErrorMessage } from './errorMessages';

describe('convertBackendErrorMessage', () => {
  it('should convert insufficient credits error with numbers', () => {
    const error = 'Insufficient credits: need 5, have 2';
    const result = convertBackendErrorMessage(error);
    expect(result).toBe('Request needs 5 validations but only 2 remaining today.');
  });

  it('should convert insufficient credits error without numbers to no credits message', () => {
    const error = 'Insufficient credits: need unknown, have unknown';
    const result = convertBackendErrorMessage(error);
    expect(result).toBe('No credits remaining. Purchase more to continue.');
  });

  it('should convert daily limit exceeded error', () => {
    const error = 'Daily citation limit exceeded (999/1000). Resets at midnight UTC.';
    const result = convertBackendErrorMessage(error);
    expect(result).toBe('Daily limit (1000) reached. Resets at midnight UTC.');
  });

  it('should convert zero credits error', () => {
    const error = 'User has 0 credits remaining';
    const result = convertBackendErrorMessage(error);
    expect(result).toBe('No credits remaining. Purchase more to continue.');
  });

  it('should convert fetch error', () => {
    const error = 'fetch error - Unable to reach server';
    const result = convertBackendErrorMessage(error);
    expect(result).toBe('Unable to connect to the validation service. Please check if the backend is running.');
  });

  it('should convert network error', () => {
    const error = 'Network error occurred';
    const result = convertBackendErrorMessage(error);
    expect(result).toBe('Network error occurred. Please check your connection and try again.');
  });

  it('should return original error if no specific handling', () => {
    const error = 'Some other error message';
    const result = convertBackendErrorMessage(error);
    expect(result).toBe('Some other error message');
  });
});