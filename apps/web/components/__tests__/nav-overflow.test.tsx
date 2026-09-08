import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { chromium, type Browser, type Page } from "@playwright/test";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { AccountSwitcher } from "../AccountSwitcher";
import { AppShell } from "../AppShell";
import { ThemeToggle } from "../ThemeToggle";
import { getDictionary } from "../../i18n";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
  usePathname: () => "/es",
  useSearchParams: () => new URLSearchParams(),
}));

// Use the already approved Playwright dependency for real DOM/accessibility
// queries: this repository has no jsdom/happy-dom dependency. CI uses the
// pinned Chromium; an explicit local channel is optional, never required.
let browser: Browser;
let page: Page;
beforeAll(async () => {
  browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || undefined });
});
beforeEach(async () => {
  page = await browser.newPage();
});
afterEach(async () => { await page?.close(); });
afterAll(async () => { await browser?.close(); });

describe.each(["es", "en"])("responsive navbar accessibility (%s)", (locale) => {
  const dict = getDictionary(locale);
  const accountLabels = {
    ...dict.account.switcher,
    logout: dict.nav.logout,
    listHeading: dict.account.list.heading,
  };

  it("preserves the theme name and pressed state when its text is hidden", async () => {
    await page.setContent(renderToStaticMarkup(<ThemeToggle labels={dict.theme.toggle} />));
    const button = page.getByRole("button", { name: dict.theme.toggle.switchToLight, exact: true });
    expect(await button.count()).toBe(1);
    expect(await button.getAttribute("aria-pressed")).toBe("false");
    const label = button.locator("span");
    expect(await label.getAttribute("class")).toBe("hidden md:inline");
    const before = await button.locator("*").count();
    // Hiding the visible text must not remove the accessible name. Geometry
    // and compiled responsive CSS are verified in the phase browser pass.
    await label.evaluate((element) => { element.style.display = "none"; });
    expect(await button.count()).toBe(1);
    expect(await button.locator("*").count()).toBe(before);
    expect(await button.getAttribute("aria-pressed")).toBe("false");
  });

  it("keeps simulated account identification accessible in the generic fallback", async () => {
    await page.setContent(renderToStaticMarkup(<AccountSwitcher locale={locale} labels={accountLabels} />));
    const button = page.getByRole("button", { name: dict.account.switcher.label, exact: true });
    expect(await button.count()).toBe(1);
    expect(await button.getAttribute("aria-label")).toMatch(/simulada|simulated/i);
    expect(await button.getAttribute("aria-haspopup")).toBe("menu");
    expect(await button.getAttribute("aria-expanded")).toBe("false");
    const label = button.locator("span").first();
    expect(await label.getAttribute("class")).toBe("hidden md:inline");
    await label.evaluate((element) => { element.style.display = "none"; });
    expect(await button.count()).toBe(1);
  });

  it("keeps both controls in the header in the same DOM order at every width", async () => {
    await page.setContent(renderToStaticMarkup(
      <AppShell locale={locale} isAuthenticated><main>Test content</main></AppShell>,
    ));
    const header = page.getByRole("banner");
    const initialMarkup = await header.innerHTML();
    for (const width of [320, 375, 768, 1280]) {
      await page.setViewportSize({ width, height: 800 });
      expect(await header.innerHTML()).toBe(initialMarkup);
      expect(await header.getByRole("button").allTextContents()).toEqual([
        `${dict.theme.toggle.label}: ${dict.theme.toggle.dark}`,
        `${dict.account.switcher.label}▾`,
        dict.nav.openMenu,
      ]);
      expect(await page.getByRole("dialog").count()).toBe(0);
    }
  });
});
