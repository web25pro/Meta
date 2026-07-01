import * as React from 'react';
import { cn } from '../lib/cn';

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  /** Optional trailing adornment (e.g. show/hide password toggle). */
  trailing?: React.ReactNode;
}

/** Form input — white surface, 1px border, cobalt focus ring (Chapter 3). */
export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, trailing, id, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div>
        {label && (
          <label
            htmlFor={inputId}
            className="mb-2 block text-label font-medium text-ink-primary"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'w-full rounded-card border bg-bg-primary px-md py-3 text-body text-ink-primary',
              'placeholder:text-ink-muted transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-brand-cobalt focus:ring-offset-0',
              error ? 'border-danger' : 'border-line',
              trailing && 'pr-11',
              className,
            )}
            {...props}
          />
          {trailing && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted">
              {trailing}
            </div>
          )}
        </div>
        {error ? (
          <p className="mt-1 text-label text-danger">{error}</p>
        ) : hint ? (
          <p className="mt-1 text-label text-ink-muted">{hint}</p>
        ) : null}
      </div>
    );
  },
);
Input.displayName = 'Input';
