import { expect, test } from "@playwright/test";

// The smoke login uses process-only demo credentials; failure traces are off.
test.use({ trace: "off" });

const LOCAL_BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const REQUIRED_ENV_NAMES = ["DEMO_USERNAME", "DEMO_PASSWORD"] as const;

function safeOrigin(): string {
  return new URL(LOCAL_BASE_URL).origin;
}

test.describe("deployed public demo smoke (OPS-01, T-07-02)", () => {
  test.use({ baseURL: safeOrigin() });

  // Cover images are intentionally external (data provenance/licensing: URLs
  // with attribution, never mirrored -- see catalogue/serializers.py and
  // docs/verification/catalogue-freeze.md's per-asset licensing table), so a
  // game detail page legitimately fetches from Wikimedia Commons. This is
  // the only allowlisted exception to the same-origin check below; any
  // other host still fails the test (T-07-02: redirect/asset-injection to
  // an unexpected domain).
  const ALLOWLISTED_ASSET_HOSTS = new Set(["upload.wikimedia.org", "commons.wikimedia.org", "images.igdb.com"]);

  test("public revision: health -> homepage -> login -> catalogue -> detail", async ({ page }) => {
    const missing = REQUIRED_ENV_NAMES.filter((name) => !process.env[name]);
    expect(missing, `Missing required process variables: ${missing.join(", ")}`).toEqual([]);
    const baseUrl = new URL(LOCAL_BASE_URL);
    const isLocal = ["localhost", "127.0.0.1"].includes(baseUrl.hostname);
    if (!isLocal && baseUrl.protocol !== "https:") throw new Error("Non-local BASE_URL must use HTTPS.");
    if (baseUrl.username || baseUrl.password || baseUrl.pathname !== "/" || baseUrl.search || baseUrl.hash) {
      throw new Error("PLAYWRIGHT_BASE_URL must be an origin only, without credentials, path, query, or fragment.");
    }
    const expectedOrigin = baseUrl.origin;

    const expectedCommit = process.env.EXPECTED_COMMIT;

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
    const healthBody = await health.json() as { status?: string; commit?: string };
    expect(healthBody.status).toBe("ok");
    if (expectedCommit) {
      expect(expectedCommit).toMatch(/^[0-9a-f]{40}$/i);
      expect(healthBody.commit).toBe(expectedCommit);
    }

    await page.goto("/es");
    expect(new URL(page.url()).origin).toBe(expectedOrigin);
    await expect(page.locator("main")).toBeVisible();

    await page.goto("/es/login");
    await page.getByLabel("Usuario").fill(username);
    await page.getByLabel("Contraseña").fill(password);
    await Promise.all([
      page.waitForURL(/\/es$/),
      page.getByRole("button", { name: "Entrar" }).click(),
    ]);
    expect(new URL(page.url()).origin).toBe(expectedOrigin);
    await expect(page.getByRole("region", { name: "Catálogo" })).toBeVisible();
    const session = await page.request.get("/api/accounts/me/");
    expect(session.status()).toBe(200);
    const sessionBody = (await session.json()) as { is_demo?: boolean };
    expect(sessionBody.is_demo).toBe(true);

    const firstGame = page.locator("main ul li a").first();
    await expect(firstGame).toBeVisible();
    const title = (await firstGame.locator("p").first().innerText()).trim();
    await firstGame.click();
    expect(new URL(page.url()).origin).toBe(expectedOrigin);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(title);

    expect([...unexpectedHosts], `unexpected network host(s): ${[...unexpectedHosts].join(", ")}`).toEqual([]);
    expect(failedRequests, `failed request(s): ${failedRequests.join(", ")}`).toEqual([]);
  });
});
