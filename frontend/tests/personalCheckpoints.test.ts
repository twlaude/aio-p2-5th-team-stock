import { describe, expect, it } from "vitest";

import samsungFixture from "../src/mocks/analyses/samsung.json";
import usersFixture from "../src/mocks/users.json";
import { createMockClient } from "../src/services/backend_api/mock";
import type { DemoUsersFixture, MemberAnalysisResponse, PersonalizedCheckpoints } from "../src/services/backend_api/client";

interface SamsungFixture {
  member_profiles: Record<string, PersonalizedCheckpoints>;
}

const users = (usersFixture as DemoUsersFixture).users;
const samsung = samsungFixture as SamsungFixture;

function expectMember(response: Awaited<ReturnType<ReturnType<typeof createMockClient>["createAnalysis"]>>): asserts response is MemberAnalysisResponse {
  expect(response.status).toMatch(/success|partial_completed/);
  expect("access_level" in response && response.access_level).toBe("member");
}

describe("personalized checkpoints", () => {
  it("returns non-empty checkpoints for every demo user", async () => {
    const api = createMockClient({ delayMs: 0 });

    for (const user of users) {
      const login = await api.login({ username: user.username, password: "Demo1234!" });
      const response = await api.createAnalysis({ query: "삼성전자" }, login.access_token);
      expectMember(response);
      expect(response.personalized_checkpoints.personal_summary.trim().length).toBeGreaterThan(0);
      expect(response.personalized_checkpoints.priority_checks.length).toBeGreaterThanOrEqual(1);
    }
  });

  it("keeps all nine risk and horizon personal summaries distinct", () => {
    const summaries = Object.values(samsung.member_profiles).map((profile) => profile.personal_summary);

    expect(Object.keys(samsung.member_profiles).sort()).toEqual([
      "aggressive-long",
      "aggressive-medium",
      "aggressive-short",
      "balanced-long",
      "balanced-medium",
      "balanced-short",
      "conservative-long",
      "conservative-medium",
      "conservative-short",
    ]);
    expect(new Set(summaries).size).toBe(9);
  });
});
