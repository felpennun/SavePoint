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

export interface SocialRecommendationInput {
  recipient_alias: string;
  work_id: string;
  text: string;
}

export type SocialRecommendationResult =
  | { kind: "ok" }
  | { kind: "cooldown"; retryAfterSeconds: number }
  | { kind: "error"; status: number };

function retryAfterSeconds(response: Response, body: unknown): number {
  const headerValue = response.headers.get("Retry-After");
  const headerSeconds = headerValue === null ? NaN : Number(headerValue);
  if (Number.isFinite(headerSeconds) && headerSeconds > 0) return Math.ceil(headerSeconds);
  if (typeof body === "object" && body !== null) {
    const value = (body as { retry_after_seconds?: unknown }).retry_after_seconds;
    if (typeof value === "number" && Number.isFinite(value) && value > 0) return Math.ceil(value);
  }
  return 1;
}

export async function sendSocialRecommendation(
  input: SocialRecommendationInput,
): Promise<SocialRecommendationResult> {
  let response: Response;
  try {
    response = await apiFetch("/api/social/recommendations/", { method: "POST", body: input });
  } catch {
    return { kind: "error", status: 0 };
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // A status code remains authoritative when the response has no JSON body.
  }
  if (response.status === 429) {
    return { kind: "cooldown", retryAfterSeconds: retryAfterSeconds(response, body) };
  }
  return response.ok ? { kind: "ok" } : { kind: "error", status: response.status };
}

export async function markSocialMessageRead(messageId: string): Promise<boolean> {
  try {
    const response = await apiFetch(
      `/api/social/messages/${encodeURIComponent(messageId)}/read/`,
      { method: "POST" },
    );
    return response.ok;
  } catch {
    return false;
  }
}

export async function getSocialUnreadCount(): Promise<number | null> {
  try {
    const response = await apiFetch("/api/social/messages/unread-count/");
    if (!response.ok) return null;
    const body = (await response.json()) as { unread_count?: unknown };
    return typeof body.unread_count === "number" && Number.isInteger(body.unread_count) && body.unread_count >= 0
      ? body.unread_count
      : null;
  } catch {
    return null;
  }
}
