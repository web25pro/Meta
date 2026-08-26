import * as React from 'react';
import { cn } from '../lib/cn';

export type PandaTier = 'cub' | 'juvenile' | 'adult' | 'alpha' | 'legend';

export interface PandaMascotProps {
  size?: number;
  /** Subtle breathing animation (scale 1.0 → 1.02, 2s loop). */
  breathing?: boolean;
  /**
   * Growth tier — overrides `size` with a tier-appropriate value and adds
   * glow / particle effects. When provided, the panda "grows" as the user
   * earns more PP.
   */
  tier?: PandaTier;
  className?: string;
}

const TIER_CONFIG: Record<PandaTier, { size: number; ring: string; glow: string; label: string }> = {
  cub:      { size: 64,  ring: '',                          glow: '',                              label: 'Cub' },
  juvenile: { size: 80,  ring: 'ring-2 ring-forest-400/40', glow: '',                              label: 'Juvenile' },
  adult:    { size: 100, ring: 'ring-2 ring-forest-500/50', glow: 'shadow-[0_0_20px_rgba(16,160,99,0.25)]', label: 'Adult' },
  alpha:    { size: 130, ring: 'ring-2 ring-reward-gold/50', glow: 'shadow-[0_0_28px_rgba(184,134,11,0.3)]', label: 'Alpha' },
  legend:   { size: 160, ring: 'ring-2 ring-reward-gold/60', glow: 'animate-gold-pulse',           label: 'Legend' },
};

/** Map PP balance to a growth tier. */
export function getPandaTier(pp: number): PandaTier {
  if (pp >= 5000) return 'legend';
  if (pp >= 2000) return 'alpha';
  if (pp >= 500)  return 'adult';
  if (pp >= 100)  return 'juvenile';
  return 'cub';
}

/**
 * LPanda mascot — used in onboarding, loading states, empty states, and
 * achievement modals. When `tier` is provided, the panda grows and gains
 * visual effects based on the user's PP balance.
 */
export function PandaMascot({
  size,
  breathing = true,
  tier,
  className,
}: PandaMascotProps) {
  const config = tier ? TIER_CONFIG[tier] : null;
  const resolvedSize = config?.size ?? size ?? 120;
  const showSparkles = tier === 'legend' || tier === 'alpha';

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)}>
      {/* Sparkle particles for alpha+ tiers */}
      {showSparkles && (
        <div className="pointer-events-none absolute inset-0" aria-hidden="true">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="forest-sparkle absolute rounded-full bg-reward-gold/60"
              style={{
                width: 3 + (i % 3),
                height: 3 + (i % 3),
                left: `${15 + i * 14}%`,
                top: `${10 + (i * 17) % 80}%`,
                animationDelay: `${i * 0.6}s`,
              }}
            />
          ))}
        </div>
      )}

      {/* Main panda circle */}
      <div
        className={cn(
          'inline-flex items-center justify-center rounded-full bg-brand-ice transition-all duration-700',
          breathing && !config?.glow?.startsWith('animate') && 'animate-breathe',
          config?.ring,
          config?.glow,
        )}
        style={{ width: resolvedSize, height: resolvedSize }}
        role="img"
        aria-label={`LPanda mascot${tier ? ` — ${config?.label} tier` : ''}`}
      >
        <svg
          viewBox="0 0 100 100"
          width={resolvedSize * 0.72}
          height={resolvedSize * 0.72}
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
          {/* Gold scarf accent for alpha+ tiers */}
          {(tier === 'alpha' || tier === 'legend') && (
            <path d="M32 82 Q50 92 68 82" stroke="#B8860B" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
          )}
        </svg>
      </div>

      {/* Tier label */}
      {tier && config && (
        <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 whitespace-nowrap">
          <span
            className={cn(
              'rounded-pill px-sm py-[2px] text-[10px] font-semibold uppercase tracking-wider',
              tier === 'legend'
                ? 'bg-reward-gold/20 text-reward-gold'
                : tier === 'alpha'
                  ? 'bg-reward-amber/20 text-reward-amber'
                  : 'bg-forest-500/15 text-forest-600',
            )}
          >
            {config.label}
          </span>
        </div>
      )}
    </div>
  );
}
