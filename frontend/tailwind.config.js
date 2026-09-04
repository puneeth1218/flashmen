/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Command Center Threat Intelligence Colors
        paper: '#09090b',        // Primary card/page surface (zinc-950)
        canvas: '#07090e',       // Deep high-tech cyber background
        ink: '#ffffff',          // Primary text
        'mid-gray': '#94a3b8',   // Secondary text (slate-400)
        hairline: '#1e293b',     // Crisp borders (slate-800)
        'cool-wash': '#0f172a',  // Hover states (slate-900)
        faded: '#000000',        // Global nav overlay
        'electric-blue': '#38bdf8', // Accent highlight (Sky-400)
        'link-blue': '#60a5fa',  // Inline links
        ember: '#ef4444',        // Alert/Nuevo badge
        
        // Threat Status Tokens
        'threat-critical': '#ef4444',
        'threat-warning': '#f59e0b',
        'threat-benign': '#10b981',
        'threat-cyan': '#06b6d4',
        'entity-wallet': '#8b5cf6',
        'entity-ip': '#06b6d4',
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
      },
      boxShadow: {
        'cyber-glow': '0 0 20px -5px rgba(6, 182, 212, 0.15)',
        'threat-glow': '0 0 25px -5px rgba(239, 68, 68, 0.25)',
        'emerald-glow': '0 0 20px -5px rgba(16, 185, 129, 0.25)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'border-flow': 'border-flow 4s ease infinite',
      }
    },
  },
  plugins: [],
}
