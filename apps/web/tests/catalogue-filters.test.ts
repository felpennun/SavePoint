import { describe, expect, it } from "vitest";

import { buildQuery, parseFilters, SORT_KEYS } from "@/lib/catalogue-filters";

describe("catalogue default PopScore", () => {
  it("selects PopScore without requiring a text query", () => {
    expect(parseFilters({}, 2026).sort).toBe("popscore_desc");
    expect(SORT_KEYS).toEqual([
      "popscore_desc",
      "relevance",
      "title_asc",
      "title_desc",
      "release_newest",
      "release_oldest",
      "rating_desc",
    ]);
  });

  it("keeps the default PopScore mode stable in shareable URLs", () => {
    expect(buildQuery(parseFilters({}, 2026))).toBe("");
    expect(buildQuery(parseFilters({ q: "Elden Ring" }, 2026))).toBe("?q=Elden+Ring");
  });
});
