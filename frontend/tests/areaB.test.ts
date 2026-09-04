import { describe, expect, it } from "vitest";

import { formatDecimal, formatSignedDecimal, formatSignedRate, easeOutCubic } from "../src/components/common/CountUp";
import { preparePendingReturn } from "../src/components/stock/GuestGate";
import { clearPendingQuery, readPendingQuery } from "../src/state/search";

function installWindowStorage() {
  const values = new Map<string, string>();
  const previous = Reflect.get(globalThis, "window");
  const storage: Storage = {
    get length() {
      return values.size;
    },
    clear: () => values.clear(),
    getItem: (key) => values.get(key) ?? null,
    key: (index) => Array.from(values.keys())[index] ?? null,
    removeItem: (key) => values.delete(key),
    setItem: (key, value) => values.set(key, value),
  };

  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { localStorage: storage },
  });

  return () => {
    if (previous === undefined) {
      Reflect.deleteProperty(globalThis, "window");
      return;
    }
    Object.defineProperty(globalThis, "window", { configurable: true, value: previous });
  };
}

describe("pendingQuery 복귀", () => {
  it("로그인 이동 전에 검색어를 저장한다", () => {
    const restore = installWindowStorage();
    try {
      expect(preparePendingReturn("삼성전자")).toBe("/login");
      expect(readPendingQuery()).toBe("삼성전자");
      clearPendingQuery();
      expect(readPendingQuery()).toBeNull();
    } finally {
      restore();
    }
  });
});

describe("카운트업 포맷", () => {
  it("숫자와 등락률을 계약대로 표시한다", () => {
    expect(formatDecimal(78500)).toBe("78,500");
    expect(formatSignedDecimal(2450)).toBe("+2,450");
    expect(formatSignedDecimal(-1200)).toBe("-1,200");
    expect(formatSignedRate(3.2)).toBe("+3.2%");
    expect(formatSignedRate(-1.55)).toBe("-1.55%");
    expect(easeOutCubic(1)).toBe(1);
  });
});
