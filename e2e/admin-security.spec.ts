import { expect, test, type Page } from "@playwright/test";

// Admin credentials must not be retained in failure traces.
test.use({ trace: "off" });

type CapabilityName = "can_view_research" | "can_manage_platform";

async function login(
  page: Page,
  usernameName: string,
  passwordName: string,
  expectedCapability: { name: CapabilityName; value: boolean },
) {
  const username = process.env[usernameName];
  const password = process.env[passwordName];
  if (!username || !password) throw new Error(`Missing ${usernameName}/${passwordName}; values withheld by design.`);
  await page.goto("/en/login");
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(password);
  await Promise.all([
    page.waitForURL(/\/en\/catalogue$/),
    page.getByRole("button", { name: "Log in" }).click(),
  ]);
  await expect(page.getByRole("region", { name: "Catalogue" })).toBeVisible();
  const session = await page.request.get("/api/accounts/me/");
  expect(session.status()).toBe(200);
  const body = (await session.json()) as { capabilities?: Record<string, boolean> };
  expect(body.capabilities?.[expectedCapability.name]).toBe(expectedCapability.value);
}

test.describe("Django Platform Admin browser boundary", () => {
  test("Platform Admin can enter the allowlisted Django Admin surface", async ({ page }) => {
    await login(page, "PLATFORM_ADMIN_USERNAME", "PLATFORM_ADMIN_PASSWORD", {
      name: "can_manage_platform",
      value: true,
    });
    await page.goto("/admin/");
    await expect(page).toHaveURL(/\/admin\/$/);
    await expect(page.getByText("SavePoint Platform Admin")).toBeVisible();
    await expect(page.getByRole("heading", { name: /Platform operations|Site administration/i })).toBeVisible();
    await expect(page.getByText(/Users|Catalog|Evaluation|Audit/i).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /delete|re-run|rerun|re-run evaluation/i })).toHaveCount(0);
  });

  test("Research Viewer cannot obtain administrative operations", async ({ page }) => {
    await login(page, "RESEARCH_VIEWER_USERNAME", "RESEARCH_VIEWER_PASSWORD", {
      name: "can_manage_platform",
      value: false,
    });
    await page.goto("/admin/");
    await expect(page).toHaveURL(/\/admin\/login\//);
    await expect(page.getByRole("textbox")).toHaveCount(2);
    await expect(page.getByRole("heading", { name: "Platform operations" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /delete|re-run|rerun|re-run evaluation/i })).toHaveCount(0);
  });

  test("Research Viewer has no mutation controls on the research route", async ({ page }) => {
    await login(page, "RESEARCH_VIEWER_USERNAME", "RESEARCH_VIEWER_PASSWORD", {
      name: "can_view_research",
      value: true,
    });
    await page.goto("/en/research");
    await expect(page.getByTestId("research-panel")).toBeVisible();
    await expect(page.getByRole("button", { name: /delete|borrar|re-run|relanzar|run evaluation/i })).toHaveCount(0);
    await expect(page.getByText("This panel has no destructive actions.")).toBeVisible();
  });
});
