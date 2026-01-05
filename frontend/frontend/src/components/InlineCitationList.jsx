import './InlineCitationList.css'

function InlineCitationList({ citations, refIndex }) {
  if (!citations || citations.length === 0) return null

  return (
    <div className="inline-citation-list" data-testid={`inline-list-${refIndex}`}>
      <div className="inline-header">
        📍 Cited {citations.length}× in document
      </div>
      <ul className="inline-items">
        {citations.map(cite => (
          <li key={cite.id} className={`inline-item status-${cite.match_status}`}>
            <code>{cite.citation_text}</code>

            {cite.match_status === 'matched' && (
              <span className="status-icon matched">✓</span>
            )}

            {cite.match_status === 'mismatch' && (
              <div className="mismatch-details">
                <span className="status-icon mismatch">⚠️</span>
                <span className="mismatch-reason">{cite.mismatch_reason}</span>
                {cite.suggested_correction && (
                  <span className="correction">
                    → Should be: <code>{cite.suggested_correction}</code>
                  </span>
                )}
              </div>
            )}

            {cite.match_status === 'ambiguous' && (
              <div className="ambiguous-details">
                <span className="status-icon ambiguous">❓</span>
                <span className="ambiguous-note">Matches multiple references</span>
                {cite.suggested_correction && (
                  <span className="correction">{cite.suggested_correction}</span>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default InlineCitationList
