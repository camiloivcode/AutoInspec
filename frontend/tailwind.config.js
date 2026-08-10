/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        // Overpass is a Highway Gothic derivative — the typeface of road signage.
        display: ['Overpass', 'system-ui', 'sans-serif'],
        body: ['Overpass', 'system-ui', 'sans-serif'],
        mono: ['"Overpass Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        // Surfaces and text: asphalt scale, driven by CSS vars so dark mode
        // needs no `dark:` duplication at the call site.
        bg: {
          DEFAULT: 'rgb(var(--color-bg) / <alpha-value>)',
          subtle: 'rgb(var(--color-bg-subtle) / <alpha-value>)',
        },
        surface: {
          DEFAULT: 'rgb(var(--color-surface) / <alpha-value>)',
          raised: 'rgb(var(--color-surface-raised) / <alpha-value>)',
        },
        border: {
          DEFAULT: 'rgb(var(--color-border) / <alpha-value>)',
          strong: 'rgb(var(--color-border-strong) / <alpha-value>)',
        },
        fg: {
          DEFAULT: 'rgb(var(--color-fg) / <alpha-value>)',
          muted: 'rgb(var(--color-fg-muted) / <alpha-value>)',
          subtle: 'rgb(var(--color-fg-subtle) / <alpha-value>)',
        },

        // Signage code: green guides, yellow warns, red prohibits. Never decorative.
        signal: {
          50: '#e8f3ed',
          100: '#c5e2d3',
          200: '#8ec5a9',
          300: '#4fa47c',
          400: '#1d855a',
          500: '#00693E',
          600: '#005733',
          700: '#004628',
          800: '#00351e',
          900: '#002415',
        },
        plate: {
          50: '#fdf7e3',
          100: '#fbedbb',
          200: '#f7de85',
          300: '#f4d052',
          400: '#F2C230',
          500: '#dfa910',
          600: '#b8880b',
          700: '#8c6708',
          800: '#5f4605',
          900: '#3a2b03',
        },
        stop: {
          50: '#fdeaed',
          100: '#f9c6cd',
          200: '#f08c9c',
          300: '#e2536b',
          400: '#d42545',
          500: '#C8102E',
          600: '#a60d26',
          700: '#820a1e',
          800: '#5c0715',
          900: '#3a040d',
        },
      },
      borderRadius: {
        // Shape lock: sign plates 12px, chips 6px, status indicators pill.
        plate: '12px',
        chip: '6px',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out forwards',
        'slide-up': 'slideUp 0.35s ease-out forwards',
        'scale-in': 'scaleIn 0.25s ease-out forwards',
        hazard: 'hazard 1s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.97)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        // Diagonal hazard stripes travelling one full band per cycle.
        hazard: {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '32px 0' },
        },
      },
    },
  },
  plugins: [],
}
