# Code Review Request: citations-s62x

## Issue
**ID**: citations-s62x
**Title**: P3.4: Update UploadArea for real DOCX upload
**Status**: Implementation complete, tests passing (8/8)

## Summary
Updated UploadArea component from mock implementation to real DOCX upload with backend integration.

## Key Changes

### 1. UploadArea.jsx - Real Backend Integration
- Removed mock `useFileProcessing` hook
- Added real FormData POST to `/api/validate/async`
- DOCX-only file validation (extension + MIME type check)
- New props: `selectedStyle`, `onUploadStart`, `onUploadComplete`, `onUploadError`
- Uploading state with visual feedback (spinner)

### 2. UploadArea.module.css - Uploading State Styles
- Added `.uploading` class for active upload state
- Added `.spinningIcon` with rotation animation
- Added `.uploadHint` for user messaging

### 3. App.jsx - Props Update
- Changed from `onFileSelected` prop to new callback props
- Added `handleUploadStart`, `handleUploadComplete`, `handleUploadError` handlers
- Integrated with existing polling and tracking system

### 4. UploadArea.test.jsx - Complete Test Rewrite
- Mocked fetch API for backend calls
- 8 tests covering: DOCX acceptance, non-DOCX rejection, file size validation, drag states, successful upload, error handling, parse error messaging

## Verification
- ✅ Frontend tests: 8/8 passing (UploadArea.test.jsx)
- ✅ File validation: .docx only, 10MB max
- ✅ Error handling: "Try pasting instead" for parse errors
- ✅ Backend integration: FormData POST to `/api/validate/async`

## Review Scope
Please review:
1. **Implementation correctness**: Does the FormData POST match backend expectations?
2. **Error handling**: Are parse errors properly detected and messaged?
3. **Test coverage**: Do tests adequately cover the new functionality?
4. **Props API**: Is the new callback-based API appropriate?
5. **Edge cases**: File size, MIME type, drag/drop behavior

## Diffs to Review
BASE: `aa7d233` (before UploadArea changes)
HEAD: `4cb18ab` (final UploadArea implementation)

---

Please provide feedback on:
- Any bugs or issues found
- Suggested improvements
- Whether this is ready to merge/approve
