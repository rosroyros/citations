/**
 * Standalone MiniChecker entry point
 * Exports a mountMiniChecker function for embedding in static HTML pages
 */
import { createRoot } from 'react-dom/client'
import MiniChecker from './components/MiniChecker'
import './components/MiniChecker.css'

/**
 * Mount MiniChecker component to a DOM element
 * @param {string} elementId - ID of the DOM element to mount to
 * @param {Object} options - Component props
 * @param {string} options.placeholder - Placeholder text for textarea
 * @param {string} options.prefillExample - Example citation to prefill
 * @param {function} options.onFullChecker - Callback when "Open Full Checker" is clicked
 */
function mountMiniChecker(elementId, options = {}) {
  const element = document.getElementById(elementId)

  if (!element) {
    console.error(`MiniChecker: Element with id "${elementId}" not found`)
    return
  }

  // Clear placeholder content
  element.innerHTML = ''

  // Create root and render component
  const root = createRoot(element)
  root.render(
    <MiniChecker
      placeholder={options.placeholder}
      prefillExample={options.prefillExample}
      onFullChecker={options.onFullChecker || (() => window.location.href = '/')}
    />
  )

  console.log('MiniChecker mounted to', elementId)
}

// Expose to window for vanilla JS usage
window.mountMiniChecker = mountMiniChecker

// Export for potential module usage
export { mountMiniChecker }
