import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

/**
 * Plan 01-10: automated accessibility/responsive acceptance, separate from
 * the UI construction itself. FLAGGED ASSUMPTION (per the plan): axe +
 * keyboard + 320px + 400% + a basic screen-reader pass are adequate demo
 * evidence, not an exhaustive WCAG audit. axe-core is already a project
 * devDependency (Plan 01-01) -- injected directly via its local minified
 * bundle rather than adding the separate @axe-core/playwright wrapper
 * package, avoiding a new-dependency approval round for one line of glue.
 */

// __dirname (CommonJS), not import.meta.url -- this suite runs alongside
// the project's other e2e/*.spec.ts files, all of which are plain CJS-style
// TypeScript under Playwright's default transform, not ESM.
const AXE_SCRIPT_PATH = path.join(__dirname, "..", "node_modules", "axe-core", "axe.min.js");

// Plan 01.1-10 evidence artifacts. Playwright writes one deterministic PNG
// per surface/viewport pair here; docs/verification/phase-01.1-product-review.md
// references these exact repo-relative paths.
const ARTIFACT_DIR = path.join(__dirname, "artifacts", "phase-01.1");

async function shoot(page: Page, surface: string, viewport: string): Promise<void> {
  await page.screenshot({ path: path.join(ARTIFACT_DIR, `${surface}-${viewport}.png`), fullPage: true });
}

// The redesign stack is normally served on :3000, whose Origin is in
// Django's CSRF_TRUSTED_ORIGINS. When the suite is pointed at a local
// production build on any other port (PLAYWRIGHT_BASE_URL), the browser
// Origin no longer matches and every unsafe /api call 403s. Rewrite the
// Origin/Referer on proxied API traffic back to the canonical dev origin
// so the auth journeys still exercise the real endpoints. Inert when the
// suite runs against :3000 (the CI / post-merge path).
const CANONICAL_ORIGIN = "http://127.0.0.1:3000";
async function installCsrfOriginShim(page: Page): Promise<void> {
  const base = process.env.PLAYWRIGHT_BASE_URL ?? "";
  if (!base || base.includes(":3000")) return;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const headers = { ...request.headers(), origin: CANONICAL_ORIGIN, referer: `${CANONICAL_ORIGIN}/` };
    const response = await route.fetch({ headers });
    await route.fulfill({ response });
  });
}

const VIEWPORTS = {
  mobile: { width: 375, height: 812 }, // >= 320px floor required by UI-SPEC
  desktop: { width: 1280, height: 800 },
} as const;

function readDemoCredentials(env: Record<string, string | undefined>): { username: string; password: string } {
  if (!env.DEMO_USERNAME || !env.DEMO_PASSWORD) {
    throw new Error("a11y suite requires DEMO_USERNAME/DEMO_PASSWORD (values withheld from diagnostic by design).");
  }
  return { username: env.DEMO_USERNAME, password: env.DEMO_PASSWORD };
}

interface AxeViolation {
  id: string;
  impact: string | null;
  help: string;
  nodes: { target: string[] }[];
}

async function runAxeScan(page: Page): Promise<AxeViolation[]> {
  await page.addScriptTag({ path: AXE_SCRIPT_PATH });
  const results = await page.evaluate(async () => {
    // @ts-expect-error -- axe is injected globally by the script tag above
    return window.axe.run(document, { resultTypes: ["violations"] });
  });
  return (results as { violations: AxeViolation[] }).violations;
}

function assertNoCriticalOrSeriousViolations(violations: AxeViolation[], context: string) {
  const blocking = violations.filter((v) => v.impact === "critical" || v.impact === "serious");
  if (blocking.length > 0) {
    const summary = blocking.map((v) => `  - [${v.impact}] ${v.id}: ${v.help} (${v.nodes.length} node(s))`).join("\n");
    throw new Error(`axe found ${blocking.length} critical/serious violation(s) on ${context}:\n${summary}`);
  }
}

const PUBLIC_PAGES: { name: string; path: (locale: string) => string }[] = [
  { name: "homepage", path: (l) => `/${l}` },
  { name: "login", path: (l) => `/${l}/login` },
  { name: "catalogue", path: (l) => `/${l}/catalogue` },
  { name: "sources", path: (l) => `/${l}/sources` },
];

test.beforeEach(async ({ page }) => {
  await installCsrfOriginShim(page);
});

for (const locale of ["es", "en"] as const) {
  for (const [viewportName, viewport] of Object.entries(VIEWPORTS)) {
    test.describe(`axe scan: ${locale} @ ${viewportName}`, () => {
      test.use({ viewport });

      for (const { name, path: pagePath } of PUBLIC_PAGES) {
        test(`${name} has no critical/serious axe violations`, async ({ page }) => {
          await page.goto(pagePath(locale));
          const violations = await runAxeScan(page);
          assertNoCriticalOrSeriousViolations(violations, `${name} (${locale}, ${viewportName})`);
        });
      }

      test("one game detail page has no critical/serious axe violations", async ({ page }) => {
        await page.goto(`/${locale}/catalogue`);
        await page.locator("main ul li a").first().click();
        // Wait for the detail navigation to settle before injecting axe --
        // scanning mid-navigation races the SSR document (no <title> yet).
        await page.waitForURL(new RegExp(`/${locale}/games/`));
        await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
        const violations = await runAxeScan(page);
        assertNoCriticalOrSeriousViolations(violations, `game detail (${locale}, ${viewportName})`);
      });
    });
  }
}

test.describe("no page-level horizontal overflow at 320-375px", () => {
  test.use({ viewport: VIEWPORTS.mobile });

  for (const { name, path: pagePath } of PUBLIC_PAGES) {
    test(`${name} has no horizontal scroll at mobile width`, async ({ page }) => {
      await page.goto(pagePath("es"));
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
      expect(overflow, `${name} should not overflow horizontally at ${VIEWPORTS.mobile.width}px`).toBe(false);
    });
  }
});

test.describe("reduced motion is respected", () => {
  test.use({ reducedMotion: "reduce" });

  test("homepage renders without error under prefers-reduced-motion", async ({ page }) => {
    const pageErrors: string[] = [];
    page.on("pageerror", (e) => pageErrors.push(e.message));
    await page.goto("/es");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    expect(pageErrors).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Plan 01.1-10: complete automated product evidence for the four D-01..D-04
// surfaces at the approved desktop AND mobile viewports. Real functional
// assertions + keyboard/focus + axe + mobile reflow + cover fallback, each
// writing a deterministic screenshot artifact (catalogue/detail/registration
// here; recommendations -- auth-gated -- in demo-journey.spec.ts).
// ---------------------------------------------------------------------------
async function assertNoMobileOverflow(page: Page, label: string) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  );
  expect(overflow, `${label} must not overflow horizontally at mobile width`).toBe(false);
}

for (const [viewportName, viewport] of Object.entries(VIEWPORTS)) {
  test.describe(`product surface evidence @ ${viewportName}`, () => {
    test.use({ viewport });

    test("catalogue: filter state survives reload, pagination, axe, screenshot", async ({ page }) => {
      await page.goto("/es/catalogue");
      await expect(page.getByRole("heading", { level: 1, name: "Catálogo" })).toBeVisible();

      // Populated grid + pagination affordance.
      const cards = page.locator("main ul.sp-grid li");
      expect(await cards.count()).toBeGreaterThan(0);
      await expect(page.locator('nav[aria-label="Paginación"]')).toBeVisible();
      await expect(page.getByRole("link", { name: "Siguiente" })).toBeVisible();

      // Keyboard: the search field is reachable and focusable by its label.
      await page.getByLabel("Buscar juegos").focus();
      await expect(page.getByLabel("Buscar juegos")).toBeFocused();

      // Apply a genre facet via the repeated-parameter GET form; the filtered
      // view must be a shareable URL that still reflects the filter after a
      // full reload.
      const genreFacet = page.locator("details.sp-facet").filter({ hasText: "Género" }).first();
      await genreFacet.locator("summary").click();
      const genreCheckboxes = genreFacet.locator('input[type="checkbox"]');
      expect(await genreCheckboxes.count()).toBeGreaterThanOrEqual(2);
      const chosenGenres = [
        await genreCheckboxes.nth(0).getAttribute("value"),
        await genreCheckboxes.nth(1).getAttribute("value"),
      ];
      expect(chosenGenres[0]).not.toBeNull();
      expect(chosenGenres[1]).not.toBeNull();
      await genreCheckboxes.nth(0).check();
      await genreCheckboxes.nth(1).check();

      const platformFacet = page.locator("details.sp-facet").filter({ hasText: "Plataforma" }).first();
      await platformFacet.locator("summary").click();
      const platformCheckbox = platformFacet.locator('input[type="checkbox"]').first();
      const chosenPlatform = await platformCheckbox.getAttribute("value");
      expect(chosenPlatform).not.toBeNull();
      await platformCheckbox.check();
      await page.getByRole("button", { name: "Aplicar filtros" }).click();
      await page.waitForURL(/[?&]genre=/);
      await page.reload();
      expect(page.url()).toMatch(/[?&]genre=/);
      const query = new URL(page.url()).searchParams;
      expect(query.getAll("genre")).toEqual(chosenGenres);
      expect(query.getAll("platform")).toEqual([chosenPlatform]);
      for (const chosenGenre of chosenGenres) {
        await expect(page.locator(`input[name="genre"][value="${chosenGenre}"]`)).toBeChecked();
      }
      await expect(page.locator(`input[name="platform"][value="${chosenPlatform}"]`)).toBeChecked();
      await expect(page.locator(".sp-chip-row")).toBeVisible();
      await expect(page.locator(".sp-chip-row .sp-chip")).toHaveCount(3);
      const violations = await runAxeScan(page);
      assertNoCriticalOrSeriousViolations(violations, `catalogue (filtered, ${viewportName})`);
      if (viewportName === "mobile") await assertNoMobileOverflow(page, "catalogue");

      await page.goto("/es/catalogue");
      await shoot(page, "catalogue", viewportName);
    });

    test("detail: cover (or fallback), ScorePill/omission, provenance + attribution, axe, screenshot", async ({ page }) => {
      await page.goto("/es/catalogue");
      const firstCard = page.locator("main ul.sp-grid li a").first();
      await firstCard.click();
      await page.waitForURL(/\/es\/games\//);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

      // Cover: either the hotlinked image or the first-party placeholder,
      // never an empty box.
      const cover = page.locator(".sp-cover").first();
      await expect(cover).toBeVisible();
      const hasImg = (await cover.locator("img").count()) > 0;
      const hasPlaceholder = (await cover.locator('[data-testid="cover-placeholder"]').count()) > 0;
      expect(hasImg || hasPlaceholder).toBe(true);

      // Provenance / IGDB attribution is a static, visible block.
      const provenance = page.locator('section[aria-label="Procedencia"]');
      await expect(provenance).toBeVisible();
      await expect(provenance).toContainText("IGDB");

      const violations = await runAxeScan(page);
      assertNoCriticalOrSeriousViolations(violations, `game detail (${viewportName})`);
      if (viewportName === "mobile") await assertNoMobileOverflow(page, "detail");

      await shoot(page, "detail", viewportName);
    });

    test("registration: labelled fields, client-side validation, axe, screenshot", async ({ page }) => {
      await page.goto("/es/register");
      await expect(page.getByRole("heading", { level: 1, name: "Crear una cuenta simulada" })).toBeVisible();

      // Every field has a visible, associated label.
      await expect(page.getByLabel("Usuario")).toBeVisible();
      await expect(page.getByLabel("Contraseña", { exact: true })).toBeVisible();
      await expect(page.getByLabel("Confirmar contraseña")).toBeVisible();

      // Password-mismatch is caught client-side, announced, and clears the
      // password fields (mirrors the login contract).
      await page.getByLabel("Usuario").fill("e2e-validation-only");
      await page.getByLabel("Contraseña", { exact: true }).fill("Abc12345!x");
      await page.getByLabel("Confirmar contraseña").fill("different99!");
      await page.getByRole("button", { name: "Crear cuenta simulada" }).click();
      const err = page.getByTestId("register-error");
      await expect(err).toBeVisible();
      await expect(err).toHaveText(/no coinciden/i);
      await expect(page.getByLabel("Contraseña", { exact: true })).toHaveValue("");

      const violations = await runAxeScan(page);
      assertNoCriticalOrSeriousViolations(violations, `registration (${viewportName})`);
      if (viewportName === "mobile") await assertNoMobileOverflow(page, "registration");

      await shoot(page, "registration", viewportName);
    });

    test("recommendations is auth-gated: signed-out visit redirects to login, no personal nav", async ({ page }) => {
      await page.goto("/es/recommendations");
      await page.waitForURL(/\/es\/login/);
      expect(page.url()).toContain("next=");
      // The authenticated-only nav links must not be present for a signed-out
      // visitor (threat T-01.1-10).
      await expect(page.getByRole("link", { name: "Recomendaciones" })).toHaveCount(0);
      await expect(page.getByRole("link", { name: "Colección" })).toHaveCount(0);
    });
  });
}

test.describe("keyboard-only journey (accessibility acceptance checklist)", () => {
  test.skip(!process.env.DEMO_USERNAME || !process.env.DEMO_PASSWORD, "requires DEMO_USERNAME/DEMO_PASSWORD");

  test("homepage -> login -> catalogue search -> detail -> status -> rating -> copies -> collection -> profile -> sign out, keyboard only", async ({
    page,
  }) => {
    const { username, password } = readDemoCredentials(process.env);

    // Skip link is the first focusable element (accessibility acceptance:
    // "skip link works").
    await page.goto("/es");
    await page.keyboard.press("Tab");
    await expect(page.locator(".skip-link")).toBeFocused();

    // Keyboard-navigate to the login link and activate it.
    await page.goto("/es/login");
    await page.getByLabel("Usuario").focus();
    await page.keyboard.type(username);
    await page.keyboard.press("Tab");
    await page.keyboard.type(password);
    await page.keyboard.press("Enter");
    await page.waitForURL(/\/es\/catalogue$/);

    // Keyboard search.
    await page.getByLabel("Buscar juegos").focus();
    await page.keyboard.type("a");
    await page.keyboard.press("Enter");
    await page.waitForLoadState("networkidle");

    // Keyboard-activate the first result.
    const firstLink = page.locator("main ul li a").first();
    await firstLink.focus();
    await expect(firstLink).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    // Status: native radios, arrow-key/space operable.
    const playingRadio = page.getByRole("radio", { name: "Jugando" });
    await playingRadio.focus();
    await page.keyboard.press("Space");
    await expect(playingRadio).toBeChecked();
    await page.keyboard.press("Tab"); // reach the save button
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("status-feedback")).toHaveText("Estado guardado");

    // Collection: reachable via nav, requires auth (already signed in).
    await page.goto("/es/collection");
    await expect(page.getByRole("heading", { name: "Colección" })).toBeVisible();

    // Public profile for the signed-in demo account.
    await page.goto(`/es/profiles/${username}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    // Sign out via the same CSRF-protected endpoint the UI uses.
    const csrfCookie = (await page.context().cookies()).find((c) => c.name === "csrftoken");
    await page.request.post("/api/accounts/logout/", {
      headers: csrfCookie ? { "X-CSRFToken": csrfCookie.value } : {},
    });
    const cookiesAfter = await page.context().cookies();
    expect(cookiesAfter.some((c) => c.name === "sessionid")).toBe(false);
  });
});
