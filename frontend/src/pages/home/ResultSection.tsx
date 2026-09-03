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

/** 영역 B 소유 — 공개 결과(가격·스파크라인·한줄결론·why)·비회원 게이트. */
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
  const ambientTopics = result.access_level === "member" ? deriveTopics(result.detail?.sources ?? []) : (result.topics_preview ?? []);

  const handleWhy = () => {
    // motion 4b-9
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
      {/* motion 4b-4 */}
      <PriceHeader company={result.company} price={result.price} />
      <Sparkline stockCode={result.company.stock_code} changeRate={result.price.change_rate} />
      <ResultAmbient topics={ambientTopics} runId={runId}>
        <OneLiner text={result.one_line_summary} />
      </ResultAmbient>
      <WhyButton onClick={handleWhy} />
      {result.access_level === "guest" && gateOpen
        ? <GuestGate companyName={result.company.company_name} query={submittedQuery ?? query} />
        : null}
    </motion.section>
  );
}
