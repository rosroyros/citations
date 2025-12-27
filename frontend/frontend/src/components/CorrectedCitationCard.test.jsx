import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import CorrectedCitationCard from './CorrectedCitationCard'
import * as analytics from '../utils/analytics'

// Mock analytics
vi.mock('../utils/analytics', () => ({
    trackEvent: vi.fn()
}))

describe('CorrectedCitationCard', () => {
    const defaultProps = {
        correctedCitation: 'Smith, J. (2023). <em>Test Citation</em>. Journal.',
        citationNumber: 1,
        sourceType: 'journal',
        jobId: 'job-123'
    }

    beforeEach(() => {
        vi.clearAllMocks()
        vi.useFakeTimers()

        // Mock clipboard
        Object.assign(navigator, {
            clipboard: {
                write: vi.fn().mockResolvedValue(),
                writeText: vi.fn().mockResolvedValue()
            }
        })

        // Mock ClipboardItem
        global.ClipboardItem = vi.fn()
    })

    afterEach(() => {
        vi.useRealTimers()
    })

    it('renders correctly with corrected citation', () => {
        render(<CorrectedCitationCard {...defaultProps} />)
        expect(screen.getByText('✓ CORRECTED')).toBeTruthy()
        expect(screen.getByText('Test Citation')).toBeTruthy() // checking part of HTML
        expect(screen.getByText('Copy')).toBeTruthy()
    })

    it('does not render if correctedCitation is missing', () => {
        const { container } = render(<CorrectedCitationCard {...defaultProps} correctedCitation={null} />)
        expect(container.firstChild).toBeNull()
    })

    it('copies to clipboard on button click (using rich text)', async () => {
        render(<CorrectedCitationCard {...defaultProps} />)

        const copyButton = screen.getByText('Copy')
        await act(async () => {
            fireEvent.click(copyButton)
        })

        expect(global.ClipboardItem).toHaveBeenCalled()
        expect(navigator.clipboard.write).toHaveBeenCalled()

        // Verify analytics
        expect(analytics.trackEvent).toHaveBeenCalledWith('correction_copied', {
            job_id: 'job-123',
            citation_number: 1,
            source_type: 'journal'
        })

        // Verify visual feedback
        expect(screen.getByText('Copied')).toBeTruthy()

        // Verify feedback timeout
        act(() => {
            vi.advanceTimersByTime(2000)
        })
        expect(screen.getByText('Copy')).toBeTruthy()
    })

    it('falls back to plain text if rich copy fails', async () => {
        // Mock rich copy failure
        global.ClipboardItem = undefined // Simulate not supported

        render(<CorrectedCitationCard {...defaultProps} />)

        const copyButton = screen.getByText('Copy')
        await act(async () => {
            fireEvent.click(copyButton)
        })

        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
            expect.stringContaining('Smith, J. (2023). Test Citation. Journal.')
        )
        expect(screen.getByText('Copied')).toBeTruthy()
    })

    it('copies when clicking the citation text', async () => {
        render(<CorrectedCitationCard {...defaultProps} />)

        const citationText = screen.getByText('Test Citation').closest('.citation-content')
        await act(async () => {
            fireEvent.click(citationText)
        })

        expect(navigator.clipboard.write).toHaveBeenCalled()
        expect(screen.getByText('Copied')).toBeTruthy()
    })

    it('handles keyboard activation (Enter key)', async () => {
        render(<CorrectedCitationCard {...defaultProps} />)

        const citationText = screen.getByText('Test Citation').closest('.citation-content')
        await act(async () => {
            fireEvent.keyDown(citationText, { key: 'Enter' })
        })

        expect(navigator.clipboard.write).toHaveBeenCalled()
        expect(screen.getByText('Copied')).toBeTruthy()
    })
})
