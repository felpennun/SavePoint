import { describe, expect, it } from "vitest";

import { buildQuery, parseFilters } from "@/lib/catalogue-filters";

describe("catalogue default relevance", () => {
  it("selects relevance without requiring a text query", () => {
    expect(parseFilters({}, 2026).sort).toBe("relevance");
  });

  it("keeps the default relevance mode stable in shareable URLs", () => {
    expect(buildQuery(parseFilters({}, 2026))).toBe("");
    expect(buildQuery(parseFilters({ q: "Elden Ring" }, 2026))).toBe("?q=Elden+Ring");
  });
});
