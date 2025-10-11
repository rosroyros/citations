import { useState } from 'react'
import './App.css'

function App() {
  const [citations, setCitations] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()

    console.log('Form submitted with citations:', citations)

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
          citations: citations,
          style: 'apa7',
        }),
      })

      console.log('API response status:', response.status)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Validation failed')
      }

      const data = await response.json()
      console.log('API response data:', data)

      setResults(data)
    } catch (err) {
      console.error('API call error:', err)
      setError(err.message)
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
          <label htmlFor="citations">Enter citations (one per line):</label>
          <textarea
            id="citations"
            value={citations}
            onChange={(e) => setCitations(e.target.value)}
            rows={10}
            placeholder="Paste your citations here..."
            disabled={loading}
          />
        </div>

        <button type="submit" disabled={loading || !citations.trim()}>
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
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default App
