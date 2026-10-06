/** Minutes without any interaction after which a signed-in session is closed.
 * The API enforces the same limit with a sliding session cookie
 * (`SESSION_COOKIE_AGE` in apps/api/config/settings.py). */
export const IDLE_LIMIT_MS = 30 * 60 * 1000;

/** How often the guard checks the clock; also re-checked when the tab wakes up. */
export const IDLE_CHECK_INTERVAL_MS = 30 * 1000;

/** While the person is active, ping the API at most this often so the server
 * session keeps sliding even on pages that make no requests of their own. */
export const KEEPALIVE_INTERVAL_MS = 5 * 60 * 1000;

/** localStorage key shared by every tab, so activity in one keeps all alive. */
export const LAST_ACTIVITY_KEY = "savepoint:last-activity";

export function isIdleExpired(lastActivityMs: number, nowMs: number, limitMs: number = IDLE_LIMIT_MS): boolean {
  return nowMs - lastActivityMs >= limitMs;
}

/** Ends the session on the API (best effort) and loads `destination` with a
 * full page load so nothing of the previous account stays on screen. */
export async function signOutAndRedirect(destination: string): Promise<void> {
  try {
    await fetch("/api/accounts/csrf/", { credentials: "same-origin" });
    const csrfToken = document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1];
    await fetch("/api/accounts/logout/", {
      method: "POST",
      credentials: "same-origin",
      headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
    });
  } catch {
    /* the redirect below happens regardless */
  }
  window.location.replace(destination);
}
