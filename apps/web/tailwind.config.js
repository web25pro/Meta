/** @type {import('tailwindcss').Config} */
const preset = require('../../packages/ui/tailwind-preset.cjs');

module.exports = {
  darkMode: ['class'],
  presets: [preset],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    // Include the shared design system so its Tailwind classes are emitted.
    '../../packages/ui/src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      // shadcn/ui bridge — maps existing semantic classes onto the new tokens.
      colors: {
        border: 'hsl(var(--border-hsl))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },

        // ── Legacy palette compatibility ────────────────────────────────
        // Pre-rebrand pages (dashboard, auth) reference these scales. They are
        // re-mapped onto the white & blue "Panda in the Jungle" brand so the
        // rebrand propagates to existing screens without rewriting each page.
        // `jungle` (was brown) → panda-navy ramp; `secondary` (was bamboo
        // brown) → blue ramp; `panda.bamboo` (was green) → reward gold.
        jungle: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#3b82f6',
          500: '#1e5fa8',
          600: '#1a4f8c',
          700: '#143d6e',
          800: '#0f2a4d',
          900: '#0a1628',
        },
        panda: {
          white: '#ffffff',
          black: '#0f172a',
          eye: '#0a1628',
          bamboo: '#b8860b',
        },
        blue: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#1e5fa8',
          700: '#184e8a',
          800: '#143d6e',
          900: '#0a1628',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#1e5fa8',
          700: '#184e8a',
          800: '#143d6e',
          900: '#0a1628',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
          50: '#f8faff',
          100: '#eff6ff',
          200: '#dbeafe',
          300: '#bfdbfe',
          400: '#93c5fd',
          500: '#3b82f6',
          600: '#1e5fa8',
          700: '#184e8a',
          800: '#143d6e',
          900: '#0a1628',
        },
      },
    },
  },
  plugins: [],
};
