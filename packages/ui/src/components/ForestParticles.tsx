'use client';

import * as React from 'react';
import { cn } from '../lib/cn';

/** Pre-computed random-ish positions for particles (avoids Math.random in render). */
const FIREFLY_DATA = [
  { x: 12, y: 25, delay: 0, dur: 4.2, size: 3 },
  { x: 28, y: 60, delay: 1.1, dur: 5.0, size: 2.5 },
  { x: 45, y: 18, delay: 2.3, dur: 3.8, size: 3.5 },
  { x: 62, y: 72, delay: 0.7, dur: 4.6, size: 2 },
  { x: 78, y: 35, delay: 1.8, dur: 5.4, size: 3 },
  { x: 88, y: 55, delay: 3.1, dur: 4.0, size: 2.5 },
  { x: 35, y: 82, delay: 0.4, dur: 4.8, size: 3 },
  { x: 55, y: 42, delay: 2.6, dur: 3.6, size: 2 },
  { x: 18, y: 70, delay: 1.4, dur: 5.2, size: 3.5 },
  { x: 72, y: 15, delay: 3.5, dur: 4.4, size: 2.5 },
  { x: 92, y: 80, delay: 0.9, dur: 3.9, size: 3 },
  { x: 8,  y: 48, delay: 2.0, dur: 5.1, size: 2 },
  { x: 50, y: 90, delay: 1.6, dur: 4.3, size: 3 },
  { x: 38, y: 12, delay: 3.3, dur: 4.7, size: 2.5 },
  { x: 68, y: 50, delay: 0.2, dur: 5.3, size: 3.5 },
];

const LEAF_DATA = [
  { x: 5, delay: 0, dur: 12, rot: 15, size: 14 },
  { x: 20, delay: 3, dur: 15, rot: -20, size: 10 },
  { x: 35, delay: 1.5, dur: 11, rot: 30, size: 12 },
  { x: 50, delay: 5, dur: 14, rot: -10, size: 16 },
  { x: 65, delay: 2, dur: 13, rot: 25, size: 11 },
  { x: 80, delay: 4, dur: 16, rot: -15, size: 13 },
  { x: 92, delay: 0.5, dur: 12, rot: 20, size: 15 },
  { x: 15, delay: 6, dur: 14, rot: -25, size: 10 },
  { x: 42, delay: 3.5, dur: 11, rot: 35, size: 12 },
  { x: 75, delay: 1, dur: 15, rot: -30, size: 14 },
];

function Firefly({ x, y, delay, dur, size }: typeof FIREFLY_DATA[number]) {
  return (
    <div
      className="forest-firefly absolute rounded-full"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        width: size,
        height: size,
        animationDelay: `${delay}s`,
        animationDuration: `${dur}s`,
      }}
    />
  );
}

function FallingLeaf({ x, delay, dur, rot, size }: typeof LEAF_DATA[number]) {
  return (
    <div
      className="forest-leaf absolute"
      style={{
        left: `${x}%`,
        top: '-5%',
        width: size,
        height: size,
        animationDelay: `${delay}s`,
        animationDuration: `${dur}s`,
        transform: `rotate(${rot}deg)`,
      }}
    >
      <svg viewBox="0 0 24 24" fill="none" className="h-full w-full" aria-hidden="true">
        <path
          d="M12 2C8 6 4 12 4 16c0 4 3 6 8 6s8-2 8-6c0-4-4-10-8-14z"
          fill="currentColor"
          className="text-forest-500/40"
        />
        <path
          d="M12 6c-2 4-4 8-4 10"
          stroke="currentColor"
          strokeWidth="0.5"
          className="text-forest-600/30"
        />
      </svg>
    </div>
  );
}

/**
 * Ambient forest particles — golden fireflies that drift and pulse, plus
 * falling green leaves. Pure CSS animation, no JS timers.
 */
export function ForestParticles({ className }: { className?: string }) {
  return (
    <div
      className={cn('pointer-events-none fixed inset-0 z-[1] overflow-hidden', className)}
      aria-hidden="true"
    >
      {FIREFLY_DATA.map((f, i) => (
        <Firefly key={`ff-${i}`} {...f} />
      ))}
      {LEAF_DATA.map((l, i) => (
        <FallingLeaf key={`lf-${i}`} {...l} />
      ))}
    </div>
  );
}
