import { render, screen } from '@testing-library/react'
import InlineCitationList from './InlineCitationList'

describe('InlineCitationList', () => {
  it('renders nothing when citations is null', () => {
    const { container } = render(<InlineCitationList citations={null} refIndex={0} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when citations is empty', () => {
    const { container } = render(<InlineCitationList citations={[]} refIndex={0} />)
    expect(container.firstChild).toBeNull()
  })

  it('shows citation count in header', () => {
    const citations = [
      { id: 'c1', citation_text: '(Smith, 2019)', match_status: 'matched' },
      { id: 'c2', citation_text: '(Smith, 2019)', match_status: 'matched' }
    ]
    render(<InlineCitationList citations={citations} refIndex={0} />)

    expect(screen.getByText(/Cited 2× in document/)).toBeInTheDocument()
  })

  it('shows single citation count', () => {
    const citations = [
      { id: 'c1', citation_text: '(Smith, 2019)', match_status: 'matched' }
    ]
    render(<InlineCitationList citations={citations} refIndex={0} />)

    expect(screen.getByText(/Cited 1× in document/)).toBeInTheDocument()
  })

  it('renders matched citation with checkmark', () => {
    const citations = [
      { id: 'c1', citation_text: '(Smith, 2019)', match_status: 'matched' }
    ]
    render(<InlineCitationList citations={citations} refIndex={0} />)

    expect(screen.getByText('(Smith, 2019)')).toBeInTheDocument()
    expect(screen.getByText('✓')).toBeInTheDocument()
  })

  it('renders mismatch with reason and correction', () => {
    const citations = [{
      id: 'c1',
      citation_text: '(Smith, 2019)',
      match_status: 'mismatch',
      mismatch_reason: 'Year mismatch: inline says 2019, reference says 2020',
      suggested_correction: '(Smith, 2020)'
    }]
    render(<InlineCitationList citations={citations} refIndex={0} />)

    expect(screen.getByText('⚠️')).toBeInTheDocument()
    expect(screen.getByText(/Year mismatch/)).toBeInTheDocument()
    expect(screen.getByText('(Smith, 2020)')).toBeInTheDocument()
  })

  it('renders mismatch without correction', () => {
    const citations = [{
      id: 'c1',
      citation_text: '(Smith, 2019)',
      match_status: 'mismatch',
      mismatch_reason: 'Author name mismatch'
    }]
    render(<InlineCitationList citations={citations} refIndex={0} />)

    expect(screen.getByText('⚠️')).toBeInTheDocument()
    expect(screen.getByText(/Author name mismatch/)).toBeInTheDocument()
    // Should not show correction
    expect(screen.queryByText(/Should be:/)).not.toBeInTheDocument()
  })

  it('renders ambiguous citation with notice', () => {
    const citations = [{
      id: 'c1',
      citation_text: '(Smith 15)',
      match_status: 'ambiguous',
      suggested_correction: 'Add title: (Smith, Novel 15)'
    }]
    render(<InlineCitationList citations={citations} refIndex={0} />)

    expect(screen.getByText('❓')).toBeInTheDocument()
    expect(screen.getByText('Matches multiple references')).toBeInTheDocument()
    expect(screen.getByText('Add title: (Smith, Novel 15)')).toBeInTheDocument()
  })

  it('renders ambiguous citation without correction', () => {
    const citations = [{
      id: 'c1',
      citation_text: '(Smith 15)',
      match_status: 'ambiguous'
    }]
    render(<InlineCitationList citations={citations} refIndex={0} />)

    expect(screen.getByText('❓')).toBeInTheDocument()
    expect(screen.getByText('Matches multiple references')).toBeInTheDocument()
  })

  it('has correct test id with refIndex', () => {
    const citations = [{ id: 'c1', citation_text: '(Test)', match_status: 'matched' }]
    const { container } = render(<InlineCitationList citations={citations} refIndex={5} />)

    expect(container.firstChild).toHaveAttribute('data-testid', 'inline-list-5')
  })

  it('renders mixed status citations correctly', () => {
    const citations = [
      { id: 'c1', citation_text: '(Smith, 2020)', match_status: 'matched' },
      { id: 'c2', citation_text: '(Jones, 2019)', match_status: 'mismatch', mismatch_reason: 'Year mismatch', suggested_correction: '(Jones, 2020)' },
      { id: 'c3', citation_text: '(Brown 15)', match_status: 'ambiguous', suggested_correction: 'Add year' }
    ]
    render(<InlineCitationList citations={citations} refIndex={0} />)

    expect(screen.getByText('✓')).toBeInTheDocument()
    expect(screen.getByText('⚠️')).toBeInTheDocument()
    expect(screen.getByText('❓')).toBeInTheDocument()
    expect(screen.getByText(/Cited 3× in document/)).toBeInTheDocument()
  })

  it('applies correct status class for matched', () => {
    const citations = [{ id: 'c1', citation_text: '(Test)', match_status: 'matched' }]
    const { container } = render(<InlineCitationList citations={citations} refIndex={0} />)

    const listItem = container.querySelector('.status-matched')
    expect(listItem).toBeInTheDocument()
  })

  it('applies correct status class for mismatch', () => {
    const citations = [{ id: 'c1', citation_text: '(Test)', match_status: 'mismatch', mismatch_reason: 'Test' }]
    const { container } = render(<InlineCitationList citations={citations} refIndex={0} />)

    const listItem = container.querySelector('.status-mismatch')
    expect(listItem).toBeInTheDocument()
  })

  it('applies correct status class for ambiguous', () => {
    const citations = [{ id: 'c1', citation_text: '(Test)', match_status: 'ambiguous' }]
    const { container } = render(<InlineCitationList citations={citations} refIndex={0} />)

    const listItem = container.querySelector('.status-ambiguous')
    expect(listItem).toBeInTheDocument()
  })
})
