import type { ReactNode } from "react";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import "../globals.css";
import { AppShell } from "@/components/AppShell";
import { SUPPORTED_LOCALES, type Locale } from "@/middleware";

export const metadata = {
  title: "SavePoint",
  description: "SavePoint controlled academic video-game catalogue demo",
  icons: {
    icon: [{ url: "/icon.svg", type: "image/svg+xml" }],
  },
  openGraph: {
    title: "SavePoint",
    description: "A controlled, reproducible personal video-game catalogue, with explainable recommendations.",
    images: [{ url: "/brand/banner-og.svg", width: 1200, height: 630, alt: "SavePoint" }],
  },
};

/** Root layout -- there is no app/layout.tsx above this one; this segment
 * layout owns <html>/<body> so it can set lang={locale} from the route
 * and data-theme from the sp-theme cookie (D-UI-1: server-side so the
 * persisted theme is present in the first painted HTML -- no flash). */
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
  const theme = cookieStore.get("sp-theme")?.value === "light" ? "light" : "dark";

  return (
    <html lang={locale} data-theme={theme}>
      <body>
        <AppShell locale={locale} isAuthenticated={isAuthenticated}>
          {children}
        </AppShell>
      </body>
    </html>
  );
}
