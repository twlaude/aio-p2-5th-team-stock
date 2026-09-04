import { describe, expect, it } from "vitest";

import { countOf, deriveCommunity, deriveDisclosureChecks, deriveItems, deriveTopics, evidenceLevelText, fgiLabel } from "../src/components/analysis/deriveEvidence";
import { lastSessionVolumeDescription, temperatureDescription } from "../src/components/analysis/GaugeCard";
import samsungFixture from "../src/mocks/analyses/samsung.json";
import type { AnalysisDetail } from "../src/services/backend_api/client";

interface SamsungFixture {
  member_detail: AnalysisDetail;
  partial_detail: AnalysisDetail;
}

const samsung = samsungFixture as SamsungFixture;

describe("analysis evidence derivation", () => {
  it("derives community meta from the Samsung member fixture", () => {
    expect(deriveCommunity(samsung.member_detail.sources)).toEqual({
      samples: 480,
      positive: 52,
      neutral: 31,
      negative: 17,
      fgi: 68,
      topics: deriveTopics(samsung.member_detail.sources),
    });
    expect(fgiLabel(68)).toBe("탐욕");
  });

  it("keeps partial responses without community meta empty", () => {
    expect(deriveCommunity(samsung.partial_detail.sources)).toBeNull();
  });

  it("describes the complete market temperature inputs without a partial notice", () => {
    expect(temperatureDescription(samsung.member_detail.market_temperature.data_coverage, samsung.member_detail.market_temperature.weight_covered)).toEqual({
      primary: "거래량 변화 · 뉴스 기사량 · 커뮤니티 글 수 · 공포탐욕 강도 기준. 이 종목의 평소 대비예요. 상승 가능성이 아니에요.",
      partial: null,
    });
  });

  it("describes community exclusion and adds the partial-data sentence", () => {
    expect(temperatureDescription(samsung.partial_detail.market_temperature.data_coverage, samsung.partial_detail.market_temperature.weight_covered)).toEqual({
      primary: "거래량 변화 · 뉴스 기사량 기준 (커뮤니티 제외)",
      partial: "일부 자료를 못 받아 받은 자료만으로 계산했어요.",
    });
  });

  it("shows the last-session date only for the last-session volume basis", () => {
    expect(lastSessionVolumeDescription("last_session", "2026-09-03")).toBe("거래량은 9월 3일 거래일 기준이에요.");
    expect(lastSessionVolumeDescription("intraday_pace", "2026-09-04")).toBeNull();
  });

  it("derives source items, source counts, and evidence segment count", () => {
    expect(deriveItems(samsung.member_detail.sources, "news")).toHaveLength(5);
    expect(countOf(samsung.member_detail.sources, "news")).toBe(5);
    expect(countOf(samsung.member_detail.sources, "disclosure")).toBe(3);
    expect(evidenceLevelText("high")).toEqual({ text: "많이 확인됨", segments: 3 });
    expect(deriveItems(samsung.member_detail.sources, "disclosure")[0].disclosureKind).toBe("major");
  });

  it("derives community topics from source meta only", () => {
    const topics = deriveTopics(samsung.member_detail.sources);
    expect(topics).toHaveLength(12);
    expect(topics.slice(0, 3)).toEqual([
      { text: "AI 메모리", sentiment: "positive", weight: 5 },
      { text: "HBM 수요", sentiment: "positive", weight: 5 },
      { text: "외국인 수급", sentiment: "positive", weight: 4 },
    ]);
    expect(deriveTopics(samsung.partial_detail.sources)).toEqual([]);
  });

  it("derives confirmed and unconfirmed disclosure facts from source meta", () => {
    expect(deriveDisclosureChecks(samsung.member_detail.sources)).toEqual({
      confirmed: ["메모리 설비 투자 지속", "반기보고서 재무 지표 제출", "현금성 자산 규모"],
      unconfirmed: ["파운드리 수익성 회복 시점", "AI 메모리 단가 지속성", "단기 주가 촉매"],
    });
  });
});

import { deriveGapCheck } from "../src/components/analysis/deriveEvidence";

describe("deriveGapCheck — 환호 vs 근거", () => {
  const news = (n: number, issue = 1) => Array.from({ length: n }, (_, i) => ({ source_type: "news" as const, title: `n${i}`, meta: { issue_count: issue } }));
  it("관심 높고 공식 확인 낮으면 온도차 큼 + 반복 기사 신호", () => {
    const gap = deriveGapCheck({ temperatureScore: 86, evidenceLevel: "low", sources: news(5, 3), changeRate: 4.2 });
    expect(gap.level).toBe("large");
    expect(gap.signals.some((s) => s.text.includes("반복"))).toBe(true);
    expect(gap.signals.some((s) => s.text.includes("공시로 확인된 내용이 없어요"))).toBe(true);
  });
  it("관심 낮고 공식 확인 높으면 조용한 편", () => {
    const gap = deriveGapCheck({ temperatureScore: 42, evidenceLevel: "high", sources: [], changeRate: 0.2 });
    expect(gap.level).toBe("quiet");
  });
  it("온도 v2 문턱값(60/60/80/45) — 관심 높음 라벨부터 온도차가 잡힌다", () => {
    expect(deriveGapCheck({ temperatureScore: 60, evidenceLevel: "low", sources: [], changeRate: 0 }).level).toBe("large");
    expect(deriveGapCheck({ temperatureScore: 59, evidenceLevel: "low", sources: [], changeRate: 0 }).level).toBe("small");
    expect(deriveGapCheck({ temperatureScore: 60, evidenceLevel: "medium", sources: [], changeRate: 0 }).level).toBe("some");
    expect(deriveGapCheck({ temperatureScore: 45, evidenceLevel: "high", sources: [], changeRate: 0 }).level).toBe("small");
  });
});
