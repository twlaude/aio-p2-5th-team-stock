import { useMemo } from "react";
import { motion, useReducedMotion } from "motion/react";

import "./sparkline.css";

interface SparklineProps {
  stockCode: string;
  changeRate: number;
}

function seedFrom(stockCode: string) {
  return stockCode.split("").reduce((seed, char) => seed + char.charCodeAt(0), 17);
}

function next(seed: number) {
  return (seed * 1664525 + 1013904223) >>> 0;
}

function buildPoints(stockCode: string, changeRate: number) {
  const pointCount = 17;
  const upward = changeRate >= 0;
  let seed = seedFrom(stockCode);
  const ys = Array.from({ length: pointCount }, (_, index) => {
    seed = next(seed);
    const wave = (seed / 2 ** 32 - 0.5) * 18;
    const progress = index / (pointCount - 1);
    const trend = upward ? 90 - progress * 68 : 30 + progress * 64;
    return Math.max(18, Math.min(102, trend + wave));
  });
  ys[pointCount - 1] = upward ? 20 : 92;

  return ys.map((y, index) => `${(880 / (pointCount - 1)) * index},${y.toFixed(1)}`).join(" ");
}

export function Sparkline({ stockCode, changeRate }: SparklineProps) {
  const reducedMotion = useReducedMotion();
  const points = useMemo(() => buildPoints(stockCode, changeRate), [changeRate, stockCode]);
  const lastPoint = points.split(" ").at(-1)?.split(",").map(Number) ?? [880, changeRate >= 0 ? 20 : 92];

  return (
    <svg className="sparkline" width="880" height="120" viewBox="0 0 880 120" fill="none" aria-hidden="true">
      <line className="sparkline__baseline" x1="0" y1="90" x2="880" y2="90" />
      <motion.polyline
        className="sparkline__line"
        points={points}
        pathLength={1}
        initial={reducedMotion ? { opacity: 0 } : { pathLength: 0 }}
        animate={reducedMotion ? { opacity: 1 } : { pathLength: 1 }}
        transition={{ duration: reducedMotion ? 0.2 : 0.9, ease: "easeOut" }}
      />
      {/* motion 4b-7 */}
      <motion.circle
        className="sparkline__dot"
        cx={lastPoint[0]}
        cy={lastPoint[1]}
        r="4"
        initial={{ opacity: 0, scale: 1 }}
        animate={reducedMotion ? { opacity: 1 } : { opacity: [0, 1, 0.9], scale: [1, 1.9, 1] }}
        transition={{ delay: reducedMotion ? 0 : 0.9, duration: reducedMotion ? 0.2 : 0.45 }}
      />
    </svg>
  );
}
