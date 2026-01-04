import { render, screen } from '@testing-library/react'
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
})
