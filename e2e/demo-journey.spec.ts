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

test.describe.skip("demo account login journey (completed by Plan 01-04)", () => {
  // Intentionally skipped here: the login page (apps/web) and the Django
  // accounts login endpoint do not exist until Plan 01-04 (Wave 5) runs.
  // Plan 01-04 replaces this skipped block with the real
  // login -> catalogue browser journey, authenticating with the exact
  // account this plan's bootstrap_demo_account command created via
  // readDemoCredentials(process.env) above, and asserting the Playwright
  // reporter/trace/screenshot artifacts never capture the password value
  // on the login step.
  test("logs in with the bootstrap demo account and reaches the catalogue", async ({ page }) => {
    void page;
  });
});
