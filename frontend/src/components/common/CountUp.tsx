import { useEffect, useState } from "react";

export function formatDecimal(n: number): string {
  return new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 0 }).format(Math.round(n));
}

export function formatSignedDecimal(n: number): string {
  if (Math.round(n) === 0) {
    return "0";
  }
  return `${n > 0 ? "+" : ""}${formatDecimal(n)}`;
}

export function formatSignedRate(r: number): string {
  if (r === 0) {
    return "0%";
  }
  return `${r > 0 ? "+" : ""}${r}%`;
}

export function easeOutCubic(t: number): number {
  return 1 - (1 - t) ** 3;
}

function prefersReducedMotion() {
  return typeof window !== "undefined"
    && typeof window.matchMedia === "function"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

interface CountUpProps {
  value: number;
  durationMs?: number;
  format?: (value: number) => string;
}

export function CountUp({ value, durationMs = 800, format = formatDecimal }: CountUpProps) {
  const [displayValue, setDisplayValue] = useState(() => (prefersReducedMotion() ? value : 0));

  useEffect(() => {
    // motion 4b-6
    if (prefersReducedMotion()) {
      setDisplayValue(value);
      return;
    }

    let frameId = 0;
    const startedAt = performance.now();
    setDisplayValue(0);

    const tick = (now: number) => {
      const progress = Math.min(1, (now - startedAt) / durationMs);
      setDisplayValue(value * easeOutCubic(progress));
      if (progress < 1) {
        frameId = requestAnimationFrame(tick);
      }
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [durationMs, value]);

  return <span>{format(displayValue)}</span>;
}
