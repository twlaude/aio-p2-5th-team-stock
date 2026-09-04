import { useLayoutEffect, useMemo, useRef, useState, type CSSProperties, type MouseEvent, type ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";

import type { TopicEvidence } from "../analysis/deriveEvidence";
import { shortenTopic } from "./shortenTopic";
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
  label: string;
  halfW: number;
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

export const COMPACT_TOPIC_LIMIT = 6;

export function selectCompactTopics(topics: TopicEvidence[]) {
  return topics
    .map((topic, index) => ({ topic, index, label: shortenTopic(topic.text) }))
    .sort((a, b) => b.topic.weight - a.topic.weight)
    .slice(0, COMPACT_TOPIC_LIMIT);
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
  containerHalf: number;
  hostHalfH: number;
  bubble: BubbleRect;
  avoid: { left: number; right: number; top: number; bottom: number }[];
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

function boundsFor(host: HTMLElement, availableWidth: number): Bounds | null {
  const bubble = measureBubble(host);
  if (!bubble) return null;
  const hostRect = host.getBoundingClientRect();
  const hostCenterX = hostRect.left + hostRect.width / 2;
  const hostCenterY = hostRect.top + host.offsetHeight / 2;
  const avoid = [...(host.closest(".result-section") ?? host).querySelectorAll<HTMLElement>(
    ".one-liner__caption, .one-liner__materials, .why-button",
  )].map((element) => {
    const rect = element.getBoundingClientRect();
    const centerX = (rect.left + rect.right) / 2 - hostCenterX;
    const centerY = (rect.top + rect.bottom) / 2 - hostCenterY;
    return {
      left: centerX - element.offsetWidth / 2,
      right: centerX + element.offsetWidth / 2,
      top: centerY - element.offsetHeight / 2,
      bottom: centerY + element.offsetHeight / 2,
    };
  });
  return { mobile: availableWidth < 600, containerHalf: availableWidth / 2, hostHalfH: host.offsetHeight / 2, bubble, avoid };
}

/** 칩 실제 폭(반폭) 측정 — 캔버스 measureText. 캔버스 없으면(jsdom) 글자수 근사 */
function measureHalfWidths(host: HTMLElement, labels: string[], mobile: boolean): number[] {
  const fontSize = mobile ? 12 : 13;
  const extra = (mobile ? 20 : 26) + 3; // 좌우 padding + border
  const ctx = document.createElement("canvas").getContext?.("2d") ?? null;
  if (!ctx) return labels.map((label) => (label.length * fontSize + extra) / 2);
  ctx.font = `700 ${fontSize}px ${getComputedStyle(host).fontFamily || "sans-serif"}`;
  return labels.map((label) => (ctx.measureText(label).width + extra) / 2);
}

const CHIP_HALF_H = 15;
const GAP = 12; // 부유 진폭(x≤5, y≤11)까지 감안한 여유

function overlaps(a: { x: number; y: number; halfW: number }, b: { x: number; y: number; halfW: number }, gap = GAP) {
  return Math.abs(a.x - b.x) < a.halfW + b.halfW + gap && Math.abs(a.y - b.y) < CHIP_HALF_H * 2 + gap;
}

function overlapsTarget(chip: { x: number; y: number; halfW: number }, target: Bounds["avoid"][number], gap: number) {
  return chip.x + chip.halfW + gap > target.left && chip.x - chip.halfW - gap < target.right
    && chip.y + CHIP_HALF_H + gap > target.top && chip.y - CHIP_HALF_H - gap < target.bottom;
}

/**
 * 링 배치: 캡션·말풍선·재료줄을 한 덩어리로 보고 그 바깥 타원 위에 키워드를 등간격(360°)으로 두른다.
 * 형 지시(2026-09-03): "주변으로 간격 일정하게 360도로 두르게". 아래 중앙(why 버튼) 근처 점은 바깥으로 밀고, 화면이 좁아 옆구리가 안 나오면 그 점은 뺀다.
 * 모바일은 네 귀퉁이만(위 2·아래 2). 랜덤은 부유 리듬에만.
 * 2026-09-04(오현님): 주제를 shortenTopic으로 축약하고, 칩 실제 폭을 재서 앞 칩과 겹치면 각도 방향으로 바깥으로 민다. 화면 밖까지 밀려야 하면 그 칩은 뺀다.
 */
function layout(topics: TopicEvidence[], bounds: Bounds, seed: number, halfWidths: number[], labels: string[]): Placed[] {
  const rand = mulberry32(seed);
  const { bubble, mobile, hostHalfH, containerHalf } = bounds;
  const constrained = containerHalf < 600;
  const collisionGap = constrained ? 24 : GAP;
  const widest = halfWidths.length ? Math.max(...halfWidths) : mobile ? 44 : 54;
  const slots: { x: number; y: number; angle: number }[] = [];

  if (mobile) {
    // 위 2개는 캡션 양옆(차트 안 건드림), 아래 2개는 why 버튼 아래 양옆
    const xTop = Math.min(bubble.halfW - 30, containerHalf - widest - 6);
    const xBottom = Math.max(60, bubble.halfW - 40);
    slots.push(
      { x: -xTop, y: -hostHalfH + 16, angle: Math.PI },
      { x: xTop, y: -hostHalfH + 16, angle: 0 },
      { x: -xBottom, y: hostHalfH + 98, angle: Math.PI },
      { x: xBottom, y: hostHalfH + 98, angle: 0 },
    );
  } else {
    const count = 12;
    const rx = Math.min(bubble.halfW + 64, containerHalf - widest - 10);
    const ry = hostHalfH + 34;
    const step = (Math.PI * 2) / count;
    for (let i = 0; i < count; i += 1) {
      const angle = -Math.PI / 2 + step / 2 + i * step; // 반 스텝 오프셋: 위·아래 정중앙은 비움
      slots.push({ x: Math.cos(angle) * rx, y: Math.sin(angle) * ry, angle });
    }
  }

  const order = topics
    .map((topic, index) => ({ topic, index }))
    .sort((a, b) => b.topic.weight - a.topic.weight)
    .slice(0, slots.length);

  const placed: Placed[] = [];
  order.forEach(({ topic, index: topicIndex }, slotIndex) => {
    const slot = slots[slotIndex];
    const halfW = halfWidths[topicIndex] ?? widest;
    let { x, y } = slot;
    if (!mobile) {
      const bubbleMidY = (bubble.top + bubble.bottom) / 2;
      const bubbleHalfH = (bubble.bottom - bubble.top) / 2;
      if (Math.abs(y - bubbleMidY) < bubbleHalfH + CHIP_HALF_H) {
        // 옆구리: 말풍선 테두리 바깥으로. 화면 밖이면 뺀다
        const needX = bubble.halfW + halfW + 10;
        if (needX > containerHalf - 8) return;
        x = Math.sign(x) * needX;
      }
      if (Math.sin(slot.angle) > 0.85) {
        // 아래 중앙 근처: why 버튼(반폭 ~90)과 안 겹치게 바깥으로
        x = Math.sign(x) * Math.max(Math.abs(x), 150 + halfW + 12);
      }
    }
    // 충돌 해소: 앞서 놓인 칩과 겹치면 각도 방향으로 바깥으로 민다(최대 8단계). 화면 밖이면 뺀다
    const dirX = Math.cos(slot.angle);
    const dirY = Math.sin(slot.angle);
    let tries = 0;
    while (placed.some((other) => overlaps({ x, y, halfW }, other, collisionGap))
      || (constrained && bounds.avoid.some((target) => overlapsTarget({ x, y, halfW }, target, GAP)))) {
      if (tries >= 8) return;
      x += dirX * 22;
      y += dirY * 12;
      tries += 1;
    }
    if (Math.abs(x) + halfW > containerHalf - 6) return;

    const weight = Math.max(1, Math.min(5, topic.weight));
    placed.push({
      topic,
      label: labels[topicIndex] ?? topic.text,
      halfW,
      x,
      y,
      scale: 0.84 + weight * 0.06,
      delay: 0.4 + placed.length * 0.045,
      floatDuration: 4.5 + rand() * 3.5,
      floatDelay: rand() * -6,
      ampX: (rand() > 0.5 ? 1 : -1) * (2 + rand() * 3),
      ampY: (rand() > 0.5 ? 1 : -1) * (6 + rand() * 5),
      rot: (rand() > 0.5 ? 1 : -1) * (1 + rand() * 1.5),
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
      if (!hostRef.current) return;
      setBounds(boundsFor(hostRef.current, hostRef.current.clientWidth));
    };
    measure();
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(measure);
    if (hostRef.current) observer?.observe(hostRef.current);
    window.addEventListener("resize", measure);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);

  const seed = useMemo(() => hashText(topics.map((t) => t.text).join("|")) ^ (runId * 2654435761), [topics, runId]);
  const labels = useMemo(() => topics.map((t) => shortenTopic(t.text)), [topics]);
  const compactTopics = useMemo(() => selectCompactTopics(topics), [topics]);
  const placed = useMemo(() => {
    if (!bounds || bounds.mobile || !topics.length || !hostRef.current) return [];
    const halfWidths = measureHalfWidths(hostRef.current, labels, bounds.mobile);
    return layout(topics, bounds, seed, halfWidths, labels);
  }, [bounds, topics, seed, labels]);
  const canHover = typeof window !== "undefined" && window.matchMedia?.("(hover: hover) and (pointer: fine)").matches;

  return (
    <div
      ref={hostRef}
      className="result-ambient-host"
      onMouseMove={canHover && !reducedMotion ? (event) => pushBubbles(event.currentTarget, event) : undefined}
      onMouseLeave={canHover && !reducedMotion ? (event) => pushBubbles(event.currentTarget, null) : undefined}
    >
      {bounds?.mobile && compactTopics.length ? (
        <div className="result-ambient__compact" aria-hidden="true" data-count={compactTopics.length}>
          {compactTopics.map(({ topic, index, label }) => (
            <span
              key={`${runId}-${topic.text}-${index}`}
              className={`result-ambient__topic result-ambient__topic--${topic.sentiment}`}
            >
              {label}
            </span>
          ))}
        </div>
      ) : null}
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
                {item.label}
              </span>
            </motion.span>
          ))}
        </div>
      ) : null}
      <div className="result-ambient-host__content">{children}</div>
    </div>
  );
}
