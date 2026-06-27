import * as React from 'react';

export interface CountUpProps {
  value: number;
  /** Duration in ms. */
  duration?: number;
  className?: string;
  format?: (n: number) => string;
}

/**
 * Animated number that counts up from 0 on mount — used for PP/stat displays
 * (Chapter 3.7: "count up from 0 on first enter viewport, ease-out-expo").
 */
export function CountUp({
  value,
  duration = 1200,
  className,
  format = (n) => Math.round(n).toLocaleString('en-US'),
}: CountUpProps) {
  const [display, setDisplay] = React.useState(0);

  React.useEffect(() => {
    let raf = 0;
    let start: number | null = null;
    const easeOutExpo = (t: number) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t));
    const tick = (ts: number) => {
      if (start === null) start = ts;
      const p = Math.min(1, (ts - start) / duration);
      setDisplay(value * easeOutExpo(p));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);

  return <span className={className}>{format(display)}</span>;
}
