/**
 * Meta-Jungle Design System — Tailwind Preset
 * "White & Blue · Panda in the Jungle"  (Master Prompt v3.0, Chapter 3)
 *
 * Single source of truth for the brand. Consumed by every app/package:
 *   presets: [require('../../packages/ui/tailwind-preset.cjs')]
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
  theme: {
    extend: {
      colors: {
        // ── Chapter 3.2 — Color Token System ──────────────────────────────
        // Backgrounds
        bg: {
          primary: '#FFFFFF', // Main app background — pure white (panda fur)
          surface: '#F8FAFF', // Cards, sidebars, panels — off-white with blue tint
          elevated: '#EFF6FF', // Hover states, dropdowns, modals — ice blue mist
          dark: '#0A1628', // Hero sections, nav bar, footer — panda navy night
          'dark-mid': '#1A3A5C', // Dark cards, feature headers — deep jungle blue
        },
        // Brand
        brand: {
          cobalt: '#1E5FA8', // Primary CTA, active nav, focus rings
          sky: '#3B82F6', // Secondary actions, links, highlights, icons
          ice: '#DBEAFE', // Accent backgrounds, selected states, badge fills
        },
        // Reward (bamboo gold — PP amounts, prizes, premium tiers ONLY)
        reward: {
          gold: '#B8860B',
          amber: '#D97706', // Streak fire, warnings, expiring timers
        },
        // Semantic
        success: '#10B981',
        danger: '#DC2626',
        // Text
        ink: {
          primary: '#0F172A', // Body text on white
          muted: '#64748B', // Labels, placeholders, metadata, timestamps
          inverse: '#FFFFFF', // Text on dark/blue backgrounds
        },
        // Borders
        line: {
          DEFAULT: '#CBD5E1',
          blue: '#BFDBFE', // Selected/active states
        },

        // Convenience aliases used across screens.
        // NOTE: no `bamboo` color alias — `bg-bamboo` is the bamboo texture
        // background-image (below); use `reward-gold` for the gold color.
        'panda-navy': '#0A1628',
        cobalt: '#1E5FA8',
        sky: '#3B82F6',
        ice: '#DBEAFE',
      },

      // ── Chapter 3.3 — Typography ──────────────────────────────────────────
      fontFamily: {
        // Display / Heading 1 / Brand wordmark + display numbers
        display: ['var(--font-space-grotesk)', 'Space Grotesk', 'sans-serif'],
        // Body / Headings 2 / Labels
        sans: ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
        // Wallet addresses, tx hashes, contract IDs
        mono: ['var(--font-jetbrains-mono)', 'JetBrains Mono', 'monospace'],
      },
      fontSize: {
        // Role-based scale from Chapter 3.3
        display: ['56px', { lineHeight: '1.05', fontWeight: '700' }],
        'display-lg': ['72px', { lineHeight: '1.0', fontWeight: '700' }],
        h1: ['36px', { lineHeight: '1.15', fontWeight: '600' }],
        h2: ['24px', { lineHeight: '1.25', fontWeight: '600' }],
        body: ['15px', { lineHeight: '1.6', fontWeight: '400' }],
        label: ['12px', { lineHeight: '1.4', fontWeight: '500' }],
      },

      // ── Chapter 3.4 — Spacing System (8px base grid) ─────────────────────
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '16px',
        lg: '24px',
        xl: '32px',
        '2xl': '48px',
        '3xl': '64px',
      },

      borderRadius: {
        card: '12px',
        pill: '9999px',
      },

      boxShadow: {
        // Layered, soft elevation — premium fintech feel (Chapter 3.6)
        card: '0 1px 2px rgba(10,22,40,0.04), 0 4px 12px rgba(10,22,40,0.06)',
        'card-hover': '0 2px 6px rgba(10,22,40,0.06), 0 16px 36px rgba(10,22,40,0.12)',
        glow: '0 0 24px rgba(184, 134, 11, 0.45)', // bamboo gold pulse
        'glow-cobalt': '0 8px 28px rgba(30, 95, 168, 0.35)', // CTA lift
        ring: '0 0 0 1px rgba(30,95,168,0.08)',
      },

      backgroundImage: {
        // Cobalt → navy gradient (CTA hover, podium, landing nav) — Chapter 3.5
        'brand-gradient': 'linear-gradient(135deg, #1E5FA8 0%, #0A1628 100%)',
        // Richer hero gradient with depth
        'hero-gradient':
          'radial-gradient(1200px 500px at 15% -10%, rgba(30,95,168,0.55) 0%, transparent 60%), radial-gradient(900px 500px at 100% 0%, rgba(59,130,246,0.28) 0%, transparent 55%), linear-gradient(180deg, #0A1628 0%, #0A1628 100%)',
        // Soft ice wash for elevated surfaces
        'ice-wash': 'linear-gradient(180deg, #FFFFFF 0%, #F8FAFF 100%)',
        // Diagonal bamboo line texture (subtle jungle aesthetic) — Chapter 3.5
        bamboo:
          'repeating-linear-gradient(45deg, rgba(30,95,168,0.06) 0px, rgba(30,95,168,0.06) 1px, transparent 1px, transparent 14px)',
      },

      // ── Chapter 3.7 — Motion & Animation ─────────────────────────────────
      keyframes: {
        breathe: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.02)' },
        },
        'count-up-in': {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'page-in': {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'pulse-ring': {
          '0%': { boxShadow: '0 0 0 0 rgba(217, 119, 6, 0.5)' },
          '70%': { boxShadow: '0 0 0 10px rgba(217, 119, 6, 0)' },
          '100%': { boxShadow: '0 0 0 0 rgba(217, 119, 6, 0)' },
        },
        'gold-pulse': {
          '0%, 100%': { boxShadow: '0 0 12px rgba(184,134,11,0.35)' },
          '50%': { boxShadow: '0 0 24px rgba(184,134,11,0.7)' },
        },
      },
      animation: {
        breathe: 'breathe 2s ease-in-out infinite', // panda mascot
        'count-up': 'count-up-in 1.2s cubic-bezier(0.16, 1, 0.3, 1)',
        'page-in': 'page-in 180ms ease-out',
        shimmer: 'shimmer 1.6s linear infinite', // ice-blue skeleton (never spinners)
        'pulse-ring': 'pulse-ring 600ms ease-out', // streak activation
        'gold-pulse': 'gold-pulse 2s ease-in-out infinite', // legendary NFT glow
      },

      transitionTimingFunction: {
        'out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
};
