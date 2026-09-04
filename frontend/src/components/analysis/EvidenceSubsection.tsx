import { AlertCircle, CheckCircle2, ExternalLink, FileText, MessageCircle, Newspaper } from "lucide-react";
import { useState, type CSSProperties } from "react";

import { type CommunityEvidence, type DisclosureChecks, type EvidenceItem, type TopicEvidence, fgiLabel } from "./deriveEvidence";
import "./evidenceSubsection.css";
import { useInView } from "./useInView";

type EvidenceKind = "community" | "news" | "disclosure";

interface EvidenceSubsectionProps {
  id: string;
  kind: EvidenceKind;
  summary: string | null;
  count: number;
  community?: CommunityEvidence | null;
  items?: EvidenceItem[];
  checks?: DisclosureChecks;
  failed?: boolean;
  index?: number;
  onRetry?: () => void | Promise<void>;
}

const copy = {
  community: { title: "커뮤니티 반응", footer: "네이버 종목토론방 집계 · 사실이 아닌 시장 반응", failedBody: "커뮤니티 서버가 응답하지 않아 이 부분은 뺐어요. 시장 관심 온도는 뉴스·가격만으로 계산됐어요.", failedFooter: "MCP 부분 실패 · status: partial_success", Icon: MessageCircle },
  news: { title: "최신 뉴스", footer: "원문 링크 제공 · 제목만으로 원인 단정 금지", failedBody: "뉴스 데이터를 불러오지 못해 이 부분은 뺐어요. 남은 공식 자료만으로 정리했어요.", failedFooter: "뉴스 부분 실패 · status: partial_success", Icon: Newspaper },
  disclosure: { title: "기업보고서 · 공시", footer: "공식 자료와 AI 해석은 구분 표시", failedBody: "공시 데이터를 불러오지 못해 이 부분은 뺐어요. 뉴스와 가격 흐름만으로 정리했어요.", failedFooter: "공시 부분 실패 · status: partial_success", Icon: FileText },
} satisfies Record<EvidenceKind, { title: string; footer: string; failedBody: string; failedFooter: string; Icon: typeof MessageCircle }>;

const classes = (...items: Array<string | false>) => items.filter(Boolean).join(" ");
const topicClass = (sentiment: TopicEvidence["sentiment"]) => `analysis-evidence-topic analysis-evidence-topic--${sentiment}`;

function metaText(kind: EvidenceKind, count: number, community: CommunityEvidence | null | undefined) {
  if (kind === "community") return community ? `7일 · 표본 ${community.samples}건` : "집계 요약";
  if (kind === "news") return count > 0 ? `${count}건 · 중복 제거` : "요약 중심";
  return count > 0 ? `DART 30일 · ${count}건` : "DART 요약";
}


function CommunityBody({ community, summary, visible }: { community: CommunityEvidence | null | undefined; summary: string | null; visible: boolean }) {
  const fgi = typeof community?.fgi === "number" ? Math.max(0, Math.min(100, community.fgi)) : null;
  const fgiText = fgiLabel(community?.fgi);
  const metrics = community
    ? [
        ["긍정", community.positive, "positive"],
        ["중립", community.neutral, "neutral"],
        ["부정", community.negative, "negative"],
      ] as const
    : [];

  return (
    <>
      {summary ? <p className="analysis-evidence-subsection__summary">{summary}</p> : null}
      {community ? (
        <div className="analysis-community-grid">
          <div className="analysis-community-metrics" aria-label="커뮤니티 반응 비율">
            {metrics.map(([label, value, tone], index) => (
              <div className="analysis-community-metric" key={label}>
                <div className="analysis-community-metric__number">{value}%</div>
                <div className="analysis-community-metric__label">{label}</div>
                <div className="analysis-community-metric__track">
                  <span className={`analysis-community-metric__fill analysis-community-metric__fill--${tone}`} style={{ "--metric-width": `${value}%`, "--metric-delay": `${index * 300}ms` } as CSSProperties} />
                </div>
              </div>
            ))}
          </div>
          {fgi !== null && fgiText ? (
            <div className="analysis-community-fgi" aria-label={`공포탐욕 지수 ${fgi}`}>
              <svg viewBox="0 0 160 92" role="img" aria-hidden="true">
                <path className="analysis-community-fgi__track" d="M24 78 A56 56 0 0 1 136 78" pathLength="100" />
                <path className="analysis-community-fgi__fill" d="M24 78 A56 56 0 0 1 136 78" pathLength="100" style={{ "--fgi-width": visible ? fgi : 0 } as CSSProperties} />
              </svg>
              <div className="analysis-community-fgi__value">{fgi}</div>
              <div className="analysis-community-fgi__label">{fgiText}</div>
            </div>
          ) : null}
        </div>
      ) : null}
      {community?.topics.length ? (
        <div className="analysis-topic-area" aria-label="커뮤니티 주요 주제">
          <div className="analysis-topic-area__title">주요 주제</div>
          <div className="analysis-topic-list">
            {community.topics.slice(0, 8).map((topic) => <span className={topicClass(topic.sentiment)} key={topic.text}>{topic.text}</span>)}
          </div>
        </div>
      ) : null}
    </>
  );
}

function SourceLink({ item, kind }: { item: EvidenceItem; kind: Exclude<EvidenceKind, "community"> }) {
  const meta = kind === "disclosure" ? [item.receiptNo, item.publishedAtLabel].filter(Boolean).join(" · ") : [item.publisher, item.publishedAtLabel].filter(Boolean).join(" · ");
  const content = (
    <>
      <span className="analysis-source-item__title">{item.title}</span>
      {meta ? <span className="analysis-source-item__meta">{meta}</span> : null}
      {item.issueCount && item.issueCount > 1 ? <span className="analysis-source-item__badge">기사 {item.issueCount}건</span> : null}
      {item.url ? <ExternalLink size={15} strokeWidth={1.8} aria-hidden="true" /> : null}
    </>
  );
  return item.url ? <a className="analysis-source-item" href={item.url} target="_blank" rel="noreferrer">{content}</a> : <div className="analysis-source-item">{content}</div>;
}

function SourceList({ items, kind }: { items: EvidenceItem[]; kind: Exclude<EvidenceKind, "community"> }) {
  return items.length ? <div className="analysis-source-list">{items.map((item) => <SourceLink item={item} kind={kind} key={`${item.title}-${item.publishedAtLabel}`} />)}</div> : null;
}

function DisclosureCheckPanels({ checks }: { checks: DisclosureChecks | undefined }) {
  const panels = [
    { title: "확인된 것", items: checks?.confirmed ?? [], Icon: CheckCircle2 },
    { title: "아직 확인 안 된 것", items: checks?.unconfirmed ?? [], Icon: AlertCircle },
  ];
  if (!panels.some((panel) => panel.items.length)) return null;
  return (
    <div className="analysis-disclosure-checks">
      {panels.map(({ title, items, Icon }) => (
        <div className="analysis-disclosure-checks__panel" key={title}>
          <h4><Icon size={17} strokeWidth={1.8} />{title}</h4>
          <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      ))}
    </div>
  );
}

export function EvidenceSubsection({ id, kind, summary, count, community, items = [], checks, failed = false, index = 0, onRetry }: EvidenceSubsectionProps) {
  const { ref, inView } = useInView<HTMLElement>();
  const [shimmer, setShimmer] = useState(false);
  const { Icon } = copy[kind];
  const handleRetry = () => {
    setShimmer(true);
    window.setTimeout(() => {
      setShimmer(false);
      void onRetry?.();
    }, 600);
  };

  return (
    <section
      id={id}
      ref={ref}
      className={classes("analysis-evidence-subsection", `analysis-evidence-subsection--${kind}`, inView && "analysis-evidence-subsection--visible", failed && "analysis-evidence-subsection--failed", shimmer && "analysis-evidence-subsection--shimmer")}
      style={{ "--subsection-delay": `${index * 80}ms` } as CSSProperties}
    >
      <div className="analysis-evidence-subsection__surface">
        <header className="analysis-evidence-subsection__header">
          <div className="analysis-evidence-subsection__title"><Icon size={24} strokeWidth={1.9} /><h3>{copy[kind].title}</h3></div>
          <div className="analysis-evidence-subsection__meta">{metaText(kind, count, community)}</div>
        </header>
        {failed ? (
          <div className="analysis-evidence-subsection__failed-state">
            <div className="analysis-evidence-subsection__failed-label"><AlertCircle size={17} strokeWidth={2} />불러오지 못함</div>
            <p>{copy[kind].failedBody}</p>
            <button className="analysis-evidence-subsection__retry" type="button" onClick={handleRetry}>다시 시도</button>
            <div className="analysis-evidence-subsection__footer">{copy[kind].failedFooter}</div>
          </div>
        ) : (
          <>
            {kind === "community" ? <CommunityBody community={community} summary={summary} visible={inView} /> : null}
            {kind === "news" ? <><p className="analysis-evidence-subsection__summary">{summary}</p><SourceList items={items} kind="news" /></> : null}
            {kind === "disclosure" ? <><p className="analysis-evidence-subsection__summary">{summary}</p><SourceList items={items} kind="disclosure" /><DisclosureCheckPanels checks={checks} /></> : null}
            <div className="analysis-evidence-subsection__footer">{kind === "community" && community ? `네이버 종목토론방 집계 · 표본 ${community.samples}건 · 사실이 아닌 시장 반응` : copy[kind].footer}</div>
          </>
        )}
      </div>
    </section>
  );
}
