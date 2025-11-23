import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import ValidationTable from '../components/ValidationTable'

describe('ValidationTable', () => {
  const mockResults = [
    {
      citation_number: 1,
      original: 'Smith, J. (2023). Test citation.',
      source_type: 'journal article',
      errors: []
    },
    {
      citation_number: 2,
      original: 'Doe, J. (2023). Another test.',
      source_type: 'journal article',
      errors: [{ component: 'Authors', problem: 'Missing initials' }]
    },
    {
      citation_number: 3,
      original: 'Brown, A. (2023). Third test.',
      source_type: 'journal article',
      errors: [{ component: 'Date', problem: 'Missing year' }]
    }
  ]

  describe('Full Results Display', () => {
    it('displays correct header with citation count', () => {
      render(<ValidationTable results={mockResults} />)

      expect(screen.getByText('Validation Results')).toBeInTheDocument()
      expect(screen.getByText('3 citations')).toBeInTheDocument()
      expect(screen.getByText('1 perfect')).toBeInTheDocument()
      expect(screen.getByText('2 need fixes')).toBeInTheDocument()
    })

    it('does not show partial indicator', () => {
      render(<ValidationTable results={mockResults} />)

      expect(screen.queryByText('⚠️ Partial')).not.toBeInTheDocument()
      expect(screen.queryByText('submitted')).not.toBeInTheDocument()
      expect(screen.queryByText('processed')).not.toBeInTheDocument()
      expect(screen.queryByText('remaining')).not.toBeInTheDocument()
    })

    it('uses default props when not provided', () => {
      render(<ValidationTable results={mockResults} />)

      // Should render without errors using default values
      expect(screen.getByText('Validation Results')).toBeInTheDocument()
      expect(screen.getByText('3 citations')).toBeInTheDocument()
    })
  })

  describe('Partial Results Display', () => {
    it('displays partial indicator when isPartial is true', () => {
      render(
        <ValidationTable
          results={mockResults}
          isPartial={true}
          totalSubmitted={5}
          citationsRemaining={2}
        />
      )

      expect(screen.getByText('Validation Results ⚠️ Partial')).toBeInTheDocument()
    })

    it('displays submitted count with breakdown', () => {
      render(
        <ValidationTable
          results={mockResults}
          isPartial={true}
          totalSubmitted={5}
          citationsRemaining={2}
        />
      )

      expect(screen.getByText('5 submitted')).toBeInTheDocument()
      expect(screen.getByText('(3 processed • 2 remaining)')).toBeInTheDocument()
    })

    it('displays correct perfect and need fixes counts', () => {
      render(
        <ValidationTable
          results={mockResults}
          isPartial={true}
          totalSubmitted={5}
          citationsRemaining={2}
        />
      )

      expect(screen.getByText('1 perfect')).toBeInTheDocument()
      expect(screen.getByText('2 need fixes')).toBeInTheDocument()
    })

    it('handles edge case with zero remaining citations', () => {
      render(
        <ValidationTable
          results={mockResults}
          isPartial={true}
          totalSubmitted={3}
          citationsRemaining={0}
        />
      )

      expect(screen.getByText('3 submitted')).toBeInTheDocument()
      expect(screen.getByText('(3 processed • 0 remaining)')).toBeInTheDocument()
    })

    it('handles edge case with zero processed citations', () => {
      render(
        <ValidationTable
          results={[]}
          isPartial={true}
          totalSubmitted={5}
          citationsRemaining={5}
        />
      )

      expect(screen.getByText('5 submitted')).toBeInTheDocument()
      expect(screen.getByText('(0 processed • 5 remaining)')).toBeInTheDocument()
      expect(screen.getByText('0 perfect')).toBeInTheDocument()
      expect(screen.getByText('0 need fixes')).toBeInTheDocument()
    })
  })

  describe('Calculation Logic', () => {
    it('correctly calculates perfect and error counts', () => {
      const mixedResults = [
        { citation_number: 1, errors: [] },
        { citation_number: 2, errors: [] },
        { citation_number: 3, errors: [{ component: 'Test' }] },
        { citation_number: 4, errors: [] },
        { citation_number: 5, errors: [{ component: 'Test' }] }
      ]

      render(<ValidationTable results={mixedResults} />)

      expect(screen.getByText('5 citations')).toBeInTheDocument()
      expect(screen.getByText('3 perfect')).toBeInTheDocument()
      expect(screen.getByText('2 need fixes')).toBeInTheDocument()
    })

    it('handles empty results array', () => {
      render(<ValidationTable results={[]} />)

      expect(screen.getByText('Validation Results')).toBeInTheDocument()
      expect(screen.getByText('0 citations')).toBeInTheDocument()
      expect(screen.getByText('0 perfect')).toBeInTheDocument()
      expect(screen.getByText('0 need fixes')).toBeInTheDocument()
    })

    it('handles results with undefined errors', () => {
      const resultsWithUndefinedErrors = [
        { citation_number: 1, original: 'Test', errors: undefined },
        { citation_number: 2, original: 'Test', errors: [] },
        { citation_number: 3, original: 'Test', errors: [{ component: 'Test' }] }
      ]

      render(<ValidationTable results={resultsWithUndefinedErrors} />)

      expect(screen.getByText('3 citations')).toBeInTheDocument()
      expect(screen.getByText('2 perfect')).toBeInTheDocument()  // undefined and empty array count as perfect
      expect(screen.getByText('1 need fixes')).toBeInTheDocument()
    })
  })

  describe('Visual Elements', () => {
    it('applies correct CSS classes for partial results', () => {
      const { container } = render(
        <ValidationTable
          results={mockResults}
          isPartial={true}
          totalSubmitted={5}
          citationsRemaining={2}
        />
      )

      expect(container.querySelector('.partial-indicator')).toBeInTheDocument()
      expect(container.querySelector('.partial-info')).toBeInTheDocument()
      expect(container.querySelector('.partial-breakdown')).toBeInTheDocument()
    })

    it('does not apply partial CSS classes for full results', () => {
      const { container } = render(<ValidationTable results={mockResults} />)

      expect(container.querySelector('.partial-indicator')).not.toBeInTheDocument()
      expect(container.querySelector('.partial-info')).not.toBeInTheDocument()
      expect(container.querySelector('.partial-breakdown')).not.toBeInTheDocument()
    })
  })
})