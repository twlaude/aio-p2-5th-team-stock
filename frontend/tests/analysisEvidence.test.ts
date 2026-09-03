import { describe, expect, it } from "vitest";

import { countOf, deriveCommunity, deriveItems, evidenceLevelText, fgiLabel } from "../src/components/analysis/deriveEvidence";
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
    });
    expect(fgiLabel(68)).toBe("탐욕");
  });

  it("keeps partial responses without community meta empty", () => {
    expect(deriveCommunity(samsung.partial_detail.sources)).toBeNull();
  });

  it("derives source items, source counts, and evidence segment count", () => {
    expect(deriveItems(samsung.member_detail.sources, "news")).toHaveLength(2);
    expect(countOf(samsung.member_detail.sources, "news")).toBe(2);
    expect(countOf(samsung.member_detail.sources, "disclosure")).toBe(1);
    expect(evidenceLevelText("high")).toEqual({ text: "충분", segments: 3 });
  });
});
