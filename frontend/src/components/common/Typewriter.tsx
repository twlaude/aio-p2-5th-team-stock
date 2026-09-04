import { useEffect, useState } from "react";

function prefersReducedMotion() {
  return typeof window !== "undefined"
    && typeof window.matchMedia === "function"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

interface TypewriterProps {
  text: string;
  speedMs?: number;
  startDelayMs?: number;
}

export function Typewriter({ text, speedMs = 28, startDelayMs = 0 }: TypewriterProps) {
  const [visibleCount, setVisibleCount] = useState(() => text.length);
  const [done, setDone] = useState(true);

  useEffect(() => {
    // motion 4b-8
    if (prefersReducedMotion()) {
      setVisibleCount(text.length);
      setDone(true);
      return;
    }

    let intervalId = 0;
    setVisibleCount(0);
    setDone(false);

    const timeoutId = window.setTimeout(() => {
      intervalId = window.setInterval(() => {
        setVisibleCount((count) => {
          const nextCount = count + 1;
          if (nextCount >= text.length) {
            window.clearInterval(intervalId);
            setDone(true);
            return text.length;
          }
          return nextCount;
        });
      }, speedMs);
    }, startDelayMs);

    return () => {
      window.clearTimeout(timeoutId);
      window.clearInterval(intervalId);
    };
  }, [speedMs, startDelayMs, text]);

  return (
    <span className="typewriter" aria-label={text}>
      <span aria-hidden="true">
        {text.slice(0, visibleCount)}
        {!done ? <span className="typewriter__cursor">|</span> : null}
      </span>
    </span>
  );
}
