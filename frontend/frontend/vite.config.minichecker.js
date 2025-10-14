import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Build configuration for standalone MiniChecker component
export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: path.resolve(__dirname, 'src/mini-checker-standalone.jsx'),
      name: 'MiniChecker',
      formats: ['iife'], // Immediately-invoked function expression for browser
      fileName: () => 'mini-checker.js'
    },
    rollupOptions: {
      output: {
        // Put all code in a single file
        inlineDynamicImports: true,
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === 'style.css') {
            return 'mini-checker.css'
          }
          return assetInfo.name
        }
      }
    },
    outDir: '../../backend/pseo/builder/assets/js',
    emptyOutDir: false, // Don't clear the entire assets dir
    cssCodeSplit: false
  }
})
