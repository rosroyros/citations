import { render, screen, fireEvent } from '@testing-library/react'
import OrphanWarningBox from './OrphanWarningBox'

describe('OrphanWarningBox', () => {
  test('renders nothing when no orphans', () => {
    const { container } = render(<OrphanWarningBox orphans={[]} />)
    expect(container.firstChild).toBeNull()
  })

  test('renders nothing when orphans is null', () => {
    const { container } = render(<OrphanWarningBox orphans={null} />)
    expect(container.firstChild).toBeNull()
  })

  test('renders nothing when orphans is undefined', () => {
    const { container } = render(<OrphanWarningBox orphans={undefined} />)
    expect(container.firstChild).toBeNull()
  })

  test('renders single orphan citation', () => {
    const orphans = [
      { id: 'c10', citation_text: '(Brown, 2021)', citation_count: 1 }
    ]
    render(<OrphanWarningBox orphans={orphans} />)

    expect(screen.getByText('(Brown, 2021)')).toBeInTheDocument()
    expect(screen.getByText('cited 1×')).toBeInTheDocument()
    expect(screen.getByText('1 Citation Missing from References')).toBeInTheDocument()
  })

  test('renders multiple orphan citations with plural header', () => {
    const orphans = [
      { id: 'c10', citation_text: '(Brown, 2021)', citation_count: 1 },
      { id: 'c11', citation_text: '(Wilson, 2018)', citation_count: 2 }
    ]
    render(<OrphanWarningBox orphans={orphans} />)

    expect(screen.getByText('(Brown, 2021)')).toBeInTheDocument()
    expect(screen.getByText('(Wilson, 2018)')).toBeInTheDocument()
    expect(screen.getByText('cited 1×')).toBeInTheDocument()
    expect(screen.getByText('cited 2×')).toBeInTheDocument()
    expect(screen.getByText('2 Citations Missing from References')).toBeInTheDocument()
  })

  test('renders warning icon', () => {
    const orphans = [
      { id: 'c10', citation_text: '(Brown, 2021)', citation_count: 1 }
    ]
    const { container } = render(<OrphanWarningBox orphans={orphans} />)

    const icon = container.querySelector('.warning-icon')
    expect(icon).toBeInTheDocument()
    expect(icon.textContent).toBe('⚠️')
  })

  test('has data-testid for E2E testing', () => {
    const orphans = [
      { id: 'c10', citation_text: '(Brown, 2021)', citation_count: 1 }
    ]
    const { container } = render(<OrphanWarningBox orphans={orphans} />)

    expect(container.firstChild).toHaveAttribute('data-testid', 'orphan-warning')
  })

  describe('Collapsible behavior', () => {
    test('shows all orphans when 3 or fewer', () => {
      const orphans = [
        { id: 'c1', citation_text: '(One, 2021)' },
        { id: 'c2', citation_text: '(Two, 2021)' },
        { id: 'c3', citation_text: '(Three, 2021)' }
      ]
      render(<OrphanWarningBox orphans={orphans} />)

      expect(screen.getByText('(One, 2021)')).toBeInTheDocument()
      expect(screen.getByText('(Two, 2021)')).toBeInTheDocument()
      expect(screen.getByText('(Three, 2021)')).toBeInTheDocument()
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })

    test('collapses list and shows toggle button when more than 3 orphans', () => {
      const orphans = [
        { id: 'c1', citation_text: '(One, 2021)' },
        { id: 'c2', citation_text: '(Two, 2021)' },
        { id: 'c3', citation_text: '(Three, 2021)' },
        { id: 'c4', citation_text: '(Four, 2021)' },
        { id: 'c5', citation_text: '(Five, 2021)' }
      ]
      render(<OrphanWarningBox orphans={orphans} />)

      // First 3 should be visible
      expect(screen.getByText('(One, 2021)')).toBeInTheDocument()
      expect(screen.getByText('(Two, 2021)')).toBeInTheDocument()
      expect(screen.getByText('(Three, 2021)')).toBeInTheDocument()

      // Last 2 should be hidden
      expect(screen.queryByText('(Four, 2021)')).not.toBeInTheDocument()
      expect(screen.queryByText('(Five, 2021)')).not.toBeInTheDocument()

      // Toggle button should show hidden count
      expect(screen.getByRole('button', { name: 'Show 2 more...' })).toBeInTheDocument()
    })

    test('expands and collapses when toggle button clicked', () => {
      const orphans = [
        { id: 'c1', citation_text: '(One, 2021)' },
        { id: 'c2', citation_text: '(Two, 2021)' },
        { id: 'c3', citation_text: '(Three, 2021)' },
        { id: 'c4', citation_text: '(Four, 2021)' }
      ]
      render(<OrphanWarningBox orphans={orphans} />)

      // Initially collapsed
      expect(screen.queryByText('(Four, 2021)')).not.toBeInTheDocument()

      // Click to expand
      const toggleBtn = screen.getByRole('button', { name: 'Show 1 more...' })
      fireEvent.click(toggleBtn)

      // Now all should be visible
      expect(screen.getByText('(Four, 2021)')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Show less' })).toBeInTheDocument()

      // Click to collapse again
      fireEvent.click(screen.getByRole('button', { name: 'Show less' }))
      expect(screen.queryByText('(Four, 2021)')).not.toBeInTheDocument()
    })
  })
})

