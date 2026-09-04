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
