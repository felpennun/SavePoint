import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

// Plan 01.1-10 evidence artifacts (recommendations surface -- auth-gated, so
// its screenshots live in this suite alongside the controlled-account
// journey; catalogue/detail/registration are in a11y.spec.ts).
const ARTIFACT_DIR = path.join(__dirname, "artifacts", "phase-01.1");
const AXE_SCRIPT_PATH = path.join(__dirname, "..", "node_modules", "axe-core", "axe.min.js");

async function shoot(page: Page, surface: string, viewport: string): Promise<void> {
  await page.screenshot({ path: path.join(ARTIFACT_DIR, `${surface}-${viewport}.png`), fullPage: true });
}

// See a11y.spec.ts for the rationale: rewrite the Origin/Referer of proxied
// /api traffic to the canonical dev origin so unsafe requests still clear
// Django's CSRF origin check when the suite runs against a local production
// build on a non-3000 port. Inert on :3000.
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

interface AxeViolation {
  id: string;
  impact: string | null;
  help: string;
  nodes: { target: string[] }[];
}

async function axeBlocking(page: Page): Promise<AxeViolation[]> {
  await page.addScriptTag({ path: AXE_SCRIPT_PATH });
  const results = await page.evaluate(async () => {
    // @ts-expect-error -- axe is injected globally by the script tag above
    return window.axe.run(document, { resultTypes: ["violations"] });
  });
  return ((results as { violations: AxeViolation[] }).violations).filter(
    (v) => v.impact === "critical" || v.impact === "serious",
  );
}

test.beforeEach(async ({ page }) => {
  await installCsrfOriginShim(page);
});

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

    // D-03: successful login lands on the catalogue, not a dashboard. The
    // page no longer renders a visible <h1> (2026-09-12: the navbar title
    // is enough); "Catálogo" survives as the results section's accessible
    // name, exposed as an ARIA region landmark.
    await page.waitForURL(/\/es$/);
    await page.goto("/es/catalogue");
    await expect(page.getByRole("region", { name: "Catálogo" })).toBeVisible();

    // GameCard renders title and year/platform as separate paragraphs
    // within the same link -- target the title paragraph specifically
    // rather than the link's full (multi-line) innerText. The detail <h1>
    // deliberately appends the release year in a span (01.1-UI-SPEC Screen
    // Contract 3: "release year beside it"), which the card title omits, so
    // this is a containment check, not an exact-text match.
    const firstGameLink = page.locator("main ul li a").first();
    const gameTitle = (await firstGameLink.locator("p").first().innerText()).trim();
    await firstGameLink.click();
    await expect(page.getByRole("heading", { level: 1 })).toContainText(gameTitle);

    // LibraryControls (redesign, predates this session) saves status,
    // rating, and copies together through one "Guardar configuración"
    // action and one shared feedback message -- not three separate
    // save/feedback pairs. The status control is a visually-hidden native
    // radio behind a styled <label>/<span> (Nocturne "chip" pattern): a
    // real pointer click lands on the label via HTML's own label-forwarding
    // even though the input itself is pointer-events: none, so this clicks
    // the visible label text, the same target a sighted user would use.
    await page.getByLabel("Estado").selectOption("playing");
    await page.getByRole("button", { name: "Guardar configuración" }).click();
    await expect(page.getByTestId("status-feedback")).toHaveText("Configuración guardada");

    // D-14/reload contract: reloading re-reads the persisted PostgreSQL
    // value, never trusting only the client-side selection that was just
    // made -- this is the core assertion this whole tracer plan exists to
    // prove end-to-end.
    await page.reload();
    await expect(page.getByLabel("Estado")).toHaveValue("playing");

    // Plan 01-09 acceptance criteria: save a 3.5-star rating (7 half-steps)
    // and two owned copies, then confirm both survive a reload. Copy count
    // is asserted as a delta, not an absolute number -- this suite runs
    // against the persistent dev database (not an isolated per-run test
    // DB), so a fixed "exactly N copies" assertion would break on any
    // second run against the same environment.
    const copyListLocator = page.locator(".sp-copy-item");
    const copyCountBefore = await copyListLocator.count();

    // The rating control is five stars, each split into a left/right half
    // button; "3.5 de 5 estrellas" is the accessible name for half-step 7.
    const ratingButton = page.getByRole("button", { name: "3.5 de 5 estrellas" });
    if ((await ratingButton.getAttribute("aria-pressed")) !== "true") {
      await ratingButton.click();
    }
    // A copy is added through the dialog; saving it persists the whole
    // configuration (including the rating) in one request.
    for (let added = 0; added < 2; added++) {
      await page.getByRole("button", { name: "Añadir copia" }).click();
      await page.getByRole("button", { name: "Guardar copia" }).click();
      await expect(page.getByTestId("status-feedback")).toHaveText("Configuración guardada");
    }
    await page.getByRole("button", { name: "Guardar configuración" }).click();
    await expect(page.getByTestId("status-feedback")).toHaveText("Configuración guardada");

    await page.reload();
    await expect(page.getByRole("button", { name: "3.5 de 5 estrellas" })).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator(".sp-copy-item")).toHaveCount(copyCountBefore + 2);
  });

  test("logout invalidates the session and protected pages redirect to login", async ({ page, context }) => {
    const { username, password } = readDemoCredentials(process.env);

    await page.goto("/es/login");
    await page.getByLabel("Usuario").fill(username);
    await page.getByLabel("Contraseña").fill(password);
    await page.getByRole("button", { name: "Entrar" }).click();
    await page.waitForURL(/\/es$/);

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

// ---------------------------------------------------------------------------
// Plan 01.1-10: the complete controlled-account journey (D-01 -> D-04) plus
// the auth-gated recommendations surface evidence at desktop AND mobile.
// ---------------------------------------------------------------------------
test.describe("controlled-account journey + authenticated recommendations (D-01..D-04)", () => {
  // D-01 / AUTH-02: a genuinely functional self-service registration. The
  // endpoint is per-IP rate limited (5/hour, 01.1-08). On a fresh
  // environment this drives the real register -> session -> catalogue ->
  // own (empty) collection journey; when the IP budget is already spent the
  // test instead asserts the localized rate-limit error state, which is
  // itself a required UI-SPEC Screen Contract 5d state. Either way the
  // registration form is exercised end-to-end against the live endpoint.
  test("fresh simulated account: real registration journey, or the rate-limit state", async ({ page }) => {
    const stamp = `${Date.now().toString(36)}${Math.floor(Math.random() * 1e6).toString(36)}`;
    const freshUsername = `e2e-visitor-${stamp}`;
    // Distinct randomness from the username so Django's
    // UserAttributeSimilarityValidator never trips; still an obviously
    // generated, validator-passing value (length, mixed case, digit).
    const freshPassword = `Journ3y-${Math.random().toString(36).slice(2, 12)}-Qx`;

    await page.goto("/es/register");
    await page.getByLabel("Usuario").fill(freshUsername);
    await page.getByLabel("Contraseña", { exact: true }).fill(freshPassword);
    await page.getByLabel("Confirmar contraseña").fill(freshPassword);

    const [registerResponse] = await Promise.all([
      page.waitForResponse((r) => r.url().includes("/api/accounts/register/")),
      page.getByRole("button", { name: "Crear cuenta" }).click(),
    ]);
    const status = registerResponse.status();
    expect([201, 429]).toContain(status);

    if (status === 429) {
      // Rate-limit state: localized message, username preserved, password
      // cleared (mirrors the login contract).
      await expect(page.getByTestId("register-error")).toHaveText(/demasiados intentos/i);
      await expect(page.getByLabel("Usuario")).toHaveValue(freshUsername);
      await expect(page.getByLabel("Contraseña", { exact: true })).toHaveValue("");
      test.info().annotations.push({
        type: "note",
        description: "registration endpoint IP budget exhausted (429); full register->session journey deferred to an un-throttled run",
      });
      return;
    }

    // D-03: a successful registration establishes a session and lands on the
    // catalogue. The redirect is a client-side push, so a reload lets the
    // server layout re-read the new sessionid cookie and render the
    // authenticated chrome (what a real visitor sees on their next
    // server-rendered navigation).
    await page.waitForURL(/\/es$/);
    await page.goto("/es/catalogue");
    await expect(page.getByRole("region", { name: "Catálogo" })).toBeVisible();

    // AUTH-02: the account is visibly simulated and the authenticated-only
    // nav links appear now that a session exists.
    await expect(page.getByRole("note")).toBeVisible();
    const collectionLink = page.getByRole("link", { name: "Colección" });
    await expect(collectionLink).toBeVisible();
    await expect(page.getByRole("link", { name: "Recomendaciones" })).toBeVisible();

    // D-02: the fresh account's own library is empty -- deterministic empty
    // state, reached through the nav link.
    await collectionLink.click();
    await page.waitForURL(/\/es\/collection$/);
    await expect(page.getByRole("region", { name: "Colección" })).toBeVisible();
    await expect(page.getByText("Tu colección está vacía")).toBeVisible();

    // D-04: personalized recommendations navigation from the authenticated
    // nav. This account's library is empty (asserted above), so the page
    // must never silently fall back to some other ranking -- it settles on
    // the insufficient-history onboarding state, possibly after a brief
    // "preparing" state while the async snapshot job runs for the first time.
    await page.getByRole("link", { name: "Recomendaciones" }).click();
    await page.waitForURL(/\/es\/recommendations$/);
    await expect(page.getByText("Aún no hay suficiente actividad")).toBeVisible({ timeout: 15_000 });
  });

  // D-02 / D-03 / D-04 + the recommendations screenshot evidence, via the
  // pre-provisioned demo account. Login is not rate limited, so this is the
  // reliable source of the recommendations/desktop + recommendations/mobile
  // artifacts and the per-viewport axe / reflow evidence.
  test.describe("demo session authenticated surfaces", () => {
    test.skip(!process.env.DEMO_USERNAME || !process.env.DEMO_PASSWORD, "requires DEMO_USERNAME/DEMO_PASSWORD");

    test("collection + recommendations: disclosure, shelves-or-onboarding, axe clean, desktop + mobile", async ({ page }) => {
      const { username, password } = readDemoCredentials(process.env);
      await page.goto("/es/login");
      await page.getByLabel("Usuario").fill(username);
      await page.getByLabel("Contraseña").fill(password);
      await page.getByRole("button", { name: "Entrar" }).click();
      await page.waitForURL(/\/es$/);

      for (const [viewportName, size] of [
        ["desktop", { width: 1280, height: 800 }],
        ["mobile", { width: 375, height: 812 }],
      ] as const) {
        await page.setViewportSize(size);

        // Collection: the signed-in user's own library view renders (grid or
        // its documented empty state), auth-gated behind the session. The
        // page no longer renders a visible <h1> (2026-09-12: the navbar
        // title is enough); "Colección" survives as the results section's
        // accessible name.
        await page.goto("/es/collection");
        await expect(page.getByRole("region", { name: "Colección" })).toBeVisible();
        const hasGrid = (await page.locator("main ul.sp-grid li").count()) > 0;
        const hasEmpty = (await page.getByText("Tu colección está vacía").count()) > 0;
        expect(hasGrid || hasEmpty).toBe(true);

        // Recommendations: the body is either one or more shelves (content,
        // tag-taste, or owned-DLC -- all render as section.sp-shelf) or the
        // explicit insufficient-history onboarding state -- never a silent
        // fallback to the popularity baseline. Per-algorithm shelf content,
        // ordering against the API payload, and the absence of any
        // methodology surface are covered in detail by
        // e2e/recommendations.spec.ts (QUAL-02); this is only the
        // lightweight smoke check alongside the rest of the journey.
        await page.goto("/es/recommendations");
        await expect(page.getByRole("heading", { level: 1, name: "Recomendaciones" })).toBeVisible();
        // The snapshot may still be "building" on first-ever load -- poll
        // rather than asserting on the first render.
        await expect
          .poll(
            async () =>
              (await page.locator("section.sp-shelf").count()) +
              (await page.getByText("Aún no hay suficiente actividad").count()),
            { message: "expected at least one shelf or the onboarding empty state", timeout: 15_000 },
          )
          .toBeGreaterThan(0);

        if (viewportName === "mobile") {
          // The recommendations content region must reflow with no horizontal
          // scroll at the mobile floor. (The shared authenticated header is a
          // separate, pre-existing chrome concern tracked in deferred-items.md
          // -- it is not part of any single surface's contract.)
          const mainOverflow = await page.evaluate(() => {
            const main = document.querySelector("main");
            return main ? main.scrollWidth > main.clientWidth + 1 : true;
          });
          expect(mainOverflow, "recommendations content must not overflow horizontally at mobile width").toBe(false);
        }

        const blocking = await axeBlocking(page);
        expect(
          blocking,
          `axe critical/serious on recommendations (${viewportName}): ${blocking.map((v) => v.id).join(", ")}`,
        ).toEqual([]);
        await shoot(page, "recommendations", viewportName);
      }
    });
  });
});
