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
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: '#64748b',  // Slate gray for secondary elements
          foreground: "var(--secondary-foreground)",
        },
        success: {
          DEFAULT: '#10b981',  // Green for success states and checkmarks
        },
        // Text colors matching the site
        heading: '#1f2937',    // Dark gray for headings
        body: '#6b7280',       // Medium gray for body text
        
        // Shadcn UI colors
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        background: "var(--background)",
        foreground: "var(--foreground)",
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
      },
      fontFamily: {
        // Using system fonts to match the clean, professional look
        heading: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'system-ui', 'sans-serif'],
        body: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        // Rounded corners matching the site's modern style
        card: '0.75rem',  // 12px border radius
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [
    require("tailwindcss-animate"),
  ],
}

