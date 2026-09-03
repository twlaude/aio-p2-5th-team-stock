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
      className={["mascot", `mascot--${state}`, className].filter(Boolean).join(" ")}
      data-state={state}
      width={size}
      height={size}
      viewBox="0 0 120 140"
      fill="none"
      role="img"
      aria-label="살래말래 마스코트"
    >
      <path d="M60 14 C90 14 106 36 106 64 C106 92 88 108 60 108 C32 108 14 92 14 64 C14 36 30 14 60 14 Z" fill="#ffffff" stroke="var(--c-ink)" strokeWidth="2.5" />
      <circle cx="34" cy="74" r="6" fill="var(--c-cheek)" />
      <circle cx="86" cy="74" r="6" fill="var(--c-cheek)" />
      <rect x="42" y="52" width="6" height="14" rx="3" fill="var(--c-ink)" />
      <rect x="72" y="52" width="6" height="14" rx="3" fill="var(--c-ink)" />
      <path d="M48 80 Q60 90 72 80" stroke="var(--c-ink)" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M60 14 C58 8 62 4 66 6" stroke="var(--c-ink)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}
