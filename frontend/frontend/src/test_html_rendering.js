// Simple test to check HTML rendering
import React from 'react';
import { createRoot } from 'react-dom/client';

const testData = {
  results: [{
    citation_number: 1,
    original: 'Smith, J. <strong>2009</strong>. <em>Journal article</em>.',
    source_type: 'test',
    errors: []
  }]
};

function TestComponent() {
  return (
    <div>
      <h1>HTML Rendering Test</h1>
      <div>
        <p>Direct HTML: <strong>2009</strong> <em>Test</em></p>
        <p>DangerouslySetInnerHTML:
          <div dangerouslySetInnerHTML={{ __html: testData.results[0].original }} />
        </p>
        <p>Raw string: {testData.results[0].original}</p>
      </div>
    </div>
  );
}

const root = createRoot(document.getElementById('root'));
root.render(<TestComponent />);