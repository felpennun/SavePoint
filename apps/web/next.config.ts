import type { NextConfig } from "next";

// Same-origin proxy to Django (server-side only, never a NEXT_PUBLIC_* var):
// the browser only ever talks to this Next.js origin, so the session/CSRF
// cookies Django sets stay same-origin and no CORS-with-credentials
// configuration is needed (avoids the anti-pattern flagged in project
// research: "Introducir CORS con cookies sin necesidad").
const API_PROXY_TARGET = process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
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
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_PROXY_TARGET}/api/:path*/` }];
  },
};

export default nextConfig;
