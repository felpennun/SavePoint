import { expect, test } from "@playwright/test";

// Deliberately never throws at module-load time (unlike an earlier version
// of this file): a bare `playwright test` run (no path filter, as Plan
// 01-14's own <verify> block requires) must still register and run every
// other spec even when no deployment env vars are set locally -- this spec
// just skips itself instead, matching the pattern already used by
// demo-journey.spec.ts and a11y.spec.ts's DEMO_USERNAME/DEMO_PASSWORD gate.
const REQUIRED_ENV_NAMES = ["BASE_URL", "EXPECTED_COMMIT", "DEMO_USERNAME", "DEMO_PASSWORD"] as const;

function missingEnvNames(): string[] {
  return REQUIRED_ENV_NAMES.filter((name) => !process.env[name]);
}

function safeOrigin(): string | undefined {
  try {
    return new URL(process.env.BASE_URL ?? "").origin;
  } catch {
    return undefined;
  }
}

test.describe("deployed public demo smoke (OPS-01, T-07-02)", () => {
  test.skip(missingEnvNames().length > 0, `requires ${REQUIRED_ENV_NAMES.join(", ")}`);

  // baseURL must be computed even when the env is missing/malformed (the
  // skip above still lets this describe body register) -- safeOrigin()
  // never throws; the strict validation happens inside the test itself,
  // where a real failure is meaningful instead of hiding every other spec.
  test.use({ baseURL: safeOrigin() });

  // Cover images are intentionally external (data provenance/licensing: URLs
  // with attribution, never mirrored -- see catalogue/serializers.py and
  // docs/verification/catalogue-freeze.md's per-asset licensing table), so a
  // game detail page legitimately fetches from Wikimedia Commons. This is
  // the only allowlisted exception to the same-origin check below; any
  // other host still fails the test (T-07-02: redirect/asset-injection to
  // an unexpected domain).
  const ALLOWLISTED_ASSET_HOSTS = new Set(["upload.wikimedia.org", "commons.wikimedia.org"]);

  test("public revision: health -> homepage -> login -> catalogue -> detail", async ({ page }) => {
    const baseUrl = new URL(process.env.BASE_URL!);
    if (baseUrl.protocol !== "https:") {
      throw new Error("BASE_URL must use HTTPS.");
    }
    if (baseUrl.username || baseUrl.password || baseUrl.pathname !== "/" || baseUrl.search || baseUrl.hash) {
      throw new Error("BASE_URL must be an origin only, without credentials, path, query, or fragment.");
    }
    const expectedOrigin = baseUrl.origin;

    const expectedCommit = process.env.EXPECTED_COMMIT!;
    if (!/^[0-9a-f]{40}$/i.test(expectedCommit)) {
      throw new Error("EXPECTED_COMMIT must be a full 40-character Git SHA.");
    }

    const username = process.env.DEMO_USERNAME!;
    const password = process.env.DEMO_PASSWORD!;
    const unexpectedHosts = new Set<string>();
    const failedRequests: string[] = [];

    page.on("request", (request) => {
      const requestUrl = new URL(request.url());
      if (requestUrl.protocol === "http:" || requestUrl.protocol === "https:") {
        if (requestUrl.origin !== expectedOrigin && !ALLOWLISTED_ASSET_HOSTS.has(requestUrl.host)) {
          unexpectedHosts.add(requestUrl.host);
        }
      }
    });
    page.on("requestfailed", (request) => {
      // net::ERR_ABORTED is Chromium's cancellation code for a request the
      // browser itself gave up on -- almost always a Next.js <Link>
      // background prefetch (nav bar, catalogue cards) that was still in
      // flight when the page navigated away, not a real network/server
      // failure. Recording only genuine failures keeps this check
      // meaningful instead of permanently red on every run against a real
      // client-side-routed app.
      if (request.failure()?.errorText === "net::ERR_ABORTED") return;
      // Record only method and URL origin/path; never headers, cookies or body.
      const url = new URL(request.url());
      failedRequests.push(`${request.method()} ${url.origin}${url.pathname}`);
    });

    const health = await page.request.get("/health/", { maxRedirects: 0 });
    expect(health.status()).toBe(200);
    expect(new URL(health.url()).origin).toBe(expectedOrigin);
    await expect(health.json()).resolves.toEqual({ status: "ok", commit: expectedCommit });

    await page.goto("/es");
    expect(new URL(page.url()).origin).toBe(expectedOrigin);
    await expect(page.locator("main")).toBeVisible();

    await page.goto("/es/login");
    await page.getByLabel("Usuario").fill(username);
    await page.getByLabel("Contraseña").fill(password);
    await page.getByRole("button", { name: "Entrar" }).click();
    await page.waitForURL(/\/es\/catalogue$/);
    expect(new URL(page.url()).origin).toBe(expectedOrigin);
    await expect(page.getByRole("heading", { name: "Catálogo" })).toBeVisible();

    const firstGame = page.locator("main ul li a").first();
    await expect(firstGame).toBeVisible();
    const title = (await firstGame.locator("p").first().innerText()).trim();
    await firstGame.click();
    expect(new URL(page.url()).origin).toBe(expectedOrigin);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);

    expect([...unexpectedHosts], `unexpected network host(s): ${[...unexpectedHosts].join(", ")}`).toEqual([]);
    expect(failedRequests, `failed request(s): ${failedRequests.join(", ")}`).toEqual([]);
  });
});
