// Mock data for testing validation UX without backend
export const MOCK_RESULTS = {
  results: [
    {
      citation_number: 1,
      original: "Smith, J., & Jones, M. (2023). Understanding research methods. <em>Journal of Academic Studies</em>, 45(2), 123-145. https://doi.org/10.1234/example",
      source_type: "Journal Article",
      errors: []
    },
    {
      citation_number: 2,
      original: "Brown, A. (2022). Writing in APA style. Academic Press.",
      source_type: "Book",
      errors: [
        {
          component: "Publisher Location",
          problem: "Missing publisher location",
          correction: "Add city and state/country: Academic Press. Boston, MA."
        }
      ]
    },
    {
      citation_number: 3,
      original: "Taylor, R., Davis, K., & Wilson, L. (2024). Climate change impacts. <em>Nature</em>, 612, 45-52.",
      source_type: "Journal Article",
      errors: []
    },
    {
      citation_number: 4,
      original: "Johnson M (2021) Data Science Fundamentals New York Publisher",
      source_type: "Book",
      errors: [
        {
          component: "Author Name",
          problem: "Missing period after initial",
          correction: "Johnson, M."
        },
        {
          component: "Title",
          problem: "Title should be in sentence case and italicized",
          correction: "<em>Data science fundamentals</em>"
        },
        {
          component: "Publisher",
          problem: "Missing colon between location and publisher",
          correction: "New York: Publisher"
        }
      ]
    },
    {
      citation_number: 5,
      original: "World Health Organization. (2023). <em>Global health report 2023</em>. https://www.who.int/reports/2023",
      source_type: "Report",
      errors: []
    }
  ],
  isPartial: false
}

export const MOCK_PARTIAL_RESULTS = {
  results: MOCK_RESULTS.results.slice(0, 3),
  isPartial: true,
  citations_checked: 3,
  citations_remaining: 2,
  partial: true
}

// Mock inline citation results (for full document validation)
export const MOCK_INLINE_RESULTS = [
  // Matched citations for ref 0 (Smith et al., 2023)
  {
    id: "c1",
    citation_text: "(Smith, 2019)",
    match_status: "mismatch",
    matched_ref_index: 0,
    matched_ref_indices: null,
    mismatch_reason: "Year mismatch: inline says 2019, reference says 2023",
    format_errors: [],
    suggested_correction: "(Smith et al., 2023)"
  },
  {
    id: "c2",
    citation_text: "(Smith et al., 2023)",
    match_status: "matched",
    matched_ref_index: 0,
    matched_ref_indices: null,
    mismatch_reason: null,
    format_errors: [],
    suggested_correction: null
  },

  // Matched citations for ref 1 (Brown, 2022)
  {
    id: "c3",
    citation_text: "(Brown, 2022)",
    match_status: "matched",
    matched_ref_index: 1,
    matched_ref_indices: null,
    mismatch_reason: null,
    format_errors: [],
    suggested_correction: null
  },

  // Mismatch citation for ref 2 (Taylor et al., 2024)
  {
    id: "c4",
    citation_text: "(Taylor, 2019)",
    match_status: "mismatch",
    matched_ref_index: 2,
    matched_ref_indices: null,
    mismatch_reason: "Year mismatch: inline says 2019, reference says 2024",
    format_errors: [],
    suggested_correction: "(Taylor et al., 2024)"
  },
  {
    id: "c5",
    citation_text: "(Taylor et al., 2024)",
    match_status: "matched",
    matched_ref_index: 2,
    matched_ref_indices: null,
    mismatch_reason: null,
    format_errors: [],
    suggested_correction: null
  },

  // Format error citation for ref 3 (Johnson, 2021)
  {
    id: "c6",
    citation_text: "Johnson M 2021",
    match_status: "matched",
    matched_ref_index: 3,
    matched_ref_indices: null,
    mismatch_reason: null,
    format_errors: [
      {
        component: "Parentheses",
        problem: "Missing parentheses around author and year",
        correction: "(Johnson, 2021)"
      },
      {
        component: "Author",
        problem: "Missing period after initial",
        correction: "Johnson, M."
      }
    ],
    suggested_correction: "(Johnson, 2021)"
  }
]

// Mock orphan citations (citations with no matching reference)
export const MOCK_ORPHAN_CITATIONS = [
  {
    id: "c10",
    citation_text: "(Brown, 2021)",
    match_status: "not_found",
    matched_ref_index: null,
    matched_ref_indices: null,
    mismatch_reason: "No matching reference found for Brown, 2021",
    format_errors: [],
    suggested_correction: null
  },
  {
    id: "c11",
    citation_text: "(Wilson, 2018)",
    match_status: "not_found",
    matched_ref_index: null,
    matched_ref_indices: null,
    mismatch_reason: "No matching reference found for Wilson, 2018",
    format_errors: [],
    suggested_correction: null
  },
  {
    id: "c12",
    citation_text: "(Martinez et al., 2020)",
    match_status: "not_found",
    matched_ref_index: null,
    matched_ref_indices: null,
    mismatch_reason: "No matching reference found for Martinez et al., 2020",
    format_errors: [],
    suggested_correction: null
  }
]

// Mock full document validation response with inline citations
export const MOCK_FULL_DOC_RESULTS = {
  results: MOCK_RESULTS.results.map((result, idx) => ({
    ...result,
    inline_citations: MOCK_INLINE_RESULTS.filter(c => c.matched_ref_index === idx)
  })),
  validation_type: "full_doc",
  orphan_citations: MOCK_ORPHAN_CITATIONS,
  stats: {
    ref_count: 5,
    inline_count: 9,
    orphan_count: 3,
    perfect_count: 3,
    error_count: 3
  },
  isPartial: false
}

// Mock gated response (free tier - shows first 3 references)
export const MOCK_GATED_RESULTS = {
  results: MOCK_FULL_DOC_RESULTS.results.slice(0, 3),
  validation_type: "full_doc",
  orphan_citations: MOCK_ORPHAN_CITATIONS,
  stats: {
    ref_count: 5,
    inline_count: 9,
    orphan_count: 3,
    perfect_count: 3,
    error_count: 3
  },
  isPartial: true,
  is_gated: true,
  refs_shown: 3,
  refs_remaining: 2,
  partial: true
}

// Simulates a delayed API response
export const mockValidationAPI = (delay = 3000) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_RESULTS)
    }, delay)
  })
}

// Simulates a delayed full document API response
export const mockFullDocValidationAPI = (delay = 3000) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_FULL_DOC_RESULTS)
    }, delay)
  })
}
