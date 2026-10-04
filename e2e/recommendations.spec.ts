import { expect, test, type Page } from "@playwright/test";

/**
 * QUAL-02 evidence (Phase 3, 03-VALIDATION.md "Rankings reales en web" /
 * 03-04-PLAN.md task 2): the recommendations page must render the same
 * ranking the backend actually computed -- same items, same order, per
 * algorithm section -- and must never leak the evaluation/thesis surface
 * (charts, algorithm/run selectors, methodology copy) into the product.
 *
 * Ground truth comes straight from `GET /api/recommendations/snapshot/`
 * (the same endpoint `RecommendationsClient` fetches), read via
 * `page.request` so it shares the browser context's session cookie -- not
 * from a second, separately-authenticated client.
 */

const CONTENT_ALGORITHM_IDS = [
  "content-cbf-weighted-v1",
  "content-cbf-mmr-pop-v2",
  "recency-v1",
] as const;

// Methodology/evaluation vocabulary that belongs in the thesis, never on
// this product surface (D-09's own limitation copy is the one permitted,
// deliberately generic sentence -- checked separately, not via this list).
const METHODOLOGY_TERMS = [
  "nDCG",
  "Wilcoxon",
  "bootstrap",
  "Friedman",
  "leave-one-out",
  "leave-fraction-out",
  "protocolo v",
  "p-valor",
  "Holm",
];

interface ContentRecommendationItem {
  work_id: string;
  slug: string;
  score: number;
}

interface RecommendationSnapshot {
  status: string;
  sections: {
    content: Record<string, { results: ContentRecommendationItem[] }>;
    tags: unknown;
  } | null;
}

async function login(page: Page, username: string, password: string): Promise<void> {
  await page.goto("/es/login");
  await page.getByLabel("Usuario").fill(username);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL(/\/es$/);
}

/** Poll the same endpoint the client polls, until the async refresh job
 * settles (or the snapshot is simply empty for this account -- also a
 * terminal state, not a timeout). */
async function waitForSettledSnapshot(page: Page): Promise<RecommendationSnapshot> {
  let last: RecommendationSnapshot | null = null;
  await expect
    .poll(
      async () => {
        const response = await page.request.get("/api/recommendations/snapshot/");
        if (!response.ok()) return "error";
        last = (await response.json()) as RecommendationSnapshot;
        return last.status;
      },
      { message: "recommendation snapshot never left building/stale", timeout: 30_000 },
    )
    .not.toMatch(/^(building|stale)$/);
  return last as unknown as RecommendationSnapshot;
}

test.describe("recommendations page reflects the real backend ranking (QUAL-02)", () => {
  test.skip(!process.env.DEMO_USERNAME || !process.env.DEMO_PASSWORD, "requires DEMO_USERNAME/DEMO_PASSWORD");

  test("every rendered content shelf matches the API's item order and score-desc claim", async ({ page }) => {
    await login(page, process.env.DEMO_USERNAME!, process.env.DEMO_PASSWORD!);
    const snapshot = await waitForSettledSnapshot(page);

    await page.goto("/es/recommendations");
    await expect(page.getByRole("heading", { level: 1, name: "Recomendaciones" })).toBeVisible();

    const content = snapshot.sections?.content ?? {};
    const renderedSections = CONTENT_ALGORITHM_IDS.filter((id) => (content[id]?.results.length ?? 0) > 0);

    // This account must actually have content to compare against, or the
    // rest of this test would vacuously pass without checking anything.
    test.skip(renderedSections.length === 0, "demo account currently has no non-empty content section to compare");

    for (const algorithmId of renderedSections) {
      const apiResults = content[algorithmId].results;

      // score-desc contract, straight from the payload (the DOM never
      // exposes the numeric score, only order and identity).
      for (let i = 1; i < apiResults.length; i++) {
        expect(
          apiResults[i - 1].score,
          `${algorithmId}: result ${i - 1} (${apiResults[i - 1].score}) must be >= result ${i} (${apiResults[i].score})`,
        ).toBeGreaterThanOrEqual(apiResults[i].score);
      }

      // The page shows one algorithm at a time: pick it in the rail first.
      await page.locator(".sp-reco-rail-item").nth(renderedSections.indexOf(algorithmId)).click();
      const section = page.locator("section.sp-reco-detail");
      await expect(section, `missing rendered shelf for ${algorithmId}`).toBeVisible();

      const hrefs = await section.locator("ol.sp-shelf-track li a").evaluateAll((links) =>
        links.map((link) => (link as HTMLAnchorElement).getAttribute("href")),
      );
      const domSlugs = hrefs.map((href) => href?.split("/").filter(Boolean).pop());
      const apiSlugs = apiResults.map((item) => item.slug);
      expect(domSlugs, `${algorithmId}: DOM card order must match the API's item order`).toEqual(apiSlugs);
    }
  });

  test("no chart, algorithm/run selector, placeholder, or methodology copy leaks onto the page", async ({ page }) => {
    await login(page, process.env.DEMO_USERNAME!, process.env.DEMO_PASSWORD!);
    await waitForSettledSnapshot(page);
    await page.goto("/es/recommendations");
    await expect(page.getByRole("heading", { level: 1, name: "Recomendaciones" })).toBeVisible();

    // This is a fixed, deterministic product page: no chart library surface,
    // and nothing that lets a visitor pick an algorithm or a historical run
    // (the mono algorithm-id tag beside each heading is a label, not a
    // control -- it is not a <select>/<button role="listbox"> etc.).
    expect(await page.locator("canvas").count()).toBe(0);
    expect(await page.locator("svg.recharts-surface, .recharts-wrapper").count()).toBe(0);
    expect(await page.locator("select").count()).toBe(0);
    expect(await page.getByRole("combobox").count()).toBe(0);

    const bodyText = (await page.locator("main").innerText()).toLowerCase();
    for (const term of METHODOLOGY_TERMS) {
      expect(bodyText, `methodology term "${term}" must not appear on the product page`).not.toContain(term.toLowerCase());
    }
  });

  test("320px reflow, dark/light theming, and keyboard reachability", async ({ page }) => {
    await login(page, process.env.DEMO_USERNAME!, process.env.DEMO_PASSWORD!);
    await waitForSettledSnapshot(page);

    await page.setViewportSize({ width: 320, height: 800 });
    await page.goto("/es/recommendations");
    await expect(page.getByRole("heading", { level: 1, name: "Recomendaciones" })).toBeVisible();
    // Give any shelf/onboarding state time to settle before measuring.
    await page
      .locator("section.sp-shelf, text=Aún no hay suficiente actividad")
      .first()
      .waitFor({ timeout: 15_000 })
      .catch(() => undefined);

    const overflowsAt320 = await page.evaluate(() => {
      const main = document.querySelector("main");
      return main ? main.scrollWidth > main.clientWidth + 1 : true;
    });
    expect(overflowsAt320, "recommendations content must not overflow horizontally at 320px").toBe(false);

    const consoleErrors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });

    const backgroundInTheme = async (theme: "dark" | "light") => {
      await page.evaluate((t) => document.documentElement.setAttribute("data-theme", t), theme);
      return page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    };
    const darkBackground = await backgroundInTheme("dark");
    const lightBackground = await backgroundInTheme("light");
    expect(darkBackground, "dark and light themes must paint a different page background").not.toBe(lightBackground);
    expect(consoleErrors, `console errors while toggling theme: ${consoleErrors.join("; ")}`).toEqual([]);

    // Keyboard: Tab from the top of the document must eventually reach a
    // real shelf card link, not skip over the shelves entirely.
    await page.evaluate(() => document.body.focus());
    let reachedShelfLink = false;
    for (let i = 0; i < 40 && !reachedShelfLink; i++) {
      await page.keyboard.press("Tab");
      reachedShelfLink = await page.evaluate(() => {
        const active = document.activeElement;
        return !!active && !!active.closest(".sp-shelf-track");
      });
    }
    expect(reachedShelfLink, "Tab navigation must be able to reach a shelf card link").toBe(true);
    const focusedIsVisible = await page.evaluate(() => {
      const active = document.activeElement as HTMLElement | null;
      if (!active) return false;
      const rect = active.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    });
    expect(focusedIsVisible, "the keyboard-focused shelf link must be visible, not display:none/hidden").toBe(true);
  });
});
