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
  hostHalfH: number;
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
  return { mobile: viewportWidth <= 480, viewportHalf: viewportWidth / 2, hostHalfH: host.offsetHeight / 2, bubble };
}

/**
 * 링 배치: 캡션·말풍선·재료줄을 한 덩어리로 보고 그 바깥 타원 위에 키워드를 등간격(360°)으로 두른다.
 * 형 지시(2026-09-03): "주변으로 간격 일정하게 360도로 두르게". 아래 중앙(why 버튼) 근처 점은 바깥으로 밀고, 화면이 좁아 옆구리가 안 나오면 그 점은 뺀다.
 * 모바일은 네 귀퉁이만(위 2·아래 2). 랜덤은 부유 리듬에만.
 */
function layout(topics: TopicEvidence[], bounds: Bounds, seed: number): Placed[] {
  const rand = mulberry32(seed);
  const { bubble, mobile, hostHalfH, viewportHalf } = bounds;
  const chipHalfW = mobile ? 44 : 54;
  const chipHalfH = 15;
  const points: { x: number; y: number }[] = [];

  if (mobile) {
    // 위 2개는 캡션 양옆(차트 안 건드림), 아래 2개는 why 버튼 아래 양옆
    const xTop = Math.min(bubble.halfW - 30, viewportHalf - chipHalfW - 6);
    const xBottom = Math.max(60, bubble.halfW - 56);
    points.push({ x: -xTop, y: -hostHalfH - 4 }, { x: xTop, y: -hostHalfH - 4 }, { x: -xBottom, y: hostHalfH + 98 }, { x: xBottom, y: hostHalfH + 98 });
  } else {
    const count = 12;
    const rx = Math.min(bubble.halfW + 64, viewportHalf - chipHalfW - 10);
    const ry = hostHalfH + 34;
    const step = (Math.PI * 2) / count;
    for (let i = 0; i < count; i += 1) {
      const angle = -Math.PI / 2 + step / 2 + i * step; // 반 스텝 오프셋: 위·아래 정중앙은 비움
      let x = Math.cos(angle) * rx;
      const y = Math.sin(angle) * ry;
      const bubbleMidY = (bubble.top + bubble.bottom) / 2;
      const bubbleHalfH = (bubble.bottom - bubble.top) / 2;
      if (Math.abs(y - bubbleMidY) < bubbleHalfH + chipHalfH) {
        // 옆구리: 말풍선 테두리 바깥으로. 화면 밖이면 뺀다
        const needX = bubble.halfW + chipHalfW + 10;
        if (needX > viewportHalf - 8) continue;
        x = Math.sign(x) * needX;
      }
      if (Math.sin(angle) > 0.85) {
        // 아래 중앙 근처: why 버튼(반폭 ~90)과 안 겹치게 바깥으로
        x = Math.sign(x) * Math.max(Math.abs(x), 90 + chipHalfW + 14);
      }
      points.push({ x, y });
    }
  }

  const chosen = [...topics].sort((a, b) => b.weight - a.weight).slice(0, points.length);
  return chosen.map((topic, index) => {
    const slot = points[index];
    const weight = Math.max(1, Math.min(5, topic.weight));
    return {
      topic,
      x: slot.x,
      y: slot.y,
      scale: 0.84 + weight * 0.06,
      delay: 0.4 + index * 0.045,
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
