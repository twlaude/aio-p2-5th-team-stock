import { describe, expect, it } from "vitest";

import { createMockClient } from "../src/services/backend_api/mock";

describe("result ambient topics", () => {
  it("guest 삼성전자 응답에 mock 표시용 topics_preview가 실린다", async () => {
    const api = createMockClient({ delayMs: 0 });
    const response = await api.createAnalysis({ query: "삼성전자" });
    expect(response.status).toBe("success");
    if (response.status !== "success" || response.access_level !== "guest") throw new Error("guest 응답이어야 한다");
    expect(response.topics_preview?.length).toBeGreaterThanOrEqual(8);
    expect(response.topics_preview?.every((t) => ["positive", "neutral", "negative"].includes(t.sentiment))).toBe(true);
  });
  it("guest 템플릿 종목도 topics_preview를 가진다", async () => {
    const api = createMockClient({ delayMs: 0 });
    const response = await api.createAnalysis({ query: "SK하이닉스" });
    if (response.status !== "success" || response.access_level !== "guest") throw new Error("guest 응답이어야 한다");
    expect(response.topics_preview?.length).toBe(8);
  });
});
