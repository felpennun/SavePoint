"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

/** Compact locale switch that preserves the current route and query string. */
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
    <nav aria-label={currentLocale === "es" ? "Idioma" : "Language"} className="flex items-center gap-1">
      {(["es", "en"] as const).map((option) => (
        <Link
          key={option}
          href={hrefFor(option)}
          aria-current={currentLocale === option ? "page" : undefined}
          aria-label={option === "es" ? "Español" : "English"}
          onClick={() => remember(option)}
          className="sp-btn-secondary"
          style={{
            minWidth: "2.5rem",
            paddingInline: "0.55rem",
            fontWeight: currentLocale === option ? 700 : 400,
            color: currentLocale === option ? "var(--color-text-primary)" : "var(--color-text-secondary)",
          }}
        >
          {option.toUpperCase()}
        </Link>
      ))}
    </nav>
  );
}
