import { AlertCircle } from "lucide-react";
import { useState, type CSSProperties, type MouseEvent } from "react";

import type { SourceType } from "../../services/backend_api/client";
import { type CommunityEvidence, type EvidenceItem, fgiLabel } from "./deriveEvidence";
import "./evidenceCard.css";
import { useInView } from "./useInView";

type EvidenceCardKind = SourceType;

interface EvidenceCardProps {
  kind: EvidenceCardKind;
  summary: string | null;
  count: number;
  items?: EvidenceItem[];
  community?: CommunityEvidence | null;
  failed?: boolean;
  index?: number;
  onRetry?: () => void | Promise<void>;
}

const copy = {
  community: {
    title: "커뮤니티 반응",
    footer: "네이버 종목토론방 집계 · 사실이 아닌 시장 반응",
    failedBody: "커뮤니티 서버가 응답하지 않아 이 부분은 뺐어요. 시장 관심 온도는 뉴스·가격만으로 계산됐어요.",
    failedFooter: "MCP 부분 실패 · status: partial_completed",
  },
  news: {
    title: "최신 뉴스",
    footer: "원문 링크 제공 · 제목만으로 원인 단정 금지",
    failedBody: "뉴스 데이터를 불러오지 못해 이 부분은 뺐어요. 남은 공식 자료만으로 정리했어요.",
    failedFooter: "뉴스 부분 실패 · status: partial_completed",
  },
  disclosure: {
    title: "기업보고서 · 공시",
    footer: "공식 자료와 AI 해석은 구분 표시",
    failedBody: "공시 데이터를 불러오지 못해 이 부분은 뺐어요. 뉴스와 가격 흐름만으로 정리했어요.",
    failedFooter: "공시 부분 실패 · status: partial_completed",
  },
} satisfies Record<EvidenceCardKind, { title: string; footer: string; failedBody: string; failedFooter: string }>;

function metaText(kind: EvidenceCardKind, count: number, community: CommunityEvidence | null | undefined) {
  if (kind === "community") {
    return community ? `7일 · 표본 ${community.samples}건` : "7일";
  }
  if (kind === "news") {
    return `${count}건 · 중복 제거`;
  }
  return "DART 30일";
}

function communityWidths(community: CommunityEvidence | null | undefined) {
  const positive = community?.positive ?? 0;
  const neutral = community?.neutral ?? 0;
  const negative = community?.negative ?? 0;
  const total = positive + neutral + negative;
  if (total <= 0) {
    return [0, 0, 0];
  }
  return [positive, neutral, negative].map((value) => (value / total) * 100);
}

export function EvidenceCard({ kind, summary, count, items = [], community, failed = false, index = 0, onRetry }: EvidenceCardProps) {
  const { ref, inView } = useInView<HTMLDivElement>();
  const [shimmer, setShimmer] = useState(false);
  const widths = communityWidths(community);
  const label = community?.fgi === null ? null : fgiLabel(community?.fgi);

  const handleRetry = () => {
    setShimmer(true);
    window.setTimeout(() => {
      setShimmer(false);
      void onRetry?.();
    }, 600);
  };

  const handleMouseMove = (event: MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - 0.5;
    const y = (event.clientY - rect.top) / rect.height - 0.5;
    event.currentTarget.style.setProperty("--tilt-x", `${(-y * 8).toFixed(2)}deg`);
    event.currentTarget.style.setProperty("--tilt-y", `${(x * 8).toFixed(2)}deg`);
  };

  const resetTilt = (event: MouseEvent<HTMLDivElement>) => {
    event.currentTarget.style.setProperty("--tilt-x", "0deg");
    event.currentTarget.style.setProperty("--tilt-y", "0deg");
  };

  return (
    // motion 4b-11, motion 4b-12, motion 4b-17
    <div
      ref={ref}
      className={[
        "analysis-evidence-card",
        inView ? "analysis-evidence-card--visible" : "",
        failed ? "analysis-evidence-card--failed" : "",
        shimmer ? "analysis-evidence-card--shimmer" : "",
      ].join(" ")}
      style={{ "--card-delay": `${index * 80}ms` } as CSSProperties}
      onMouseMove={handleMouseMove}
      onMouseLeave={resetTilt}
    >
      <div className="analysis-evidence-card__header">
        <div className="analysis-evidence-card__title">{copy[kind].title}</div>
        {failed ? (
          <div className="analysis-evidence-card__failed-label">
            <AlertCircle size={14} strokeWidth={2} />
            <span>불러오지 못함</span>
          </div>
        ) : (
          <div className="analysis-evidence-card__meta">{metaText(kind, count, community)}</div>
        )}
      </div>

      {failed ? (
        <>
          <div className="analysis-evidence-card__summary">{copy[kind].failedBody}</div>
          <button className="analysis-evidence-card__retry" type="button" onClick={handleRetry}>
            다시 시도
          </button>
          <div className="analysis-evidence-card__footer">{copy[kind].failedFooter}</div>
        </>
      ) : kind === "community" && community ? (
        <>
          <div className="analysis-evidence-card__stack" aria-label="커뮤니티 반응 비율">
            {widths.map((width, segmentIndex) => (
              <span
                key={segmentIndex}
                className={`analysis-evidence-card__stack-segment analysis-evidence-card__stack-segment--${segmentIndex}`}
                style={
                  {
                    "--segment-width": `${width}%`,
                    "--segment-grow-delay": `${segmentIndex * 300}ms`,
                  } as CSSProperties
                }
              />
            ))}
          </div>
          <div className="analysis-evidence-card__body">
            긍정 {community.positive}% · 중립 {community.neutral}% · 부정 {community.negative}%
          </div>
          <div className="analysis-evidence-card__summary">
            {summary}
            {community.fgi !== null && label ? (
              <>
                {" "}
                공포탐욕 {community.fgi} <span className="analysis-evidence-card__mute">{label}</span>
              </>
            ) : null}
          </div>
          <div className="analysis-evidence-card__footer">{copy[kind].footer}</div>
        </>
      ) : (
        <>
          <div className="analysis-evidence-card__summary">{summary}</div>
          {items.length > 0 ? (
            <div className="analysis-evidence-card__items">
              {items.map((item) => (
                <div key={`${item.title}-${item.publishedAtLabel}`} className="analysis-evidence-card__item">
                  {item.title}
                  {(item.publisher || item.publishedAtLabel) && (
                    <span className="analysis-evidence-card__mute">
                      {" "}
                      · {[item.publisher, item.publishedAtLabel].filter(Boolean).join(" ")}
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : null}
          <div className="analysis-evidence-card__footer">{copy[kind].footer}</div>
        </>
      )}
    </div>
  );
}
