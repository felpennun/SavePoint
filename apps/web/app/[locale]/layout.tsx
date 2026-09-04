import type { ReactNode } from "react";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import "../globals.css";
import { AppShell } from "@/components/AppShell";
import { SUPPORTED_LOCALES, type Locale } from "@/middleware";

export const metadata = {
  title: "SavePoint",
  description: "SavePoint controlled academic video-game catalogue demo",
};

/** Root layout -- there is no app/layout.tsx above this one; this segment
 * layout owns <html>/<body> so it can set lang={locale} from the route. */
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

  const cookieStore = await cookies();
  const isAuthenticated = cookieStore.has("sessionid");

  return (
    <html lang={locale}>
      <body>
        <AppShell locale={locale} isAuthenticated={isAuthenticated}>
          {children}
        </AppShell>
      </body>
    </html>
  );
}
