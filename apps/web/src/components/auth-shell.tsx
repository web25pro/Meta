import { PandaMascot, Foliage } from '@meta-jungle/ui';

/**
 * Shared auth layout — navy + bamboo texture backdrop with a white card,
 * Meta-Jungle wordmark and panda mascot. Used by every /auth screen.
 */
export function AuthShell({
  title,
  subtitle,
  children,
  footer,
  wide = false,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-hero-gradient p-md">
      <div className="bamboo-texture pointer-events-none absolute inset-0 opacity-40" />
      <Foliage />
      <div className={`relative z-10 w-full ${wide ? 'max-w-xl' : 'max-w-md'}`}>
        <div className="mb-lg flex flex-col items-center text-center">
          <PandaMascot size={84} />
          <span className="mt-md font-display text-2xl font-bold text-ink-inverse">
            Meta-Jungle
          </span>
          {subtitle && <p className="mt-1 text-label text-brand-ice">{subtitle}</p>}
        </div>

        <div className="rounded-card border border-line bg-bg-primary p-xl shadow-card-hover">
          <h1 className="mb-lg font-display text-h1 text-ink-primary">{title}</h1>
          {children}
        </div>

        {footer && (
          <div className="mt-lg text-center text-label text-brand-ice">{footer}</div>
        )}
      </div>
    </div>
  );
}
