# Validation Latency UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign validation results with table-based layout and progressive loading to improve perceived performance during 45-60s GPT-5-mini validation.

**Architecture:** Replace card-based results with scannable table. Progressive text reveal (0-10s) followed by rotating status messages (10-60s). Site-wide design system refinements for cohesive academic aesthetic.

**Tech Stack:** React 18, TipTap editor, CSS modules, existing FastAPI backend

---

## Phase 1: Design System Foundation

### Task 1: Update Global CSS Variables

**Files:**
- Modify: `frontend/frontend/src/index.css:1-63`

**Step 1: Replace color system in index.css**

Update the `:root` section with refined color palette:

```css
:root {
  /* Typography */
  --font-body: 'Work Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-heading: 'Work Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Courier New', monospace;

  /* Brand color - use sparingly (CTAs only) */
  --color-brand: #9333ea;
  --color-brand-hover: #7c3aed;
  --color-brand-light: rgba(147, 51, 234, 0.1);

  /* Text hierarchy */
  --color-text-primary: #1a1f36;
  --color-text-secondary: #4a5568;
  --color-text-tertiary: #718096;

  /* Semantic colors */
  --color-success: #047857;
  --color-success-bg: #ecfdf5;
  --color-success-border: #a7f3d0;

  --color-error: #b45309;
  --color-error-bg: #fffbeb;
  --color-error-border: #fcd34d;

  --color-info: #0369a1;
  --color-info-bg: #e0f2fe;

  /* Backgrounds */
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #fafbfc;
  --color-bg-tertiary: #f3f4f6;

  /* Refined gradient background */
  --gradient-bg: linear-gradient(135deg, #f0f9ff 0%, #faf5ff 50%, #fdf4ff 100%);

  /* Borders & shadows */
  --border-color: #e5e7eb;
  --border-color-light: #f3f4f6;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.03);

  /* Spacing system */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-2xl: 3rem;
  --space-3xl: 4rem;

  font-family: var(--font-body);
  line-height: 1.5;
  font-weight: 400;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;
}
```

**Step 2: Update body and typography styles**

```css
body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
  background: var(--gradient-bg);
  color: var(--color-text-secondary);
}

a {
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color 0.2s ease;
}

a:hover {
  color: var(--color-brand);
}

h1 {
  font-family: var(--font-heading);
  font-size: 2.5rem;
  line-height: 1.1;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--color-text-primary);
}

button {
  border-radius: 8px;
  border: none;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  font-family: var(--font-heading);
  cursor: pointer;
  transition: all 0.25s;
  background: var(--color-brand);
  color: white;
}

button:hover:not(:disabled) {
  background: var(--color-brand-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(147, 51, 234, 0.2);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
```

**Step 3: Verify changes**

Run: `cd frontend/frontend && npm run dev`
Check: Open browser, verify gradient background and text colors updated

**Step 4: Commit**

```bash
git add frontend/frontend/src/index.css
git commit -m "feat: update global design system with refined color palette"
```

---

### Task 2: Update App.css Site-Wide Styles

**Files:**
- Modify: `frontend/frontend/src/App.css:0-450`

**Step 1: Update header styles**

Replace header section with refined styling:

```css
/* Header */
.header {
  background: white;
  box-shadow: var(--shadow-sm);
  border-bottom: 1px solid var(--border-color-light);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logo-icon {
  width: 2rem;
  height: 2rem;
  color: var(--color-brand);
  flex-shrink: 0;
}

.logo-text {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: -0.02em;
}

.credit-display {
  font-size: 0.9rem;
  color: var(--color-brand);
  font-weight: 500;
}
```

**Step 2: Update hero section styles**

```css
/* Hero Section */
.hero {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-3xl) var(--space-xl);
}

.hero-content {
  display: flex;
  gap: 2rem;
  align-items: center;
  justify-content: center;
  max-width: 1200px;
  margin: 0 auto;
}

.hero-text {
  flex: 1;
  max-width: 900px;
  text-align: center;
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--color-text-primary);
  margin-bottom: var(--space-md);
}

.hero-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  font-weight: 400;
  line-height: 1.5;
}
```

**Step 3: Update button and input styles**

```css
/* Input Section */
.input-section {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 2rem 3rem;
}

.input-section form {
  background: white;
  border-radius: 12px;
  padding: var(--space-xl);
  box-shadow: var(--shadow-md);
}

.input-section label {
  display: block;
  font-family: var(--font-heading);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 0.75rem;
}

.citation-editor {
  border: 2px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  min-height: 250px;
  font-family: var(--font-mono);
  line-height: 1.6;
  text-align: left;
  outline: none;
  transition: all 0.2s;
  background: var(--color-bg-secondary);
}

.citation-editor:focus {
  border-color: var(--color-brand);
  background: white;
  box-shadow: 0 0 0 3px var(--color-brand-light);
}

button[type="submit"] {
  width: 100%;
  margin-top: var(--space-lg);
  background: var(--color-brand);
  color: white;
}

.feature-pill {
  background: var(--color-bg-primary);
  border: 1px solid var(--border-color);
  padding: var(--space-sm) var(--space-md);
  border-radius: 999px;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}
```

**Step 4: Update error message styling**

```css
.error {
  max-width: 900px;
  margin: 2rem auto;
  padding: var(--space-lg);
  background: var(--color-error-bg);
  border: 1px solid var(--color-error-border);
  border-left: 3px solid var(--color-error);
  border-radius: 8px;
  color: var(--color-error);
}

.error strong {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
}
```

**Step 5: Verify changes**

Run: `npm run dev`
Check: Verify header, hero, inputs use new design system

**Step 6: Commit**

```bash
git add frontend/frontend/src/App.css
git commit -m "feat: apply refined design system to site-wide components"
```

---

## Phase 2: Validation Table Components

### Task 3: Create ValidationTable Component

**Files:**
- Create: `frontend/frontend/src/components/ValidationTable.jsx`
- Create: `frontend/frontend/src/components/ValidationTable.css`

**Step 1: Create ValidationTable.jsx**

```jsx
import { useState } from 'react'
import './ValidationTable.css'

function ValidationTable({ results }) {
  const [expandedRows, setExpandedRows] = useState(() => {
    // Initialize with error rows expanded
    const initial = {}
    results.forEach(result => {
      initial[result.citation_number] = result.errors.length > 0
    })
    return initial
  })

  const toggleRow = (citationNumber) => {
    setExpandedRows(prev => ({
      ...prev,
      [citationNumber]: !prev[citationNumber]
    }))
  }

  const perfectCount = results.filter(r => r.errors.length === 0).length
  const errorCount = results.filter(r => r.errors.length > 0).length

  return (
    <div className="validation-table-container">
      <div className="table-header">
        <h2>Validation Results</h2>
        <div className="table-stats">
          <span className="stat-item">
            <strong>{results.length}</strong> citations
          </span>
          <span className="stat-separator">•</span>
          <span className="stat-item">
            <span className="stat-badge success">{perfectCount}</span>
            perfect
          </span>
          <span className="stat-separator">•</span>
          <span className="stat-item">
            <span className="stat-badge error">{errorCount}</span>
            need fixes
          </span>
        </div>
      </div>

      <table className="validation-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Citation</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {results.map((result) => {
            const isExpanded = expandedRows[result.citation_number]
            const hasErrors = result.errors.length > 0

            return (
              <tr
                key={result.citation_number}
                className={isExpanded && hasErrors ? 'expanded' : ''}
              >
                <td>
                  <span className="citation-num">{result.citation_number}</span>
                </td>
                <td>
                  <div
                    className={`citation-text ${!hasErrors && !isExpanded ? 'truncated' : ''}`}
                    dangerouslySetInnerHTML={{ __html: result.original }}
                  />
                  {isExpanded && (
                    <div className="source-type">
                      {result.source_type}
                    </div>
                  )}

                  {hasErrors && isExpanded && (
                    <div className="error-details">
                      <ul className="error-list">
                        {result.errors.map((error, index) => (
                          <li key={index} className="error-item">
                            <div className="error-component">
                              {error.component}
                            </div>
                            <div className="error-problem">
                              {error.problem}
                            </div>
                            {error.correction && (
                              <div className="error-correction">
                                <strong>Should be:</strong> {error.correction}
                              </div>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </td>
                <td>
                  <div className="status-cell">
                    <div className={`status-icon ${hasErrors ? 'error' : 'success'}`}>
                      {hasErrors ? '✗' : '✓'}
                    </div>
                    <span className="status-text">
                      {hasErrors ? `${result.errors.length} issue${result.errors.length > 1 ? 's' : ''}` : 'Perfect'}
                    </span>
                  </div>
                </td>
                <td>
                  <button
                    className="action-btn"
                    onClick={() => toggleRow(result.citation_number)}
                    aria-label={isExpanded ? 'Collapse' : 'Expand'}
                  >
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d={isExpanded ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"}
                      />
                    </svg>
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default ValidationTable
```

**Step 2: Create ValidationTable.css**

```css
.validation-table-container {
  max-width: 1100px;
  margin: 2rem auto;
  padding: 0 1rem;
}

/* Table Header */
.table-header {
  background: var(--color-bg-primary);
  border-radius: 12px 12px 0 0;
  padding: var(--space-lg);
  border: 1px solid var(--border-color);
  border-bottom: 2px solid var(--border-color);
}

.table-header h2 {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.5rem 0;
}

.table-stats {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.stat-separator {
  color: var(--border-color);
  font-weight: 300;
}

.stat-item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.stat-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 0.25rem;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
}

.stat-badge.success {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.stat-badge.error {
  background: var(--color-error-bg);
  color: var(--color-error);
}

/* Table Structure */
.validation-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: var(--color-bg-primary);
  border: 1px solid var(--border-color);
  border-top: none;
  border-radius: 0 0 12px 12px;
}

.validation-table thead {
  background: var(--color-bg-secondary);
}

.validation-table thead th {
  font-family: var(--font-heading);
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-tertiary);
  text-align: left;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
}

.validation-table thead th:first-child {
  width: 50px;
}

.validation-table thead th:last-child {
  width: 60px;
}

.validation-table thead th:nth-child(3) {
  width: 140px;
}

/* Table Rows */
.validation-table tbody tr {
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.15s ease;
}

.validation-table tbody tr:nth-child(even) {
  background: #fafbfc;
}

.validation-table tbody tr:hover {
  background: #f3f4f6;
}

.validation-table tbody tr.expanded {
  background: #fffbeb;
  border-left: 3px solid #fcd34d;
}

.validation-table tbody td {
  padding: 0.75rem 1rem;
  vertical-align: top;
}

/* Citation Number */
.citation-num {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
}

/* Citation Text */
.citation-text {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.citation-text.truncated {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.citation-text em {
  font-style: italic;
}

.source-type {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  margin-top: 0.5rem;
  font-style: italic;
}

/* Status Column */
.status-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.status-icon.success {
  background: var(--color-success-bg);
  color: var(--color-success);
  border: 1.5px solid var(--color-success-border);
}

.status-icon.error {
  background: var(--color-error-bg);
  color: var(--color-error);
  border: 1.5px solid var(--color-error-border);
}

.status-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

/* Actions Column */
.action-btn {
  background: none;
  border: none;
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
}

.action-btn svg {
  width: 20px;
  height: 20px;
}

/* Error Details */
.error-details {
  padding: 1rem;
  margin-top: 0.75rem;
  background: var(--color-error-bg);
  border-left: 3px solid var(--color-error);
  border-radius: 4px;
}

.error-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.error-item {
  margin-bottom: 1rem;
}

.error-item:last-child {
  margin-bottom: 0;
}

.error-component {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-error);
  margin-bottom: 0.25rem;
}

.error-problem {
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin-bottom: 0.25rem;
  padding-left: 1rem;
}

.error-correction {
  font-size: 0.8125rem;
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  background: rgba(255, 255, 255, 0.6);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  margin-top: 0.375rem;
}

.error-correction strong {
  color: var(--color-text-tertiary);
  font-weight: 500;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .table-header {
    padding: var(--space-md);
  }

  .validation-table thead {
    display: none;
  }

  .validation-table tbody tr {
    display: block;
    margin-bottom: var(--space-md);
    border: 1px solid var(--border-color);
    border-radius: 8px;
  }

  .validation-table tbody td {
    display: block;
    padding: var(--space-sm);
  }

  .validation-table tbody td:first-child::before {
    content: "Citation #";
    font-weight: 600;
    margin-right: 0.5rem;
  }
}
```

**Step 3: Verify component**

Create test file temporarily:

```bash
cat > frontend/frontend/src/components/ValidationTable.test.jsx << 'EOF'
import { render, screen } from '@testing-library/react'
import ValidationTable from './ValidationTable'

test('renders validation table', () => {
  const mockResults = [
    {
      citation_number: 1,
      original: 'Test citation',
      source_type: 'Journal Article',
      errors: []
    }
  ]
  render(<ValidationTable results={mockResults} />)
  expect(screen.getByText('Validation Results')).toBeInTheDocument()
})
EOF
npm test ValidationTable.test.jsx
```

**Step 4: Commit**

```bash
git add frontend/frontend/src/components/ValidationTable.jsx frontend/frontend/src/components/ValidationTable.css
git commit -m "feat: create ValidationTable component with expand/collapse"
```

---

### Task 4: Create ValidationLoadingState Component

**Files:**
- Create: `frontend/frontend/src/components/ValidationLoadingState.jsx`
- Create: `frontend/frontend/src/components/ValidationLoadingState.css`

**Step 1: Create ValidationLoadingState.jsx**

```jsx
import { useState, useEffect, useRef } from 'react'
import './ValidationLoadingState.css'

const STATUS_MESSAGES = [
  'Checking format...',
  'Verifying authors...',
  'Analyzing structure...',
  'Reviewing punctuation...',
  'Cross-referencing APA 7...'
]

function ValidationLoadingState({ submittedHtml }) {
  const [revealedLines, setRevealedLines] = useState([])
  const [currentStatusIndex, setCurrentStatusIndex] = useState(0)
  const [isRevealing, setIsRevealing] = useState(true)
  const timerRef = useRef(null)

  useEffect(() => {
    // Parse HTML and split by <p> tags
    const parser = new DOMParser()
    const doc = parser.parseFromString(submittedHtml, 'text/html')
    const paragraphs = Array.from(doc.querySelectorAll('p'))

    const lines = paragraphs
      .map(p => p.innerHTML)
      .filter(html => {
        // Filter out empty paragraphs
        const temp = document.createElement('div')
        temp.innerHTML = html
        return temp.textContent.trim().length > 0
      })

    // Progressive reveal
    let currentIndex = 0
    const revealNextLine = () => {
      if (currentIndex < lines.length) {
        setRevealedLines(prev => [...prev, {
          html: lines[currentIndex],
          number: prev.length + 1
        }])
        currentIndex++

        // Vary timing - slower on blank lines (already filtered), normal otherwise
        const delay = 250
        timerRef.current = setTimeout(revealNextLine, delay)
      } else {
        // All lines revealed, start rotating status messages
        setIsRevealing(false)
      }
    }

    revealNextLine()

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [submittedHtml])

  useEffect(() => {
    if (!isRevealing) {
      // Rotate status messages every 5 seconds
      const interval = setInterval(() => {
        setCurrentStatusIndex(prev => (prev + 1) % STATUS_MESSAGES.length)
      }, 5000)

      return () => clearInterval(interval)
    }
  }, [isRevealing])

  const currentStatus = isRevealing
    ? 'Analyzing...'
    : STATUS_MESSAGES[currentStatusIndex]

  return (
    <div className="validation-loading-container">
      <div className="table-header">
        <h2>Validation Results</h2>
        <div className="table-stats">
          <span className="processing-text">Processing citations...</span>
        </div>
      </div>

      <table className="validation-table loading">
        <thead>
          <tr>
            <th>#</th>
            <th>Citation</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {revealedLines.map((line, index) => (
            <tr key={index} className="loading-row" style={{ animationDelay: `${index * 0.1}s` }}>
              <td>
                <span className="citation-num">{line.number}</span>
              </td>
              <td>
                <div
                  className="citation-text"
                  dangerouslySetInnerHTML={{ __html: line.html }}
                />
              </td>
              <td>
                <div className="status-cell">
                  <div className="status-icon processing">
                    <div className="spinner" />
                  </div>
                  <span className="status-text processing">{currentStatus}</span>
                </div>
              </td>
              <td></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default ValidationLoadingState
```

**Step 2: Create ValidationLoadingState.css**

```css
.validation-loading-container {
  max-width: 1100px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.validation-table.loading {
  opacity: 1;
  animation: fadeIn 0.4s ease-in;
}

.processing-text {
  color: #6366f1;
  font-weight: 500;
}

/* Loading Row Animation */
.loading-row {
  animation: slideIn 0.3s ease-in;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Processing Status Icon */
.status-icon.processing {
  background: #eef2ff;
  color: #6366f1;
  border: 1.5px solid #6366f1;
  position: relative;
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #6366f1;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1.5s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.status-text.processing {
  color: #6366f1;
}

/* Fade out animation for transition */
.fade-out {
  animation: fadeOut 0.4s ease-out forwards;
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
```

**Step 3: Verify component**

Test manually by rendering with sample HTML:

```bash
npm run dev
```

**Step 4: Commit**

```bash
git add frontend/frontend/src/components/ValidationLoadingState.jsx frontend/frontend/src/components/ValidationLoadingState.css
git commit -m "feat: create ValidationLoadingState with progressive reveal"
```

---

### Task 5: Integrate Components into App.jsx

**Files:**
- Modify: `frontend/frontend/src/App.jsx:18-426`

**Step 1: Add imports at top of App.jsx**

Add after existing imports:

```jsx
import ValidationTable from './components/ValidationTable'
import ValidationLoadingState from './components/ValidationLoadingState'
```

**Step 2: Add submittedText state**

In AppContent function, add state after existing states:

```jsx
const [submittedText, setSubmittedText] = useState('')
```

**Step 3: Update handleSubmit to capture submitted HTML**

Find the `handleSubmit` function around line 125. Add after line 146 (after `const htmlContent = editor.getHTML()`):

```jsx
// Capture submitted text for loading state
setSubmittedText(htmlContent)
```

**Step 4: Replace results section**

Find the results section starting around line 345. Replace the entire section from `{results && (` through the closing `)}` (around lines 345-426) with:

```jsx
{loading && submittedText && (
  <ValidationLoadingState submittedHtml={submittedText} />
)}

{results && !loading && (
  results.isPartial ? (
    <PartialResults
      results={results.results}
      partial={results.partial}
      citations_checked={results.citations_checked}
      citations_remaining={results.citations_remaining}
      onUpgrade={() => {
        trackEvent('upgrade_modal_shown', { trigger: 'partial_results' })
        setShowUpgradeModal(true)
      }}
    />
  ) : (
    <ValidationTable results={results.results} />
  )
)}
```

**Step 5: Remove old results CSS**

Remove the old results CSS from App.css (lines 265-450 approximately). Keep everything else.

**Step 6: Test the integration**

Run: `npm run dev`
Test:
1. Paste citations
2. Click "Check My Citations"
3. Verify loading state appears with progressive reveal
4. Verify results table appears after response

**Step 7: Commit**

```bash
git add frontend/frontend/src/App.jsx frontend/frontend/src/App.css
git commit -m "feat: integrate ValidationTable and ValidationLoadingState into App"
```

---

## Phase 3: PartialResults Update

### Task 6: Update PartialResults to Use ValidationTable

**Files:**
- Modify: `frontend/frontend/src/components/PartialResults.jsx`

**Step 1: Import ValidationTable**

Add import at top:

```jsx
import ValidationTable from './ValidationTable'
```

**Step 2: Replace component implementation**

Replace the entire component (keep the function signature) with:

```jsx
function PartialResults({ results, citations_checked, citations_remaining, onUpgrade }) {
  return (
    <div className="partial-results-container">
      <ValidationTable results={results} />

      <div className="upgrade-banner">
        <div className="upgrade-content">
          <h3>🔒 {citations_remaining} more citation{citations_remaining > 1 ? 's' : ''} available</h3>
          <p>Upgrade to see validation results for all your citations</p>
          <button onClick={onUpgrade} className="upgrade-button">
            Upgrade Now
          </button>
        </div>
      </div>
    </div>
  )
}
```

**Step 3: Update PartialResults.css**

Replace existing styles with:

```css
.partial-results-container {
  max-width: 1100px;
  margin: 0 auto;
}

.upgrade-banner {
  max-width: 1100px;
  margin: var(--space-lg) auto;
  padding: 0 1rem;
}

.upgrade-content {
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  border: 2px solid var(--color-brand);
  border-radius: 12px;
  padding: var(--space-xl);
  text-align: center;
}

.upgrade-content h3 {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-sm) 0;
}

.upgrade-content p {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-lg) 0;
}

.upgrade-button {
  background: var(--color-brand);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.upgrade-button:hover {
  background: var(--color-brand-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(147, 51, 234, 0.3);
}
```

**Step 4: Test partial results**

This needs backend testing with credit limits. For now, verify it compiles:

Run: `npm run build`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/frontend/src/components/PartialResults.jsx frontend/frontend/src/components/PartialResults.css
git commit -m "feat: update PartialResults to use ValidationTable"
```

---

## Phase 4: Testing & Polish

### Task 7: Add Accessibility Features

**Files:**
- Modify: `frontend/frontend/src/components/ValidationTable.jsx`
- Modify: `frontend/frontend/src/components/ValidationLoadingState.jsx`

**Step 1: Add ARIA labels to ValidationTable**

In ValidationTable.jsx, update the table element:

```jsx
<table className="validation-table" role="table" aria-label="Citation validation results">
```

Update the action button:

```jsx
<button
  className="action-btn"
  onClick={() => toggleRow(result.citation_number)}
  aria-label={isExpanded ? `Collapse citation ${result.citation_number}` : `Expand citation ${result.citation_number}`}
  aria-expanded={isExpanded}
>
```

**Step 2: Add keyboard navigation**

Add onKeyDown handler to the same button:

```jsx
onKeyDown={(e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    toggleRow(result.citation_number)
  }
}}
```

**Step 3: Add aria-live to loading state**

In ValidationLoadingState.jsx, update the status cell:

```jsx
<div className="status-cell" aria-live="polite" aria-atomic="true">
  <div className="status-icon processing">
    <div className="spinner" />
  </div>
  <span className="status-text processing">{currentStatus}</span>
</div>
```

**Step 4: Test accessibility**

Test with keyboard:
1. Tab to expand/collapse buttons
2. Press Enter or Space to toggle
3. Verify screen reader announces changes

**Step 5: Commit**

```bash
git add frontend/frontend/src/components/ValidationTable.jsx frontend/frontend/src/components/ValidationLoadingState.jsx
git commit -m "feat: add accessibility features to validation components"
```

---

### Task 8: Add Error State Handling

**Files:**
- Modify: `frontend/frontend/src/App.jsx:339-343`

**Step 1: Update error styling to match design system**

The error message already uses the refined styling from Task 2. Verify it shows correctly.

**Step 2: Test error scenarios**

1. Backend not running - should show connection error
2. Invalid input - should show validation error
3. Verify error message appears below editor, above where table would be

**Step 3: Add fade-out for loading state on error**

In App.jsx handleSubmit catch block, before `setError(userMessage)`, add:

```jsx
// Fade out loading state if showing
if (loading) {
  const loadingEl = document.querySelector('.validation-loading-container')
  if (loadingEl) {
    loadingEl.classList.add('fade-out')
    await new Promise(resolve => setTimeout(resolve, 400))
  }
}
```

Make the function async if not already:

```jsx
const handleSubmit = async (e) => {
```

**Step 4: Commit**

```bash
git add frontend/frontend/src/App.jsx
git commit -m "feat: improve error state handling with smooth transitions"
```

---

### Task 9: Mobile Responsive Testing

**Files:**
- Modify: `frontend/frontend/src/components/ValidationTable.css`

**Step 1: Test mobile layout**

1. Run `npm run dev`
2. Open browser dev tools
3. Toggle device emulation (iPhone, iPad, etc.)
4. Test table displays as cards on mobile
5. Verify expand/collapse works
6. Check touch targets are large enough (44x44px minimum)

**Step 2: Adjust mobile styles if needed**

If any issues, update the `@media (max-width: 768px)` section in ValidationTable.css.

**Step 3: Test loading state on mobile**

Verify progressive reveal looks good on small screens.

**Step 4: Commit any fixes**

```bash
git add frontend/frontend/src/components/ValidationTable.css
git commit -m "fix: improve mobile responsive behavior"
```

---

### Task 10: Performance Optimization

**Files:**
- Modify: `frontend/frontend/src/components/ValidationLoadingState.jsx`

**Step 1: Add cleanup to prevent memory leaks**

The current implementation already has cleanup in useEffect. Verify:

```jsx
return () => {
  if (timerRef.current) {
    clearTimeout(timerRef.current)
  }
}
```

**Step 2: Test with many citations**

Create a test with 20+ citations:
1. Paste 20 citations
2. Submit
3. Watch loading state
4. Verify no lag or memory issues

**Step 3: Optimize if needed**

If performance issues, consider:
- Reduce animation complexity
- Increase reveal delay slightly
- Use CSS animations instead of JS where possible

**Step 4: Commit optimizations**

```bash
git add frontend/frontend/src/components/ValidationLoadingState.jsx
git commit -m "perf: optimize loading state for many citations"
```

---

## Phase 5: Documentation & Deployment

### Task 11: Update Component Documentation

**Files:**
- Create: `frontend/frontend/src/components/README.md`

**Step 1: Document ValidationTable**

```markdown
# Validation Components

## ValidationTable

Displays citation validation results in a scannable table format.

**Props:**
- `results` (array): Validation results from API
  - Each result: `{ citation_number, original, source_type, errors }`

**Features:**
- Valid citations collapsed by default (first 80 chars shown)
- Invalid citations expanded by default with error details
- Click row or chevron to expand/collapse
- Alternating row backgrounds for scannability
- Amber highlighting for error rows

**Usage:**
```jsx
<ValidationTable results={validationResults} />
```

## ValidationLoadingState

Progressive loading state during 45-60s validation wait.

**Props:**
- `submittedHtml` (string): HTML from TipTap editor

**Features:**
- Splits HTML by `<p>` tags (newlines)
- Reveals one line every 250ms
- After all revealed, rotates status messages every 5s
- Preserves italics formatting

**Usage:**
```jsx
<ValidationLoadingState submittedHtml={editor.getHTML()} />
```
```

**Step 2: Commit documentation**

```bash
git add frontend/frontend/src/components/README.md
git commit -m "docs: add documentation for validation components"
```

---

### Task 12: Update Main README

**Files:**
- Modify: `README.md` (if exists at project root)

**Step 1: Add UX improvements section**

Add section documenting the validation UX:

```markdown
## Validation UX

The citation validation interface uses a progressive loading pattern to improve perceived performance during GPT-5-mini's 45-60s validation time:

1. **Progressive reveal** (0-10s): Submitted citations appear line-by-line
2. **Rotating status** (10-60s): Status messages cycle ("Checking format...", etc.)
3. **Table results**: Scannable table with expandable error details

See `docs/plans/2025-11-19-validation-latency-ux-design.md` for full design spec.
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document validation UX improvements"
```

---

### Task 13: Final Testing & Deployment

**Files:**
- N/A (testing only)

**Step 1: Run full test suite**

```bash
cd frontend/frontend
npm test
```

Expected: All tests pass

**Step 2: Build production bundle**

```bash
npm run build
```

Expected: No errors, builds successfully

**Step 3: Test production build locally**

```bash
npm run preview
```

Test full flow:
1. Submit citations
2. Watch loading state
3. View results table
4. Expand/collapse citations
5. Test mobile view

**Step 4: Deploy to production**

Follow project deployment process:

```bash
# Example - adjust for your deployment
cd /opt/citations
./deployment/scripts/deploy.sh
```

**Step 5: Verify production**

1. Visit production URL
2. Test validation flow end-to-end
3. Check mobile responsiveness
4. Verify no console errors

**Step 6: Final commit**

```bash
git add .
git commit -m "chore: final testing and deployment verification"
```

---

## Future Enhancements

### Task 14 (Future): MiniChecker UX Improvement

**This should be a separate beads epic/issue created after main work is complete.**

Apply the same design improvements to MiniChecker:
- Progressive loading state
- Table format for multiple citations (currently only shows first)
- Refined design system colors/typography
- Consider adding credit integration

---

## Summary

**Total Tasks:** 13 main implementation tasks + 1 future enhancement

**Estimated Timeline:** 2-3 days for experienced developer

**Key Technologies:** React 18, TipTap, CSS custom properties

**Testing Strategy:** Manual testing for UI/UX, accessibility testing with keyboard/screen reader

**Success Criteria:**
- ✅ Loading state shows progressive reveal
- ✅ Status messages rotate after reveal complete
- ✅ Results display in scannable table
- ✅ Error citations expanded by default
- ✅ Smooth fade transition between states
- ✅ Mobile responsive
- ✅ Accessible (keyboard nav, ARIA labels)
