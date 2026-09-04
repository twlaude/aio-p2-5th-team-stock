import { describe, expect, it } from "vitest";

import type { AnalysisResponse, GuestAnalysisResponse, MemberAnalysisResponse, UnsupportedCompanyResponse } from "../src/services/backend_api/client";
import { createMockClient } from "../src/services/backend_api/mock";

function topLevelKeys(response: AnalysisResponse) {
  return Object.keys(response).filter((key) => key !== "topics_preview").sort();
}

function expectGuest(response: AnalysisResponse): asserts response is GuestAnalysisResponse {
  expect(response.status).toBe("success");
  expect("access_level" in response && response.access_level).toBe("guest");
}

function expectMember(response: AnalysisResponse): asserts response is MemberAnalysisResponse {
  expect(response.status).toMatch(/success|partial_completed/);
  expect("access_level" in response && response.access_level).toBe("member");
}

function expectUnsupported(response: AnalysisResponse): asserts response is UnsupportedCompanyResponse {
  expect(response.status).toBe("unsupported_company");
}

describe("mock backend api contract", () => {
  it("returns the supported company contract", async () => {
    const api = createMockClient({ delayMs: 0 });
    const response = await api.getCompanies();

    expect(response.status).toBe("success");
    expect(response.snapshot_date).toBe("2026-09-01");
    expect(response.companies).toHaveLength(20);
    expect(Object.keys(response.companies[0]).sort()).toEqual(["company_name", "market", "rank", "stock_code"]);
  });

  it("returns the guest analysis contract fields", async () => {
    const api = createMockClient({ delayMs: 0 });
    const response = await api.createAnalysis({ query: "삼성전자" });

    expectGuest(response);
    expect(topLevelKeys(response)).toEqual([
      "access_level",
      "company",
      "detail",
      "one_line_summary",
      "personalized_checkpoints",
      "price",
      "request_id",
      "requires_login",
      "status",
    ]);
    expect(response.requires_login).toBe(true);
    expect(response.detail).toBeNull();
    expect(response.personalized_checkpoints).toBeNull();
    expect(response.company).toEqual({
      company_name: "삼성전자",
      stock_code: "005930",
      supported: true,
    });
  });

  it("returns the member analysis contract fields", async () => {
    const api = createMockClient({ delayMs: 0 });
    const login = await api.login({ username: "demo003", password: "Demo1234!" });
    const response = await api.createAnalysis({ query: "005930" }, login.access_token);

    expectMember(response);
    expect(response.status).toBe("success");
    expect(response.requires_login).toBe(false);
    expect(Object.keys(response.detail).sort()).toEqual([
      "community_summary",
      "disclosure_summary",
      "evidence_level",
      "market_temperature",
      "news_summary",
      "sources",
    ]);
    expect(response.detail.market_temperature.data_coverage).toEqual(["price", "news", "disclosure", "community"]);
    expect(response.personalized_checkpoints.priority_checks).toHaveLength(3);
    expect(response.personalized_checkpoints.personal_summary).toContain("큰 변동도 감수하는");
  });

  it("returns the unsupported company contract fields", async () => {
    const api = createMockClient({ delayMs: 0 });
    const response = await api.createAnalysis({ query: "NAVER" });

    expectUnsupported(response);
    expect(topLevelKeys(response)).toEqual(["actions", "message", "status"]);
    expect(response.actions).toEqual(["지원 기업 20개 보기", "다른 종목 검색하기"]);
  });

  it("returns the partial completed contract fields", async () => {
    const api = createMockClient({ delayMs: 0, scenario: "partial" });
    const login = await api.login({ username: "demo005", password: "Demo1234!" });
    const response = await api.createAnalysis({ query: "삼성전자" }, login.access_token);

    expectMember(response);
    expect(response.status).toBe("partial_completed");
    expect(response.detail.market_temperature.data_coverage).toEqual(["price", "news", "disclosure"]);
    expect(response.detail.community_summary).toBeNull();
    expect(response.detail.sources.every((source) => source.source_type !== "community")).toBe(true);
  });
});
