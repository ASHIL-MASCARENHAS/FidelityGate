/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: {
          dark: '#080d17',
          card: '#0d1525',
          cardHover: '#131e33',
          border: '#1f2e45',
          muted: '#182438'
        },
        cyan: {
          DEFAULT: '#54d6e8',
          glow: '#38bdf8',
          dim: '#164e63'
        },
        gate: {
          accept: '#39d3a4',
          acceptDim: 'rgba(57, 211, 164, 0.15)',
          evidence: '#f3b64b',
          evidenceDim: 'rgba(243, 182, 75, 0.15)',
          abstain: '#ff667d',
          abstainDim: 'rgba(255, 102, 125, 0.15)'
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace', 'ui-monospace'],
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(84, 214, 232, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(84, 214, 232, 0.6)' },
        }
      }
    },
  },
  plugins: [],
}
