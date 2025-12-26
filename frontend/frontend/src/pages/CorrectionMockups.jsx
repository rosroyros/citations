import React, { useState } from 'react';
import '../components/ValidationTable.css';

// Mock data for demonstration
const mockCitation = {
    citation_number: 1,
    original: 'Smith, J. (2023). The impact of climate change on biodiversity. <em>Nature Journal</em>, 45(2), 123-145.',
    source_type: 'journal article',
    errors: [
        {
            component: 'Volume/Issue',
            problem: 'Issue number should not be included when pagination is continuous',
            correction: '<em>Nature Journal</em>, 45, 123-145'
        },
        {
            component: 'DOI',
            problem: 'Missing DOI or URL',
            correction: 'Add https://doi.org/xxx or Retrieved from URL'
        }
    ],
    corrected_citation: 'Smith, J. (2023). The impact of climate change on biodiversity. <em>Nature Journal</em>, 45, 123-145. https://doi.org/10.1000/example'
};

const mockCitationPerfect = {
    citation_number: 2,
    original: 'Johnson, A. B., & Williams, C. D. (2022). Understanding human behavior. <em>Psychology Today</em>, 12, 50-75. https://doi.org/10.1000/psych',
    source_type: 'journal article',
    errors: [],
    corrected_citation: null
};

// Copy to clipboard with rich text support
const copyToClipboard = async (html, plainText) => {
    try {
        const blob = new Blob([html], { type: 'text/html' });
        const plainBlob = new Blob([plainText], { type: 'text/plain' });
        await navigator.clipboard.write([
            new ClipboardItem({
                'text/html': blob,
                'text/plain': plainBlob
            })
        ]);
        return true;
    } catch (err) {
        await navigator.clipboard.writeText(plainText);
        return true;
    }
};

const stripHtml = (html) => {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    return doc.body.textContent || '';
};

/* ============================================
   REFINED COPY BUTTON COMPONENT
   Uses app design system colors:
   - --color-success: #047857
   - --color-success-bg: #ecfdf5  
   - --color-success-border: #a7f3d0
   ============================================ */
function CopyButton({ onClick, copied }) {
    const baseStyles = {
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.375rem',
        padding: '0.375rem 0.625rem',
        borderRadius: '4px',
        fontSize: '0.75rem',
        fontWeight: '500',
        fontFamily: 'var(--font-mono, ui-monospace, monospace)',
        transition: 'all 0.15s ease',
        color: copied ? '#047857' : '#718096',
    };

    const hoverStyles = {
        background: copied ? 'var(--color-success-bg, #ecfdf5)' : '#f3f4f6',
    };

    return (
        <button
            onClick={onClick}
            style={baseStyles}
            onMouseEnter={(e) => {
                e.target.style.background = hoverStyles.background;
                if (!copied) e.target.style.color = '#047857';
            }}
            onMouseLeave={(e) => {
                e.target.style.background = 'none';
                if (!copied) e.target.style.color = '#718096';
            }}
            title={copied ? 'Copied to clipboard!' : 'Copy corrected citation'}
        >
            {copied ? (
                <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
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
    );
}

function CorrectionMockups() {
    const [copiedId, setCopiedId] = useState(null);

    const handleCopy = async (id, html) => {
        const success = await copyToClipboard(html, stripHtml(html));
        if (success) {
            setCopiedId(id);
            setTimeout(() => setCopiedId(null), 2000);
        }
    };

    return (
        <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', background: 'var(--gradient-bg, #f9fafb)', minHeight: '100vh' }}>
            <h1 style={{ marginBottom: '0.5rem', color: 'var(--color-text-primary, #1a1f36)' }}>Corrected Citation - Refined Mockup</h1>
            <p style={{ marginBottom: '2rem', color: 'var(--color-text-secondary, #4a5568)' }}>
                Option 4: Prominent card at top with sleek copy button using app design system.
            </p>

            {/* ============================================ */}
            {/* FINAL DESIGN: Prominent Card at Top */}
            {/* ============================================ */}
            <section style={{ marginBottom: '3rem' }}>
                <h2 style={{
                    background: 'var(--color-brand, #9333ea)',
                    color: 'white',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px 8px 0 0',
                    margin: 0,
                    fontWeight: '600',
                    fontSize: '1rem'
                }}>
                    Final Design Specification
                </h2>

                <div className="validation-table-container" style={{ background: 'white', borderRadius: '0 0 8px 8px', padding: '1rem' }}>
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
                            {/* Row with errors - expanded */}
                            <tr className="expanded has-errors">
                                <td><span className="citation-num">1</span></td>
                                <td>
                                    <div className="citation-text" dangerouslySetInnerHTML={{ __html: mockCitation.original }} />
                                    <div className="source-type">{mockCitation.source_type}</div>

                                    {/* === CORRECTED CITATION CARD === */}
                                    {/* Uses app CSS variables for consistency */}
                                    <div style={{
                                        marginTop: '1rem',
                                        padding: '0.875rem 1rem',
                                        background: 'var(--color-success-bg, #ecfdf5)',
                                        borderRadius: '6px',
                                        border: '1px solid var(--color-success-border, #a7f3d0)',
                                        borderLeft: '3px solid var(--color-success, #047857)'
                                    }}>
                                        <div style={{
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                            marginBottom: '0.5rem'
                                        }}>
                                            <span style={{
                                                fontWeight: '600',
                                                color: 'var(--color-success, #047857)',
                                                fontSize: '0.8125rem',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '0.375rem',
                                                textTransform: 'uppercase',
                                                letterSpacing: '0.03em'
                                            }}>
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                    <polyline points="20 6 9 17 4 12"></polyline>
                                                </svg>
                                                Corrected
                                            </span>
                                            <CopyButton
                                                onClick={() => handleCopy('final-1', mockCitation.corrected_citation)}
                                                copied={copiedId === 'final-1'}
                                            />
                                        </div>
                                        <div style={{
                                            fontFamily: 'var(--font-mono, ui-monospace, monospace)',
                                            fontSize: '0.875rem',
                                            lineHeight: '1.6',
                                            color: 'var(--color-text-primary, #1a1f36)',
                                            background: 'rgba(255, 255, 255, 0.7)',
                                            padding: '0.625rem 0.75rem',
                                            borderRadius: '4px'
                                        }} dangerouslySetInnerHTML={{ __html: mockCitation.corrected_citation }} />
                                    </div>

                                    {/* Error details below */}
                                    <div className="error-details" style={{ marginTop: '0.75rem' }}>
                                        <div style={{
                                            fontSize: '0.6875rem',
                                            fontWeight: '600',
                                            color: 'var(--color-text-tertiary, #718096)',
                                            textTransform: 'uppercase',
                                            letterSpacing: '0.05em',
                                            marginBottom: '0.625rem'
                                        }}>
                                            Issues Found ({mockCitation.errors.length})
                                        </div>
                                        <ul className="error-list">
                                            {mockCitation.errors.map((error, index) => (
                                                <li key={index} className="error-item">
                                                    <div className="error-component">{error.component}</div>
                                                    <div className="error-problem">{error.problem}</div>
                                                    <div className="error-correction">
                                                        <strong>Should be:</strong> <span dangerouslySetInnerHTML={{ __html: error.correction }} />
                                                    </div>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </td>
                                <td>
                                    <div className="status-cell">
                                        <div className="status-icon error">✗</div>
                                        <span className="status-text">2 issues</span>
                                    </div>
                                </td>
                                <td>
                                    <button className="action-btn">
                                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
                                        </svg>
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            {/* ============================================ */}
            {/* PERFECT CITATION (no errors) */}
            {/* ============================================ */}
            <section style={{ marginBottom: '3rem' }}>
                <h2 style={{
                    background: 'var(--color-success, #047857)',
                    color: 'white',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px 8px 0 0',
                    margin: 0,
                    fontWeight: '600',
                    fontSize: '1rem'
                }}>
                    Perfect Citation (No Correction Needed)
                </h2>

                <div className="validation-table-container" style={{ background: 'white', borderRadius: '0 0 8px 8px', padding: '1rem' }}>
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
                            <tr>
                                <td><span className="citation-num">2</span></td>
                                <td>
                                    <div className="citation-text" dangerouslySetInnerHTML={{ __html: mockCitationPerfect.original }} />
                                    <div className="source-type">{mockCitationPerfect.source_type}</div>
                                </td>
                                <td>
                                    <div className="status-cell">
                                        <div className="status-icon success">✓</div>
                                        <span className="status-text">Perfect</span>
                                    </div>
                                </td>
                                <td>
                                    <button className="action-btn">
                                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            {/* ============================================ */}
            {/* UI SPECIFICATIONS */}
            {/* ============================================ */}
            <section style={{
                background: 'white',
                borderRadius: '8px',
                border: '1px solid var(--border-color, #e5e7eb)',
                overflow: 'hidden'
            }}>
                <h2 style={{
                    background: 'var(--color-bg-secondary, #fafbfc)',
                    color: 'var(--color-text-primary, #1a1f36)',
                    padding: '0.75rem 1rem',
                    margin: 0,
                    fontWeight: '600',
                    fontSize: '1rem',
                    borderBottom: '1px solid var(--border-color, #e5e7eb)'
                }}>
                    📋 UI Specifications for Implementation Plan
                </h2>

                <div style={{ padding: '1.5rem' }}>
                    <h3 style={{ color: 'var(--color-text-primary)', fontSize: '0.9375rem', marginBottom: '0.75rem' }}>Corrected Citation Card</h3>
                    <table style={{ width: '100%', fontSize: '0.8125rem', borderCollapse: 'collapse', marginBottom: '1.5rem' }}>
                        <tbody>
                            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280', width: '140px' }}>Background</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>var(--color-success-bg) = #ecfdf5</td>
                            </tr>
                            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280' }}>Border</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>1px solid var(--color-success-border) = #a7f3d0</td>
                            </tr>
                            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280' }}>Left Accent</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>3px solid var(--color-success) = #047857</td>
                            </tr>
                            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280' }}>Border Radius</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>6px</td>
                            </tr>
                            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280' }}>Padding</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>0.875rem 1rem</td>
                            </tr>
                            <tr>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280' }}>Margin Top</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>1rem (above error-details)</td>
                            </tr>
                        </tbody>
                    </table>

                    <h3 style={{ color: 'var(--color-text-primary)', fontSize: '0.9375rem', marginBottom: '0.75rem' }}>Copy Button</h3>
                    <table style={{ width: '100%', fontSize: '0.8125rem', borderCollapse: 'collapse', marginBottom: '1.5rem' }}>
                        <tbody>
                            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280', width: '140px' }}>Style</td>
                                <td style={{ padding: '0.5rem 0' }}>Ghost button (no background, icon + text)</td>
                            </tr>
                            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280' }}>Default Color</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>#718096 (tertiary)</td>
                            </tr>
                            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280' }}>Hover Color</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>#047857 (success) + #f3f4f6 bg</td>
                            </tr>
                            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280' }}>Copied State</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>#047857 + checkmark icon + "Copied" text</td>
                            </tr>
                            <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280' }}>Icon Size</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>14px × 14px</td>
                            </tr>
                            <tr>
                                <td style={{ padding: '0.5rem 0', fontWeight: '500', color: '#6b7280' }}>Font</td>
                                <td style={{ padding: '0.5rem 0', fontFamily: 'monospace' }}>0.75rem, font-weight: 500, font-mono</td>
                            </tr>
                        </tbody>
                    </table>

                    <h3 style={{ color: 'var(--color-text-primary)', fontSize: '0.9375rem', marginBottom: '0.75rem' }}>Analytics Events</h3>
                    <div style={{
                        background: 'var(--color-bg-secondary, #fafbfc)',
                        padding: '0.75rem 1rem',
                        borderRadius: '4px',
                        fontFamily: 'monospace',
                        fontSize: '0.8125rem',
                        lineHeight: 1.7
                    }}>
                        <div><strong>Event:</strong> correction_copied</div>
                        <div><strong>Properties:</strong> job_id, citation_number, source_type</div>
                    </div>

                    <h3 style={{ color: 'var(--color-text-primary)', fontSize: '0.9375rem', marginTop: '1.5rem', marginBottom: '0.75rem' }}>Dashboard Enhancements</h3>
                    <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8125rem', lineHeight: 1.8, color: 'var(--color-text-secondary)' }}>
                        <li>Add <code>corrections_copied</code> column (count of copies per job)</li>
                        <li>Add citation results column: <span style={{ color: '#047857', fontWeight: 600 }}>X</span> / <span style={{ color: '#b45309', fontWeight: 600 }}>Y</span> format (valid/invalid)</li>
                    </ul>
                </div>
            </section>
        </div>
    );
}

export default CorrectionMockups;
