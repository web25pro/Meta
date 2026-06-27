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
  // Primary CTA — cobalt with subtle depth + lift
  cobalt:
    'bg-brand-cobalt text-ink-inverse shadow-card hover:bg-[#184E8A] hover:shadow-glow-cobalt hover:-translate-y-px',
  // Outline / ghost — transparent so it adapts to dark or light surfaces
  ghost:
    'bg-transparent text-brand-cobalt border border-line-blue hover:bg-bg-elevated hover:border-brand-sky',
  // Cobalt → navy gradient (use sparingly; hero CTA)
  gradient:
    'bg-brand-gradient text-ink-inverse shadow-card hover:shadow-glow-cobalt hover:-translate-y-px',
  // Reward action
  gold: 'bg-reward-gold text-ink-inverse shadow-card hover:brightness-110 hover:-translate-y-px',
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
