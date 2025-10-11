import { useState } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Placeholder from '@tiptap/extension-placeholder'
import './App.css'

function App() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Placeholder.configure({
        placeholder: `Example:

Smith, J., & Jones, M. (2023). Understanding research methods. Journal of Academic Studies, 45(2), 123-145. https://doi.org/10.1234/example

Brown, A. (2022). Writing in APA style. Academic Press.`,
      }),
    ],
    editorProps: {
      attributes: {
        class: 'citation-editor',
      },
    },
  })

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!editor) return

    const htmlContent = editor.getHTML()
    const textContent = editor.getText()

    console.log('Form submitted with citations:', textContent)
    console.log('HTML content:', htmlContent)

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      console.log('Calling API: http://localhost:8000/api/validate')

      const response = await fetch('http://localhost:8000/api/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          citations: htmlContent,
          style: 'apa7',
        }),
      })

      console.log('API response status:', response.status)

      if (!response.ok) {
        const errorData = await response.json()
        // FastAPI uses 'detail', but support both 'detail' and 'error' keys
        throw new Error(errorData.detail || errorData.error || 'Validation failed')
      }

      const data = await response.json()
      console.log('API response data:', data)

      setResults(data)
    } catch (err) {
      console.error('API call error:', err)

      // User-friendly error messages
      let userMessage = err.message
      if (err.message.includes('fetch')) {
        userMessage = 'Unable to connect to the validation service. Please check if the backend is running.'
      } else if (err.message.includes('Network')) {
        userMessage = 'Network error occurred. Please check your connection and try again.'
      }

      console.log('Displaying user-facing error:', userMessage)
      setError(userMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <svg className="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" fill="currentColor"/>
              <path d="M7 12L10.5 15.5L17 9" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <h1 className="logo-text">Citation Format Checker</h1>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h2 className="hero-title">
            Stop spending 5 minutes fixing every citation
          </h2>
          <p className="hero-subtitle">
            Citation generators create errors. We catch them. Get instant validation for your APA references and save hours of manual checking.
          </p>
          <div className="hero-stat">
            <span className="stat-icon">⚠️</span>
            <span className="stat-text">90.9% of papers contain formatting errors</span>
          </div>
        </div>
      </section>

      {/* Input Section */}
      <section className="input-section">
        <form onSubmit={handleSubmit}>
          <div>
            <label>Paste your citations below (APA 7th edition)</label>
            <EditorContent editor={editor} />
            <p className="input-helper">
              Paste one or multiple citations. We'll check each one.
            </p>
          </div>

          <button type="submit" disabled={loading || !editor || editor.isEmpty}>
            {loading ? 'Validating...' : 'Check My Citations'}
          </button>

          {/* Feature Pills */}
          <div className="feature-pills">
            <span className="feature-pill">✓ Capitalization check</span>
            <span className="feature-pill">✓ Italics validation</span>
            <span className="feature-pill">✓ DOI formatting</span>
            <span className="feature-pill">✓ Punctuation rules</span>
          </div>
        </form>
      </section>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {results && (
        <div className="results">
          <div className="results-summary">
            <h2>Validation Results</h2>
            <div className="summary-stats">
              <div className="summary-stat">
                <span className="stat-number">{results.results.length}</span>
                <span className="stat-label">Citations Checked</span>
              </div>
              <div className="summary-stat">
                <span className="stat-number">
                  {results.results.filter(r => r.errors.length === 0).length}
                </span>
                <span className="stat-label">Perfect</span>
              </div>
              <div className="summary-stat">
                <span className="stat-number">
                  {results.results.filter(r => r.errors.length > 0).length}
                </span>
                <span className="stat-label">Need Fixes</span>
              </div>
            </div>
          </div>

          {results.results.map((result) => (
            <div key={result.citation_number} className="citation-result">
              <h3>
                Citation #{result.citation_number}
                {result.errors.length === 0 ? ' ✅' : ' ❌'}
              </h3>

              <div className="original-citation">
                <strong>Original:</strong>
                <div
                  className="citation-html"
                  dangerouslySetInnerHTML={{ __html: result.original }}
                />
              </div>

              <div className="source-type">
                <em>Source type: {result.source_type}</em>
              </div>

              {result.errors.length === 0 ? (
                <div className="no-errors">
                  <p>✅ No errors found - this citation follows APA 7th edition guidelines!</p>
                </div>
              ) : (
                <div className="errors-list">
                  <strong>Errors found:</strong>
                  {result.errors.map((error, index) => (
                    <div key={index} className="error-item">
                      <div className="error-component">
                        <strong>❌ {error.component}:</strong>
                      </div>
                      <div className="error-problem">
                        <em>Problem:</em> {error.problem}
                      </div>
                      <div className="error-correction">
                        <em>Correction:</em> {error.correction}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Benefits Section */}
      <section className="benefits">
        <div className="benefits-content">
          <h3 className="benefits-title">Why students choose Citation Format Checker</h3>
          <div className="benefits-grid">
            <div className="benefit-card">
              <div className="benefit-icon">⚡</div>
              <h4 className="benefit-title">Save hours</h4>
              <p className="benefit-text">
                Stop manually checking every citation. Get instant validation in seconds.
              </p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">🎯</div>
              <h4 className="benefit-title">Catch generator errors</h4>
              <p className="benefit-text">
                EasyBib, Zotero, and others make mistakes. We find them before your professor does.
              </p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">✅</div>
              <h4 className="benefit-title">Never lose points</h4>
              <p className="benefit-text">
                Submit with confidence. No more losing grades on formatting mistakes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <p className="footer-text">© 2025 Citation Format Checker. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

export default App
