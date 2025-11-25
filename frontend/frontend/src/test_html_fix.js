// Test to verify HTML formatting fix
import React from 'react';
import { createRoot } from 'react-dom/client';

// Import the CSS to ensure it's loaded
import './components/ValidationTable.css';

function TestHTMLFix() {
  const testResults = [
    {
      citation_number: 1,
      original: 'Smith, J. <strong>2009</strong>. <em>Journal article</em>.',
      source_type: 'journal',
      errors: []
    },
    {
      citation_number: 2,
      original: 'Johnson, M. <strong>2018</strong>. <em>Nature Publishing</em>, 15(3), 234-256.',
      source_type: 'journal',
      errors: []
    }
  ];

  const checkComputedStyle = () => {
    console.log('=== Checking CSS Computed Styles ===');

    // Create test elements
    const testDiv = document.createElement('div');
    testDiv.innerHTML = `
      <div class="citation-text">Smith, J. <strong>2009</strong>. <em>Journal article</em>.</div>
    `;

    document.body.appendChild(testDiv);

    const strongElement = testDiv.querySelector('strong');
    const emElement = testDiv.querySelector('em');

    if (strongElement) {
      const strongWeight = window.getComputedStyle(strongElement).fontWeight;
      console.log('Strong element font-weight:', strongWeight);
      console.log('Bold styling applied:', strongWeight === '600' || strongWeight === '700' || strongWeight === 'bold');
    }

    if (emElement) {
      const emStyle = window.getComputedStyle(emElement).fontStyle;
      console.log('Em element font-style:', emStyle);
      console.log('Italic styling applied:', emStyle === 'italic');
    }

    // Clean up
    document.body.removeChild(testDiv);
  };

  React.useEffect(() => {
    // Check styles after component mounts
    setTimeout(checkComputedStyle, 100);
  }, []);

  return React.createElement('div', {
    style: { padding: '20px', fontFamily: 'Arial, sans-serif' }
  },
    React.createElement('h1', null, 'HTML Formatting Fix Test'),

    React.createElement('h2', null, 'Expected Results:'),
    React.createElement('ul', null,
      React.createElement('li', null, '<strong>2009</strong> should appear as bold text'),
      React.createElement('li', null, '<em>Journal article</em> should appear as italic text'),
      React.createElement('li', null, 'Check console for computed style verification')
    ),

    ...testResults.map((result) =>
      React.createElement('div', {
        key: result.citation_number,
        style: {
          border: '1px solid #ddd',
          padding: '15px',
          margin: '10px 0',
          borderRadius: '5px'
        }
      },
        React.createElement('h3', null, `Citation #${result.citation_number}`),
        React.createElement('div', {
          className: 'citation-text',
          dangerouslySetInnerHTML: { __html: result.original }
        }),
        React.createElement('div', { style: { marginTop: '10px', fontSize: '12px', color: '#666' } },
          `Type: ${result.source_type}`
        )
      )
    ),

    React.createElement('div', {
      style: {
        marginTop: '30px',
        padding: '15px',
        backgroundColor: '#e8f5e8',
        borderRadius: '5px'
      }
    },
      React.createElement('h3', null, 'Fix Applied:'),
      React.createElement('pre', { style: { fontSize: '12px', backgroundColor: '#f5f5f5', padding: '10px' } },
        `.citation-text strong {\n  font-weight: 600;\n}`
      ),
      React.createElement('p', null,
        'The missing CSS rule for .citation-text strong has been added to ValidationTable.css'
      )
    )
  );
}

// Test function
const testHTMLFormatting = () => {
  console.log('Testing HTML formatting fix...');

  // Create test container
  const container = document.createElement('div');
  document.body.appendChild(container);

  // Render component
  const root = createRoot(container);
  root.render(React.createElement(TestHTMLFix));

  console.log('Test component rendered. Check visual output and console for style verification.');

  return root;
};

// Export for manual testing
export default TestHTMLFix;
export { testHTMLFormatting };