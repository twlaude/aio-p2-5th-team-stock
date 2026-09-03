import { describe, expect, it, vi } from "vitest";

import { heroMascotState, mascotClassName } from "../src/components/mascot/mascotState";
import { handleSearchSubmit, normalizeQuery } from "../src/components/stock/searchSubmit";

describe("hero A mascot helpers", () => {
  it("maps hero state to mascot state and class names", () => {
    expect(heroMascotState({ status: "loading", typing: false, unsupported: false, errored: false })).toBe("thinking");
    expect(heroMascotState({ status: "ready", typing: true, unsupported: true, errored: false })).toBe("oops");
    expect(heroMascotState({ status: "error", typing: false, unsupported: false, errored: true })).toBe("oops");
    expect(heroMascotState({ status: "idle", typing: true, unsupported: false, errored: false })).toBe("typing");
    expect(heroMascotState({ status: "idle", typing: false, unsupported: false, errored: false })).toBe("idle");
    expect(mascotClassName("idle")).toBe("mascot mascot--idle");
    expect(mascotClassName("oops", "hero__mascot-svg")).toBe("mascot mascot--oops hero__mascot-svg");
  });
});

describe("hero A search submit helper", () => {
  it("normalizes non-empty queries and skips blank submissions", () => {
    const submit = vi.fn();

    expect(normalizeQuery("  삼성전자   우선주  ")).toBe("삼성전자 우선주");
    expect(handleSearchSubmit("   ", submit)).toBe(false);
    expect(submit).not.toHaveBeenCalled();
    expect(handleSearchSubmit("  삼성전자   005930  ", submit)).toBe(true);
    expect(submit).toHaveBeenCalledTimes(1);
    expect(submit).toHaveBeenCalledWith("삼성전자 005930");
  });
});
