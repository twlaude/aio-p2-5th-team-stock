import "./mascot.css";

import { mascotClassName } from "./mascotState";

/** 마스코트 인터페이스 — 화면 흐름 상태 8종 + 공포탐욕 무드 4종(scared·worried·greedy·ecstatic). 내부 구현은 영역 A 소유. 다른 영역은 import만. */
export type MascotState = "idle" | "typing" | "submit" | "thinking" | "reveal" | "peek" | "wink" | "oops" | "scared" | "worried" | "greedy" | "ecstatic";

export interface MascotProps {
  state?: MascotState;
  size?: number;
  className?: string;
  /** typing 상태일 때 말풍선에 보여줄 입력 중인 글자 (끝 4자만 표시) */
  typingText?: string;
}

const TYPING_MAX_CHARS = 4;

export function Mascot({ state = "idle", size = 120, className, typingText = "" }: MascotProps) {
  const typed = Array.from(typingText.trim()).slice(-TYPING_MAX_CHARS).join("");
  const pillWidth = Math.max(30, 18 + typed.length * 13);
  const pillX = 60 - pillWidth / 2;
  return (
    <svg
      className={mascotClassName(state, className)}
      data-state={state}
      width={size}
      height={size}
      viewBox="0 0 120 140"
      fill="none"
      role="img"
      aria-label="살래말래 마스코트"
    >
      <g className="mascot__body">
        <path className="mascot__shell" d="M60 14 C90 14 106 36 106 64 C106 92 88 108 60 108 C32 108 14 92 14 64 C14 36 30 14 60 14 Z" />
        <circle className="mascot__cheek" cx="34" cy="74" r="6" />
        <circle className="mascot__cheek" cx="86" cy="74" r="6" />
        {renderEyes(state)}
        {renderMouth(state)}
        <path className="mascot__sprout" d="M60 14 C58 8 62 4 66 6" />
        {state === "thinking" ? <text className="mascot__q" x="92" y="30">?</text> : null}
        {state === "reveal" ? (
          <>
            <path className="mascot__spark mascot__spark--one" d="M100 20 l3 8 8 3 -8 3 -3 8 -3 -8 -8 -3 8 -3z" />
            <path className="mascot__spark mascot__spark--two" d="M14 30 l2 6 6 2 -6 2 -2 6 -2 -6 -6 -2 6 -2z" />
          </>
        ) : null}
        {state === "oops" ? <path className="mascot__drop" d="M96 44 c0 0 -6 8 -6 12 a6 6 0 0 0 12 0 c0 -4 -6 -12 -6 -12z" /> : null}
        {renderMoodExtras(state)}
      </g>
      {state === "typing" ? (
        <g className="mascot__type-pill">
          <rect x={pillX} y="112" width={pillWidth} height="18" rx="9" />
          <text x={pillX + 10} y="125">{typed}</text>
          <rect className="mascot__cursor" x={pillX + 10 + typed.length * 13} y="117" width="2" height="10" rx="1" />
        </g>
      ) : null}
      {state === "thinking" ? (
        <g className="mascot__bubble">
          <rect x="82" y="36" width="34" height="22" rx="11" />
          <circle className="mascot__dot mascot__dot--one" cx="94" cy="47" r="3" />
          <circle className="mascot__dot mascot__dot--two" cx="103" cy="47" r="3" />
          <circle className="mascot__dot mascot__dot--three" cx="112" cy="47" r="3" />
        </g>
      ) : null}
      {state === "reveal" ? (
        <g className="mascot__reveal-bubble">
          <rect x="76" y="26" width="54" height="30" rx="15" />
          <text x="88" y="45">봤어요</text>
        </g>
      ) : null}
    </svg>
  );
}

function renderEyes(state: MascotState) {
  if (state === "greedy" || state === "ecstatic") {
    const big = state === "ecstatic";
    const cashClass = big ? "mascot__cash mascot__cash--big" : "mascot__cash";
    return (
      <g className="mascot__eyes">
        <text className={cashClass} x="45" y={big ? 69 : 67} textAnchor="middle">$</text>
        <text className={`${cashClass} mascot__cash--late`} x="75" y={big ? 69 : 67} textAnchor="middle">$</text>
      </g>
    );
  }

  if (state === "scared" || state === "worried") {
    const small = state === "scared";
    return (
      <g className="mascot__eyes">
        <rect className="mascot__eye" x="42" y={small ? 55 : 52} width="6" height={small ? 9 : 14} rx="3" />
        <rect className="mascot__eye" x="72" y={small ? 55 : 52} width="6" height={small ? 9 : 14} rx="3" />
        {/* 안쪽이 올라간 걱정 눈썹 (바깥이 높으면 화난 얼굴이 된다) */}
        <path d={small ? "M38 55 L50 49" : "M40 52 L50 48"} />
        <path d={small ? "M82 55 L70 49" : "M80 52 L70 48"} />
      </g>
    );
  }

  if (state === "submit" || state === "reveal") {
    return (
      <g className="mascot__eyes">
        <path d="M40 60 Q45 54 50 60" />
        <path d="M70 60 Q75 54 80 60" />
      </g>
    );
  }

  if (state === "wink") {
    return (
      <g className="mascot__eyes">
        <rect className="mascot__eye" x="42" y="52" width="6" height="14" rx="3" />
        <rect className="mascot__eye mascot__eye--wink-open" x="72" y="52" width="6" height="14" rx="3" />
        <path className="mascot__wink" d="M70 60 Q75 56 80 60" />
      </g>
    );
  }

  return (
    <g className="mascot__eyes">
      <rect className="mascot__eye" x="42" y="52" width="6" height="14" rx="3" />
      <rect className="mascot__eye" x="72" y="52" width="6" height="14" rx="3" />
    </g>
  );
}

function renderMouth(state: MascotState) {
  if (state === "scared") {
    return <path className="mascot__mouth" d="M48 84 q4 -4 8 0 t8 0 t8 0" />;
  }

  if (state === "worried") {
    return <path className="mascot__mouth" d="M48 86 Q60 79 72 86" />;
  }

  if (state === "greedy") {
    return <path className="mascot__mouth mascot__mouth--fill" d="M46 79 Q60 94 74 79 Z" />;
  }

  if (state === "ecstatic") {
    return (
      <>
        <path className="mascot__mouth mascot__mouth--fill" d="M42 76 Q60 104 78 76 Z" />
        <path className="mascot__tongue" d="M54 90 Q60 100 66 90 Z" />
      </>
    );
  }

  if (state === "submit") {
    return <path className="mascot__mouth mascot__mouth--fill" d="M46 78 Q60 96 74 78 Z" />;
  }

  if (state === "thinking") {
    return <circle className="mascot__mouth mascot__mouth--round" cx="60" cy="82" r="5" />;
  }

  if (state === "oops") {
    return <path className="mascot__mouth" d="M48 86 Q60 78 72 86" />;
  }

  return <path className="mascot__mouth" d="M48 80 Q60 90 72 80" />;
}

function renderMoodExtras(state: MascotState) {
  if (state === "scared") {
    return (
      <>
        <path className="mascot__sweat" d="M96 44 c0 0 -6 8 -6 12 a6 6 0 0 0 12 0 c0 -4 -6 -12 -6 -12z" />
        <path className="mascot__sweat mascot__sweat--two" d="M24 40 c0 0 -5 7 -5 10 a5 5 0 0 0 10 0 c0 -3 -5 -10 -5 -10z" />
      </>
    );
  }

  if (state === "worried") {
    return <path className="mascot__sweat" d="M96 44 c0 0 -6 8 -6 12 a6 6 0 0 0 12 0 c0 -4 -6 -12 -6 -12z" />;
  }

  if (state === "greedy") {
    return (
      <>
        <path className="mascot__spark mascot__spark--one" d="M100 20 l3 8 8 3 -8 3 -3 8 -3 -8 -8 -3 8 -3z" />
        <path className="mascot__drool mascot__drool--small" d="M73 86 c0 0 -3 5 -3 8 a3 3 0 0 0 6 0 c0 -3 -3 -8 -3 -8z" />
      </>
    );
  }

  if (state === "ecstatic") {
    return (
      <>
        <path className="mascot__spark mascot__spark--one" d="M100 20 l3 8 8 3 -8 3 -3 8 -3 -8 -8 -3 8 -3z" />
        <path className="mascot__spark mascot__spark--two" d="M14 30 l2 6 6 2 -6 2 -2 6 -2 -6 -6 -2 6 -2z" />
        <path className="mascot__drool" d="M76 84 c2 4 3 9 3 13 a4 4 0 0 1 -8 0 c0 -4 2 -9 5 -13z" />
        <g className="mascot__coin mascot__coin--one">
          <circle cx="102" cy="40" r="7" />
          <text x="102" y="44" textAnchor="middle">$</text>
        </g>
        <g className="mascot__coin mascot__coin--two">
          <circle cx="18" cy="48" r="6" />
          <text x="18" y="51.5" textAnchor="middle">$</text>
        </g>
      </>
    );
  }

  return null;
}
