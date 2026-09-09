import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";

import { deriveTopics } from "../../components/analysis/deriveEvidence";
import { GuestGate } from "../../components/stock/GuestGate";
import { OneLiner } from "../../components/stock/OneLiner";
import { PriceHeader } from "../../components/stock/PriceHeader";
import { ResultAmbient } from "../../components/stock/ResultAmbient";
import { Sparkline } from "../../components/stock/Sparkline";
import { WhyButton } from "../../components/stock/WhyButton";
import { useSearch } from "../../state/searchStore";
import "./result.css";

/** 공개 분석 결과와 비회원 안내를 표시한다. */
export function ResultSection() {
  const { query, result, runId, status, submittedQuery } = useSearch();
  const [gateOpen, setGateOpen] = useState(false);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    setGateOpen(false);
  }, [runId]);

  if (status !== "ready" || !result || result.status === "unsupported_company") {
    return null;
  }

  // 앰비언트 키워드: 회원=sources의 커뮤니티 주제, 비회원=mock 표시용 topics_preview(계약 밖 optional). 라이브 백엔드는 둘 다 없으면 미표시.
  const sources = result.access_level === "member" ? result.detail?.sources ?? [] : [];
  const materials = result.access_level === "member"
    ? {
        news: sources.filter((s) => s.source_type === "news").length,
        disclosure: sources.filter((s) => s.source_type === "disclosure").length,
        community: sources.find((s) => s.source_type === "community")?.meta?.samples as number | undefined,
      }
    : undefined;
  const ambientTopics = result.access_level === "member" ? deriveTopics(result.detail?.sources ?? []) : (result.topics_preview ?? []);

  const handleWhy = () => {
    if (result.access_level === "member") {
      document.getElementById("evidence")?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    setGateOpen(true);
    requestAnimationFrame(() => {
      document.getElementById("guest-gate")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  return (
    <motion.section
      className="result-section"
      key={runId}
      initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 24 }}
      animate={reducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
    >
      <PriceHeader company={result.company} price={result.price} />
      <Sparkline stockCode={result.company.stock_code} changeRate={result.price.change_rate} />
      <ResultAmbient topics={ambientTopics} runId={runId}>
        <OneLiner text={result.one_line_summary} materials={materials} />
      </ResultAmbient>
      <WhyButton onClick={handleWhy} />
      {result.access_level === "guest" && gateOpen
        ? <GuestGate companyName={result.company.company_name} query={submittedQuery ?? query} />
        : null}
    </motion.section>
  );
}
