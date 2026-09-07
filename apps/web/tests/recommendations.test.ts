import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getPersonalRecommendations,
  groupRecommendationsByGenre,
  type PersonalRecommendationItem,
  type PersonalRecommendationsResult,
} from "@/lib/api";

function makeItem(
  slug: string,
  score: number,
  genres: Array<[slug: string, name: string, weight: number]>,
): PersonalRecommendationItem {
  return {
    work_id: `id-${slug}`,
    slug,
    title: `Title ${slug}`,
    score,
    catalogue_rating: 80,
    catalogue_rating_count: 1200,
    year: null,
    platform_summary: "",
    cover: { url: null, is_placeholder: true, alt: `Title ${slug}` },
    matched_genres: genres.map(([gslug, name, weight]) => ({ slug: gslug, name, weight })),
  };
}

function makeResult(
  overrides: Partial<PersonalRecommendationsResult> = {},
): PersonalRecommendationsResult {
  return {
    algorithm_id: "genre-taste-v1",
    generated_at: "2026-09-06T00:00:00+00:00",
    input_snapshot_sha256: "deadbeef",
    insufficient_history: false,
    limitation: "Deterministic genre-frequency heuristic computed at request time.",
    results: [],
    ...overrides,
  };
}

describe("groupRecommendationsByGenre (REC-10, D-UI-4)", () => {
  it("returns no shelves for the insufficient-history shape", () => {
    expect(groupRecommendationsByGenre(makeResult({ insufficient_history: true }))).toEqual([]);
  });

  it("returns no shelves when there are no ranked results", () => {
    expect(groupRecommendationsByGenre(makeResult({ results: [] }))).toEqual([]);
  });

  it("groups flat results into genre shelves ordered by the user's taste weight", () => {
    const result = makeResult({
      results: [
        makeItem("a", 10, [
          ["rpg", "RPG", 8],
          ["action", "Action", 5],
        ]),
        makeItem("b", 7, [["action", "Action", 5]]),
        makeItem("c", 3, [["puzzle", "Puzzle", 2]]),
      ],
    });

    const shelves = groupRecommendationsByGenre(result);

    expect(shelves.map((s) => s.genreSlug)).toEqual(["rpg", "action", "puzzle"]);
    expect(shelves[0].genre).toBe("RPG");
    expect(shelves[0].tasteWeight).toBe(8);
    // score order from the DTO is preserved inside each shelf
    expect(shelves[1].items.map((i) => i.slug)).toEqual(["a", "b"]);
  });

  it("places an item that matches several genres on each of those shelves", () => {
    const result = makeResult({
      results: [
        makeItem("a", 10, [
          ["rpg", "RPG", 8],
          ["action", "Action", 5],
        ]),
        makeItem("b", 7, [["action", "Action", 5]]),
      ],
    });

    const shelves = groupRecommendationsByGenre(result);
    const rpg = shelves.find((s) => s.genreSlug === "rpg");
    const action = shelves.find((s) => s.genreSlug === "action");

    expect(rpg?.items.some((i) => i.slug === "a")).toBe(true);
    expect(action?.items.some((i) => i.slug === "a")).toBe(true);
  });

  it("caps the number of shelves (default 4)", () => {
    const result = makeResult({
      results: [
        makeItem("a", 10, [["g1", "G1", 10]]),
        makeItem("b", 9, [["g2", "G2", 9]]),
        makeItem("c", 8, [["g3", "G3", 8]]),
        makeItem("d", 7, [["g4", "G4", 7]]),
        makeItem("e", 6, [["g5", "G5", 6]]),
      ],
    });

    expect(groupRecommendationsByGenre(result)).toHaveLength(4);
  });

  it("caps the number of items per shelf", () => {
    const result = makeResult({
      results: Array.from({ length: 15 }, (_, i) =>
        makeItem(`w${i}`, 100 - i, [["rpg", "RPG", 5]]),
      ),
    });

    const [shelf] = groupRecommendationsByGenre(result, { maxItemsPerShelf: 12 });
    expect(shelf.items).toHaveLength(12);
  });

  it("breaks ties between equal-weight genres by slug ascending for determinism", () => {
    const result = makeResult({
      results: [
        makeItem("a", 5, [["zeta", "Zeta", 5]]),
        makeItem("b", 4, [["alpha", "Alpha", 5]]),
      ],
    });

    expect(groupRecommendationsByGenre(result).map((s) => s.genreSlug)).toEqual(["alpha", "zeta"]);
  });
});

describe("getPersonalRecommendations (REC-10, T-01.1-10)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maps a 403 from the authenticated endpoint to an unauthorized result", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 403 })));
    expect(await getPersonalRecommendations("sessionid=x")).toEqual({ kind: "unauthorized" });
  });

  it("maps a network failure to an error result", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("boom")));
    expect(await getPersonalRecommendations("sessionid=x")).toEqual({ kind: "error" });
  });

  it("returns the parsed DTO and forwards the session cookie + limit query param", async () => {
    const dto = makeResult({ results: [makeItem("a", 1, [["rpg", "RPG", 1]])] });
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(dto), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const res = await getPersonalRecommendations("sessionid=abc", 5);

    expect(res).toEqual({ kind: "ok", data: dto });
    const calledUrl = new URL(String(fetchMock.mock.calls[0][0]));
    expect(calledUrl.pathname).toBe("/api/recommendations/genre-taste/");
    expect(calledUrl.searchParams.get("limit")).toBe("5");
    expect(fetchMock.mock.calls[0][1].headers).toMatchObject({ Cookie: "sessionid=abc" });
  });
});
