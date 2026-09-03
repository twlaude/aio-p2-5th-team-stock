import { useLayoutEffect, useMemo, useRef, useState, type CSSProperties, type MouseEvent, type ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";

import type { TopicEvidence } from "../analysis/deriveEvidence";
import "./result-ambient.css";

/**
 * 결과 한줄 결론 주변에 커뮤니티 주제 키워드가 "팍" 퍼졌다가(burst) 둥실둥실 떠 있는 레이어.
 * 형 지시(2026-09-03): "결과문 띄우자나. 그 주변에 팍 퍼지는 이팩트 주면서 둥실둥실 떠잇게".
 * 키워드는 집계 주제만(원문 댓글 아님 — 커뮤니티 계약). motion 4b-8 확장.
 */

interface ResultAmbientProps {
  topics: TopicEvidence[];
  runId: number;
  children: ReactNode;
}

interface Placed {
  topic: TopicEvidence;
  x: number;
  y: number;
  scale: number;
  delay: number;
  floatDuration: number;
  floatDelay: number;
  ampX: number;
  ampY: number;
  rot: number;
}

function mulberry32(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hashText(text: string) {
  let h = 2166136261;
  for (const ch of text) {
    h ^= ch.charCodeAt(0);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

interface Bounds {
  mobile: boolean;
  maxX: number;
  maxY: number;
  keepOutX: number;
  keepOutY: number;
  minGap: number;
  count: number;
}

function boundsFor(hostWidth: number, viewportWidth: number): Bounds {
  const mobile = viewportWidth <= 480;
  if (mobile) {
    return { mobile, maxX: viewportWidth / 2 - 54, maxY: 196, keepOutX: hostWidth / 2, keepOutY: 104, minGap: 56, count: 6 };
  }
  return { mobile, maxX: Math.min(viewportWidth / 2 - 76, 600), maxY: 212, keepOutX: Math.min(hostWidth / 2 + 10, 470), keepOutY: 112, minGap: 72, count: 12 };
}

/** 키워드가 앉을 수 있는 자리: 결론 말풍선 좌우 여백 + 말풍선 아래 띠(why 버튼 자리 제외). 그래프·가격 위로는 안 올라간다. */
function sampleCandidate(rand: () => number, b: Bounds): { x: number; y: number } {
  const lerp = (lo: number, hi: number) => lo + rand() * (hi - lo);
  if (b.mobile) {
    // 모바일: 말풍선 위 띠 / 아래 띠(why 버튼 중앙 제외)
    if (rand() < 0.5) return { x: lerp(-b.maxX, b.maxX), y: lerp(-158, -b.keepOutY - 8) };
    const x = lerp(-b.maxX, b.maxX);
    const y = lerp(b.keepOutY + 8, b.maxY);
    if (Math.abs(x) < 112 && y < b.keepOutY + 78) return { x: x < 0 ? x - 120 : x + 120, y };
    return { x: Math.max(-b.maxX, Math.min(b.maxX, x)), y };
  }
  const roll = rand();
  if (roll < 0.28) return { x: lerp(-b.maxX, -b.keepOutX - 12), y: lerp(-150, 150) };
  if (roll < 0.56) return { x: lerp(b.keepOutX + 12, b.maxX), y: lerp(-150, 150) };
  const x = lerp(-b.maxX + 40, b.maxX - 40);
  const y = lerp(b.keepOutY + 14, b.maxY);
  if (Math.abs(x) < 150 && y < b.keepOutY + 82) return { x: x < 0 ? x - 160 : x + 160, y };
  return { x, y };
}

function layout(topics: TopicEvidence[], bounds: Bounds, seed: number): Placed[] {
  const rand = mulberry32(seed);
  const chosen = [...topics].sort((a, b) => b.weight - a.weight).slice(0, bounds.count);
  const placed: Placed[] = [];

  chosen.forEach((topic, index) => {
    let best: { x: number; y: number; score: number } | null = null;
    for (let attempt = 0; attempt < 60; attempt += 1) {
      const candidate = sampleCandidate(rand, bounds);
      const x = Math.max(-bounds.maxX, Math.min(bounds.maxX, candidate.x));
      const y = Math.max(-bounds.maxY, Math.min(bounds.maxY, candidate.y));
      if (Math.abs(x) < bounds.keepOutX && Math.abs(y) < bounds.keepOutY) continue;
      const nearest = placed.reduce((min, p) => Math.min(min, Math.hypot((p.x - x) * 0.7, p.y - y)), Infinity);
      if (!best || nearest > best.score) best = { x, y, score: nearest };
      if (nearest >= bounds.minGap) break;
    }
    if (!best) return;
    const weight = Math.max(1, Math.min(5, topic.weight));
    placed.push({
      topic,
      x: best.x,
      y: best.y,
      scale: 0.86 + weight * 0.07,
      delay: 0.38 + index * 0.035,
      floatDuration: 4 + rand() * 4,
      floatDelay: rand() * -6,
      ampX: (rand() > 0.5 ? 1 : -1) * (3 + rand() * 3),
      ampY: (rand() > 0.5 ? 1 : -1) * (8 + rand() * 6),
      rot: (rand() > 0.5 ? 1 : -1) * (1.5 + rand() * 1.5),
    });
  });
  return placed;
}

function pushBubbles(host: HTMLElement, event: MouseEvent<HTMLElement> | null) {
  for (const bubble of host.querySelectorAll<HTMLElement>(".result-ambient__topic")) {
    let pushX = "0px";
    let pushY = "0px";
    if (event) {
      const rect = bubble.getBoundingClientRect();
      const dx = rect.left + rect.width / 2 - event.clientX;
      const dy = rect.top + rect.height / 2 - event.clientY;
      const distance = Math.hypot(dx, dy);
      if (distance > 0 && distance < 120) {
        const strength = ((120 - distance) / 120) * 14;
        pushX = `${((dx / distance) * strength).toFixed(1)}px`;
        pushY = `${((dy / distance) * strength).toFixed(1)}px`;
      }
    }
    bubble.style.setProperty("--push-x", pushX);
    bubble.style.setProperty("--push-y", pushY);
  }
}

export function ResultAmbient({ topics, runId, children }: ResultAmbientProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const reducedMotion = useReducedMotion();
  const [bounds, setBounds] = useState<Bounds | null>(null);

  useLayoutEffect(() => {
    const measure = () => {
      const width = hostRef.current?.clientWidth ?? 880;
      setBounds(boundsFor(width, window.innerWidth));
    };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  const seed = useMemo(() => hashText(topics.map((t) => t.text).join("|")) ^ (runId * 2654435761), [topics, runId]);
  const placed = useMemo(() => (bounds && topics.length ? layout(topics, bounds, seed) : []), [bounds, topics, seed]);
  const canHover = typeof window !== "undefined" && window.matchMedia?.("(hover: hover) and (pointer: fine)").matches;

  return (
    <div
      ref={hostRef}
      className="result-ambient-host"
      onMouseMove={canHover && !reducedMotion ? (event) => pushBubbles(event.currentTarget, event) : undefined}
      onMouseLeave={canHover && !reducedMotion ? (event) => pushBubbles(event.currentTarget, null) : undefined}
    >
      {placed.length ? (
        <div className={`result-ambient${reducedMotion ? " result-ambient--static" : ""}`} aria-hidden="true" data-count={placed.length}>
          {placed.map((item, index) => (
            <motion.span
              key={`${runId}-${item.topic.text}-${index}`}
              className="result-ambient__anchor"
              initial={reducedMotion ? { x: item.x, y: item.y, opacity: 0 } : { x: 0, y: 0, scale: 0.3, opacity: 0 }}
              animate={{ x: item.x, y: item.y, scale: 1, opacity: 1 }}
              transition={
                reducedMotion
                  ? { duration: 0.4, delay: 0.2 }
                  : { type: "spring", stiffness: 150, damping: 13, mass: 0.9, delay: item.delay, opacity: { duration: 0.25, delay: item.delay } }
              }
            >
              <span
                className={`result-ambient__topic result-ambient__topic--${item.topic.sentiment}`}
                style={
                  {
                    "--topic-scale": item.scale,
                    "--float-duration": `${item.floatDuration.toFixed(2)}s`,
                    "--float-delay": `${(item.delay + 0.9 + item.floatDelay).toFixed(2)}s`,
                    "--amp-x": `${item.ampX.toFixed(1)}px`,
                    "--amp-y": `${item.ampY.toFixed(1)}px`,
                    "--rot": `${item.rot.toFixed(2)}deg`,
                  } as CSSProperties
                }
              >
                {item.topic.text}
              </span>
            </motion.span>
          ))}
        </div>
      ) : null}
      <div className="result-ambient-host__content">{children}</div>
    </div>
  );
}
