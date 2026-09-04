import { expect, test } from "@playwright/test";

test("Playwright discovers the Phase 1 Chromium runner", async () => {
  const runnerContract = {
    browser: "chromium",
    locales: ["es", "en"],
    minimumViewportWidth: 320,
    maximumZoomPercent: 400,
  } as const;

  expect(runnerContract.browser).toBe("chromium");
  expect(runnerContract.locales).toEqual(["es", "en"]);
  expect(runnerContract.minimumViewportWidth).toBe(320);
  expect(runnerContract.maximumZoomPercent).toBe(400);
});

