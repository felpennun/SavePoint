import { describe, expect, it } from "vitest";

import {
  buildQuery,
  countActiveFilters,
  parseFilters,
  removeHref,
  restrictSelectedFilters,
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

  it("serializes every CAT-05 repeated facet with backend parameter names", () => {
    const filters = parseFilters(
      {
        platform: ["switch", "pc"],
        tag: ["rpg", "strategy"],
        edition: "deluxe",
        genre: ["role-playing-games-rpg", "adventure"],
        franchise: "zelda",
        developer: "nintendo",
        publisher: "nintendo",
        mode: "single-player",
        year_from: "1990",
        year_to: "2020",
        date_from: "1990-01-01",
        date_to: "2020-12-31",
        min_rating: "80",
        sort: "rating_desc",
      },
      2026,
    );

    expect(buildQuery(filters, 3)).toBe(
      "?platform=switch&platform=pc&tag=rpg&tag=strategy&edition=deluxe&genre=role-playing-games-rpg&genre=adventure&franchise=zelda&developer=nintendo&publisher=nintendo&mode=single-player&year_from=1990&year_to=2020&date_from=1990-01-01&date_to=2020-12-31&min_rating=80&sort=rating_desc&page=3",
    );
  });

  it("keeps the complete query when moving between pages", () => {
    const filters = parseFilters(
      {
        q: "zelda",
        platform: ["switch", "pc"],
        genre: "adventure",
        date_from: "2010",
        date_to: "2020",
        sort: "title_asc",
      },
      2026,
    );

    const pageTwo = buildQuery(filters, 2);
    expect(pageTwo).toContain("platform=switch&platform=pc");
    expect(pageTwo).toContain("genre=adventure");
    expect(pageTwo).toContain("date_from=2010&date_to=2020");
    expect(pageTwo).toContain("sort=title_asc");
    expect(pageTwo).toContain("page=2");
    expect(pageTwo).not.toContain("page=1");
  });

  it("drops malformed scalar bounds while retaining valid repeated facets", () => {
    const filters = parseFilters(
      {
        platform: ["switch"],
        year_from: "not-a-year",
        date_to: "2020-13-40",
        min_rating: "101",
      },
      2026,
    );

    expect(filters.platform).toEqual(["switch"]);
    expect(filters.year_from).toBeUndefined();
    expect(filters.date_to).toBeUndefined();
    expect(filters.min_rating).toBeUndefined();
  });

  it("removes one value from any repeated CAT-05 facet", () => {
    expect(
      removeHref("?genre=rpg&genre=adventure&publisher=nintendo&mode=co-op", "genre", "rpg"),
    ).toBe("?genre=adventure&publisher=nintendo&mode=co-op");
  });

  it("does not render unknown facet values as selectable controls", () => {
    const filters = parseFilters(
      { genre: ["known-genre", "untrusted-slug"], publisher: "untrusted-publisher" },
      2026,
    );

    const visible = restrictSelectedFilters(filters, {
      genres: [{ value: "known-genre", label: "Known genre" }],
      publishers: [],
    });

    expect(visible.genre).toEqual(["known-genre"]);
    expect(visible.publisher).toEqual([]);
  });

  it("counts all selected CAT-05 dimensions as active filters", () => {
    const filters = parseFilters(
      {
        edition: "deluxe",
        genre: ["rpg", "adventure"],
        date_from: "2010",
        date_to: "2020",
      },
      2026,
    );

    expect(countActiveFilters(filters)).toBe(5);
  });
});
