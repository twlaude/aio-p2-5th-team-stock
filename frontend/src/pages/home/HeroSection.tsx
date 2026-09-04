import { motion, useReducedMotion, type Variants } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Mascot } from "../../components/mascot/Mascot";
import { heroMascotState } from "../../components/mascot/mascotState";
import { CompanyChips } from "../../components/stock/CompanyChips";
import { ErrorNotice } from "../../components/stock/ErrorNotice";
import { LoadingBlock } from "../../components/stock/LoadingBlock";
import { SearchBar } from "../../components/stock/SearchBar";
import { UnsupportedNotice } from "../../components/stock/UnsupportedNotice";
import { useSearch } from "../../state/searchStore";
import "./hero.css";

// motion 4b-1
const heroContainer: Variants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.07,
    },
  },
};

const heroItem: Variants = {
  hidden: {
    opacity: 0,
    y: 16,
  },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: "easeOut",
    },
  },
};

/** 영역 A 소유 — 검색 히어로(마스코트·검색바·칩·20종목 시트·로딩·미지원·에러). 아래는 스텁. */
export function HeroSection() {
  const { error, query, result, status, submittedQuery, retry, setQuery, submit } = useSearch();
  const reducedMotion = useReducedMotion();
  const [typing, setTyping] = useState(false);
  const [submitPulse, setSubmitPulse] = useState(false);
  const [companiesError, setCompaniesError] = useState<string | null>(null);
  const pulseTimer = useRef<number | null>(null);
  const scenarioStarted = useRef(false);

  const unsupported = result?.status === "unsupported_company";
  const errored = status === "error";
  const companiesErrored = Boolean(companiesError);
  const compressed = status !== "idle";
  const mascotState = submitPulse && status === "loading"
    ? "submit"
    : heroMascotState({ status, typing, unsupported, errored });

  const stopPulse = useCallback(() => {
    if (pulseTimer.current !== null) {
      window.clearTimeout(pulseTimer.current);
      pulseTimer.current = null;
    }
    setSubmitPulse(false);
  }, []);

  const startPulse = useCallback(() => {
    stopPulse();
    setSubmitPulse(true);
    pulseTimer.current = window.setTimeout(() => setSubmitPulse(false), 600);
  }, [stopPulse]);

  const submitWithPulse = useCallback((nextQuery: string) => {
    startPulse();
    setTyping(false);
    setCompaniesError(null);
    void submit(nextQuery);
  }, [startPulse, submit]);

  const retryWithPulse = useCallback(() => {
    startPulse();
    void retry();
  }, [retry, startPulse]);

  useEffect(() => stopPulse, [stopPulse]);

  // motion 4b-4
  useEffect(() => {
    if (scenarioStarted.current || status !== "idle" || submittedQuery) {
      return;
    }

    const scenario = new URLSearchParams(window.location.search).get("scenario");
    const scenarioQuery = scenario === "unsupported"
      ? "NAVER"
      : scenario === "slow" || scenario === "error" || scenario === "partial"
        ? "삼성전자"
        : "";
    if (scenarioQuery) {
      scenarioStarted.current = true;
      submitWithPulse(scenarioQuery);
    }
  }, [status, submittedQuery, submitWithPulse]);

  const shellClassName = [
    "hero-shell",
    compressed ? "hero-shell--compressed" : "",
    unsupported ? "hero-shell--notice" : "",
    errored || companiesErrored ? "hero-shell--error" : "",
  ].filter(Boolean).join(" ");

  return (
    <section className={shellClassName}>
      {/* motion 4b-2 */}
      <div className="hero__blob hero__blob--one" aria-hidden="true" />
      <div className="hero__blob hero__blob--two" aria-hidden="true" />
      <motion.div className="hero__content" initial={reducedMotion ? "show" : "hidden"} animate="show" variants={heroContainer}>
        <motion.div className="hero__mascot" variants={heroItem}>
          <Mascot state={mascotState} size={120} typingText={query} />
        </motion.div>
        <motion.h1 className="hero__title" variants={heroItem}>
          어떤 종목이 궁금하세요?
        </motion.h1>
        <motion.p className="hero__subtitle" variants={heroItem}>
          가격 뒤에 있는 뉴스, 공시, 시장 반응을 한 번에 봐요.
        </motion.p>
        <motion.div className="hero__search" variants={heroItem}>
          <SearchBar value={query} status={status} unsupported={unsupported} onChange={setQuery} onSubmit={submitWithPulse} onTypingChange={setTyping} />
        </motion.div>
        <motion.div className="hero__chips" variants={heroItem}>
          <CompanyChips onSelectCompany={submitWithPulse} onError={setCompaniesError} />
        </motion.div>
      </motion.div>
      {status === "loading" ? <LoadingBlock /> : null}
      {unsupported ? <UnsupportedNotice query={submittedQuery} message={result.message} onSelectCompany={submitWithPulse} /> : null}
      {errored ? <ErrorNotice message={error} onRetry={retryWithPulse} /> : null}
      {companiesError ? <ErrorNotice message={companiesError} onRetry={() => setCompaniesError(null)} /> : null}
    </section>
  );
}
