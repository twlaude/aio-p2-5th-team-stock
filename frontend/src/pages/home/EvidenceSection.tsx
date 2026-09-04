import { MessageCircle, Newspaper, FileText, Scale } from "lucide-react";
import { useEffect, useState, type CSSProperties } from "react";

import { EvidenceSubsection } from "../../components/analysis/EvidenceSubsection";
import { GapCheckCard } from "../../components/analysis/GapCheckCard";
import { GaugeCard } from "../../components/analysis/GaugeCard";
import { PartialNotice, type FailedKind } from "../../components/analysis/PartialNotice";
import { PeekMascot } from "../../components/analysis/PeekMascot";
import { countOf, deriveCommunity, deriveDisclosureChecks, deriveGapCheck, deriveItems } from "../../components/analysis/deriveEvidence";
import { useSearch } from "../../state/searchStore";
import "./evidenceSection.css";

type EvidenceTab = "gap" | "community" | "news" | "disclosure";

const tabs = [
  { key: "gap", id: "evidence-gap", label: "분위기 vs 근거", Icon: Scale },
  { key: "community", id: "evidence-community", label: "커뮤니티 반응", Icon: MessageCircle },
  { key: "news", id: "evidence-news", label: "최신 뉴스", Icon: Newspaper },
  { key: "disclosure", id: "evidence-disclosure", label: "기업보고서·공시", Icon: FileText },
] satisfies Array<{ key: EvidenceTab; id: string; label: string; Icon: typeof MessageCircle }>;

export function EvidenceSection() {
  const { result, status, retry } = useSearch();
  const [activeTab, setActiveTab] = useState<EvidenceTab>("gap");
  const [navOffset, setNavOffset] = useState(0);

  useEffect(() => {
    const updateOffset = () => {
      setNavOffset(Math.round(document.querySelector(".nav")?.getBoundingClientRect().height ?? 0));
    };
    updateOffset();
    window.addEventListener("resize", updateOffset);
    return () => window.removeEventListener("resize", updateOffset);
  }, []);

  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") {
      return;
    }
    const nodes = tabs.map((tab) => document.getElementById(tab.id)).filter((node): node is HTMLElement => Boolean(node));
    if (nodes.length === 0) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        const next = tabs.find((tab) => tab.id === visible?.target.id)?.key;
        if (next) {
          setActiveTab(next);
        }
      },
      {
        rootMargin: `-${navOffset + 88}px 0px -45% 0px`,
        threshold: [0.24, 0.42, 0.6],
      },
    );
    nodes.forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, [result, navOffset]);

  if (status !== "ready" || !result) {
    return null;
  }
  if (result.status === "unsupported_company") {
    return null;
  }
  if (result.access_level !== "member" || !result.detail) {
    return null;
  }

  const detail = result.detail;
  const sources = detail.sources;
  const community = deriveCommunity(sources);
  const newsItems = deriveItems(sources, "news");
  const disclosureItems = deriveItems(sources, "disclosure");
  const disclosureChecks = deriveDisclosureChecks(sources);
  const hasCommunityCoverage = detail.market_temperature.data_coverage.includes("community");
  const communityFailed = detail.community_summary === null || !hasCommunityCoverage;
  const newsFailed = detail.news_summary === null;
  const disclosureFailed = detail.disclosure_summary === null;
  const failedKinds: FailedKind[] = [
    ...(communityFailed ? (["community"] as const) : []),
    ...(newsFailed ? (["news"] as const) : []),
    ...(disclosureFailed ? (["disclosure"] as const) : []),
  ];

  const handleTabClick = (id: string, key: EvidenceTab) => {
    setActiveTab(key);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <section id="evidence" className="sallae-evidence-section" style={{ "--nav-offset": `${navOffset}px` } as CSSProperties}>
      <div className="sallae-evidence-section__inner">
        {result.status === "partial_success" ? <PartialNotice failed={failedKinds} /> : null}
        <div className="sallae-evidence-section__gauges">
          <GaugeCard
            variant="temperature"
            score={detail.market_temperature.score}
            label={detail.market_temperature.label}
            dataCoverage={detail.market_temperature.data_coverage}
          />
          <GaugeCard variant="evidence" level={detail.evidence_level.level} reason={detail.evidence_level.reason} />
        </div>
        <nav className="sallae-evidence-section__tabs" aria-label="근거 상세 이동">
          <div className="sallae-evidence-section__tab-row">
            {tabs.map(({ key, id, label, Icon }) => (
              <button
                type="button"
                className={["sallae-evidence-section__tab", activeTab === key ? "sallae-evidence-section__tab--active" : ""].join(" ")}
                aria-current={activeTab === key ? "true" : undefined}
                key={key}
                onClick={() => handleTabClick(id, key)}
              >
                <Icon size={17} strokeWidth={1.9} />
                {label}
              </button>
            ))}
          </div>
        </nav>
        <div className="sallae-evidence-section__subsections">
          <GapCheckCard
            id="evidence-gap"
            index={0}
            gap={deriveGapCheck({
              temperatureScore: detail.market_temperature.score,
              evidenceLevel: detail.evidence_level.level,
              sources,
              changeRate: result.price.change_rate,
            })}
          />
          <EvidenceSubsection
            id="evidence-community"
            kind="community"
            summary={detail.community_summary}
            count={countOf(sources, "community")}
            community={community}
            failed={communityFailed}
            index={0}
            onRetry={retry}
          />
          <EvidenceSubsection
            id="evidence-news"
            kind="news"
            summary={detail.news_summary}
            count={countOf(sources, "news")}
            items={newsItems}
            failed={newsFailed}
            index={1}
            onRetry={retry}
          />
          <EvidenceSubsection
            id="evidence-disclosure"
            kind="disclosure"
            summary={detail.disclosure_summary}
            count={countOf(sources, "disclosure")}
            items={disclosureItems}
            checks={disclosureChecks}
            failed={disclosureFailed}
            index={2}
            onRetry={retry}
          />
        </div>
      </div>
      <PeekMascot />
    </section>
  );
}
