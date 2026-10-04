import { expect, test, type Page } from "@playwright/test";

// Credentials are entered into the browser but must never be retained in a
// Playwright trace, including when a test fails.
test.use({ trace: "off" });

const REQUIRED_ENV_NAMES = [
  "RESEARCH_VIEWER_USERNAME",
  "RESEARCH_VIEWER_PASSWORD",
  "PLATFORM_ADMIN_USERNAME",
  "PLATFORM_ADMIN_PASSWORD",
  "DEMO_USERNAME",
  "DEMO_PASSWORD",
] as const;

const SAME_ORIGIN = new URL(process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000").origin;
const ALLOWED_ASSET_ORIGINS = new Set([SAME_ORIGIN, "https://images.igdb.com"]);

function requireCredentials(usernameName: string, passwordName: string) {
  const username = process.env[usernameName];
  const password = process.env[passwordName];
  if (!username || !password) {
    throw new Error(`Missing ${usernameName}/${passwordName}; values withheld by design.`);
  }
  return { username, password };
}

type CapabilityName = "can_view_research" | "can_manage_platform";

async function login(
  page: Page,
  locale: "es" | "en",
  usernameName: string,
  passwordName: string,
  expectedCapability?: { name: CapabilityName; value: boolean },
) {
  const credentials = requireCredentials(usernameName, passwordName);
  await page.goto(`/${locale}/login`);
  await page.getByLabel(/Usuario|Username/).fill(credentials.username);
  await page.getByLabel(/Contrase|Password/).fill(credentials.password);
  await Promise.all([
    page.waitForURL(new RegExp(`/${locale}$`)),
    page.getByRole("button", { name: /Entrar|Log in/ }).click(),
  ]);
  await expect(page.getByRole("region", { name: /Catálogo|Catalogue/ })).toBeVisible();

  const session = await page.request.get("/api/accounts/me/");
  expect(session.status()).toBe(200);
  if (expectedCapability) {
    const body = (await session.json()) as { capabilities?: Record<string, boolean> };
    expect(body.capabilities?.[expectedCapability.name]).toBe(expectedCapability.value);
  }
}

async function installLocalNetworkGuards(page: Page) {
  const unexpectedOrigins = new Set<string>();
  const sensitiveResponses: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      (url.protocol === "http:" || url.protocol === "https:") &&
      !ALLOWED_ASSET_ORIGINS.has(url.origin)
    ) {
      unexpectedOrigins.add(url.origin);
    }
  });
  page.on("response", async (response) => {
    const url = new URL(response.url());
    if (url.origin !== SAME_ORIGIN || !url.pathname.startsWith("/api/")) return;
    const contentType = response.headers()["content-type"] ?? "";
    if (!contentType.includes("json") && !contentType.includes("text")) return;
    try {
      const body = (await response.text()).toLowerCase();
      for (const marker of ["password", "secret", "set-cookie", "authorization", "per_user", "traceback"]) {
        if (body.includes(marker)) sensitiveResponses.push(`${url.pathname}:${marker}`);
      }
    } catch {
      // A response that disappears during navigation is not a secret disclosure.
    }
  });
  return { unexpectedOrigins, sensitiveResponses };
}

async function selectFirstRealOption(page: Page, selector: string) {
  const select = page.locator(selector);
  if (await select.locator("option").count() > 1) await select.selectOption({ index: 1 });
}

test.describe("research panel preflight", () => {
  test("requires every runtime credential contract without echoing values", () => {
    const missing = REQUIRED_ENV_NAMES.filter((name) => !process.env[name]);
    expect(missing, `Missing required process variables: ${missing.join(", ")}`).toEqual([]);
  });
});

test.describe("research panel authenticated browser tracer", () => {
  test("signed-out research access redirects to the localized login", async ({ page }) => {
    await page.context().clearCookies();
    await page.goto("/es/research");
    await expect(page).toHaveURL(/\/es\/login\?next=%2Fes%2Fresearch|\/es\/login\?next=\/es\/research/);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Iniciar sesión");
  });

  test("Research Viewer sees real comparison, filters, equivalent table/SVG, and exports", async ({ page }) => {
    const network = await installLocalNetworkGuards(page);
    await login(page, "es", "RESEARCH_VIEWER_USERNAME", "RESEARCH_VIEWER_PASSWORD", {
      name: "can_view_research",
      value: true,
    });
    await page.goto("/es/research");

    await expect(page.getByTestId("research-panel")).toBeVisible();
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Panel de investigación");
    await expect(page.getByRole("form", { name: "Filtros de investigación" })).toBeVisible();
    await expect(page.getByTestId("research-chart")).toBeVisible();
    await expect(page.getByTestId("research-table")).toBeVisible();
    await expect(page.getByText("No hay acciones destructivas en este panel.")).toBeVisible();
    await expect(page.getByRole("button", { name: /re-?run|delete|borrar|relanzar/i })).toHaveCount(0);

    const tableRows = page.getByTestId("research-table").locator("tbody tr");
    const chartRows = page.getByTestId("research-chart").locator("svg g");
    expect(await tableRows.count()).toBeGreaterThan(0);
    expect(await chartRows.count()).toBe(await tableRows.count());
    await expect(chartRows.first()).toContainText((await tableRows.first().locator("th").innerText()).trim());

    await selectFirstRealOption(page, "#research-run");
    await selectFirstRealOption(page, "#research-algorithm");
    await selectFirstRealOption(page, "#research-cohort");
    await selectFirstRealOption(page, "#research-metric");
    await page.getByRole("button", { name: "Aplicar filtros" }).click();
    await page.waitForLoadState("networkidle");
    expect(new URL(page.url()).searchParams.toString()).not.toBe("");
    await expect(page.getByTestId("research-table")).toBeVisible();

    const downloads = page.locator('a[href^="/api/evaluation/exports/"]');
    expect(await downloads.count()).toBeGreaterThanOrEqual(3);
    for (const link of await downloads.all()) {
      const href = await link.getAttribute("href");
      expect(href).toMatch(/^\/api\/evaluation\/exports\//);
      const response = await page.request.get(new URL(href!, SAME_ORIGIN).toString());
      expect(response.status()).toBe(200);
      const body = (await response.text()).toLowerCase();
      expect(body).not.toMatch(/per_user|password|secret|set-cookie|authorization|traceback/);
    }

    expect([...network.unexpectedOrigins]).toEqual([]);
    expect(network.sensitiveResponses).toEqual([]);
  });

  for (const locale of ["es", "en"] as const) {
    test(`localized populated panel has the same accessible structure (${locale})`, async ({ page }) => {
      const network = await installLocalNetworkGuards(page);
      await login(page, locale, "RESEARCH_VIEWER_USERNAME", "RESEARCH_VIEWER_PASSWORD", {
        name: "can_view_research",
        value: true,
      });
      await page.goto(`/${locale}/research`);
      await expect(page.getByTestId("research-panel")).toBeVisible();
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await expect(page.getByRole("table")).toHaveCount(1);
      await expect(page.getByRole("figure")).toHaveCount(1);
      await expect(page.getByTestId("research-table-scroll")).toHaveAttribute("tabindex", "0");
      await expect(page.getByRole("link", { name: /csv/i })).toBeVisible();
      await expect(page.getByRole("link", { name: /json|evidencia|evidence/i }).first()).toBeVisible();
      expect([...network.unexpectedOrigins]).toEqual([]);
      expect(network.sensitiveResponses).toEqual([]);
    });
  }
});

test.describe("research panel denied account", () => {
  test("authenticated account without Research Viewer receives neutral 404", async ({ page }) => {
    await login(page, "en", "DEMO_USERNAME", "DEMO_PASSWORD", {
      name: "can_view_research",
      value: false,
    });
    await page.goto("/en/research");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(/^(404|Page not found)$/);
    await expect(page.getByTestId("research-panel")).toHaveCount(0);
    await expect(page.getByText(/Research Viewer|research panel/i)).toHaveCount(0);

    const response = await page.request.get("/api/evaluation/comparison/");
    expect(response.status()).toBe(404);
  });
});

test.describe("research panel keyboard and reflow", () => {
  test.use({ viewport: { width: 320, height: 800 } });

  test("keeps page overflow internal at 320px and exposes table navigation", async ({ page }) => {
    await login(page, "es", "RESEARCH_VIEWER_USERNAME", "RESEARCH_VIEWER_PASSWORD", {
      name: "can_view_research",
      value: true,
    });
    await page.goto("/es/research");
    const dimensions = await page.evaluate(() => ({
      pageWidth: document.documentElement.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
      tableWidth: document.querySelector<HTMLElement>("[data-testid=research-table-scroll]")?.scrollWidth ?? 0,
    }));
    expect(dimensions.pageWidth).toBeLessThanOrEqual(dimensions.viewportWidth + 1);
    expect(dimensions.tableWidth).toBeGreaterThanOrEqual(dimensions.viewportWidth);
    await page.getByTestId("research-table-scroll").focus();
    await expect(page.getByTestId("research-table-scroll")).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: /csv/i })).toBeFocused();
  });

  test("does not expose horizontal page overflow at 400 percent zoom", async ({ page }) => {
    await login(page, "en", "RESEARCH_VIEWER_USERNAME", "RESEARCH_VIEWER_PASSWORD", {
      name: "can_view_research",
      value: true,
    });
    await page.goto("/en/research");
    await page.evaluate(() => { document.documentElement.style.zoom = "4"; });
    const dimensions = await page.evaluate(() => ({
      pageWidth: document.documentElement.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
    }));
    // CSS zoom is a deterministic browser-test approximation. Its raw
    // scrollWidth is expressed in physical pixels, so compare it with the
    // correspondingly scaled viewport; the 320px test covers true reflow.
    expect(dimensions.pageWidth).toBeLessThanOrEqual(dimensions.viewportWidth * 4 + 1);
  });
});
