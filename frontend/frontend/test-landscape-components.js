// Test file for landscape variants
// This file can be used to test the components programmatically

// Mock data for testing
const mockResults = [
  { errors: [] }, // valid
  { errors: [] }, // valid
  { errors: [] }, // valid
  { errors: [] }, // valid
  { errors: [] }, // valid
  { errors: [] }, // valid
  { errors: [] }, // valid
  { errors: [] }, // valid
  { errors: ['Missing author'] }, // has error
  { errors: ['Invalid ISBN'] }, // has error
];

const mockTrackingData = {
  session_id: 'test-session-123',
  validation_id: 'test-validation-456',
};

// Test function to render each variant
function testLandscapeVariants() {
  const variants = ['landscape1', 'landscape2', 'landscape3'];
  const testContainer = document.createElement('div');
  testContainer.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 9999;
    max-width: 300px;
  `;

  variants.forEach((variant, index) => {
    setTimeout(() => {
      console.log(`Testing variant: ${variant}`);

      // This would normally render the React component
      // For testing purposes, we're just logging
      const perfectCount = mockResults.filter(r => (r.errors?.length || 0) === 0).length;
      const errorCount = mockResults.filter(r => (r.errors?.length || 0) > 0).length;

      console.log(`Variant ${variant}: ${perfectCount} valid, ${errorCount} errors`);

      // Add test indicator to page
      const indicator = document.createElement('div');
      indicator.style.cssText = `
        padding: 10px;
        margin: 5px 0;
        background: ${variant === 'landscape1' ? '#e0f2fe' : variant === 'landscape2' ? '#f0fdf4' : '#fef3c7'};
        border-radius: 4px;
        font-size: 14px;
      `;
      indicator.textContent = `✓ ${variant} ready`;
      testContainer.appendChild(indicator);

    }, index * 1000);
  });

  document.body.appendChild(testContainer);

  // Add instructions
  const instructions = document.createElement('div');
  instructions.innerHTML = `
    <h4>Landscape Variants Test</h4>
    <p>Use these variant names in the GatedResults component:</p>
    <ul style="margin: 0; padding-left: 20px;">
      <li><code>landscape1</code> - Classic Horizontal</li>
      <li><code>landscape2</code> - Split Layout</li>
      <li><code>landscape3</code> - Floating Elements</li>
    </ul>
    <p style="margin-top: 10px; font-size: 12px; color: #666;">
      Example: &lt;GatedResults variant="landscape1" /&gt;
    </p>
  `;
  testContainer.insertBefore(instructions, testContainer.firstChild);
}

// Export for use in tests
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    mockResults,
    mockTrackingData,
    testLandscapeVariants
  };
}

// Auto-run if in browser
if (typeof window !== 'undefined') {
  // Only run after page loads
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', testLandscapeVariants);
  } else {
    testLandscapeVariants();
  }
}