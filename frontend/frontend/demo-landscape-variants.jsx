// Demo component to showcase all landscape variants
import React, { useState } from 'react'
import GatedResults from './src/components/GatedResults'

// Mock data for demonstration
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

const DemoLandscapeVariants = () => {
  const [currentVariant, setCurrentVariant] = useState('landscape1')
  const [isGated, setIsGated] = useState(true)

  const handleReveal = async () => {
    // Simulate loading
    await new Promise(resolve => setTimeout(resolve, 1500))
    setIsGated(false)
  }

  const resetDemo = () => {
    setIsGated(true)
  }

  const variants = [
    { id: 'landscape1', name: 'Classic Horizontal', description: 'Icon → Title/Summary → Button' },
    { id: 'landscape2', name: 'Split Layout', description: 'Icon/Title centered, Summary/Button on right' },
    { id: 'landscape3', name: 'Floating Elements', description: 'Creative overlapping layout with decorative elements' },
  ]

  return (
    <div style={{
      minHeight: '100vh',
      background: '#f5f5f5',
      padding: '20px',
      fontFamily: "'Work Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '10px', color: '#1f2937' }}>
          Gated Results Landscape Variants
        </h1>
        <p style={{ fontSize: '1.125rem', color: '#6b7280', marginBottom: '40px' }}>
          Three landscape-oriented glassmorphism variants for gated validation results
        </p>

        {/* Variant selector */}
        <div style={{
          display: 'flex',
          gap: '20px',
          marginBottom: '40px',
          flexWrap: 'wrap'
        }}>
          {variants.map(variant => (
            <button
              key={variant.id}
              onClick={() => {
                setCurrentVariant(variant.id)
                setIsGated(true)
              }}
              style={{
                padding: '16px 24px',
                borderRadius: '12px',
                border: `2px solid ${currentVariant === variant.id ? '#8b5cf6' : '#e5e7eb'}`,
                background: currentVariant === variant.id ? '#f3f4f6' : 'white',
                cursor: 'pointer',
                transition: 'all 0.2s',
                textAlign: 'left'
              }}
            >
              <div style={{ fontWeight: 600, color: '#1f2937', marginBottom: '4px' }}>
                {variant.name}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                {variant.description}
              </div>
            </button>
          ))}
        </div>

        {/* Current variant demonstration */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '30px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '20px'
          }}>
            <div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1f2937', margin: 0 }}>
                {variants.find(v => v.id === currentVariant)?.name}
              </h2>
              <p style={{ color: '#6b7280', margin: '4px 0 0 0' }}>
                Variant: <code style={{ background: '#f3f4f6', padding: '2px 6px', borderRadius: '4px' }}>
                  {currentVariant}
                </code>
              </p>
            </div>
            <button
              onClick={resetDemo}
              disabled={isGated}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                background: isGated ? '#e5e7eb' : '#3b82f6',
                color: isGated ? '#9ca3af' : 'white',
                border: 'none',
                cursor: isGated ? 'not-allowed' : 'pointer',
                fontWeight: 500
              }}
            >
              {isGated ? 'Gated Active' : 'Reset Gated View'}
            </button>
          </div>

          {/* Validation table container */}
          <div style={{
            position: 'relative',
            width: '100%',
            height: '280px',
            background: '#f9fafb',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            overflow: 'hidden'
          }}>
            {/* Simulated table content */}
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(135deg, #f3f4f6, #e5e7eb)',
              opacity: 0.8,
              padding: '20px'
            }}>
              {[...Array(8)].map((_, i) => (
                <div key={i} style={{
                  height: '20px',
                  margin: '8px 0',
                  background: 'rgba(255, 255, 255, 0.5)',
                  borderRadius: '4px'
                }} />
              ))}
            </div>

            {/* Gated Results component */}
            {isGated && (
              <GatedResults
                results={mockResults}
                onReveal={handleReveal}
                trackingData={mockTrackingData}
                variant={currentVariant}
              />
            )}

            {/* Results content when revealed */}
            {!isGated && (
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'rgba(255, 255, 255, 0.95)',
                padding: '40px',
                animation: 'fadeIn 0.3s ease-out'
              }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '20px' }}>📊</div>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1f2937', marginBottom: '10px' }}>
                    Validation Results Revealed
                  </h3>
                  <p style={{ color: '#6b7280', marginBottom: '20px' }}>
                    The gated results have been successfully revealed! This is where the actual validation table would appear.
                  </p>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                    gap: '16px',
                    marginTop: '30px'
                  }}>
                    <div style={{ background: '#ecfdf5', padding: '16px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '2rem', fontWeight: 700, color: '#059669' }}>8</div>
                      <div style={{ color: '#047857', fontSize: '0.875rem' }}>Valid Citations</div>
                    </div>
                    <div style={{ background: '#fef2f2', padding: '16px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '2rem', fontWeight: 700, color: '#dc2626' }}>2</div>
                      <div style={{ color: '#b91c1c', fontSize: '0.875rem' }}>Found Errors</div>
                    </div>
                    <div style={{ background: '#eff6ff', padding: '16px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '2rem', fontWeight: 700, color: '#2563eb' }}>10</div>
                      <div style={{ color: '#1d4ed8', fontSize: '0.875rem' }}>Total Citations</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Usage instructions */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '30px',
          marginTop: '40px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1f2937', marginBottom: '16px' }}>
            Usage Instructions
          </h3>
          <div style={{ background: '#f9fafb', padding: '20px', borderRadius: '8px', marginBottom: '16px' }}>
            <code style={{ fontSize: '0.875rem' }}>
              {`<GatedResults variant="${currentVariant}" results={results} onReveal={handleReveal} />`}
            </code>
          </div>
          <p style={{ color: '#6b7280', lineHeight: 1.6, margin: 0 }}>
            Simply set the <code style={{ background: '#f3f4f6', padding: '2px 6px', borderRadius: '4px' }}>variant</code> prop
            to one of the landscape options: <code style={{ background: '#f3f4f6', padding: '2px 6px', borderRadius: '4px' }}>landscape1</code>,
            <code style={{ background: '#f3f4f6', padding: '2px 6px', borderRadius: '4px' }}>landscape2</code>, or
            <code style={{ background: '#f3f4f6', padding: '2px 6px', borderRadius: '4px' }}>landscape3</code>.
          </p>
        </div>
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  )
}

export default DemoLandscapeVariants