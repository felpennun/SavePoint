"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * The router keeps the pages already visited for a short while (see
 * `staleTimes` in next.config.ts) so going back and forth is instant. Any
 * successful write to the API (status, rating, lists, friends, login...) makes
 * those copies stale, so every successful non-GET request to `/api/` drops
 * them and refreshes the page being shown.
 */
export function RouterCacheGuard() {
  const router = useRouter();

  useEffect(() => {
    const originalFetch = window.fetch;
    let timer: ReturnType<typeof setTimeout> | undefined;

    window.fetch = async (input, init) => {
      const response = await originalFetch(input, init);
      try {
        const method = (init?.method ?? (input instanceof Request ? input.method : "GET")).toUpperCase();
        const target = typeof input === "string" ? input : input instanceof URL ? input.pathname : input.url;
        if (method !== "GET" && method !== "HEAD" && response.ok && target.includes("/api/")) {
          clearTimeout(timer);
          timer = setTimeout(() => router.refresh(), 150);
        }
      } catch {
        // never let the bookkeeping break a request
      }
      return response;
    };

    return () => {
      window.fetch = originalFetch;
      clearTimeout(timer);
    };
  }, [router]);

  return null;
}
