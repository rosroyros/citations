import { useState } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import './App.css'

function App() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
    ],
    content: '<p>Paste your citations here...</p>',
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
      <h1>Citation Validator</h1>
      <p>Validate your APA 7th edition citations</p>

      <form onSubmit={handleSubmit}>
        <div>
          <label>Enter citations (formatting preserved):</label>
          <EditorContent editor={editor} />
        </div>

        <button type="submit" disabled={loading || !editor || editor.isEmpty}>
          {loading ? 'Validating...' : 'Validate Citations'}
        </button>
      </form>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {results && (
        <div className="results">
          <h2>Validation Results</h2>
          {results.results.map((result) => (
            <div key={result.citation_number} className="citation-result">
              <h3>
                Citation #{result.citation_number}
                {result.errors.length === 0 ? ' ✅' : ' ❌'}
              </h3>

              <div className="original-citation">
                <strong>Original:</strong>
                <p>{result.original}</p>
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
    </div>
  )
}

export default App
