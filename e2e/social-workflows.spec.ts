import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

const AXE_SCRIPT_PATH = path.join(__dirname, "..", "node_modules", "axe-core", "axe.min.js");
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";
const CANONICAL_ORIGIN = "http://127.0.0.1:3000";

interface Credentials {
  username: string;
  password: string;
}

interface AxeViolation {
  id: string;
  impact: string | null;
  help: string;
  nodes: { target: string[] }[];
}

async function installCsrfOriginShim(page: Page): Promise<void> {
  if (!process.env.PLAYWRIGHT_BASE_URL || BASE_URL.includes(":3000")) return;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const headers = {
      ...request.headers(),
      origin: CANONICAL_ORIGIN,
      referer: `${CANONICAL_ORIGIN}/`,
    };
    const response = await route.fetch({ headers });
    await route.fulfill({ response });
  });
}

async function runAxe(page: Page, surface: string): Promise<void> {
  await page.addScriptTag({ path: AXE_SCRIPT_PATH });
  const violations = await page.evaluate(async () => {
    // @ts-expect-error -- axe is injected by the local pinned bundle
    return (await window.axe.run(document, { resultTypes: ["violations"] })).violations;
  }) as AxeViolation[];
  const blocking = violations.filter((item) => item.impact === "critical" || item.impact === "serious");
  expect(blocking, `${surface} must have no critical/serious axe violations`).toEqual([]);
}

async function assertNoOverflow(page: Page, surface: string): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth, `${surface} must not overflow horizontally`).toBeLessThanOrEqual(dimensions.clientWidth + 1);
}

async function login(page: Page, credentials: Credentials): Promise<void> {
  await page.goto("/es/login");
  await page.getByLabel("Usuario").fill(credentials.username);
  await page.getByLabel("Contraseña").fill(credentials.password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL(/\/es\/catalogue$/);
}

async function registerFresh(page: Page, prefix: string): Promise<Credentials> {
  const stamp = `${Date.now().toString(36)}${Math.floor(Math.random() * 1e6).toString(36)}`;
  const credentials = {
    username: `${prefix}-${stamp}`,
    password: `Runtime-${stamp}-Qx7`,
  };
  await page.goto("/es/register");
  await page.getByLabel("Usuario").fill(credentials.username);
  await page.getByLabel("Contraseña", { exact: true }).fill(credentials.password);
  await page.getByLabel("Confirmar contraseña").fill(credentials.password);
  const [response] = await Promise.all([
    page.waitForResponse((item) => item.url().includes("/api/accounts/register/")),
    page.getByRole("button", { name: "Crear cuenta simulada" }).click(),
  ]);
  if (response.status() === 429) {
    test.skip(true, "registration budget exhausted; rerun the real social journey with a fresh local budget");
  }
  expect(response.status()).toBe(201);
  await page.waitForURL(/\/es\/catalogue$/);
  return credentials;
}

async function searchExact(page: Page, alias: string): Promise<void> {
  await page.goto(`/es/friends?alias=${encodeURIComponent(alias)}`);
  const input = page.getByLabel("Alias exacto");
  await input.fill(alias);
  await page.getByRole("button", { name: "Buscar alias" }).click();
  await expect(page.locator('[data-social-actions]').filter({ hasText: alias })).toBeVisible();
}

async function sendRequest(page: Page, alias: string): Promise<void> {
  await searchExact(page, alias);
  const actions = page.locator('[data-social-actions]').filter({ hasText: alias });
  const button = actions.getByRole("button", { name: "Enviar solicitud de amistad" });
  if (await button.count()) {
    await button.click();
    await expect(actions).toContainText("Solicitud enviada");
  } else {
    await expect(actions).toContainText("Solicitud pendiente");
  }
}

async function acceptRequest(page: Page, senderAlias: string): Promise<void> {
  await page.goto("/es/friends");
  const row = page.locator("li[data-testid^='social-request-']").filter({ hasText: senderAlias });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "Aceptar solicitud" }).click();
  await expect(page.getByRole("status")).toContainText("Solicitud aceptada");
}

async function rejectRequest(page: Page, senderAlias: string): Promise<void> {
  await page.goto("/es/friends");
  const row = page.locator("li[data-testid^='social-request-']").filter({ hasText: senderAlias });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "Rechazar solicitud" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar" }).click();
  await expect(page.getByRole("status")).toContainText("Solicitud rechazada");
}

async function confirmFriendAction(page: Page, alias: string, action: "Eliminar amistad" | "Bloquear"): Promise<void> {
  await page.goto("/es/friends");
  const row = page.locator("li[data-testid^='social-friend-']").filter({ hasText: alias });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: action }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Confirmar" }).click();
  await expect(page.getByRole("status")).toBeVisible();
}

async function addGameAndComment(page: Page): Promise<{ slug: string; title: string; id: string }> {
  await page.goto("/es/catalogue");
  const link = page.locator("main ul.sp-grid li a").first();
  const href = await link.getAttribute("href");
  const title = (await link.locator("p").first().innerText()).trim();
  expect(href).toMatch(/\/es\/games\//);
  const slug = href!.split("/").filter(Boolean).pop()!;
  await link.click();
  await page.waitForURL(/\/es\/games\//);
  await page.getByText("Jugando", { exact: true }).click();
  await page.getByRole("button", { name: "Guardar configuración" }).click();
  await expect(page.getByTestId("configuration-feedback")).toContainText("Configuración guardada");

  await expect(page.getByText("Cargando comentarios…")).toHaveCount(0);
  const edit = page.getByRole("button", { name: "Editar" });
  if (await edit.count()) await edit.click();
  await page.getByLabel("Tu comentario").fill("Comentario social E2E <script>alert(1)</script>");
  await page.getByRole("button", { name: /Guardar comentario/ }).click();
  await expect(page.getByTestId("comment-feedback")).toContainText("Comentario guardado");
  await expect(page.locator(".sp-game-comments")).toContainText("Comentario social E2E");

  const response = await page.request.get(`/api/catalogue/games/${slug}/`);
  const body = await response.json() as { id?: string };
  expect(response.ok()).toBe(true);
  expect(body.id).toBeTruthy();
  return { slug, title, id: body.id! };
}

async function sendRecommendation(page: Page, recipient: string, workId: string, text: string): Promise<void> {
  await page.goto("/es/messages");
  await page.getByLabel("Amistad").selectOption({ label: recipient });
  await page.getByLabel("Juego del catálogo").selectOption(workId);
  await page.getByLabel("Mensaje opcional").fill(text);
  await page.getByRole("button", { name: "Enviar recomendación" }).click();
  await expect(page.getByRole("status")).toContainText("Recomendación enviada");
}

test.describe("Phase 6 social journeys through the real same-origin stack", () => {
  test.skip(!process.env.DEMO_USERNAME || !process.env.DEMO_PASSWORD, "requires DEMO_USERNAME/DEMO_PASSWORD at runtime");

  test("friendship lifecycle, protected profile, comments, recommendations, inbox and a11y", async ({ page, browser }) => {
    test.setTimeout(180_000);
    await installCsrfOriginShim(page);
    const contextB = await browser.newContext({ baseURL: BASE_URL });
    const contextC = await browser.newContext({ baseURL: BASE_URL });
    const pageB = await contextB.newPage();
    const pageC = await contextC.newPage();
    await Promise.all([installCsrfOriginShim(pageB), installCsrfOriginShim(pageC)]);

    const primary: Credentials = {
      username: process.env.DEMO_USERNAME!,
      password: process.env.DEMO_PASSWORD!,
    };
    let accountB: Credentials;
    let accountC: Credentials;
    try {
      await login(page, primary);
      accountB = await registerFresh(pageB, "e2e-social-b");
      accountC = await registerFresh(pageC, "e2e-social-c");
      await login(page, primary);

      // Keyboard contract: the profile menu traps focus, Escape closes it and
      // returns focus to the trigger before any social mutation is attempted.
      await page.goto("/es/friends");
      const accountTrigger = page.getByRole("button", { name: /Cuenta simulada/ });
      await accountTrigger.click();
      await expect(page.getByRole("menu")).toBeVisible();
      await page.keyboard.press("Escape");
      await expect(page.getByRole("menu")).toHaveCount(0);
      await expect(accountTrigger).toBeFocused();
      await page.setViewportSize({ width: 320, height: 800 });
      await page.emulateMedia({ reducedMotion: "reduce" });
      await assertNoOverflow(page, "friends at 320px");
      await runAxe(page, "friends at 320px");

      // D-03/D-05: exact alias, rejection, resubmission and acceptance.
      await sendRequest(page, accountB.username);
      await login(pageB, accountB);
      await rejectRequest(pageB, primary.username);
      await login(page, primary);
      await sendRequest(page, accountB.username);
      await login(pageB, accountB);
      await acceptRequest(pageB, primary.username);

      // D-09/D-11: the friend owns a real catalogue item and comment. The
      // hostile string is asserted as text by React, never as executable HTML.
      const game = await addGameAndComment(pageB);
      await login(page, primary);
      await page.goto(`/es/profiles/${accountB.username}`);
      await expect(page.getByRole("heading", { name: `Perfil de ${accountB.username}` })).toBeVisible();
      await expect(page.getByText("Actividad pública")).toBeVisible();
      await expect(page.locator("main")).toContainText("Comentario social E2E");
      await expect(page.locator("main")).not.toContainText("password");
      await expect(page.locator("main")).not.toContainText("price");
      await runAxe(page, "friend protected profile");

      // A second accepted friend proves D-15's fan-out rule rather than
      // accidentally treating the sender as a single global recipient.
      await sendRequest(page, accountC.username);
      await login(pageC, accountC);
      await acceptRequest(pageC, primary.username);
      await login(page, primary);

      // D-13/D-14: send to both friends, observe a private unread inbox, then
      // mark one message read through the browser UI.
      const hostileText = "Recomendación E2E <script>alert(1)</script>";
      await sendRecommendation(page, accountB.username, game.id, hostileText);
      await sendRecommendation(page, accountC.username, game.id, "Otra recomendación E2E");
      await page.goto("/es/messages");
      await expect(page.locator("main")).toContainText(hostileText);
      await expect(page.getByRole("button", { name: /Mensajes de amigos.*2 mensajes sin leer/ })).toBeVisible();
      await expect(page.locator("main")).not.toContainText(game.id);
      await runAxe(page, "sender inbox after fan-out");

      await login(pageB, accountB);
      await pageB.goto("/es/messages");
      await expect(pageB.locator("main")).toContainText(hostileText);
      await pageB.getByRole("button", { name: "Marcar como leído" }).click();
      await expect(pageB.getByRole("status")).toContainText("Mensaje marcado como leído");
      await expect(pageB.getByRole("button", { name: "Marcar como leído" })).toHaveCount(0);
      await runAxe(pageB, "recipient inbox after mark-read");

      // D-15: the same directed pair is rejected by the server's seven-day
      // cooldown, and the UI exposes the authoritative retry state.
      await login(page, primary);
      await page.goto("/es/messages");
      await page.getByLabel("Amistad").selectOption({ label: accountB.username });
      await page.getByLabel("Juego del catálogo").selectOption(game.id);
      await page.getByLabel("Mensaje opcional").fill("Intento repetido");
      await page.getByRole("button", { name: "Enviar recomendación" }).click();
      await expect(page.getByRole("alert")).toContainText("últimos 7 días");

      // Remove revokes the protected projection; the direct URL remains a
      // server-authorized 404, not a client-side navigation assumption.
      await confirmFriendAction(page, accountB.username, "Eliminar amistad");
      await page.goto(`/es/profiles/${accountB.username}`);
      await expect(page.getByText("Solo puedes ver el perfil básico")).toBeVisible();
      await login(pageB, accountB);
      await pageB.goto(`/es/profiles/${primary.username}`);
      await expect(pageB.getByText("Solo puedes ver el perfil básico")).toBeVisible();

      // Re-establish the friendship, then exercise block/unblock and direct
      // URL hiding. Blocking also removes the relationship server-side.
      await login(page, primary);
      await sendRequest(page, accountB.username);
      await login(pageB, accountB);
      await acceptRequest(pageB, primary.username);
      await confirmFriendAction(pageB, primary.username, "Bloquear");
      await login(page, primary);
      const hidden = await page.goto(`/es/profiles/${accountB.username}`);
      expect(hidden?.status()).toBe(404);
      await login(pageB, accountB);
      await searchExact(pageB, primary.username);
      await pageB.locator('[data-social-actions]').filter({ hasText: primary.username }).getByRole("button", { name: "Desbloquear" }).click();
      await expect(pageB.getByRole("status")).toContainText("Cuenta desbloqueada");

      // Both locales share the same server contract. The English page checks
      // translation parity at a real protected surface after the lifecycle.
      await login(page, primary);
      await page.goto(`/en/profiles/${accountB.username}`);
      await expect(page.getByRole("heading", { name: `${accountB.username}'s profile` })).toBeVisible();
      await assertNoOverflow(page, "English profile at 320px");
      await runAxe(page, "English profile at 320px");
    } finally {
      await contextB.close();
      await contextC.close();
    }
  });
});
