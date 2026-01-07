import { renderHook } from '@testing-library/react'
import { useInlineCitations } from './useInlineCitations'
import { describe, it, expect } from 'vitest'

describe('useInlineCitations', () => {
  it('returns hasInline=false when no inline results', () => {
    const { result } = renderHook(() =>
      useInlineCitations([{ citation_number: 1 }], null, [])
    )
    expect(result.current.hasInline).toBe(false)
    expect(result.current.organized).toHaveLength(1)
    expect(result.current.stats).toBeNull()
  })

  it('merges inline citations into refs', () => {
    const refs = [{ citation_number: 1 }, { citation_number: 2 }]
    const inline = [
      { id: 'c1', matched_ref_index: 0, match_status: 'matched' },
      { id: 'c2', matched_ref_index: 0, match_status: 'matched' },
      { id: 'c3', matched_ref_index: 1, match_status: 'mismatch' }
    ]

    const { result } = renderHook(() =>
      useInlineCitations(refs, inline, [])
    )

    expect(result.current.organized[0].inline_citations).toHaveLength(2)
    expect(result.current.organized[1].inline_citations).toHaveLength(1)
    expect(result.current.stats.matched).toBe(2)
    expect(result.current.stats.mismatched).toBe(1)
    expect(result.current.stats.totalInline).toBe(3)
  })

  it('handles null results gracefully', () => {
    const { result } = renderHook(() =>
      useInlineCitations(null, [{ id: 'c1', matched_ref_index: 0 }], [])
    )
    
    // Should return organized as empty array and not crash
    expect(result.current.organized).toEqual([])
    expect(result.current.hasInline).toBe(true)
    expect(result.current.stats.totalInline).toBe(1)
  })
  
  it('calculates orphans correctly', () => {
     const refs = [{ citation_number: 1 }]
     const inline = [{ id: 'c1', matched_ref_index: 0, match_status: 'matched' }]
     const orphans = [{ id: 'o1' }, { id: 'o2' }]

     const { result } = renderHook(() =>
       useInlineCitations(refs, inline, orphans)
     )

     expect(result.current.stats.orphaned).toBe(2)
     expect(result.current.orphans).toHaveLength(2)
  })

  it('detects inline citations already nested in results from backend', () => {
    // Backend nests inline_citations inside each result
    const refsWithNested = [
      {
        citation_number: 1,
        inline_citations: [
          { id: 'c1', match_status: 'matched' },
          { id: 'c2', match_status: 'mismatch' }
        ]
      },
      {
        citation_number: 2,
        inline_citations: []
      }
    ]
    const orphans = [{ id: 'o1' }]

    // No separate inlineResults passed (null)
    const { result } = renderHook(() =>
      useInlineCitations(refsWithNested, null, orphans)
    )

    expect(result.current.hasInline).toBe(true)
    expect(result.current.stats.totalInline).toBe(2)
    expect(result.current.stats.matched).toBe(1)
    expect(result.current.stats.mismatched).toBe(1)
    expect(result.current.stats.orphaned).toBe(1)
    expect(result.current.organized).toEqual(refsWithNested)
  })
})
