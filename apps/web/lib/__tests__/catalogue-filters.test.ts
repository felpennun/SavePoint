import { describe, expect, it } from "vitest";

import {
  buildQuery,
  countActiveFilters,
  parseFilters,
  removeHref,
} from "@/lib/catalogue-filters";

describe("catalogue multi-select filters", () => {
  it("normalizes, de-duplicates, and removes empty facet values", () => {
    const filters = parseFilters(
      { tag: ["rpg", " strategy ", "", "rpg"], platform: [" switch ", "switch"] },
      2026,
    );

    expect(filters.tag).toEqual(["rpg", "strategy"]);
    expect(filters.platform).toEqual(["switch"]);
  });

  it("normalizes a single Next.js search param value to an array", () => {
    const filters = parseFilters({ tag: "rpg", platform: "switch" }, 2026);

    expect(filters.tag).toEqual(["rpg"]);
    expect(filters.platform).toEqual(["switch"]);
  });

  it("repeats query parameters for each selected facet value", () => {
    expect(buildQuery({ tag: ["rpg", "strategy"], platform: ["switch"] })).toBe(
      "?platform=switch&tag=rpg&tag=strategy",
    );
  });

  it("counts each selected facet value", () => {
    expect(countActiveFilters({ tag: ["rpg", "strategy"], platform: ["switch"], sort: "popscore_desc" })).toBe(3);
  });

  it("removes only the requested facet value and preserves other params", () => {
    expect(removeHref("?q=zelda&tag=rpg&tag=strategy&platform=switch&page=2", "tag", "rpg")).toBe(
      "?q=zelda&tag=strategy&platform=switch&page=2",
    );
  });
});
