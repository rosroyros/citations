import React, { useState, useEffect } from 'react';
import axios from 'axios';

const DebugValidationTable = ({ citations }) => {
  const [results, setResults] = useState([]);
  const [rawResponse, setRawResponse] = useState('');

  useEffect(() => {
    const fetchValidation = async () => {
      try {
        const response = await axios.post('/api/validate', {
          citations: citations,
          style: 'apa7'
        });

        console.log('Raw API response:', response.data);
        setRawResponse(JSON.stringify(response.data, null, 2));

        // Log the specific field we're interested in
        if (response.data.results && response.data.results[0]) {
          console.log('Original field from API:', response.data.results[0].original);
          console.log('Type of original:', typeof response.data.results[0].original);
          console.log('Character codes:');
          for (let i = 0; i < response.data.results[0].original.length; i++) {
            const char = response.data.results[0].original[i];
            if (char === '<' || char === '>') {
              console.log(`Position ${i}: ${char.charCodeAt(0)} (${char})`);
            }
          }
        }

        setResults(response.data.results);
      } catch (error) {
        console.error('Error fetching validation:', error);
      }
    };

    fetchValidation();
  }, [citations]);

  return (
    <div>
      <h2>Debug Validation Table</h2>

      <div>
        <h3>Raw API Response:</h3>
        <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', fontSize: '12px' }}>
          {rawResponse}
        </pre>
      </div>

      {results.map((result, index) => (
        <div key={index} style={{ border: '1px solid #ccc', margin: '10px', padding: '15px' }}>
          <h4>Citation #{result.citation_number}</h4>

          <div style={{ backgroundColor: '#ffeb3b' }}>
            <strong>Original field from API:</strong>
            <div style={{ fontSize: '14px', wordBreak: 'break-all' }}>
              {result.original}
            </div>
          </div>

          <div style={{ backgroundColor: '#e3f2fd' }}>
            <strong>With dangerouslySetInnerHTML:</strong>
            <div
              dangerouslySetInnerHTML={{ __html: result.original }}
              style={{ fontSize: '14px', wordBreak: 'break-all' }}
            />
          </div>

          <div style={{ backgroundColor: '#f3e5f5' }}>
            <strong>Raw text content:</strong>
            <div style={{ fontSize: '14px', wordBreak: 'break-all', whiteSpace: 'pre-wrap' }}>
              {result.original}
            </div>
          </div>

          <div>
            <strong>Source Type:</strong> {result.source_type}
          </div>
        </div>
      ))}
    </div>
  );
};

export default DebugValidationTable;