import * as React from 'react';
import { cn } from '../lib/cn';

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  className?: string;
}

/** Centered modal — navy scrim, white card, slide-up. Chapter 3 surfaces. */
export function Modal({ open, onClose, title, children, className }: ModalProps) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-bg-dark/50 p-0 sm:items-center sm:p-md"
      onClick={onClose}
    >
      <div
        className={cn(
          'w-full max-w-md animate-page-in overflow-hidden rounded-t-card bg-bg-primary shadow-card-hover sm:rounded-card',
          className,
        )}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        {title && (
          <div className="flex items-center justify-between border-b border-line px-lg py-md">
            <h2 className="font-display text-h2 text-ink-primary">{title}</h2>
            <button
              onClick={onClose}
              aria-label="Close"
              className="text-ink-muted transition-colors hover:text-ink-primary"
            >
              ✕
            </button>
          </div>
        )}
        <div className="max-h-[85vh] overflow-y-auto p-lg">{children}</div>
      </div>
    </div>
  );
}
