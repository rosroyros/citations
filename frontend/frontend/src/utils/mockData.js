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

// Simulates a delayed API response
export const mockValidationAPI = (delay = 3000) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_RESULTS)
    }, delay)
  })
}
