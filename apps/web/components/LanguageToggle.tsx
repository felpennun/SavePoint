"use client";

import { Fragment } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

/** Compact locale switch: one mono-bordered `ES / EN` pill that preserves
 * the current route and query string (Nocturne artboard 2a). */
export function LanguageToggle({ locale }: { locale: string }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentLocale = locale === "en" ? "en" : "es";
  const query = searchParams.toString();

  function hrefFor(nextLocale: "es" | "en"): string {
    const nextPath = pathname.replace(/^\/(?:es|en)(?=\/|$)/, `/${nextLocale}`);
    return `${nextPath}${query ? `?${query}` : ""}`;
  }

  function remember(nextLocale: "es" | "en") {
    document.cookie = `locale=${nextLocale};path=/;max-age=31536000;SameSite=Lax`;
  }

  return (
    <nav aria-label={currentLocale === "es" ? "Idioma" : "Language"} className="sp-lang-toggle">
      {(["es", "en"] as const).map((option, index) => (
        <Fragment key={option}>
          {index > 0 ? (
            <span aria-hidden="true" className="sp-lang-sep">
              /
            </span>
          ) : null}
          <Link
            href={hrefFor(option)}
            aria-current={currentLocale === option ? "page" : undefined}
            aria-label={option === "es" ? "Español" : "English"}
            onClick={() => remember(option)}
            className="sp-lang-opt"
          >
            {option.toUpperCase()}
          </Link>
        </Fragment>
      ))}
    </nav>
  );
}
