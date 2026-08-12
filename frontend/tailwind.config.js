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
        // Toned down from raw MUTCD hex — those are built for reflective outdoor
        // signs, not backlit screens, and read as over-saturated at any fill area.
        signal: {
          50: '#f2f7f4',
          100: '#dfeae4',
          200: '#bcd4c8',
          300: '#8fb8a5',
          400: '#5f9880',
          500: '#427f65',
          600: '#326651',
          700: '#2a5342',
          800: '#234437',
          900: '#1d372d',
        },
        plate: {
          50: '#fbf8ee',
          100: '#f5edcf',
          200: '#ecdca0',
          300: '#e2c86c',
          400: '#EBC24E',
          500: '#c9a233',
          600: '#a17f27',
          700: '#7d6320',
          800: '#5a481a',
          900: '#3c3115',
        },
        stop: {
          50: '#faf0f0',
          100: '#f2d7d7',
          200: '#e3aaac',
          300: '#cf7c7f',
          400: '#c05b5e',
          500: '#B34250',
          600: '#943441',
          700: '#742935',
          800: '#57212a',
          900: '#3d191f',
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
