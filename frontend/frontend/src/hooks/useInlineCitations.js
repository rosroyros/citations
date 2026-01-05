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
    // If no inline results, return original refs without inline data
    if (!inlineResults || inlineResults.length === 0) {
      return {
        organized: results || [],
        orphans: [],
        hasInline: false,
        stats: null
      }
    }

    // Merge inline citations into their parent refs
    // Each ref gets an inline_citations array with matching citations
    const organized = results.map((ref, index) => ({
      ...ref,
      inline_citations: inlineResults.filter(
        inline => inline.matched_ref_index === index
      )
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
