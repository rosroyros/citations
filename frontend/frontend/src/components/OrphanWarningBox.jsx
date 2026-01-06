import './OrphanWarningBox.css'
import { trackOrphanClick } from '../utils/analytics'

function OrphanWarningBox({ orphans }) {
  if (!orphans || orphans.length === 0) return null

  return (
    <div className="orphan-warning-box" data-testid="orphan-warning">
      <div className="orphan-header">
        <span className="warning-icon">⚠️</span>
        <strong>{orphans.length} Citation{orphans.length > 1 ? 's' : ''} Missing from References</strong>
      </div>
      <ul className="orphan-list">
        {orphans.map(orphan => (
          <li
            key={orphan.id}
            onClick={() => trackOrphanClick(orphan.citation_text)}
            style={{ cursor: 'pointer' }}
          >
            <code>{orphan.citation_text}</code>
            <span className="orphan-count">cited {orphan.citation_count}×</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default OrphanWarningBox
