/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Aceternity Dark Theme Colors
        paper: '#09090b',        // Primary card/page surface (zinc-950)
        canvas: '#000000',       // Deep black background
        ink: '#ffffff',          // Primary text
        'mid-gray': '#a1a1aa',   // Secondary text (zinc-400)
        hairline: '#27272a',     // Borders (zinc-800)
        'cool-wash': '#18181b',  // Hover states (zinc-900)
        faded: '#000000',        // Global nav overlay
        'electric-blue': '#ffffff', // Primary CTAs (White in Aceternity)
        'link-blue': '#a1a1aa',  // Inline links
        ember: '#ef4444',        // Alert/Nuevo badge
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      letterSpacing: {
        'apple-hero': '-0.04em',
        'apple-display': '-0.02em',
        'apple-heading': '-0.01em',
        'apple-subhead': '0',
        'apple-body': '0',
      },
      borderRadius: {
        'apple-card': '12px',
        'apple-pill': '999px',
      }
    },
  },
  plugins: [],
}
