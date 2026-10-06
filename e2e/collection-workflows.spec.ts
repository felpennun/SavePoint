import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

/**
 * Phase 5 (Complete Collection Workflows and Portability) UI evidence:
 * profile editing + favorites (05-01), per-work comments and custom lists
 * with reorder (05-02), extended copy metadata (05-03), and CSV export
 * (05-04). The backend contract for all of this is
 * docs/verification/phase-05/phase-05-api-handoff.md; this suite drives it through
 * the real browser UI shipped in apps/web (no direct API calls except the
 * read-only ground-truth check on the CSV export, which shares the
 * browser's own session cookie via page.request).
 *
 * Two accounts are used, matching the pattern already established in
 * e2e/demo-journey.spec.ts:
 * - A FRESH self-registered account proves D-00 (real registration, not a
 *   seeded fixture) end-to-end into profile editing + favorites. Fresh
 *   registration is per-IP rate limited (5/hour); a 429 here is a real,
 *   already-covered product state (see demo-journey.spec.ts), not a
 *   permanent skip -- when the budget is spent, that portion of the phase
 *   evidence must be re-run separately rather than faked.
 * - The pre-provisioned local demo account (DEMO_USERNAME/DEMO_PASSWORD,
 *   never a secret -- see infra/compose.yaml) is not rate-limited, so it
 *   carries comments, lists, copy metadata, and the CSV export -- the
 *   bulk of this phase's feature surface.
 */

const AXE_SCRIPT_PATH = path.join(__dirname, "..", "node_modules", "axe-core", "axe.min.js");
const ARTIFACT_DIR = path.join(__dirname, "artifacts", "phase-05");

async function shoot(page: Page, surface: string): Promise<void> {
  await page.screenshot({ path: path.join(ARTIFACT_DIR, `${surface}.png`), fullPage: true });
}

// See a11y.spec.ts for the rationale.
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

/** The game detail <h1> renders "Title (Year)"; the favorites/list <option>
 * text is just the plain work title (MyLibraryItem.work_title has no year
 * suffix) -- strip it so option-label lookups match exactly. */
function stripYearSuffix(title: string): string {
  return title.replace(/\s*\(\d{4}\)\s*$/, "").trim();
}

function readDemoCredentials(env: Record<string, string | undefined>): { username: string; password: string } {
  const missing: string[] = [];
  if (!env.DEMO_USERNAME) missing.push("DEMO_USERNAME");
  if (!env.DEMO_PASSWORD) missing.push("DEMO_PASSWORD");
  if (missing.length > 0) {
    throw new Error(`Phase 5 suite requires runtime env vars: ${missing.join(", ")} (values withheld from diagnostic by design).`);
  }
  return { username: env.DEMO_USERNAME!, password: env.DEMO_PASSWORD! };
}

/** Sets the "Jugando" status on the currently-open game detail page and
 * saves -- the minimum needed for that work to become eligible for
 * comments/favorites/lists (all require a LibraryEntry to exist first). */
async function addCurrentGameToCollection(page: Page): Promise<void> {
  await page.getByLabel("Estado").selectOption("playing");
  await expect(page.getByLabel("Estado")).toHaveValue("playing");
  await page.getByRole("button", { name: "Guardar configuración" }).click();
  await expect(page.getByTestId("status-feedback")).toHaveText("Configuración guardada");
}

test.beforeEach(async ({ page }) => {
  await installCsrfOriginShim(page);
});

test.describe("Phase 5: fresh account -> profile editor -> favorites (D-00, PROF-01, D-02)", () => {
  test("real registration, then edit the profile page (bio, favorite, privacy)", async ({ page }) => {
    const stamp = `${Date.now().toString(36)}${Math.floor(Math.random() * 1e6).toString(36)}`;
    const freshUsername = `e2e-phase5-${stamp}`;
    const freshPassword = `Phase5-${Math.random().toString(36).slice(2, 12)}-Qx`;

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
      test.info().annotations.push({
        type: "note",
        description: "registration endpoint IP budget exhausted (429); Phase 5 profile/favorites evidence for a FRESH account deferred to an un-throttled run",
      });
      return;
    }
    await page.waitForURL(/\/es$/);
    await page.goto("/es/catalogue");

    // Add one game to the fresh, empty collection so it is eligible to
    // become a favorite.
    await page.locator("main ul.sp-grid li a").first().click();
    await page.waitForURL(/\/es\/games\//);
    const gameTitle = stripYearSuffix((await page.getByRole("heading", { level: 1 }).first().textContent())?.trim() ?? "");
    await addCurrentGameToCollection(page);

    // Own profile page, reached from the account menu ("Editar perfil").
    await page.getByRole("button", { name: /Mi cuenta/ }).click();
    await page.getByRole("menuitem", { name: "Editar perfil" }).click();
    await page.waitForURL(/\/es\/profile$/);
    await expect(page.getByRole("tab", { name: "Cuenta" })).toBeVisible();

    const bioText = `Cuenta de evidencia E2E creada ${stamp}.`;
    await page.getByLabel("Biografía").fill(bioText);

    // Favorites: the one collected game is selectable in the first slot.
    await page.locator(".sp-pf-fav").first().click();
    await page.locator(".sp-pf-picker-row", { hasText: gameTitle }).click();

    await page.getByRole("tab", { name: "Privacidad" }).click();
    await page.getByRole("radiogroup", { name: "Colección" }).getByRole("radio", { name: "Amistades" }).click();
    await page.getByRole("radiogroup", { name: "Favoritos" }).getByRole("radio", { name: "Amistades" }).click();
    await page.getByRole("button", { name: "Guardar cambios" }).click();
    await expect(page.getByTestId("profile-feedback")).toHaveText("Cambios guardados");

    // Persistence: reload and the same values must come back from the API,
    // not just from local component state.
    await page.reload();
    await expect(page.getByLabel("Biografía")).toHaveValue(bioText);
    await expect(page.locator(".sp-pf-fav.is-filled")).toHaveCount(1);

    const editorViolations = await runAxeScan(page);
    assertNoCriticalOrSeriousViolations(editorViolations, "profile page (edit profile)");
    await shoot(page, "profile-owner-editor");

    // The profile view every visitor (including the owner) sees must reflect
    // the same saved data.
    await page.goto(`/es/profiles/${freshUsername}`);
    await expect(page.locator(".sp-lead", { hasText: bioText })).toBeVisible();
    await expect(page.locator(".sp-favorites-list")).toContainText(gameTitle);

    const violations = await runAxeScan(page);
    assertNoCriticalOrSeriousViolations(violations, "own profile view with favorites");
  });
});

test.describe("Phase 5: demo account — comments, lists, copy metadata, CSV export (LIB-03, LIB-04, INV-03/04, PORT-01/04)", () => {
  test.skip(!process.env.DEMO_USERNAME || !process.env.DEMO_PASSWORD, "requires DEMO_USERNAME/DEMO_PASSWORD");

  test("comment on a game, build a reorderable list, record copy metadata, export CSV", async ({ page }) => {
    // This journey deliberately covers five separate feature surfaces
    // (comments, lists+reorder, copy metadata, physical/digital toggle,
    // CSV export) end to end in one real session -- comfortably longer
    // than Playwright's 30s default single-test budget.
    test.setTimeout(120_000);
    const { username, password } = readDemoCredentials(process.env);

    await page.goto("/es/login");
    await page.getByLabel("Usuario").fill(username);
    await page.getByLabel("Contraseña").fill(password);
    await page.getByRole("button", { name: "Entrar" }).click();
    await page.waitForURL(/\/es$/);
    await page.goto("/es/catalogue");

    // Two distinct catalogue works, both added to the collection so they
    // are eligible for comments/lists/copies.
    await page.goto("/es/catalogue");
    const cards = page.locator("main ul.sp-grid li a");
    const gameAHref = await cards.nth(0).getAttribute("href");
    const gameBHref = await cards.nth(1).getAttribute("href");
    expect(gameAHref).toBeTruthy();
    expect(gameBHref).toBeTruthy();

    await page.goto(gameAHref!);
    const gameATitle = stripYearSuffix((await page.getByRole("heading", { level: 1 }).first().textContent())?.trim() ?? "");
    await addCurrentGameToCollection(page);

    await page.goto(gameBHref!);
    const gameBTitle = stripYearSuffix((await page.getByRole("heading", { level: 1 }).first().textContent())?.trim() ?? "");
    await addCurrentGameToCollection(page);

    // --- Comments (LIB-03) --------------------------------------------
    await page.goto(gameAHref!);
    const stamp = Date.now().toString(36);
    const commentText = `Comentario de evidencia E2E ${stamp}.`;
    // GameComments fetches on mount ("Cargando comentarios…" first) --
    // wait for that to resolve before branching, otherwise the visibility
    // check below races the fetch and always sees neither state yet.
    await expect(page.getByText("Cargando comentarios…")).toHaveCount(0);
    // A prior run may have already left this account's one-per-work comment
    // in the read-only "Editar/Eliminar" state; enter edit mode first so
    // the textarea (only rendered while editing) is actually present.
    const editCommentButton = page.getByRole("button", { name: "Editar" });
    if (await editCommentButton.isVisible().catch(() => false)) {
      await editCommentButton.click();
    }
    const commentBox = page.getByLabel("Tu comentario");
    await commentBox.fill(commentText);
    const saveCommentButton = page.getByRole("button", { name: /Guardar comentario/ });
    await saveCommentButton.click();
    await expect(page.getByTestId("comment-feedback")).toHaveText("Comentario guardado");
    await page.reload();
    await expect(page.locator(".sp-game-comments")).toContainText(commentText);
    const commentViolations = await runAxeScan(page);
    assertNoCriticalOrSeriousViolations(commentViolations, "game detail with own comment");
    await shoot(page, "game-detail-comment");

    // --- Custom lists + reorder (LIB-04, D-06/D-07) ---------------------
    // Lists live in the collection sidebar: "+ NUEVA" creates one and jumps to
    // it; the selected list's controls are folded under "Editar lista".
    await page.goto("/es/collection");
    await expect(page.getByRole("heading", { name: "MIS LISTAS" })).toBeVisible();
    const listName = `E2E Phase 5 ${stamp}`;
    await page.getByRole("button", { name: "+ NUEVA" }).click();
    await page.getByPlaceholder("Nombre de la lista").fill(listName);
    await page.getByRole("button", { name: "Crear", exact: true }).click();
    await page.waitForURL(/[?&]list=/);
    // Games are added with the dashed tile at the end of the list's grid, which
    // opens the collection search.
    const addToList = async (title: string) => {
      await page.locator(".sp-coll-add-tile").click();
      await page.locator("dialog[open] input[type=search]").fill(title);
      await page.locator("dialog[open] .sp-pf-picker-row").filter({ hasText: title }).first().click();
      await expect(page.locator(".sp-collection-grid > li").filter({ hasText: title }).first()).toBeVisible();
    };
    await addToList(gameATitle);
    await addToList(gameBTitle);

    // The folded "Editar lista" panel renames the list, removes several games
    // (marked with a minus badge, then confirmed) and deletes the list.
    await page.locator(".sp-coll-editor > summary").click();
    const renamed = `${listName} renombrada`;
    await page.getByLabel("Nombre de la lista").fill(renamed);
    await page.getByRole("button", { name: "Cambiar nombre" }).click();
    await expect(page.locator(".sp-coll-side-row.is-on")).toContainText(renamed);

    await page.getByRole("button", { name: "Eliminar juegos" }).click();
    await page.locator(".sp-coll-remove-toggle").first().click();
    await expect(page.locator(".sp-coll-card.is-selected")).toHaveCount(1);
    await page.getByRole("button", { name: "Confirmar borrado" }).click();
    await page.locator("dialog[open]").getByRole("button", { name: "Quitar" }).click();
    await expect(page.locator(".sp-coll-card")).toHaveCount(1);

    // Reload: the removal and the new name must have persisted server side.
    await page.reload();
    await expect(page.locator(".sp-coll-side-row.is-on")).toContainText(renamed);
    await expect(page.locator(".sp-coll-card")).toHaveCount(1);

    const collectionViolations = await runAxeScan(page);
    assertNoCriticalOrSeriousViolations(collectionViolations, "collection page with custom list");
    await shoot(page, "collection-custom-list");

    // --- Copy metadata (INV-03/INV-04) ---------------------------------
    // Arrange a clean slate first: re-running this suite repeatedly against
    // the same demo account would otherwise accumulate one extra copy row
    // per run (each "add another copy" click carries a fresh idempotency
    // key), which would make every `.last()`/page-wide count assertion
    // below ambiguous or wrong. Removing any pre-existing copies for this
    // work makes the rest of this block deterministic regardless of how
    // many times it has run before.
    await page.goto(gameAHref!);
    // LibraryControls fetches status/rating/copies on mount and renders
    // nothing else (not even a remove button) until that resolves -- wait
    // for the always-present save button first, or the loop below can spin
    // its very first .count() check before any copy row has rendered and
    // exit having "cleaned" nothing.
    await page.getByRole("button", { name: "Guardar configuración" }).waitFor();
    // Scoped to LibraryControls specifically: GameComments and CustomLists
    // reuse the same .sp-copy-remove/.sp-copy-add styling classes for their
    // own delete/edit actions (comment delete, list delete, list item
    // remove/reorder) -- an unscoped selector here would also match and
    // click the "Eliminar" button on this work's own comment.
    // Copies are listed by name; opening one shows a dialog with "Eliminar",
    // which asks for confirmation and then saves.
    const copyItems = page.locator(".sp-library-controls .sp-copy-item");
    while ((await copyItems.count()) > 0) {
      await copyItems.first().click();
      await page.locator(".sp-copy-dialog .sp-copy-remove").click();
      await page.locator(".sp-library-controls dialog.sp-confirm-dialog .sp-comment-confirm-delete").click();
      await expect(page.getByTestId("status-feedback")).toHaveText("Configuración guardada");
    }
    await expect(page.locator('[id^="copy-release-"]')).toHaveCount(0);

    await page.getByRole("button", { name: "Añadir copia" }).click();
    await expect(page.locator('[id^="copy-format-"]')).toHaveCount(1);
    await page.locator('[id^="copy-format-"]').selectOption("physical");
    await page.locator('[id^="copy-purchase-date-"]').fill("2024-06-15");
    await page.locator('[id^="copy-price-"]').fill("39.99");
    await page.locator('[id^="copy-currency-"]').fill("eur");
    await page.locator('[id^="copy-store-"]').fill("E2E Store");
    await page.locator('[id^="copy-conservation-"]').selectOption("good");
    await page.locator('[id^="copy-storage-location-"]').fill("Estantería E2E");
    await page.getByRole("button", { name: "Guardar copia" }).click();
    await expect(page.getByTestId("status-feedback")).toHaveText("Configuración guardada");

    await page.reload();
    await page.locator(".sp-library-controls .sp-copy-item").first().click();
    await expect(page.locator('[id^="copy-price-"]')).toHaveValue(/39\.99|39,99/);
    await expect(page.locator('[id^="copy-currency-"]')).toHaveValue("EUR");
    await expect(page.locator('[id^="copy-conservation-"]')).toHaveValue("good");
    await expect(page.locator('[id^="copy-storage-location-"]')).toHaveValue("Estantería E2E");

    // Physical/digital rule: switching to digital hides conservation state
    // and storage location entirely (the fields are conditionally rendered,
    // not merely disabled). Exactly one copy exists at this point, so a
    // page-wide count is unambiguous.
    await page.locator('[id^="copy-format-"]').selectOption("digital");
    await expect(page.locator('[id^="copy-conservation-"]')).toHaveCount(0);
    await expect(page.locator('[id^="copy-storage-location-"]')).toHaveCount(0);
    // Restore to physical so the saved row is left in a consistent state
    // for anyone re-running this suite against the same demo account.
    await page.locator('[id^="copy-format-"]').selectOption("physical");
    await page.getByRole("button", { name: "Guardar copia" }).click();
    await expect(page.getByTestId("status-feedback")).toHaveText("Configuración guardada");

    // --- CSV export (PORT-01/PORT-04) -----------------------------------
    // Ground truth via page.request, sharing the browser context's own
    // session cookie -- not a separately authenticated client.
    const exportResponse = await page.request.get("/api/library/export/collection.csv");
    expect(exportResponse.status()).toBe(200);
    expect(exportResponse.headers()["content-type"]).toContain("text/csv");
    expect(exportResponse.headers()["content-disposition"]).toContain("savepoint-collection-export.csv");
    const csvBody = await exportResponse.text();
    const header = csvBody.split("\n")[0].trim();
    expect(header.split(",")).toEqual([
      "schema_version",
      "record_type",
      "work_slug",
      "work_title",
      "status",
      "rating_half_steps",
      "copy_format",
      "purchase_date",
      "price",
      "currency",
      "store",
      "conservation_state",
      "storage_location",
      "comment",
      "list_name",
      "list_visibility",
      "list_position",
      "favorite_slot",
    ]);
    expect(csvBody).toContain(gameATitle);
    expect(csvBody).toContain(listName);
    expect(csvBody).toContain("E2E Store");

    // Determinism: exporting again immediately produces byte-identical
    // output (05-04's own contract).
    const secondExport = await page.request.get("/api/library/export/collection.csv");
    expect(await secondExport.text()).toBe(csvBody);

    // The export links live on the profile page (Security tab), not on the
    // collection page.
    await page.goto("/es/profile");
    await page.getByRole("tab", { name: "Seguridad" }).click();
    await expect(page.getByRole("link", { name: "Excel" })).toHaveAttribute(
      "href",
      "/api/library/export/collection.xlsx?lang=es",
    );
    await expect(page.getByRole("link", { name: "CSV" })).toHaveAttribute("href", "/api/library/export/collection.csv");
  });
});
