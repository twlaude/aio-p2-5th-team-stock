import { useEffect, useState, type CSSProperties } from "react";

import type { DataCoverage, EvidenceLevel } from "../../services/backend_api/client";
import { evidenceLevelText } from "./deriveEvidence";
import "./gaugeCard.css";
import { useInView } from "./useInView";

type GaugeCardProps =
  | {
      variant: "temperature";
      score: number;
      label: string;
      dataCoverage: DataCoverage[];
    }
  | {
      variant: "evidence";
      level: EvidenceLevel;
      reason: string;
    };

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function useCountUp(target: number, active: boolean) {
  const [value, setValue] = useState(() => (prefersReducedMotion() ? target : 0));

  useEffect(() => {
    if (!active) {
      return;
    }
    if (prefersReducedMotion()) {
      setValue(target);
      return;
    }

    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - start) / 900, 1);
      const eased = 1 - (1 - progress) ** 3;
      setValue(Math.round(target * eased));
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [active, target]);

  return value;
}

export function GaugeCard(props: GaugeCardProps) {
  const { ref, inView } = useInView<HTMLDivElement>();
  const temperature = props.variant === "temperature" ? Math.max(0, Math.min(100, props.score)) : 0;
  const count = useCountUp(temperature, inView && props.variant === "temperature");

  if (props.variant === "temperature") {
    const includesCommunity = props.dataCoverage.includes("community");
    return (
      // motion 4b-10
      <div ref={ref} className={["analysis-gauge-card", inView ? "analysis-gauge-card--visible" : ""].join(" ")}>
        <div className="analysis-gauge-card__caption">시장 관심 온도</div>
        <div className="analysis-gauge-card__headline">
          <span className="analysis-gauge-card__number">{count}</span>
          <span className="analysis-gauge-card__label">{props.label}</span>
        </div>
        <div className="analysis-gauge-card__track">
          <div className="analysis-gauge-card__fill" style={{ "--gauge-width": `${temperature}%` } as CSSProperties} />
        </div>
        <div className="analysis-gauge-card__description">
          {includesCommunity ? "커뮤니티 언급량 · 뉴스 기사량 · 거래량 변화 기준. 상승 가능성이 아니에요." : "뉴스 기사량 · 거래량 변화 기준 (커뮤니티 제외)"}
        </div>
      </div>
    );
  }

  const level = evidenceLevelText(props.level);
  return (
    // motion 4b-10
    <div ref={ref} className={["analysis-gauge-card", inView ? "analysis-gauge-card--visible" : ""].join(" ")}>
      <div className="analysis-gauge-card__caption">공시·보고서로 확인된 정도</div>
      <div className="analysis-gauge-card__headline">
        <span className="analysis-gauge-card__number">{level.text}</span>
      </div>
      <div className="analysis-gauge-card__segments" aria-label={`공시·보고서로 확인된 정도 ${level.text}`}>
        {[0, 1, 2].map((index) => (
          <span
            key={index}
            className={["analysis-gauge-card__segment", index < level.segments ? "analysis-gauge-card__segment--filled" : ""].join(" ")}
            style={{ "--segment-delay": `${index * 120}ms` } as CSSProperties}
          />
        ))}
      </div>
      <div className="analysis-gauge-card__description">{props.reason}</div>
    </div>
  );
}
