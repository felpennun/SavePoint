import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getPersonalRecommendations,
  primaryTagRecommendationShelf,
  type PersonalRecommendationItem,
  type PersonalRecommendationsResult,
} from "@/lib/api";
import { CONTENT_RECOMMENDATION_SECTIONS } from "@/lib/recommendation-sections";

it("publishes only the three content shelves chosen for users", () => {
  expect(CONTENT_RECOMMENDATION_SECTIONS.map(([algorithmId]) => algorithmId)).toEqual([
    "content-cbf-weighted-v1",
    "content-cbf-mmr-pop-v2",
    "recency-v1",
  ]);
});

function makeItem(
  slug: string,
  score: number,
  tags: Array<[slug: string, name: string, weight: number]>,
): PersonalRecommendationItem {
  return {
    work_id: `id-${slug}`,
    slug,
    title: `Title ${slug}`,
    score,
    catalogue_rating: 80,
    catalogue_rating_count: 1200,
    display_rating: 80,
    year: null,
    platform_summary: "",
    cover: { url: null, is_placeholder: true, alt: `Title ${slug}` },
    matched_tags: tags.map(([slug, name, weight]) => ({ slug, name, weight })),
  };
}

function makeResult(
  overrides: Partial<PersonalRecommendationsResult> = {},
): PersonalRecommendationsResult {
  return {
    algorithm_id: "tag-taste-v1",
    generated_at: "2026-09-06T00:00:00+00:00",
    input_snapshot_sha256: "deadbeef",
    insufficient_history: false,
    limitation: "Deterministic genre-frequency heuristic computed at request time.",
    results: [],
    ...overrides,
  };
}

describe("primaryTagRecommendationShelf (REC-10)", () => {
  it("returns no shelves for the insufficient-history shape", () => {
    expect(primaryTagRecommendationShelf(makeResult({ insufficient_history: true }))).toBeNull();
  });

  it("returns no shelves when there are no ranked results", () => {
    expect(primaryTagRecommendationShelf(makeResult({ results: [] }))).toBeNull();
  });

  it("returns only the shelf for the primary library genre", () => {
    const result = makeResult({
      primary_tag: { slug: "rpg", name: "RPG", entry_count: 6, weight: 8 },
      results: [
        makeItem("a", 10, [
          ["rpg", "RPG", 8],
          ["action", "Action", 5],
        ]),
        makeItem("b", 7, [["action", "Action", 5]]),
        makeItem("c", 3, [["puzzle", "Puzzle", 2]]),
      ],
    });

    const shelf = primaryTagRecommendationShelf(result);

    expect(shelf?.tagSlug).toBe("rpg");
    expect(shelf?.tag).toBe("RPG");
    expect(shelf?.tasteWeight).toBe(8);
    expect(shelf?.items.map((i) => i.slug)).toEqual(["a"]);
  });

  it("uses the score-weight rule only as a fallback for legacy snapshots", () => {
    const result = makeResult({
      results: [
        makeItem("a", 10, [
          ["rpg", "RPG", 8],
          ["action", "Action", 5],
        ]),
        makeItem("b", 7, [["action", "Action", 5]]),
      ],
    });

    const shelf = primaryTagRecommendationShelf(result);

    expect(shelf?.tagSlug).toBe("rpg");
    expect(shelf?.items.map((i) => i.slug)).toEqual(["a"]);
  });

  it("caps the sole shelf at twenty items", () => {
    const result = makeResult({
      primary_tag: { slug: "rpg", name: "RPG", entry_count: 30, weight: 10 },
      results: Array.from({ length: 25 }, (_, i) => makeItem(`w${i}`, 100 - i, [["rpg", "RPG", 10]])),
    });

    expect(primaryTagRecommendationShelf(result)?.items).toHaveLength(20);
  });

  it("accepts an explicit product-safe item cap", () => {
    const result = makeResult({
      results: Array.from({ length: 15 }, (_, i) =>
        makeItem(`w${i}`, 100 - i, [["rpg", "RPG", 5]]),
      ),
    });

    const shelf = primaryTagRecommendationShelf(result, { maxItems: 12 });
    expect(shelf?.items).toHaveLength(12);
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
