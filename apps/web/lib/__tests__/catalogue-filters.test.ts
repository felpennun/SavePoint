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
      { genre: ["rpg", " strategy ", "", "rpg"], platform: [" switch ", "switch"] },
      2026,
    );

    expect(filters.genre).toEqual(["rpg", "strategy"]);
    expect(filters.platform).toEqual(["switch"]);
  });

  it("normalizes a single Next.js search param value to an array", () => {
    const filters = parseFilters({ genre: "rpg", platform: "switch" }, 2026);

    expect(filters.genre).toEqual(["rpg"]);
    expect(filters.platform).toEqual(["switch"]);
  });

  it("repeats query parameters for each selected facet value", () => {
    expect(buildQuery({ genre: ["rpg", "strategy"], platform: ["switch"] })).toBe(
      "?platform=switch&genre=rpg&genre=strategy",
    );
  });

  it("counts each selected facet value", () => {
    expect(countActiveFilters({ genre: ["rpg", "strategy"], platform: ["switch"], sort: "popscore_desc" })).toBe(3);
  });

  it("removes only the requested facet value and preserves other params", () => {
    expect(removeHref("?q=zelda&genre=rpg&genre=strategy&platform=switch&page=2", "genre", "rpg")).toBe(
      "?q=zelda&genre=strategy&platform=switch&page=2",
    );
  });
});
