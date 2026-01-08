import { useState } from 'react'
import './OrphanWarningBox.css'
import { trackOrphanClick } from '../utils/analytics'

// Show this many orphans by default before collapsing
const INITIAL_DISPLAY_COUNT = 3

function OrphanWarningBox({ orphans }) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!orphans || orphans.length === 0) return null

  const hasMany = orphans.length > INITIAL_DISPLAY_COUNT
  const displayedOrphans = hasMany && !isExpanded
    ? orphans.slice(0, INITIAL_DISPLAY_COUNT)
    : orphans
  const hiddenCount = orphans.length - INITIAL_DISPLAY_COUNT

  return (
    <div className="orphan-warning-box" data-testid="orphan-warning">
      <div className="orphan-header">
        <span className="warning-icon">⚠️</span>
        <strong>{orphans.length} Citation{orphans.length > 1 ? 's' : ''} Missing from References</strong>
      </div>
      <ul className="orphan-list">
        {displayedOrphans.map(orphan => (
          <li
            key={orphan.id}
            onClick={() => trackOrphanClick(orphan.citation_text)}
            style={{ cursor: 'pointer' }}
          >
            <code>{orphan.citation_text}</code>
            {orphan.citation_count && (
              <span className="orphan-count">cited {orphan.citation_count}×</span>
            )}
          </li>
        ))}
      </ul>
      {hasMany && (
        <button
          className="orphan-toggle-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
        >
          {isExpanded ? 'Show less' : `Show ${hiddenCount} more...`}
        </button>
      )}
    </div>
  )
}

export default OrphanWarningBox
