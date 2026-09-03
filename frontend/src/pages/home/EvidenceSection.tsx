import { EvidenceCard } from "../../components/analysis/EvidenceCard";
import { GaugeCard } from "../../components/analysis/GaugeCard";
import { PartialNotice } from "../../components/analysis/PartialNotice";
import { PeekMascot } from "../../components/analysis/PeekMascot";
import { countOf, deriveCommunity, deriveItems } from "../../components/analysis/deriveEvidence";
import { useSearch } from "../../state/searchStore";
import "./evidenceSection.css";

export function EvidenceSection() {
  const { result, status, retry } = useSearch();
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
  const hasCommunityCoverage = detail.market_temperature.data_coverage.includes("community");
  const communityFailed = detail.community_summary === null || !hasCommunityCoverage;
  const newsFailed = detail.news_summary === null;
  const disclosureFailed = detail.disclosure_summary === null;

  return (
    <section id="evidence" className="sallae-evidence-section">
      <div className="sallae-evidence-section__inner">
        {result.status === "partial_completed" ? <PartialNotice /> : null}
        <div className="sallae-evidence-section__gauges">
          <GaugeCard
            variant="temperature"
            score={detail.market_temperature.score}
            label={detail.market_temperature.label}
            dataCoverage={detail.market_temperature.data_coverage}
          />
          <GaugeCard variant="evidence" level={detail.evidence_level.level} reason={detail.evidence_level.reason} />
        </div>
        <div className="sallae-evidence-section__cards">
          <EvidenceCard
            kind="community"
            summary={detail.community_summary}
            count={countOf(sources, "community")}
            community={community}
            failed={communityFailed}
            index={0}
            onRetry={retry}
          />
          <EvidenceCard kind="news" summary={detail.news_summary} count={countOf(sources, "news")} items={deriveItems(sources, "news")} failed={newsFailed} index={1} onRetry={retry} />
          <EvidenceCard
            kind="disclosure"
            summary={detail.disclosure_summary}
            count={countOf(sources, "disclosure")}
            items={deriveItems(sources, "disclosure")}
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
