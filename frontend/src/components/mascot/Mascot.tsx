import "./mascot.css";

import { mascotClassName } from "./mascotState";

/** 마스코트 인터페이스 — 상태 8종. 내부 구현은 영역 A 소유. 다른 영역은 import만. */
export type MascotState = "idle" | "typing" | "submit" | "thinking" | "reveal" | "peek" | "wink" | "oops";

export interface MascotProps {
  state?: MascotState;
  size?: number;
  className?: string;
}

export function Mascot({ state = "idle", size = 120, className }: MascotProps) {
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
      </g>
      {state === "typing" ? (
        <g className="mascot__type-pill">
          <rect x="32" y="112" width="58" height="18" rx="9" />
          <text x="42" y="125">삼성전</text>
          <rect className="mascot__cursor" x="76" y="117" width="2" height="10" rx="1" />
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
