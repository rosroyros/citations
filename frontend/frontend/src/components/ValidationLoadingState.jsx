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
