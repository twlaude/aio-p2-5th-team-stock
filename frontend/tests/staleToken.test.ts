import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AUTH_EXPIRED_EVENT, createLiveClient, StaleTokenError } from "../src/services/backend_api/live";
import { readAuthSession } from "../src/state/auth";

const AUTH_KEY = "sallae.auth.session";

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

// vitest 환경이 node라 window가 없다 → 이벤트 타깃 + 메모리 localStorage만 가진 최소 window를 꽂는다.
function memoryStorage(): Storage {
  const map = new Map<string, string>();
  return {
    getItem: (k) => map.get(k) ?? null,
    setItem: (k, v) => void map.set(k, String(v)),
    removeItem: (k) => void map.delete(k),
    clear: () => map.clear(),
    key: (i) => [...map.keys()][i] ?? null,
    get length() {
      return map.size;
    },
  };
}

beforeEach(() => {
  vi.stubGlobal("window", Object.assign(new EventTarget(), { localStorage: memoryStorage() }));
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("옛 토큰 401 처리", () => {
  it("분석 요청이 401이면 세션을 지우고 비회원으로 다시 요청한다", async () => {
    window.localStorage.setItem(AUTH_KEY, JSON.stringify({ token: "stale", tokenType: "bearer", user: {}, profileCompleted: true }));
    const guest = { status: "success", access_level: "guest" };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (_url, init) => {
      const headers = (init?.headers ?? {}) as Record<string, string>;
      return "Authorization" in headers ? jsonResponse(401, { detail: "로그인이 필요하다." }) : jsonResponse(200, guest);
    });
    const expired = vi.fn();
    window.addEventListener(AUTH_EXPIRED_EVENT, expired);

    const result = await createLiveClient().createAnalysis({ query: "삼성전자" }, "stale");

    expect(result).toEqual(guest);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(readAuthSession()).toBeNull();
    expect(expired).toHaveBeenCalledTimes(1);
  });

  it("토큰 없이 받은 401은 그대로 오류다", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(401, { detail: "x" }));
    await expect(createLiveClient().createAnalysis({ query: "삼성전자" })).rejects.toThrow("API 401");
  });

  it("프로필 조회 401도 세션을 지우고 StaleTokenError를 던진다", async () => {
    window.localStorage.setItem(AUTH_KEY, JSON.stringify({ token: "stale" }));
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(401, { detail: "x" }));
    await expect(createLiveClient().getProfile("stale")).rejects.toBeInstanceOf(StaleTokenError);
    expect(readAuthSession()).toBeNull();
  });
});
