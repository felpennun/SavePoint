import { describe, expect, it } from "vitest";

describe("SavePoint frontend test runner", () => {
  it("executes a real assertion before the application scaffold exists", () => {
    const supportedLocales = ["es", "en"] as const;
    const halfStarValues = Array.from({ length: 10 }, (_, index) => (index + 1) / 2);

    expect(supportedLocales).toEqual(["es", "en"]);
    expect(halfStarValues).toHaveLength(10);
    expect(halfStarValues.at(-1)).toBe(5);
  });
});

