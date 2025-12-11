/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors from citationformatchecker.com
        primary: {
          DEFAULT: '#9333ea',  // Brand purple
          dark: '#7c3aed',     // Hover state (darker purple)
          light: 'rgba(147, 51, 234, 0.1)',  // Light purple for backgrounds
        },
        secondary: {
          DEFAULT: '#64748b',  // Slate gray for secondary elements
        },
        success: {
          DEFAULT: '#10b981',  // Green for success states and checkmarks
        },
        // Text colors matching the site
        heading: '#1f2937',    // Dark gray for headings
        body: '#6b7280',       // Medium gray for body text
      },
      fontFamily: {
        // Using system fonts to match the clean, professional look
        heading: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'system-ui', 'sans-serif'],
        body: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        // Rounded corners matching the site's modern style
        card: '0.75rem',  // 12px border radius
      },
    },
  },
  plugins: [],
}

