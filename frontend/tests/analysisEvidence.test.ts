import { describe, expect, it } from "vitest";

import { countOf, deriveCommunity, deriveDisclosureChecks, deriveItems, deriveTopics, evidenceLevelText, fgiLabel } from "../src/components/analysis/deriveEvidence";
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

  it("derives source items, source counts, and evidence segment count", () => {
    expect(deriveItems(samsung.member_detail.sources, "news")).toHaveLength(5);
    expect(countOf(samsung.member_detail.sources, "news")).toBe(5);
    expect(countOf(samsung.member_detail.sources, "disclosure")).toBe(3);
    expect(evidenceLevelText("high")).toEqual({ text: "많이 확인됨", segments: 3 });
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
