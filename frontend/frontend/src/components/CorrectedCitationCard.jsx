import { useState, useEffect } from 'react'
import { trackEvent } from '../utils/analytics'
import './ValidationTable.css' // Using shared styles as per plan

const CorrectedCitationCard = ({
    correctedCitation,
    citationNumber,
    sourceType,
    jobId
}) => {
    const [isCopied, setIsCopied] = useState(false)

    useEffect(() => {
        let timeout
        if (isCopied) {
            timeout = setTimeout(() => {
                setIsCopied(false)
            }, 2000)
        }
        return () => clearTimeout(timeout)
    }, [isCopied])

    const handleCopy = async () => {
        if (!correctedCitation) return

        // Strip HTML tags for plain text fallback
        const plainText = correctedCitation.replace(/<[^>]*>/g, '')

        try {
            // Try rich text copy first using ClipboardItem
            // This is necessary for preserving italics/bold in Word/Docs
            if (typeof ClipboardItem !== 'undefined') {
                const htmlBlob = new Blob([correctedCitation], { type: 'text/html' })
                const textBlob = new Blob([plainText], { type: 'text/plain' })
                const data = [new ClipboardItem({
                    'text/html': htmlBlob,
                    'text/plain': textBlob
                })]
                await navigator.clipboard.write(data)
            } else {
                throw new Error('ClipboardItem not supported')
            }
        } catch (err) {
            // Fallback to plain text if rich copy fails or not supported
            try {
                await navigator.clipboard.writeText(plainText)
            } catch (fallbackErr) {
                console.error('Copy failed:', fallbackErr)
                return // Don't show copied state if both fail
            }
        }

        setIsCopied(true)
        trackEvent('correction_copied', {
            job_id: jobId,
            citation_number: citationNumber,
            source_type: sourceType
        })

        // Log to backend for dashboard (fire-and-forget, GA is primary)
        fetch('/api/correction-event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'copied',
                job_id: jobId,
                citation_number: citationNumber,
                source_type: sourceType
            })
        }).catch(() => { })
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            handleCopy()
        }
    }

    if (!correctedCitation) return null

    return (
        <div className="corrected-citation-card">
            <div className="card-header">
                <span className="citation-label">✓ CORRECTED</span>
                <button
                    className={`copy-btn ${isCopied ? 'copied' : ''}`}
                    onClick={handleCopy}
                    aria-label={isCopied ? "Citation copied" : "Copy corrected citation"}
                    type="button"
                >
                    {isCopied ? (
                        <>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                            <span>Copied</span>
                        </>
                    ) : (
                        <>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                            <span>Copy</span>
                        </>
                    )}
                </button>
            </div>
            <div
                className="citation-content clickable"
                onClick={handleCopy}
                role="button"
                tabIndex={0}
                onKeyDown={handleKeyDown}
                title="Click to copy"
                dangerouslySetInnerHTML={{ __html: correctedCitation }}
            />
        </div>
    )
}

export default CorrectedCitationCard
