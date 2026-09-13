import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const AXE_SCRIPT_PATH = path.join(__dirname, "..", "node_modules", "axe-core", "axe.min.js");
const EXTERNAL_HOSTS = ["api.igdb.com", "id.twitch.tv", "api.rawg.io"];

interface AxeViolation {
  id: string;
  impact: string | null;
  help: string;
  nodes: { target: string[] }[];
}

async function axe(page: Page): Promise<AxeViolation[]> {
  await page.addScriptTag({ path: AXE_SCRIPT_PATH });
  return await page.evaluate(async () => {
    // @ts-expect-error -- axe is injected by the local, pinned bundle above
    return (await window.axe.run(document, { resultTypes: ["violations"] })).violations;
  });
}

function assertNoSeriousAxe(violations: AxeViolation[], surface: string): void {
  const blocking = violations.filter((item) => item.impact === "critical" || item.impact === "serious");
  expect(blocking, `${surface} must have no critical/serious axe violations`).toEqual([]);
}

async function assertNoPageOverflow(page: Page, surface: string): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth, `${surface} must not overflow horizontally`).toBeLessThanOrEqual(dimensions.clientWidth + 1);
}

test.describe("Phase 6 catalogue discovery: real GET filters and local provenance", () => {
  test("search, pagination, facets and direct URLs use the real catalogue", async ({ page }) => {
    const externalRequests: string[] = [];
    page.on("request", (request) => {
      if (EXTERNAL_HOSTS.some((host) => request.url().includes(host))) externalRequests.push(request.url());
    });

    await page.goto("/es/catalogue");
    const firstCard = page.locator("main ul.sp-grid li a").first();
    await expect(firstCard).toBeVisible();
    const title = (await firstCard.locator("p").first().innerText()).trim();
    expect(title.length).toBeGreaterThan(0);

    await page.goto(`/es/catalogue?q=${encodeURIComponent(title)}`);
    await expect(page.locator("main ul.sp-grid li a").first()).toContainText(title);
    await expect(page).toHaveURL(new RegExp(`/es/catalogue\\?q=${encodeURIComponent(title).replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&")}`));

    const firstFacet = page.locator('input[name="platform"], input[name="genre"], input[name="tag"]').first();
    if (await firstFacet.count()) {
      const facetValue = await firstFacet.getAttribute("value");
      expect(facetValue).toBeTruthy();
      await page.goto(`/es/catalogue?q=${encodeURIComponent(title)}&${await firstFacet.getAttribute("name")}=${encodeURIComponent(facetValue!)}`);
      await expect(page.locator("main")).toBeVisible();
      await expect(page.locator(".sp-filterbar")).toBeVisible();
    }

    const next = page.getByRole("link", { name: "Siguiente" });
    if (await next.count()) {
      await next.click();
      await expect(page).toHaveURL(/page=2/);
      await expect(page.getByRole("navigation", { name: "Paginación" })).toBeVisible();
    }
    expect(externalRequests, "HTTP catalogue must not call live providers").toEqual([]);
  });

  test("catalogue and detail remain accessible at mobile width and reduced motion", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 800 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/en/catalogue");
    await expect(page.getByRole("region", { name: "Catalogue" })).toBeVisible();
    await assertNoPageOverflow(page, "catalogue at 320px");
    assertNoSeriousAxe(await axe(page), "catalogue at 320px");

    const card = page.locator("main ul.sp-grid li a").first();
    await card.click();
    await page.waitForURL(/\/en\/games\//);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await assertNoPageOverflow(page, "game detail at 320px");
    assertNoSeriousAxe(await axe(page), "game detail at 320px");

    // A 400% browser zoom exposes a 320 CSS-pixel layout through a 1280px
    // device viewport. Do not combine a 320px viewport with CSS zoom: that
    // double-scales the page and tests an impossible 1600% equivalent.
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.evaluate(() => {
      document.documentElement.style.zoom = "400%";
    });
    await assertNoPageOverflow(page, "game detail at 400% zoom");
    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).toBeVisible();
  });
});
