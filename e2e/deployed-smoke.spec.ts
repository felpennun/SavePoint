import { expect, test } from "@playwright/test";

function requiredEnv(name: "BASE_URL" | "EXPECTED_COMMIT" | "DEMO_USERNAME" | "DEMO_PASSWORD"): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Deployed smoke requires ${name} (value withheld from diagnostic).`);
  }
  return value;
}

const baseUrl = new URL(requiredEnv("BASE_URL"));
if (baseUrl.protocol !== "https:") {
  throw new Error("BASE_URL must use HTTPS.");
}
if (baseUrl.username || baseUrl.password || baseUrl.pathname !== "/" || baseUrl.search || baseUrl.hash) {
  throw new Error("BASE_URL must be an origin only, without credentials, path, query, or fragment.");
}

const expectedOrigin = baseUrl.origin;
const expectedCommit = requiredEnv("EXPECTED_COMMIT");
if (!/^[0-9a-f]{40}$/i.test(expectedCommit)) {
  throw new Error("EXPECTED_COMMIT must be a full 40-character Git SHA.");
}

test.use({ baseURL: expectedOrigin });

test("public revision: health -> homepage -> login -> catalogue -> detail", async ({ page }) => {
  const username = requiredEnv("DEMO_USERNAME");
  const password = requiredEnv("DEMO_PASSWORD");
  const unexpectedHosts = new Set<string>();
  const failedRequests: string[] = [];

  page.on("request", (request) => {
    const requestUrl = new URL(request.url());
    if (requestUrl.protocol === "http:" || requestUrl.protocol === "https:") {
      if (requestUrl.origin !== expectedOrigin) unexpectedHosts.add(requestUrl.host);
    }
  });
  page.on("requestfailed", (request) => {
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
