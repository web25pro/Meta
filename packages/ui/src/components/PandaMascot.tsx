import * as React from 'react';
import { cn } from '../lib/cn';

export interface PandaMascotProps {
  size?: number;
  /** Subtle breathing animation (scale 1.0 → 1.02, 2s loop). */
  breathing?: boolean;
  className?: string;
}

/**
 * LPanda mascot — used in onboarding, loading states, empty states, and
 * achievement modals. MUST sit on white or ice-blue (never dark) so the white
 * panda fur stays visible (Chapter 3.5).
 */
export function PandaMascot({
  size = 120,
  breathing = true,
  className,
}: PandaMascotProps) {
  return (
    <div
      className={cn(
        'inline-flex items-center justify-center rounded-full bg-brand-ice',
        breathing && 'animate-breathe',
        className,
      )}
      style={{ width: size, height: size }}
      role="img"
      aria-label="LPanda mascot"
    >
      <svg
        viewBox="0 0 100 100"
        width={size * 0.72}
        height={size * 0.72}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* ears */}
        <circle cx="26" cy="24" r="13" fill="#0A1628" />
        <circle cx="74" cy="24" r="13" fill="#0A1628" />
        {/* head */}
        <circle cx="50" cy="52" r="34" fill="#FFFFFF" stroke="#CBD5E1" strokeWidth="1.5" />
        {/* eye patches */}
        <ellipse cx="37" cy="48" rx="9" ry="12" fill="#0A1628" transform="rotate(-12 37 48)" />
        <ellipse cx="63" cy="48" rx="9" ry="12" fill="#0A1628" transform="rotate(12 63 48)" />
        {/* eyes */}
        <circle cx="38" cy="49" r="3.2" fill="#FFFFFF" />
        <circle cx="62" cy="49" r="3.2" fill="#FFFFFF" />
        {/* nose */}
        <ellipse cx="50" cy="63" rx="4" ry="3" fill="#0A1628" />
        {/* cobalt accent — jungle scarf */}
        <path d="M30 80 Q50 90 70 80" stroke="#1E5FA8" strokeWidth="4" strokeLinecap="round" />
      </svg>
    </div>
  );
}
