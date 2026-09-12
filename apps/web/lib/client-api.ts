"use client";

/**
 * Shared CSRF + fetch helper for authenticated mutations issued from client
 * components (browser -> same-origin Next.js proxy -> Django, RESEARCH.md
 * pattern). Mirrors the inline helper already proven in LibraryControls.tsx
 * -- factored out here so newer Phase 5 client components (profile editor,
 * favorites, comments, lists) don't each re-implement CSRF handling.
 */

function readCookie(name: string): string | undefined {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

/** Fixes the `csrftoken` cookie (GET /api/accounts/csrf/ is public and
 * requires no session) and returns its value for the `X-CSRFToken` header. */
export async function ensureCsrfToken(): Promise<string | undefined> {
  const current = readCookie("csrftoken");
  if (current) return current;
  await fetch("/api/accounts/csrf/", { credentials: "same-origin" });
  return readCookie("csrftoken");
}

/**
 * Same-origin authenticated fetch. GET/HEAD skip the CSRF round trip (Django
 * only enforces it on mutating methods); every other method fetches/reuses
 * the `csrftoken` cookie first. `body`, when present, is JSON-encoded.
 */
export async function apiFetch(
  path: string,
  init: { method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE"; body?: unknown } = {},
): Promise<Response> {
  const method = init.method ?? "GET";
  const needsCsrf = method !== "GET";
  const csrfToken = needsCsrf ? await ensureCsrfToken() : undefined;
  return fetch(path, {
    method,
    credentials: "same-origin",
    headers: {
      ...(init.body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
    },
    ...(init.body !== undefined ? { body: JSON.stringify(init.body) } : {}),
  });
}
