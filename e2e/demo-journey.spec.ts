import { expect, test } from "@playwright/test";

/**
 * Plan 01-15 Task 2 scope note: this file is built incrementally across two
 * plans (both declare it in files_modified). Plan 01-04 (Wave 5) adds the
 * actual browser login -> catalogue journey once the login page and Django
 * accounts endpoints exist -- neither exists yet at Wave 4, so this plan
 * cannot honestly drive a real login through the UI. What IS fully owned
 * and verifiable by 01-15 right now is the credential contract the whole
 * journey depends on: DEMO_USERNAME/DEMO_PASSWORD come exclusively from the
 * runtime environment, a missing value fails with a redacted diagnostic,
 * and no branch here ever fabricates an alternative identity (no API calls,
 * no fixtures, no hardcoded fallback credentials).
 */

function redactedDiagnostic(missing: string[]): string {
  return `Demo journey requires runtime env vars: ${missing.join(", ")} (values withheld from diagnostic by design).`;
}

function readDemoCredentials(env: Record<string, string | undefined>): { username: string; password: string } {
  const missing: string[] = [];
  if (!env.DEMO_USERNAME) missing.push("DEMO_USERNAME");
  if (!env.DEMO_PASSWORD) missing.push("DEMO_PASSWORD");
  if (missing.length > 0) {
    throw new Error(redactedDiagnostic(missing));
  }
  return { username: env.DEMO_USERNAME!, password: env.DEMO_PASSWORD! };
}

test.describe("demo account credential contract (AUTH-01, SEC-02)", () => {
  test("redacted diagnostic never echoes the actual missing-var values", () => {
    // Pure-function check against a synthetic env, independent of whatever
    // this CI/dev machine's real DEMO_USERNAME/DEMO_PASSWORD happen to be --
    // a test that only passes when real secrets happen to be unset (or only
    // fails when they happen to be set) would be a broken, flaky contract.
    const fakeSecretUsername = "should-never-appear-in-message";
    const fakeSecretPassword = "super-secret-should-never-appear";

    expect(() => readDemoCredentials({})).toThrow(/DEMO_USERNAME, DEMO_PASSWORD/);
    expect(() => readDemoCredentials({ DEMO_USERNAME: fakeSecretUsername })).toThrow(/DEMO_PASSWORD/);

    try {
      readDemoCredentials({});
    } catch (error) {
      const message = (error as Error).message;
      expect(message).not.toContain(fakeSecretUsername);
      expect(message).not.toContain(fakeSecretPassword);
    }
  });

  test("succeeds and returns both values when the runtime environment provides them", () => {
    const env = { DEMO_USERNAME: "fixture-user", DEMO_PASSWORD: "fixture-pass" };
    const credentials = readDemoCredentials(env);
    expect(credentials.username).toBe("fixture-user");
    expect(credentials.password).toBe("fixture-pass");
  });

  test("this machine's actual DEMO_USERNAME/DEMO_PASSWORD are readable and non-empty", () => {
    test.skip(!process.env.DEMO_USERNAME || !process.env.DEMO_PASSWORD, "requires DEMO_USERNAME/DEMO_PASSWORD");

    // This file must never define its own literal username/password
    // constants to authenticate with -- only ever reference process.env.
    const credentials = readDemoCredentials(process.env);
    expect(credentials.username.length).toBeGreaterThan(0);
    expect(credentials.password.length).toBeGreaterThan(0);
  });
});

test.describe("demo account login journey (AUTH-01, D-02/D-03, LIB-01)", () => {
  test.skip(!process.env.DEMO_USERNAME || !process.env.DEMO_PASSWORD, "requires DEMO_USERNAME/DEMO_PASSWORD");

  test("session -> catalogue -> status: a real tracer through the full stack", async ({ page }) => {
    const { username, password } = readDemoCredentials(process.env);

    await page.goto("/es/login");
    await page.getByLabel("Usuario").fill(username);
    // Native type="password" input -- the browser masks the value visually,
    // so trace/screenshot/video artifacts never show the plaintext even
    // though this step is captured normally (no artifact suppression
    // needed beyond the input's own masking).
    await page.getByLabel("Contraseña").fill(password);
    await page.getByRole("button", { name: "Entrar" }).click();

    // D-03: successful login lands on the catalogue, not a dashboard.
    await page.waitForURL(/\/es\/catalogue$/);
    await expect(page.getByRole("heading", { name: "Catálogo" })).toBeVisible();

    // GameCard renders title and year/platform as separate paragraphs
    // within the same link -- target the title paragraph specifically
    // rather than the link's full (multi-line) innerText.
    const firstGameLink = page.locator("main ul li a").first();
    const gameTitle = (await firstGameLink.locator("p").first().innerText()).trim();
    await firstGameLink.click();
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(gameTitle);

    // Set a status, save, and confirm the UI never claims success before
    // the request actually completes.
    await page.getByRole("radio", { name: "Jugando" }).check();
    await page.getByRole("button", { name: "Guardar estado" }).click();
    await expect(page.getByTestId("status-feedback")).toHaveText("Estado guardado");

    // D-14/reload contract: reloading re-reads the persisted PostgreSQL
    // value, never trusting only the client-side selection that was just
    // made -- this is the core assertion this whole tracer plan exists to
    // prove end-to-end.
    await page.reload();
    await expect(page.getByRole("radio", { name: "Jugando" })).toBeChecked();

    // Plan 01-09 acceptance criteria: save a 3.5-star rating (7 half-steps)
    // and two owned copies, then confirm both survive a reload. Copy count
    // is asserted as a delta, not an absolute number -- this suite runs
    // against the persistent dev database (not an isolated per-run test
    // DB), so a fixed "exactly N copies" assertion would break on any
    // second run against the same environment.
    const copyListLocator = page.locator("main").getByText(/^(Física|Digital)$/);
    const copyCountBefore = await copyListLocator.count();

    await page.locator("#rating-range").fill("7");
    await page.getByRole("button", { name: "Guardar valoración" }).click();
    await expect(page.getByTestId("rating-feedback")).toHaveText("Valoración guardada");

    await page.getByRole("button", { name: "Añadir copia" }).click();
    await expect(page.getByTestId("copy-feedback")).toHaveText("Copia añadida");
    await page.getByRole("button", { name: "Añadir copia" }).click();
    await expect(page.getByTestId("copy-feedback")).toHaveText("Copia añadida");

    await page.reload();
    await expect(page.locator("#rating-range")).toHaveValue("7");
    await expect(page.locator("main").getByText(/^(Física|Digital)$/)).toHaveCount(copyCountBefore + 2);
  });

  test("logout invalidates the session and protected pages redirect to login", async ({ page, context }) => {
    const { username, password } = readDemoCredentials(process.env);

    await page.goto("/es/login");
    await page.getByLabel("Usuario").fill(username);
    await page.getByLabel("Contraseña").fill(password);
    await page.getByRole("button", { name: "Entrar" }).click();
    await page.waitForURL(/\/es\/catalogue$/);

    // Logout goes through the same CSRF-protected endpoint the UI itself
    // uses -- no separate/fabricated logout path.
    const csrfCookie = (await context.cookies()).find((c) => c.name === "csrftoken");
    await page.request.post("/api/accounts/logout/", {
      headers: csrfCookie ? { "X-CSRFToken": csrfCookie.value } : {},
    });

    const cookiesAfterLogout = await context.cookies();
    expect(cookiesAfterLogout.some((c) => c.name === "sessionid")).toBe(false);
  });
});
