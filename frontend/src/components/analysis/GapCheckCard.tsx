import { AlertTriangle, CheckCircle2, Info, Scale } from "lucide-react";
import type { CSSProperties } from "react";

import type { GapCheck } from "./deriveEvidence";
import { useInView } from "./useInView";
import "./gapCheckCard.css";

interface GapCheckCardProps {
  id: string;
  gap: GapCheck;
  index: number;
}

const LEVEL_LABEL = { large: "온도차 큼", some: "온도차 있음", small: "비슷함", quiet: "조용한 편" } as const;
const TONE_ICON = { warn: AlertTriangle, ok: CheckCircle2, info: Info } as const;

/** 환호 vs 근거 — 시장 관심 온도와 공식 확인 정도의 온도차를 한눈에. 형 요청(2026-09-03): "남들이 다 환호하는데 실제로는 환호할 거리가 아니라면 주의". */
export function GapCheckCard({ id, gap, index }: GapCheckCardProps) {
  const { ref, inView } = useInView<HTMLElement>();
  const confirmPercent = [0, 28, 62, 96][gap.confirmSegments];
  return (
    <section
      id={id}
      ref={ref}
      className={["analysis-gap", `analysis-gap--${gap.level}`, inView ? "analysis-gap--visible" : ""].join(" ")}
      style={{ "--subsection-delay": `${index * 80}ms` } as CSSProperties}
    >
      <div className="analysis-gap__surface">
        <header className="analysis-gap__header">
          <div className="analysis-gap__title"><Scale size={24} strokeWidth={1.9} /><h3>환호 vs 근거</h3></div>
          <div className={`analysis-gap__badge analysis-gap__badge--${gap.level}`}>{LEVEL_LABEL[gap.level]}</div>
        </header>
        <p className="analysis-gap__verdict">{gap.verdict}</p>
        <div className="analysis-gap__bars">
          <div className="analysis-gap__bar">
            <div className="analysis-gap__bar-label"><span>시장 관심 온도</span><strong>{gap.heat}</strong></div>
            <div className="analysis-gap__track"><span className="analysis-gap__fill analysis-gap__fill--heat" style={{ "--fill": `${gap.heat}%` } as CSSProperties} /></div>
          </div>
          <div className="analysis-gap__bar">
            <div className="analysis-gap__bar-label"><span>공시·보고서로 확인</span><strong>{["", "아직 조금", "절반쯤", "많이 확인됨"][gap.confirmSegments]}</strong></div>
            <div className="analysis-gap__track"><span className="analysis-gap__fill analysis-gap__fill--confirm" style={{ "--fill": `${confirmPercent}%` } as CSSProperties} /></div>
          </div>
        </div>
        {gap.signals.length ? (
          <ul className="analysis-gap__signals">
            {gap.signals.map((signal) => {
              const Icon = TONE_ICON[signal.tone];
              return (
                <li className={`analysis-gap__signal analysis-gap__signal--${signal.tone}`} key={signal.text}>
                  <Icon size={16} strokeWidth={2} aria-hidden="true" />
                  <span>{signal.text}</span>
                </li>
              );
            })}
          </ul>
        ) : null}
        <p className="analysis-gap__advice">{gap.advice}</p>
        <div className="analysis-gap__footer">온도차는 매수·매도 신호가 아니라 "확인 순서"를 정하는 기준이에요.</div>
      </div>
    </section>
  );
}
