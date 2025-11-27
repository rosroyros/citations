# Upload Feature - Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Component Architecture](#component-architecture)
3. [Analytics Implementation](#analytics-implementation)
4. [Integration Points](#integration-points)
5. [Testing Strategy](#testing-strategy)
6. [Production Monitoring](#production-monitoring)
7. [Deployment Guide](#deployment-guide)
8. [Support Scenarios](#support-scenarios)

## Overview

The upload feature is a demand validation experiment designed to measure user interest in document upload functionality for citation extraction. The feature is **temporarily unavailable** to users, showing a coming soon modal after file processing to collect demand metrics.

### Purpose
- Validate demand for document upload feature
- Collect behavioral analytics on user interaction patterns
- Maintain zero friction user experience (no login required)
- Test file processing UX flow before building actual extraction

### User Flow
1. User drags/drops or browses for a document (PDF, DOCX, TXT, RTF)
2. File validation runs (type, size checks)
3. Processing animation displays for 1.5 seconds (simulated)
4. Coming soon modal appears explaining feature is unavailable
5. User dismisses modal and returns to main citation input

## Component Architecture

### 1. UploadArea Component

**Location:** `frontend/frontend/src/components/UploadArea.jsx`

**Purpose:** Handles file selection via drag-and-drop or file browse, validates files, and displays processing states.

**Key Features:**
- Drag-and-drop functionality with visual feedback
- File type validation (PDF, DOCX, TXT, RTF)
- File size validation (max 10MB)
- Processing state animation
- Accessibility support (ARIA labels, keyboard navigation)

**Props:**
```javascript
{
  onFileSelected: (processedFile) => void  // Callback when file processing completes
}
```

**States:**
- **Default:** Shows upload prompt with drag-and-drop area
- **Drag Over:** Visual feedback during drag operation
- **Processing:** Progress bar animation (0-100% over 1.5s)
- **Complete:** Shows processed file info with unavailable message
- **Error:** Displays validation error message

**Dependencies:**
- `useFileProcessing` hook for file processing logic
- `fileValidation.js` constants for validation rules
- `UploadArea.module.css` for component styles

**Analytics Events:**
- File selection tracked via parent component

**Accessibility:**
- `role="button"` and `tabIndex={0}` for keyboard access
- ARIA labels for screen readers
- `role="progressbar"` with `aria-valuenow` during processing
- Keyboard Enter/Space to trigger file browser

**Code Reference:** `/frontend/frontend/src/components/UploadArea.jsx:1-155`

---

### 2. ComingSoonModal Component

**Location:** `frontend/frontend/src/components/ComingSoonModal.jsx`

**Purpose:** Informs users that document upload is temporarily unavailable and redirects them to paste citations instead.

**Key Features:**
- Modal backdrop with click-to-dismiss
- Escape key dismissal
- Auto-focus return to editor after close
- Tracks modal view duration and dismissal method

**Props:**
```javascript
{
  isOpen: boolean,              // Controls modal visibility
  file: File | null,            // File object for analytics
  onClose: (data) => void,      // Callback with { dismissMethod, duration }
  textInputId?: string          // ID of input to focus after close (default: 'main-text-input')
}
```

**Dismissal Methods:**
- `'got_it'` - User clicked "Okay" button
- `'backdrop'` - User clicked modal backdrop
- `'escape'` - User pressed Escape key

**Analytics Events:**
- `modal_open` - When modal becomes visible
- `modal_close` - When modal is dismissed (includes duration, dismissMethod)

**Focus Management:**
- Attempts to find TipTap editor: `[data-testid="editor"] .ProseMirror`
- Falls back to `[contenteditable="true"]`
- Final fallback to `textInputId` prop
- Returns focus to editor for seamless UX

**Accessibility:**
- `role="dialog"` and `aria-modal="true"`
- `aria-labelledby` for screen readers
- Keyboard escape handler

**Code Reference:** `/frontend/frontend/src/components/ComingSoonModal.jsx:1-117`

---

### 3. useFileProcessing Hook

**Location:** `frontend/frontend/src/hooks/useFileProcessing.js`

**Purpose:** Manages file processing state, simulates processing animation, and extracts file content.

**API:**
```javascript
const {
  isProcessing,    // boolean - true during 1.5s animation
  progress,        // number - 0-100 progress percentage
  processedFile,   // object | null - completed file data
  processFile,     // function(File) - starts processing
  reset            // function() - resets all state
} = useFileProcessing()
```

**Processing Flow:**
1. Validates file object (must be instance of File)
2. Tracks `upload_processing_shown` event
3. Starts FileReader to extract content asynchronously
4. Runs 1.5s progress animation (updates every 50ms)
5. Tracks `upload_file_preview_rendered` event
6. Sets `processedFile` with metadata and content

**Processed File Object:**
```javascript
{
  file: File,                    // Original File object
  name: string,                  // File name
  type: string,                  // MIME type
  size: number,                  // File size in bytes
  lastModified: number,          // Timestamp
  content?: string | ArrayBuffer // Extracted content (optional)
}
```

**Constants:**
- `PROCESSING_DURATION_MS = 1500` - 1.5 seconds
- `PROGRESS_UPDATE_INTERVAL_MS = 50` - 20 FPS animation

**Analytics Events:**
- `upload_processing_shown` - When processing starts
- `upload_file_preview_rendered` - When processing completes

**Error Handling:**
- Logs errors to console if invalid file provided
- Handles FileReader errors gracefully
- No-op if file is null/invalid

**Cleanup:**
- `reset()` clears intervals, aborts FileReader, resets state
- Automatically called on unmount (component responsibility)

**Code Reference:** `/frontend/frontend/src/hooks/useFileProcessing.js:1-138`

---

## Analytics Implementation

### Overview
The upload feature tracks 10 analytics events using Google Analytics (gtag) to measure demand and user behavior.

### Analytics Utility

**Location:** `frontend/frontend/src/utils/analytics.js`

**Function:**
```javascript
trackEvent(eventName: string, params: object = {})
```

**Features:**
- Safe checking for gtag existence
- Development console logging
- Graceful degradation if gtag unavailable

**Code Reference:** `/frontend/frontend/src/utils/analytics.js:1-28`

### Event Catalog

#### 1. upload_area_clicked
**When:** User clicks anywhere on the upload area
**Purpose:** Measure initial interest in upload feature
**Parameters:**
```javascript
{
  interface_source: 'main_page'
}
```
**Code:** `App.jsx:306-310`

#### 2. upload_file_selected
**When:** User successfully selects a file (after validation)
**Purpose:** Track which file types users attempt to upload
**Parameters:**
```javascript
{
  file_type: string,    // MIME type (e.g., 'application/pdf')
  file_size: number,    // Size in bytes
  file_name: string     // Filename
}
```
**Code:** `App.jsx:291-303`

#### 3. upload_processing_shown
**When:** Processing animation starts (1.5s animation begins)
**Purpose:** Track successful file processing initiation
**Parameters:**
```javascript
{
  file_type: string,    // MIME type
  file_size: number     // Size in bytes
}
```
**Code:** `useFileProcessing.js:38-41`

#### 4. upload_file_preview_rendered
**When:** Processing completes (after 1.5s)
**Purpose:** Measure completion rate of processing animation
**Parameters:**
```javascript
{
  processing_time_ms: number,  // Actual time taken (should be ~1500ms)
  file_type: string,
  file_size: number
}
```
**Code:** `useFileProcessing.js:86-91`

#### 5. modal_open
**When:** ComingSoonModal becomes visible
**Purpose:** Track modal impression rate
**Parameters:**
```javascript
{
  modal_type: 'file_upload_coming_soon',
  file_type: string,
  file_size: number
}
```
**Code:** `ComingSoonModal.jsx:12-17`

#### 6. modal_close
**When:** User dismisses ComingSoonModal
**Purpose:** Measure modal engagement and dismissal patterns
**Parameters:**
```javascript
{
  modal_type: 'file_upload_coming_soon',
  dismiss_method: 'got_it' | 'backdrop' | 'escape',
  duration: number,       // Time modal was open (milliseconds)
  file_type: string,
  file_size: number
}
```
**Code:** `ComingSoonModal.jsx:24-30`

#### 7. upload_modal_closed
**When:** Modal close is handled in App.jsx
**Purpose:** Redundant tracking at app level (mirrors modal_close)
**Parameters:**
```javascript
{
  dismiss_method: string,
  duration: number,
  file_type: string,
  file_size: number
}
```
**Code:** `App.jsx:318-323`
**Note:** Consider consolidating with modal_close event

#### 8. editor_focused
**When:** User focuses on the main citation editor
**Purpose:** Track return to main interface after modal dismissal
**Parameters:**
```javascript
{
  editor_content_length: number,
  has_placeholder: boolean
}
```
**Code:** `App.jsx:350-353`

#### 9. editor_paste
**When:** User pastes content into editor (>50 chars)
**Purpose:** Measure adoption of paste workflow after upload failure
**Parameters:**
```javascript
{
  content_length_before: number,
  content_length_after: number,
  content_added: number
}
```
**Code:** `App.jsx:393-397`

#### 10. editor_cleared
**When:** User clears substantial content (>50 chars → <10 chars)
**Purpose:** Track user frustration or retry patterns
**Parameters:**
```javascript
{
  content_length_before: number,
  content_length_after: number
}
```
**Code:** `App.jsx:403-407`

### Event Flow Diagram

```
User Interaction Flow:
┌─────────────────────┐
│ upload_area_clicked │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│upload_file_selected │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────┐
│upload_processing_shown│
└──────────┬───────────┘
           │ (1.5s animation)
           ▼
┌───────────────────────────┐
│upload_file_preview_rendered│
└──────────┬────────────────┘
           │
           ▼
┌─────────────┐
│  modal_open │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ modal_close │
└──────┬──────┘
       │
       ▼
┌────────────────┐
│editor_focused  │ ← User returns to main interface
└────────────────┘
       │
       ▼
┌────────────────┐
│ editor_paste   │ (optional - if user pastes citations)
└────────────────┘
```

### Data Interpretation

**Demand Validation Metrics:**

1. **Upload Interest Rate**
   - Metric: `upload_area_clicked` / page views
   - Threshold: >5% indicates strong interest

2. **File Selection Rate**
   - Metric: `upload_file_selected` / `upload_area_clicked`
   - Threshold: >30% indicates serious intent

3. **Modal Completion Rate**
   - Metric: `modal_close` / `modal_open`
   - Expected: ~95%+ (should be near 100%)

4. **Return to Paste Rate**
   - Metric: `editor_paste` within 60s after `modal_close`
   - Threshold: >40% indicates smooth fallback UX

5. **Modal Engagement Duration**
   - Metric: Average `duration` in `modal_close` events
   - Interpretation:
     - <2s: Users quickly understand and move on
     - 2-10s: Users reading message carefully
     - >10s: Potential confusion or friction

6. **Dismissal Method Distribution**
   - Metric: Distribution of `dismiss_method` values
   - Expected: `'got_it'` should be majority (>70%)
   - Concern: High `'escape'` rate may indicate frustration

**File Type Preferences:**
- Track `file_type` distribution in `upload_file_selected`
- Prioritize building support for most common types first
- Example: If 80% PDF, build PDF parser first

**File Size Analysis:**
- Track `file_size` distribution
- Validate 10MB limit is appropriate
- Identify if users hit size limits frequently

### Dashboard Setup

**Recommended GA4 Custom Reports:**

1. **Upload Funnel Report**
   - Events: upload_area_clicked → upload_file_selected → modal_open → modal_close → editor_paste
   - Metrics: Conversion rate at each step
   - Breakdown: By file_type, date

2. **Engagement Report**
   - Event: modal_close
   - Metrics: Average duration, dismiss_method distribution
   - Breakdown: By date, file_type

3. **File Type Distribution**
   - Event: upload_file_selected
   - Dimension: file_type
   - Metrics: Event count, percentage

4. **User Journey Report**
   - Custom exploration combining:
     - Upload events
     - Editor events
     - Validation events
   - Goal: Understand full user behavior patterns

## Integration Points

### App.jsx Integration

**Location:** `frontend/frontend/src/App.jsx:48-50, 291-324, 649-654, 825-829`

**State Management:**
```javascript
const [showComingSoonModal, setShowComingSoonModal] = useState(false)
const [selectedFile, setSelectedFile] = useState(null)
```

**Handlers:**

1. **handleFileSelected** (App.jsx:291-303)
   - Receives processed file from UploadArea
   - Tracks `upload_file_selected` event
   - Sets modal state to visible

2. **handleComingSoonClose** (App.jsx:313-324)
   - Receives dismissal data from modal
   - Tracks `upload_modal_closed` event
   - Resets modal state

3. **handleUploadAreaClick** (App.jsx:306-310)
   - Tracks `upload_area_clicked` event
   - Currently unused - can be added to UploadArea onClick if needed

**Layout Structure:**
```jsx
<div className="input-layout">
  <div className="editor-column">
    {/* TipTap editor */}
  </div>

  <div className="upload-column">
    <UploadArea
      onFileSelected={handleFileSelected}
      onUploadAreaClick={handleUploadAreaClick}
    />
  </div>
</div>

{/* At root level */}
<ComingSoonModal
  isOpen={showComingSoonModal}
  file={selectedFile}
  onClose={handleComingSoonClose}
/>
```

**Responsive Behavior:**
- Desktop: Side-by-side layout (editor left, upload right)
- Mobile: Stacked layout (editor top, upload bottom)
- CSS handles layout via `@media` queries in `App.css`

**Code References:**
- State: `App.jsx:48-50`
- Handlers: `App.jsx:291-324`
- Render: `App.jsx:649-654, 825-829`

## Testing Strategy

### E2E Test Coverage

**Test Files:**
1. `tests/e2e/upload-area.spec.js` - UploadArea component tests
2. `tests/e2e/coming-soon-modal.spec.js` - ComingSoonModal tests
3. `tests/e2e/upload-integration.spec.js` - Full integration tests
4. `tests/e2e/upload-comprehensive.spec.js` - Edge cases and detailed scenarios

**Total Coverage:** 46 tests across 5 browsers (chromium, firefox, webkit, Mobile Chrome, Mobile Safari) = 230 test executions

### Test Categories

#### 1. Component Rendering Tests
- UploadArea renders with correct UI elements
- Drag-and-drop visual feedback
- Processing state transitions
- Error message display
- Modal structure and content

#### 2. Interaction Tests
- File selection via browse
- File selection via drag-and-drop
- Modal dismissal methods (button, backdrop, escape)
- Keyboard navigation
- Focus management

#### 3. File Validation Tests
- Valid file types (PDF, DOCX, TXT, RTF)
- Invalid file types rejected
- File size limits enforced (10MB max)
- Error messages displayed correctly

#### 4. Processing Flow Tests
- Processing animation duration (~1.5s)
- Progress bar animation (0% → 100%)
- Completion state after processing
- Coming soon modal appears after processing

#### 5. Analytics Tests
- upload_area_clicked event fires
- upload_file_selected event with correct params
- modal_open event fires
- modal_close event with dismiss method
- Editor focus tracking after modal close

#### 6. Integration Tests
- Full upload flow from selection to modal dismissal
- Editor receives focus after modal close
- Layout adapts to different screen sizes
- State management across components

#### 7. Accessibility Tests
- ARIA labels present and correct
- Keyboard navigation functional
- Screen reader compatibility
- Focus management proper

### Running Tests

```bash
# All upload tests
cd frontend/frontend
npx playwright test tests/e2e/upload-*.spec.js

# Specific test file
npx playwright test tests/e2e/upload-integration.spec.js

# Single browser
npx playwright test tests/e2e/upload-integration.spec.js --project=chromium

# With UI
npx playwright test tests/e2e/upload-integration.spec.js --ui

# Debug mode
npx playwright test tests/e2e/upload-integration.spec.js --debug
```

### Known Test Issues

**Flaky Test - Processing Duration:**
- Test: "Processing animation displays for 1.5 seconds before modal"
- File: `upload-comprehensive.spec.js:32`
- Issue: Occasionally exceeds 2000ms threshold (observed: 2008ms)
- Cause: CI/slow machine timing variance
- Recommendation: Increase tolerance to 2100ms or use waitFor with timeout

### Test Maintenance

**Adding New Tests:**
1. Follow existing test structure in `upload-comprehensive.spec.js`
2. Use `data-testid` attributes for reliable selectors
3. Add analytics tracking assertions for new events
4. Test across all browsers (default: runs on all projects)

**Debugging Failures:**
1. Check `test-results/` directory for screenshots/videos
2. Use `--ui` mode to step through tests
3. Check `playwright-report/` for HTML report
4. Enable trace: `npx playwright test --trace on`

## Production Monitoring

### Key Metrics to Track

**1. Upload Engagement Metrics**
- Upload area click rate
- File selection rate
- Processing completion rate
- Modal view rate
- Modal dismissal rate

**2. Conversion Funnel**
- Upload attempt → File selected → Processing shown → Modal shown → Modal dismissed → Editor focused
- Track drop-off at each stage
- Alert if any stage drops below threshold

**3. Performance Metrics**
- Processing animation duration (should average ~1500ms)
- Modal load time
- File validation latency
- Page load impact

**4. Error Metrics**
- File validation failures by type
- File size limit rejections
- JavaScript errors in upload flow
- Failed analytics events

**5. User Behavior Metrics**
- Time spent on modal (engagement duration)
- Dismissal method distribution
- Return-to-editor rate after modal
- Paste activity after upload attempt

### Alerting Recommendations

**Critical Alerts (P0):**
- Upload flow JavaScript errors >0.1% of attempts
- Modal render failures >1%
- Analytics event failure rate >5%

**Warning Alerts (P1):**
- Processing duration >2000ms for >10% of attempts
- Modal dismissal rate <90%
- Editor focus failure after modal >5%

**Info Alerts (P2):**
- Unusual file type distribution changes
- File size limit hits increasing trend
- Dismissal method distribution shifts

### Google Analytics Setup

**Custom Definitions:**

1. **Custom Events:**
   - All 10 upload events already defined (see Analytics section)

2. **Custom Dimensions:**
   - `file_type` - Track across all upload events
   - `dismiss_method` - For modal_close events
   - `interface_source` - Always 'main_page' for now

3. **Custom Metrics:**
   - `duration` - Modal engagement time (ms)
   - `file_size` - File size in bytes
   - `processing_time_ms` - Processing animation duration

**Conversion Goals:**
- Goal 1: File selected (upload_file_selected event)
- Goal 2: Modal viewed (modal_open event)
- Goal 3: Returned to editor (editor_focused within 10s of modal_close)

### Error Tracking

**Sentry/LogRocket Integration:**

**Events to Track:**
1. File validation errors
2. FileReader errors in useFileProcessing
3. Modal focus management failures
4. Analytics tracking failures
5. Component render errors

**Context to Capture:**
- File type and size (if available)
- User agent/browser
- Current upload state
- Component stack trace

**Example Sentry Configuration:**
```javascript
// Add to useFileProcessing.js
if (fileReader.current.error) {
  Sentry.captureException(fileReader.current.error, {
    tags: {
      component: 'useFileProcessing',
      file_type: file.type,
      file_size: file.size
    }
  })
}
```

### Dashboard Configuration

**Recommended Dashboards:**

1. **Upload Feature Health Dashboard**
   - Upload engagement funnel (real-time)
   - Error rates by component
   - Performance metrics (processing time, modal load)
   - Browser/device breakdown

2. **Demand Validation Dashboard**
   - Daily upload attempts
   - File type distribution
   - Modal engagement metrics
   - Conversion to paste behavior

3. **Technical Performance Dashboard**
   - Processing animation timing distribution
   - File validation error breakdown
   - JavaScript error trends
   - Analytics event success rates

## Deployment Guide

### Pre-Deployment Checklist

**Code Quality:**
- [ ] All E2E tests passing (46 tests × 5 browsers = 230 tests)
- [ ] No console errors in production build
- [ ] Analytics events firing correctly in staging
- [ ] Component accessibility verified (WCAG 2.1 AA)

**Analytics Configuration:**
- [ ] GA4 property configured
- [ ] Custom events tracking verified
- [ ] Custom dimensions created
- [ ] Conversion goals set up
- [ ] Dashboard templates configured

**Infrastructure:**
- [ ] Frontend build optimized (bundle size checked)
- [ ] CDN cache invalidation prepared
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured

**Documentation:**
- [ ] Technical documentation complete (this document)
- [ ] Support team trained
- [ ] FAQ updated
- [ ] Runbook created

### Deployment Steps

**1. Build and Test**
```bash
# Build frontend
cd frontend/frontend
npm run build

# Verify build
ls -lh dist/
# Check bundle size is reasonable

# Run final test suite
npx playwright test tests/e2e/upload-*.spec.js
```

**2. Deploy to Staging**
```bash
# SSH to staging server
ssh deploy@<staging-server>

# Pull latest code
cd /opt/citations
git pull origin main

# Deploy
./deployment/scripts/deploy.sh
```

**3. Staging Validation**
- [ ] Visit staging URL
- [ ] Test upload flow end-to-end
- [ ] Verify analytics events in GA4 (use debug mode)
- [ ] Test all dismissal methods
- [ ] Check mobile responsiveness
- [ ] Verify error handling

**4. Deploy to Production**
```bash
# SSH to production
ssh deploy@178.156.161.140

# Pull latest code
cd /opt/citations
git pull origin main

# Deploy
./deployment/scripts/deploy.sh

# Verify deployment
systemctl status citations-backend
curl https://citationformatcheck.com/api/health
```

**5. Post-Deployment Verification**
- [ ] Upload flow functional on production
- [ ] Analytics events firing (check GA4 real-time)
- [ ] No JavaScript errors in console
- [ ] Mobile experience working
- [ ] All browsers tested (Chrome, Firefox, Safari)

### Rollback Procedure

**Quick Rollback (if critical issue found):**

```bash
# SSH to production
ssh deploy@178.156.161.140
cd /opt/citations

# Revert to previous commit
git log --oneline -5  # Find previous stable commit
git checkout <previous-commit-hash>

# Rebuild and deploy
cd frontend/frontend
npm run build
sudo systemctl restart citations-backend
sudo systemctl restart nginx
```

**Feature Flag Rollback (alternative):**

If you implement feature flags later:
```javascript
// App.jsx
const ENABLE_UPLOAD_FEATURE = import.meta.env.VITE_ENABLE_UPLOAD === 'true'

// In render
{ENABLE_UPLOAD_FEATURE && (
  <UploadArea onFileSelected={handleFileSelected} />
)}
```

Then rollback is just:
```bash
# Update environment variable
echo "VITE_ENABLE_UPLOAD=false" >> frontend/frontend/.env.production
npm run build
```

### Performance Impact Assessment

**Before Deployment:**
- Measure baseline page load time
- Measure baseline bundle size
- Measure baseline JavaScript execution time

**After Deployment:**
- Compare page load time (target: <100ms increase)
- Compare bundle size (UploadArea + Modal = ~15KB gzipped)
- Monitor Core Web Vitals (LCP, FID, CLS)

**Expected Impact:**
- Bundle size increase: ~15-20KB (gzipped)
- Page load time: <50ms increase
- No impact on existing validation flow

### Monitoring First 24 Hours

**Hour 0-1 (Critical):**
- Monitor JavaScript errors in real-time
- Check analytics event firing rates
- Watch upload engagement metrics
- Verify no regression in main validation flow

**Hour 1-6 (Important):**
- Review error rates by browser/device
- Check performance metrics stabilizing
- Monitor user feedback channels
- Verify analytics dashboard updating

**Hour 6-24 (Standard):**
- Review full engagement funnel
- Check file type distribution
- Monitor modal engagement times
- Compare against baseline metrics

**Success Criteria (24 hours):**
- Zero critical bugs reported
- JavaScript error rate <0.1%
- Upload engagement rate >2% of page views
- Modal completion rate >95%
- No negative impact on main validation flow

## Support Scenarios

### User-Facing Information

**Feature Description:**
"The document upload feature is currently unavailable as we're preparing to support automatic citation extraction from PDFs and Word documents. For now, please paste your citations directly into the text area, and we'll validate them all at once."

**FAQ Updates:**

**Q: Can I upload a document with citations?**
A: Document upload is temporarily unavailable as we prepare to support automatic citation extraction. For now, please copy and paste your citations directly into the text area. This works great and takes just a few seconds!

**Q: What file types will you support?**
A: We're planning to support PDF, Word documents (DOCX), plain text (TXT), and Rich Text Format (RTF) files. We're collecting feedback to prioritize which format to build first.

**Q: When will document upload be available?**
A: We're currently validating user demand for this feature. If there's strong interest, we'll prioritize building it soon. In the meantime, you can paste your citations directly for instant validation.

**Q: Why does it say "coming soon" after I select a file?**
A: We're measuring interest in document upload functionality to prioritize our development roadmap. Thank you for your patience! The paste-citations workflow is fast and works perfectly for all citation checks.

### Support Ticket Handling

**Scenario 1: "Why can't I upload my document?"**

**Response Template:**
```
Hi [Name],

Thank you for trying to upload your document! The upload feature is temporarily unavailable as we're building automatic citation extraction capabilities.

In the meantime, you can:
1. Copy your citations from your document
2. Paste them into the citation checker text area
3. Click "Check My Citations" to validate them all at once

This method is actually very quick (takes just a few seconds) and works perfectly for validating your citations.

We're tracking interest in document upload to prioritize development. If this feature is important to you, please let us know what file type you wanted to upload (PDF, Word, etc.), and we'll use that to guide our development priorities.

Thanks for your understanding!

Best regards,
[Support Team]
```

**Scenario 2: "The upload button doesn't work"**

**Response Template:**
```
Hi [Name],

Thanks for reporting this! The upload area should accept files and then display a message that the feature is "coming soon."

Can you help us troubleshoot:
1. What file type were you trying to upload? (PDF, Word, etc.)
2. What happened after you selected the file? Did you see a processing animation?
3. What browser are you using? (Chrome, Firefox, Safari, etc.)

If you saw a "coming soon" message, that's expected behavior - the feature is temporarily unavailable as we build citation extraction capabilities. You can paste your citations directly into the text area as a workaround.

If you didn't see any response, there may be a technical issue we need to investigate. Please share the details above, and we'll help resolve it.

Thanks!
Best regards,
[Support Team]
```

**Scenario 3: "I uploaded a file but nothing happened"**

**Troubleshooting Steps:**
1. Check browser console for JavaScript errors
2. Verify file type is supported (PDF, DOCX, TXT, RTF)
3. Verify file size is under 10MB
4. Ask user to try different browser
5. Check if modal appeared and user missed it

**Response Template:**
```
Hi [Name],

I'm sorry you're experiencing issues! Let me help troubleshoot:

1. **File type**: We support PDF, DOCX, TXT, and RTF files. If your file is a different type, you'll need to convert it or paste the citations directly.

2. **File size**: Files must be under 10MB. If your file is larger, try splitting it or pasting citations directly.

3. **What to expect**: After selecting a file, you should see:
   - A processing animation (1-2 seconds)
   - A message explaining the feature is "coming soon"
   - An "Okay" button to return to the main interface

If you didn't see these steps, please try:
- Using a different browser (Chrome, Firefox, or Safari)
- Clearing your browser cache
- Disabling browser extensions temporarily

In the meantime, you can paste your citations directly into the text area, and we'll validate them instantly. This works perfectly and doesn't require any upload.

Please let me know if these steps help, or share more details about what you're seeing, and I'll investigate further!

Best regards,
[Support Team]
```

### User Feedback Collection

**Feedback Form Questions:**
1. What file type did you try to upload? (PDF / Word / TXT / RTF / Other)
2. How many citations were in your document? (Rough estimate)
3. How important is document upload to your workflow? (1-5 scale)
4. Would you prefer to paste citations or upload documents? (Preference scale)
5. Any other feedback about your experience?

**Feedback Channels:**
- Support email: support@citationformatcheck.com
- In-app feedback link (if added)
- Analytics events (behavioral feedback)
- Social media monitoring

### Internal Runbook

**Upload Feature Issue Resolution:**

**Issue:** JavaScript error on file upload
**Resolution:**
1. Check browser console for error details
2. Verify useFileProcessing hook not throwing errors
3. Check File API support in user's browser
4. Review Sentry for stack traces
5. Escalate to engineering if unresolved

**Issue:** Modal doesn't appear after processing
**Resolution:**
1. Verify `showComingSoonModal` state set correctly
2. Check React DevTools for state values
3. Verify modal `isOpen` prop is true
4. Check for CSS z-index issues hiding modal
5. Review browser console for errors

**Issue:** Analytics events not firing
**Resolution:**
1. Verify gtag loaded (check window.gtag exists)
2. Check GA4 measurement ID configured
3. Use GA4 DebugView to see real-time events
4. Verify trackEvent calls in code
5. Check browser ad-blockers not blocking GA

**Issue:** Poor upload performance
**Resolution:**
1. Check processing duration metrics
2. Verify FileReader not blocking main thread
3. Review bundle size and lazy loading
4. Check for memory leaks in useFileProcessing
5. Optimize if processing consistently >2000ms

### Success Metrics & Reporting

**Weekly Report Template:**

**Upload Feature - Week of [Date]**

**Engagement Metrics:**
- Upload area clicks: [count] ([%] of page views)
- Files selected: [count] ([%] of clicks)
- Processing completions: [count] ([%] of selections)
- Modals shown: [count]
- Modals dismissed: [count] ([%] completion)

**User Behavior:**
- Average modal engagement: [X]s
- Dismissal methods: Got It: [%], Backdrop: [%], Escape: [%]
- Return to editor rate: [%]
- Paste after upload attempt: [%]

**File Type Distribution:**
- PDF: [%]
- DOCX: [%]
- TXT: [%]
- RTF: [%]
- Other: [%]

**Technical Health:**
- JavaScript errors: [count] ([%] of attempts)
- Processing time P50: [X]ms, P95: [X]ms
- Modal render failures: [count]
- Analytics event success: [%]

**Insights & Recommendations:**
- [Key finding 1]
- [Key finding 2]
- [Recommended action items]

---

## Appendix

### File References

**Components:**
- UploadArea: `frontend/frontend/src/components/UploadArea.jsx`
- ComingSoonModal: `frontend/frontend/src/components/ComingSoonModal.jsx`
- UploadArea styles: `frontend/frontend/src/components/UploadArea.module.css`
- ComingSoonModal styles: `frontend/frontend/src/components/ComingSoonModal.css`

**Hooks:**
- useFileProcessing: `frontend/frontend/src/hooks/useFileProcessing.js`

**Utilities:**
- Analytics: `frontend/frontend/src/utils/analytics.js`
- File validation constants: `frontend/frontend/src/constants/fileValidation.js`

**Integration:**
- App.jsx: `frontend/frontend/src/App.jsx` (lines 48-50, 291-324, 649-654, 825-829)
- App.css: `frontend/frontend/src/App.css` (layout styles)

**Tests:**
- UploadArea tests: `frontend/frontend/tests/e2e/upload-area.spec.js`
- ComingSoonModal tests: `frontend/frontend/tests/e2e/coming-soon-modal.spec.js`
- Integration tests: `frontend/frontend/tests/e2e/upload-integration.spec.js`
- Comprehensive tests: `frontend/frontend/tests/e2e/upload-comprehensive.spec.js`

### Related Documentation
- Main README: `/Users/roy/Documents/Projects/citations/README.md`
- CLAUDE.md: `/Users/roy/Documents/Projects/citations/CLAUDE.md`
- Deployment scripts: `/Users/roy/Documents/Projects/citations/deployment/scripts/deploy.sh`

### Change Log

**2025-11-27:** Initial documentation created for production deployment
