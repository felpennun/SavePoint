import type { ReactNode } from "react";
import { notFound } from "next/navigation";

import { SUPPORTED_LOCALES, type Locale } from "@/middleware";

export const metadata = {
  title: "SavePoint",
  description: "SavePoint controlled academic video-game catalogue demo",
};

/**
 * Root layout for the app -- there is no app/layout.tsx above this one.
 * Minimal, functional bilingual strings live inline here for Plan 01-04's
 * tracer scope; apps/web/i18n/{es,en}.ts (typed dictionaries with a parity
 * test) is Plan 01-08's declared deliverable, not duplicated here.
 */
export default async function LocaleLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!SUPPORTED_LOCALES.includes(locale as Locale)) {
    notFound();
  }

  return (
    <html lang={locale}>
      <body>{children}</body>
    </html>
  );
}
