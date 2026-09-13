import { NextRequest, NextResponse } from "next/server";

export const SUPPORTED_LOCALES = ["es", "en"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "es";

// Paths (locale-relative, i.e. without the /{locale} prefix) reachable
// without an authenticated Django session. Profile routes remain public only
// for the backend's basic projection; protected profile/list content is still
// authorized by Django and never by this UX-only middleware.
const PUBLIC_PATHS = ["/", "/login", "/register", "/sources", "/catalogue", "/games", "/profiles"];
const AUTHENTICATED_PATHS = ["/collection", "/recommendations", "/friends"];

function isSupportedLocale(value: string): value is Locale {
  return (SUPPORTED_LOCALES as readonly string[]).includes(value);
}

function pickLocale(request: NextRequest): Locale {
  const cookieLocale = request.cookies.get("locale")?.value;
  if (cookieLocale && isSupportedLocale(cookieLocale)) return cookieLocale;

  const acceptLanguage = request.headers.get("accept-language") ?? "";
  const preferred = acceptLanguage.split(",")[0]?.split("-")[0]?.toLowerCase();
  if (preferred && isSupportedLocale(preferred)) return preferred;

  return DEFAULT_LOCALE;
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;
  const segments = pathname.split("/").filter(Boolean);
  const firstSegment = segments[0];

  if (!firstSegment || !isSupportedLocale(firstSegment)) {
    const locale = pickLocale(request);
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}${pathname === "/" ? "" : pathname}`;
    return NextResponse.redirect(url);
  }

  const locale = firstSegment;
  const restPath = "/" + segments.slice(1).join("/");
  const normalizedRest = restPath === "/" ? "/" : restPath.replace(/\/$/, "");
  const isPublic = PUBLIC_PATHS.some(
    (p) => normalizedRest === p || (p !== "/" && normalizedRest.startsWith(`${p}/`))
  );
  const requiresSession = AUTHENTICATED_PATHS.some(
    (p) => normalizedRest === p || normalizedRest.startsWith(`${p}/`),
  );

  // D-03: session cookie is Django's own sessionid, same-origin via the
  // rewrite proxy in next.config.ts -- the middleware never inspects its
  // value, only whether it exists.
  const hasSession = request.cookies.has("sessionid");

  if ((requiresSession || !isPublic) && !hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}/login`;
    // Only ever a same-origin path -- the login handler itself re-validates
    // this server-side before ever honoring it (open-redirect defense in
    // depth, matching accounts/views.py::LoginView).
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  // health must be excluded alongside api: next.config.ts rewrites /health/
  // straight to the API's own health check (the deployment smoke's revision
  // marker), but that rewrite never runs if the middleware gets to it first
  // -- "health" isn't a supported locale, so it was being 307-redirected to
  // /es/health/ instead of proxied, breaking the health check itself.
  matcher: ["/((?!api|health|_next|favicon.ico).*)"],
};
