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
      weightCovered: number;
      volumeBasis?: string | null;
      volumeAsOf?: string | null;
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

export function temperatureDescription(dataCoverage: DataCoverage[], weightCovered: number) {
  const primary = dataCoverage.includes("community")
    ? "거래량 변화 · 뉴스 기사량 · 커뮤니티 글 수 · 공포탐욕 강도 기준. 이 종목의 평소 대비예요. 상승 가능성이 아니에요."
    : "거래량 변화 · 뉴스 기사량 기준 (커뮤니티 제외)";
  const partial = weightCovered < 100 ? "일부 자료를 못 받아 받은 자료만으로 계산했어요." : null;
  return { primary, partial };
}

export function lastSessionVolumeDescription(volumeBasis?: string | null, volumeAsOf?: string | null) {
  const match = volumeBasis === "last_session" && volumeAsOf?.match(/^\d{4}-(\d{2})-(\d{2})$/);
  if (!match) return null;
  return `거래량은 ${Number(match[1])}월 ${Number(match[2])}일 거래일 기준이에요.`;
}

export function GaugeCard(props: GaugeCardProps) {
  const { ref, inView } = useInView<HTMLDivElement>();
  const temperature = props.variant === "temperature" ? Math.max(0, Math.min(100, props.score)) : 0;
  const count = useCountUp(temperature, inView && props.variant === "temperature");

  if (props.variant === "temperature") {
    const description = temperatureDescription(props.dataCoverage, props.weightCovered);
    const volumeDescription = lastSessionVolumeDescription(props.volumeBasis, props.volumeAsOf);
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
          {description.primary}
          {description.partial ? (
            <>
              <br />
              {description.partial}
            </>
          ) : null}
          {volumeDescription ? (
            <>
              <br />
              {volumeDescription}
            </>
          ) : null}
        </div>
      </div>
    );
  }

  const level = evidenceLevelText(props.level);
  return (
    // motion 4b-10
    <div ref={ref} className={["analysis-gauge-card", inView ? "analysis-gauge-card--visible" : ""].join(" ")}>
      <div className="analysis-gauge-card__caption">뉴스 내용이 공시·보고서로 뒷받침되는 정도</div>
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
