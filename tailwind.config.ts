import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        paper: {
          DEFAULT: '#F7F8FA',
          dark: '#08111F',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          dark: '#0D1B2A',
          raised: '#FFFFFF',
          'raised-dark': '#111F34',
        },
        ink: {
          DEFAULT: '#111827',
          dark: '#F2F5FA',
        },
        muted: {
          fg: '#657387',
          dark: '#9AA9BD',
        },
        cobalt: {
          DEFAULT: '#4169F5',
          hover: '#3154D4',
          subtle: '#EEF2FF',
          'subtle-dark': 'rgba(65, 105, 245, 0.15)',
        },
        cyan: {
          accent: '#55D9F4',
          subtle: '#E6FAFE',
          'subtle-dark': 'rgba(85, 217, 244, 0.12)',
        },
        hairline: {
          DEFAULT: '#E5E7EB',
          dark: '#22334A',
        },
        amber: {
          warning: '#F2A93B',
          'warning-subtle': '#FFFBEB',
          'warning-dark': 'rgba(242, 169, 59, 0.15)',
        },
        emerald: {
          verdict: '#22C58B',
          'verdict-subtle': '#ECFDF5',
          'verdict-dark': 'rgba(34, 197, 139, 0.15)',
        },
        rose: {
          abstain: '#F05D6D',
          'abstain-subtle': '#FEF2F2',
          'abstain-dark': 'rgba(240, 93, 109, 0.15)',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        fine: '0 1px 3px 0 rgba(17, 24, 39, 0.03), 0 1px 2px -1px rgba(17, 24, 39, 0.03)',
        elevation: '0 10px 30px -10px rgba(8, 17, 31, 0.06), 0 2px 6px -2px rgba(8, 17, 31, 0.04)',
        'cobalt-glow': '0 0 25px rgba(65, 105, 245, 0.18)',
        'cyan-glow': '0 0 25px rgba(85, 217, 244, 0.18)',
      },
    },
  },
  plugins: [],
};

export default config;
