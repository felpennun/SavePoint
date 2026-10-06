import { describe, expect, it } from "vitest";

import { IDLE_LIMIT_MS, isIdleExpired } from "../idle-session";

describe("isIdleExpired", () => {
  it("keeps the session just under thirty minutes", () => {
    expect(isIdleExpired(1_000, 1_000 + IDLE_LIMIT_MS - 1)).toBe(false);
  });

  it("expires it at thirty minutes", () => {
    expect(IDLE_LIMIT_MS).toBe(30 * 60 * 1000);
    expect(isIdleExpired(1_000, 1_000 + IDLE_LIMIT_MS)).toBe(true);
  });

  it("accepts a custom limit", () => {
    expect(isIdleExpired(0, 5_000, 5_000)).toBe(true);
  });
});
