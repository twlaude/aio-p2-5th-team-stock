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

/** 결론 말풍선의 host 중심 기준 사각형(레이아웃 값, transform 무관) */
interface BubbleRect {
  halfW: number;
  top: number; // host 중심 기준 y (음수)
  bottom: number; // host 중심 기준 y (양수)
}

interface Bounds {
  mobile: boolean;
  viewportHalf: number;
  bubble: BubbleRect;
}

function measureBubble(host: HTMLElement): BubbleRect | null {
  const bubble = host.querySelector<HTMLElement>(".one-liner__bubble");
  if (!bubble) return null;
  let top = 0;
  let node: HTMLElement | null = bubble;
  while (node && node !== host) {
    top += node.offsetTop;
    node = node.offsetParent as HTMLElement | null;
  }
  const centerY = host.offsetHeight / 2;
  return { halfW: bubble.offsetWidth / 2, top: top - centerY, bottom: top + bubble.offsetHeight - centerY };
}

function boundsFor(host: HTMLElement, viewportWidth: number): Bounds | null {
  const bubble = measureBubble(host);
  if (!bubble) return null;
  return { mobile: viewportWidth <= 480, viewportHalf: viewportWidth / 2, bubble };
}

/**
 * 슬롯 배치: 말풍선 위 가장자리 한 줄 + 아래 가장자리 한 줄. 위 줄은 캡션 자리(중앙), 아래 줄은 why 버튼 자리(중앙)를 비운다.
 * 어느 화면 폭에서도 같은 모양 — 랜덤은 ±6px 흔들림과 부유 리듬에만 쓴다.
 */
function layout(topics: TopicEvidence[], bounds: Bounds, seed: number): Placed[] {
  const rand = mulberry32(seed);
  const { bubble, mobile } = bounds;
  const chipW = mobile ? 88 : 104; // 평균 칩 폭(간격 계산용)
  const centerGapTop = mobile ? 96 : 170; // 캡션 자리
  const centerGapBottom = mobile ? 118 : 200; // why 버튼+chevron 자리
  const edgeInset = mobile ? 4 : 24;
  const usableHalf = Math.min(bubble.halfW - edgeInset, bounds.viewportHalf - chipW / 2 - 8);

  const slotsFor = (gap: number, y: number, jitterY: number) => {
    const segment = usableHalf - gap;
    const perSide = Math.max(1, Math.min(mobile ? 1 : 3, Math.floor((segment + 20) / chipW)));
    const slots: { x: number; y: number }[] = [];
    for (let i = 0; i < perSide; i += 1) {
      const t = perSide === 1 ? 0.5 : i / (perSide - 1);
      const x = gap + chipW * 0.45 + t * (segment - chipW * 0.9);
      slots.push({ x: -x, y: y + (rand() - 0.5) * jitterY }, { x, y: y + (rand() - 0.5) * jitterY });
    }
    return slots;
  };

  const rowGap = mobile ? 26 : 34;
  const slots = [
    // 모바일은 캡션이 폭을 다 차지하므로 위 줄을 캡션 위쪽으로 올린다
    ...slotsFor(mobile ? 72 : centerGapTop, mobile ? bubble.top - 50 : bubble.top - rowGap, 12),
    ...slotsFor(centerGapBottom, bubble.bottom + rowGap, 12),
  ];
  if (!mobile && slots.length < 12) {
    // 여유 있으면 아래 두 번째 줄(버튼 아래 바깥쪽)
    slots.push(...slotsFor(centerGapBottom + 60, bubble.bottom + rowGap + 54, 10).slice(0, 12 - slots.length));
  }
  // 바깥쪽부터 안쪽 순으로 정렬해 중앙에서 퍼질 때 먼 것이 먼저 출발
  slots.sort((a, b) => Math.hypot(b.x, b.y) - Math.hypot(a.x, a.y));

  const chosen = [...topics].sort((a, b) => b.weight - a.weight).slice(0, slots.length);
  return chosen.map((topic, index) => {
    const slot = slots[index];
    const weight = Math.max(1, Math.min(5, topic.weight));
    return {
      topic,
      x: slot.x + (rand() - 0.5) * 8,
      y: slot.y,
      scale: 0.84 + weight * 0.06,
      delay: 0.4 + index * 0.04,
      floatDuration: 4.5 + rand() * 3.5,
      floatDelay: rand() * -6,
      ampX: (rand() > 0.5 ? 1 : -1) * (2 + rand() * 3),
      ampY: (rand() > 0.5 ? 1 : -1) * (6 + rand() * 5),
      rot: (rand() > 0.5 ? 1 : -1) * (1 + rand() * 1.5),
    };
  });
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
      if (!hostRef.current) return;
      setBounds(boundsFor(hostRef.current, window.innerWidth));
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
                  : { type: "spring", stiffness: 210, damping: 17, mass: 0.8, delay: item.delay, opacity: { duration: 0.22, delay: item.delay } }
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
