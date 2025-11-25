import React, { useState, useEffect } from 'react';

function DebugHTMLTest() {
  const [apiResults, setApiResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Test data that matches exactly what the API returns
  const testCases = [
    {
      name: "Static HTML from API response",
      html: "Smith, J. <strong>2009</strong>. <em>Journal article</em>."
    },
    {
      name: "Bold only",
      html: "Johnson, M. <strong>2018</strong>. Research findings."
    },
    {
      name: "Italic only",
      html: "Wilson, K. <em>Academic Press</em>, New York."
    },
    {
      name: "Mixed formatting",
      html: "Davis, L. <strong>2020</strong>. <em>Nature Journal</em>, 15(3), 234-256."
    }
  ];

  // Test API call to get real data
  const testAPICall = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          citations: 'Smith, J. **2009**. _Journal article_.',
          style: 'apa7'
        })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      console.log('Real API response:', data);
      setApiResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Validate React dangerouslySetInnerHTML behavior
  const validateReactRendering = () => {
    console.log('=== React HTML Rendering Validation ===');

    const testDiv = document.createElement('div');
    testDiv.innerHTML = 'Smith, J. <strong>2009</strong>. <em>Journal article</em>.';

    console.log('Native browser rendering:');
    console.log('- innerHTML:', testDiv.innerHTML);
    console.log('- textContent:', testDiv.textContent);
    console.log('- Contains strong element:', testDiv.querySelector('strong') !== null);
    console.log('- Contains em element:', testDiv.querySelector('em') !== null);
    console.log('- Computed styles for strong:', window.getComputedStyle(testDiv.querySelector('strong')).fontWeight);
    console.log('- Computed styles for em:', window.getComputedStyle(testDiv.querySelector('em')).fontStyle);

    return testDiv;
  };

  useEffect(() => {
    validateReactRendering();
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '1200px' }}>
      <h1>HTML Rendering Debug Test</h1>

      {/* Static test cases */}
      <section style={{ marginBottom: '40px' }}>
        <h2>Static Test Cases</h2>
        {testCases.map((testCase, index) => (
          <div key={index} style={{
            marginBottom: '20px',
            border: '1px solid #ddd',
            padding: '15px',
            borderRadius: '5px'
          }}>
            <h3>{testCase.name}</h3>

            <div style={{ marginBottom: '10px' }}>
              <strong>Raw string:</strong> <code>{JSON.stringify(testCase.html)}</code>
            </div>

            <div style={{ marginBottom: '10px' }}>
              <strong>React dangerouslySetInnerHTML:</strong>
              <div
                style={{
                  padding: '10px',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '3px',
                  border: '1px solid #ccc'
                }}
                dangerouslySetInnerHTML={{ __html: testCase.html }}
              />
            </div>

            <div style={{ marginBottom: '10px' }}>
              <strong>React textContent (control):</strong>
              <div style={{ padding: '10px', backgroundColor: '#fffacd' }}>
                {testCase.html}
              </div>
            </div>
          </div>
        ))}
      </section>

      {/* API test section */}
      <section style={{ marginBottom: '40px' }}>
        <h2>Real API Test</h2>
        <button
          onClick={testAPICall}
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Loading...' : 'Test API Call'}
        </button>

        {error && (
          <div style={{ color: 'red', marginTop: '10px' }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {apiResults && (
          <div style={{ marginTop: '20px' }}>
            <h3>API Response Data:</h3>
            <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', overflow: 'auto' }}>
              {JSON.stringify(apiResults, null, 2)}
            </pre>

            {apiResults.results && apiResults.results.map((result, index) => (
              <div key={index} style={{
                marginTop: '20px',
                border: '1px solid #ddd',
                padding: '15px',
                borderRadius: '5px'
              }}>
                <h4>Citation #{result.citation_number}</h4>

                <div style={{ marginBottom: '10px' }}>
                  <strong>Raw original field:</strong> <code>{JSON.stringify(result.original)}</code>
                </div>

                <div style={{ marginBottom: '10px' }}>
                  <strong>ValidationTable rendering:</strong>
                  <div
                    className="citation-text"
                    style={{
                      padding: '10px',
                      backgroundColor: '#f5f5f5',
                      borderRadius: '3px',
                      border: '1px solid #ccc'
                    }}
                    dangerouslySetInnerHTML={{ __html: result.original }}
                  />
                </div>

                <div>
                  <strong>Type: {result.source_type}</strong>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Validation section */}
      <section>
        <h2>Browser Validation</h2>
        <div style={{
          padding: '15px',
          backgroundColor: '#e8f5e8',
          borderRadius: '5px',
          border: '1px solid #4caf50'
        }}>
          <h3>Expected Results:</h3>
          <ul>
            <li><strong>dangerouslySetInnerHTML</strong> should render <strong>bold</strong> and <em>italic</em> formatting</li>
            <li><strong>textContent</strong> should show literal HTML tags</li>
            <li>Check browser console for detailed validation logs</li>
            <li>If HTML formatting is not visible, there may be a React or CSS issue</li>
          </ul>

          <div style={{ marginTop: '10px' }}>
            <strong>Manual validation:</strong>
            <button
              onClick={validateReactRendering}
              style={{
                padding: '5px 10px',
                backgroundColor: '#4caf50',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer',
                marginLeft: '10px'
              }}
            >
              Run Browser Validation (check console)
            </button>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div style={{ marginTop: '40px' }}>
        <a href="/" style={{ color: '#007bff', textDecoration: 'none' }}>
          ← Back to Main App
        </a>
      </div>
    </div>
  );
}

export default DebugHTMLTest;