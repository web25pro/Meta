import * as React from 'react';
import { cn } from '../lib/cn';

/** A single monstera-style leaf silhouette. */
function Leaf({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg
      viewBox="0 0 100 100"
      className={className}
      style={style}
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M50 4C26 14 10 36 10 62c0 18 10 30 22 34-6-16-4-34 6-48-2 14 0 28 8 38 14-8 26-26 26-50 0-14-8-26-22-32zM50 18c8 6 12 16 12 28 0 16-8 30-18 38" opacity="0.0" />
      <path d="M52 6C30 12 12 32 12 58c0 20 12 34 26 38-8-18-6-38 4-54-3 16-1 32 9 44 16-10 28-30 28-56 0-12-10-22-27-24z" />
      <path d="M50 16c-7 9-11 21-11 33 0 13 4 24 11 31" fill="none" stroke="#08130D" strokeOpacity="0.18" strokeWidth="2" />
    </svg>
  );
}

export interface FoliageProps {
  /** Tailwind text-color class for the leaves (sets currentColor). */
  className?: string;
  /** Show the top-left cluster. */
  topLeft?: boolean;
  /** Show the bottom-right cluster. */
  bottomRight?: boolean;
}

/**
 * Decorative jungle foliage for dark hero surfaces — clean SVG leaves at low
 * opacity in the corners, with a gentle sway. Professional, never emoji.
 * Place inside a `relative overflow-hidden` container.
 */
export function Foliage({ className, topLeft = true, bottomRight = true }: FoliageProps) {
  return (
    <div className={cn('pointer-events-none absolute inset-0 overflow-hidden text-forest-500', className)} aria-hidden="true">
      {topLeft && (
        <>
          <Leaf className="absolute -left-8 -top-10 h-40 w-40 origin-bottom-right animate-sway opacity-[0.10]" />
          <Leaf className="absolute left-16 -top-16 h-28 w-28 origin-bottom-right animate-sway opacity-[0.07]" style={{ animationDelay: '1.5s', transform: 'rotate(35deg)' }} />
        </>
      )}
      {bottomRight && (
        <>
          <Leaf className="absolute -bottom-12 -right-8 h-48 w-48 origin-top-left animate-sway opacity-[0.10]" style={{ transform: 'scaleX(-1)' }} />
          <Leaf className="absolute bottom-6 right-24 h-24 w-24 origin-top-left animate-sway opacity-[0.06]" style={{ animationDelay: '2.2s', transform: 'rotate(-20deg)' }} />
        </>
      )}
    </div>
  );
}
