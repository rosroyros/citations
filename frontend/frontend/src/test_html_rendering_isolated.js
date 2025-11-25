// Direct test of HTML rendering in isolation
import React from 'react';
import { createRoot } from 'react-dom/client';

function TestHTMLRendering() {
  // Test data that matches the API response structure
  const testCases = [
    {
      name: "Direct HTML string",
      html: "Smith, J. <strong>2009</strong>. <em>Journal article</em>."
    },
    {
      name: "From API response simulation",
      html: 'Smith, J. <strong>2009</strong>. <em>Journal article</em>.'
    },
    {
      name: "Empty test",
      html: ""
    }
  ];

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>HTML Rendering Test</h1>

      {testCases.map((testCase, index) => (
        <div key={index} style={{ marginBottom: '30px', border: '1px solid #ccc', padding: '15px' }}>
          <h3>{testCase.name}</h3>

          <div style={{ marginBottom: '10px' }}>
            <strong>Raw string:</strong> {JSON.stringify(testCase.html)}
          </div>

          <div style={{ marginBottom: '10px' }}>
            <strong>Direct HTML (control):</strong>
            <div dangerouslySetInnerHTML={{ __html: testCase.html }} />
          </div>

          <div>
            <strong>TextContent (check):</strong>
            <div>{testCase.html}</div>
          </div>
        </div>
      ))}

      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f0f0f0' }}>
        <h3>Expected Results:</h3>
        <ul>
          <li>Direct HTML should show <strong>bold</strong> and <em>italic</em> formatting</li>
          <li>TextContent should show literal HTML tags</li>
          <li>If both show literal tags, there's a React/environment issue</li>
        </ul>
      </div>
    </div>
  );
}

// Test function to validate the rendering
function validateRendering() {
  console.log('=== HTML Rendering Validation ===');

  const testElement = document.createElement('div');
  testElement.innerHTML = 'Smith, J. <strong>2009</strong>. <em>Journal article</em>.';

  console.log('Native browser innerHTML result:', testElement.innerHTML);
  console.log('Native browser textContent:', testElement.textContent);
  console.log('Contains strong tag:', testElement.querySelector('strong') !== null);
  console.log('Contains em tag:', testElement.querySelector('em') !== null);

  return testElement;
}

// Auto-run validation
validateRendering();

export default TestHTMLRendering;