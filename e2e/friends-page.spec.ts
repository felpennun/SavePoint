import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const AXE_SCRIPT_PATH = path.join(__dirname, "..", "node_modules", "axe-core", "axe.min.js");

interface Credentials {
  username: string;
  password: string;
}

async function register(page: Page, prefix: string): Promise<Credentials> {
  const stamp = `${Date.now().toString(36)}${Math.floor(Math.random() * 1e6).toString(36)}`;
  const credentials = { username: `${prefix}-${stamp}`, password: `Zeph-Corridor-${Math.floor(Math.random() * 9000 + 1000)}-Loft!` };
  await page.goto("/es/register");
  await page.getByLabel("Usuario").fill(credentials.username);
  await page.getByLabel("Contraseña", { exact: true }).fill(credentials.password);
  await page.getByLabel("Confirmar contraseña").fill(credentials.password);
  const [response] = await Promise.all([
    page.waitForResponse((item) => item.url().includes("/api/accounts/register/")),
    page.getByRole("button", { name: "Crear cuenta" }).click(),
  ]);
  if (response.status() === 429) test.skip(true, "registration budget exhausted; rerun with a fresh local budget");
  expect(response.status()).toBe(201);
  await page.waitForURL(/\/es$/);
  return credentials;
}

async function collectFirstGame(page: Page): Promise<string> {
  await page.goto("/es/catalogue");
  await page.locator("main ul.sp-grid li a").first().click();
  await page.waitForURL(/\/es\/games\//);
  const title = ((await page.getByRole("heading", { level: 1 }).first().textContent()) ?? "").replace(/\s*\(\d{4}\)\s*$/, "").trim();
  await page.getByLabel("Estado").selectOption("playing");
  await page.getByRole("button", { name: "Guardar configuración" }).click();
  await expect(page.getByTestId("status-feedback")).toContainText("Configuración guardada");
  return title;
}

test.describe("Friends page: search, requests, recommendations and notifications", () => {
  test("two real accounts become friends and exchange a recommendation", async ({ page, browser }) => {
    test.setTimeout(180_000);
    const first = await register(page, "e2e-fr-a");
    const gameTitle = await collectFirstGame(page);

    const contextB = await browser.newContext({ baseURL: test.info().project.use.baseURL });
    const pageB = await contextB.newPage();
    try {
      const second = await register(pageB, "e2e-fr-b");

      // A finds B by the exact username and sends a request.
      await page.goto("/es/friends");
      await page.getByLabel("BUSCAR PERSONA").fill(second.username);
      await expect(page.locator(".sp-fr-result")).toContainText(second.username);
      await page.locator(".sp-fr-result").getByRole("button", { name: "Enviar solicitud" }).click();
      await expect(page.locator(".sp-fr-result")).toContainText("Solicitud enviada");
      await expect(page.locator(".sp-fr-pending")).toHaveCount(1);

      // B sees it in the notifications and accepts it.
      await pageB.goto("/es/friends");
      const request = pageB.locator(".sp-fr-notif", { hasText: first.username });
      await expect(request).toContainText("quiere añadirte como amistad");
      await request.getByRole("button", { name: "Aceptar", exact: true }).click();
      await expect(pageB.locator(".sp-fr-row", { hasText: first.username })).toBeVisible();

      // A is told, and can now recommend a game to B.
      await page.reload();
      await expect(page.locator(".sp-fr-notif", { hasText: "aceptó tu solicitud de amistad" })).toBeVisible();
      await page.locator(".sp-fr-row", { hasText: second.username }).click();
      await expect(page.locator(".sp-fr-hero")).toContainText("AMISTAD");
      await page.getByRole("button", { name: "Recomendarle un juego" }).click();
      await page.locator(".sp-fr-chip", { hasText: gameTitle }).first().click();
      await page.getByLabel("Nota", { exact: false }).fill("Te va a gustar");
      await page.getByRole("button", { name: "Enviar recomendación" }).click();
      await expect(page.locator(".sp-fr-banner")).toContainText("Enviaste");

      // B receives it and puts it in the backlog.
      await pageB.reload();
      const recommendation = pageB.locator(".sp-fr-notif", { hasText: "te recomienda" });
      await expect(recommendation).toContainText("Te va a gustar");
      await recommendation.getByRole("button", { name: "Añadir a pendientes" }).click();
      await expect(recommendation).toContainText("AÑADIDO A PENDIENTES");
      await pageB.goto("/es/collection");
      await expect(pageB.locator("main")).toContainText(gameTitle);

      // The page has no critical or serious accessibility violations.
      await page.goto("/es/friends");
      await expect(page.locator(".sp-fr-grid")).toBeVisible();
      await page.addScriptTag({ path: AXE_SCRIPT_PATH });
      const violations = (await page.evaluate(async () => {
        // @ts-expect-error -- axe is injected by the local pinned bundle
        return (await window.axe.run(document, { resultTypes: ["violations"] })).violations;
      })) as Array<{ impact: string | null }>;
      expect(violations.filter((item) => item.impact === "critical" || item.impact === "serious")).toEqual([]);
    } finally {
      await contextB.close();
    }
  });
});
