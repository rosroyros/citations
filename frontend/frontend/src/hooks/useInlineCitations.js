import { useMemo } from 'react'

/**
 * Hook to organize inline citation data for display.
 *
 * Merges inline citations into their parent reference entries
 * and calculates summary statistics.
 *
 * @param {Array} results - Reference validation results from API
 * @param {Array} inlineResults - Inline citation results from API
 * @param {Array} orphans - Orphan citations from API
 * @returns {Object} Organized data for display
 */
export function useInlineCitations(results = [], inlineResults, orphans) {
  return useMemo(() => {
    // Check if results already have inline_citations nested from backend
    const resultsHaveNestedInline = (results || []).some(
      r => r.inline_citations && r.inline_citations.length > 0
    )

    // If no inline results AND no nested inline data, return original refs
    if ((!inlineResults || inlineResults.length === 0) && !resultsHaveNestedInline) {
      return {
        organized: results || [],
        orphans: orphans || [],
        hasInline: false,
        stats: null
      }
    }

    // If results already have nested inline_citations from backend, use them directly
    if (resultsHaveNestedInline && (!inlineResults || inlineResults.length === 0)) {
      const allInline = (results || []).flatMap(r => r.inline_citations || [])
      const stats = {
        totalInline: allInline.length,
        matched: allInline.filter(i => i.match_status === 'matched').length,
        mismatched: allInline.filter(i => i.match_status === 'mismatch').length,
        ambiguous: allInline.filter(i => i.match_status === 'ambiguous').length,
        orphaned: (orphans || []).length
      }
      return {
        organized: results || [],
        orphans: orphans || [],
        hasInline: true,
        stats
      }
    }

    // Pre-group inline citations by ref index for O(1) lookup
    const inlineByRef = inlineResults.reduce((acc, inline) => {
      const idx = inline.matched_ref_index
      if (!acc[idx]) acc[idx] = []
      acc[idx].push(inline)
      return acc
    }, {})

    // Merge inline citations into their parent refs
    // Each ref gets an inline_citations array with matching citations
    const organized = (results || []).map((ref, index) => ({
      ...ref,
      inline_citations: inlineByRef[index] || []
    }))

    // Calculate statistics
    const stats = {
      totalInline: inlineResults.length,
      matched: inlineResults.filter(i => i.match_status === 'matched').length,
      mismatched: inlineResults.filter(i => i.match_status === 'mismatch').length,
      ambiguous: inlineResults.filter(i => i.match_status === 'ambiguous').length,
      orphaned: (orphans || []).length
    }

    return {
      organized,
      orphans: orphans || [],
      hasInline: true,
      stats
    }
  }, [results, inlineResults, orphans])
}
