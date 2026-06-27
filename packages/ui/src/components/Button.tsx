import * as React from 'react';
import { cn } from '../lib/cn';

type Variant = 'cobalt' | 'ghost' | 'gradient' | 'gold';
type Size = 'sm' | 'md' | 'lg';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variants: Record<Variant, string> = {
  // Primary CTA — cobalt filled, white text
  cobalt: 'bg-brand-cobalt text-ink-inverse hover:bg-[#184E8A] shadow-card',
  // White outline / ghost
  ghost:
    'bg-transparent text-brand-cobalt border border-line-blue hover:bg-bg-elevated',
  // Cobalt → navy gradient (use sparingly; hover on primary CTA)
  gradient: 'bg-brand-gradient text-ink-inverse hover:opacity-95 shadow-card',
  // Reward action
  gold: 'bg-reward-gold text-ink-inverse hover:brightness-110 shadow-card',
};

const sizes: Record<Size, string> = {
  sm: 'h-9 px-md text-label',
  md: 'h-11 px-lg text-body',
  lg: 'h-14 px-xl text-body',
};

/** Press: scale(0.97) 100ms (Chapter 3.7). */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'cobalt', size = 'md', ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        'inline-flex items-center justify-center gap-sm rounded-pill font-medium',
        'transition-all duration-150 active:scale-[0.97] focus-visible:outline-none',
        'focus-visible:ring-2 focus-visible:ring-brand-cobalt focus-visible:ring-offset-2',
        'disabled:pointer-events-none disabled:opacity-50',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = 'Button';
