import type { NextConfig } from "next";

// Same-origin proxy to Django (server-side only, never a NEXT_PUBLIC_* var):
// the browser only ever talks to this Next.js origin, so the session/CSRF
// cookies Django sets stay same-origin and no CORS-with-credentials
// configuration is needed (avoids the anti-pattern flagged in project
// research: "Introducir CORS con cookies sin necesidad").
const rawApiProxyTarget = process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";
// Render's safe `fromService.property: hostport` is a private-network
// host:port without a scheme. Compose supplies a complete URL. Accept both
// forms without exposing the value to the browser bundle.
const API_PROXY_TARGET = rawApiProxyTarget.includes("://") ? rawApiProxyTarget : `http://${rawApiProxyTarget}`;

const nextConfig: NextConfig = {
  // ADR-006 cover delivery: IGDB covers are hotlinked (not mirrored) from
  // images.igdb.com only -- the single approved CDN host. No other remote
  // image host is allowed (threat T-01.1-12: approved CDN only).
  images: {
    remotePatterns: [{ protocol: "https", hostname: "images.igdb.com" }],
  },
  // Two fixes needed together for the Django proxy, both about the same
  // trailing-slash mismatch: (1) skipTrailingSlashRedirect stops Next's own
  // "canonical URL" redirect response for incoming /api/* requests -- without
  // it, Next 308s "/api/x/" -> "/api/x" before the rewrite ever runs; (2) the
  // rewrite destination's :path* capture is itself normalized without a
  // trailing slash regardless of that flag, so it's appended explicitly here.
  // Every Django URL in this project is slash-terminated by convention;
  // without both fixes, Django's own APPEND_SLASH middleware redirects the
  // slash back on and the client follows it right back into the same
  // stripping -- an infinite loop.
  skipTrailingSlashRedirect: true,
  // Defense-in-depth response headers (repo-review 2026-09-06 L-02). No XSS
  // sink exists in the current React code -- all interpolation is text and
  // covers load from a fixed host template -- so this is a safety net, not a
  // patch. `script-src` keeps `'unsafe-inline'` because Next injects inline
  // bootstrap/RSC-payload scripts with no nonce by default; moving to a
  // nonce (via middleware) is the follow-up tightening. Everything else is
  // locked down: cross-origin framing, form posts to other origins, <base>
  // hijacking and plugin objects are all denied.
  async headers() {
    const csp = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob: https://images.igdb.com https://upload.wikimedia.org",
      "font-src 'self' data:",
      "connect-src 'self'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "object-src 'none'",
    ].join("; ");
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: csp },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "same-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=(), browsing-topics=()",
          },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      // Django Platform Admin is intentionally allowlisted as a same-origin
      // browser boundary; it must bypass locale middleware and reach Django
      // with the session cookie intact.
      { source: "/admin/", destination: `${API_PROXY_TARGET}/admin/` },
      { source: "/admin/:path*", destination: `${API_PROXY_TARGET}/admin/:path*/` },
      // PORT-01/PORT-04 (Phase 5): the collection CSV export is the one
      // Django URL in this project that deliberately has NO trailing slash
      // -- library/urls.py's `export/collection.csv` reads as a literal
      // downloadable filename, not a resource collection. It must be
      // rewritten before the generic `/api/:path*` rule below, which always
      // appends a trailing slash (see that rule's own comment); matched
      // first here, this route keeps its exact slash-less path end to end
      // instead of 404ing against a `.../collection.csv/` Django never
      // registered.
      {
        source: "/api/library/export/collection.csv",
        destination: `${API_PROXY_TARGET}/api/library/export/collection.csv`,
      },
      { source: "/api/:path*", destination: `${API_PROXY_TARGET}/api/:path*/` },
      // Same-origin deployment evidence endpoint. The browser smoke never
      // needs (or learns) the API service's separate provider hostname.
      { source: "/health/", destination: `${API_PROXY_TARGET}/health/` },
    ];
  },
};

export default nextConfig;
