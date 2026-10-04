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

  it("theme toggle is icon-only: name and state come from aria-* not text", async () => {
    await page.setContent(renderToStaticMarkup(<ThemeToggle labels={dict.theme.toggle} />));
    const button = page.getByRole("button", { name: dict.theme.toggle.switchToLight, exact: true });
    expect(await button.count()).toBe(1);
    expect(await button.getAttribute("aria-pressed")).toBe("false");
    // No visible label: the only child is the decorative icon.
    expect((await button.textContent())?.trim()).toBe("");
    expect(await button.locator("svg").count()).toBe(1);
    expect(await button.locator("span").count()).toBe(0);
  });

  it("account trigger is icon-only but still identifies as an account menu", async () => {
    await page.setContent(renderToStaticMarkup(<AccountSwitcher locale={locale} labels={accountLabels} />));
    const button = page.getByRole("button", { name: dict.account.switcher.label, exact: true });
    expect(await button.count()).toBe(1);
    expect(await button.getAttribute("aria-label")).toMatch(/mi cuenta|my account/i);
    expect(await button.getAttribute("aria-haspopup")).toBe("menu");
    expect(await button.getAttribute("aria-expanded")).toBe("false");
    // No visible label or caret: just the avatar icon.
    expect((await button.textContent())?.trim()).toBe("");
    expect(await button.locator("svg").count()).toBe(1);
    expect(await button.locator("span").count()).toBe(0);
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
      // Theme toggle and account trigger are icon-only (empty text); only
      // the mobile-menu button carries a visible label. Order is stable.
      expect(await header.getByRole("button").allTextContents()).toEqual([
        "",
        "",
        dict.nav.openMenu,
      ]);
      expect(await page.getByRole("dialog").count()).toBe(0);
    }
  });
});
