import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { FriendsApp } from "@/components/FriendsApp";

/** Friends: search by exact username, the friend list and profile, and the
 * notifications (requests, recommendations). `?alias=` preselects a person. */
export default async function FriendsPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams?: Promise<{ alias?: string | string[] }>;
}) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const cookieStore = await cookies();
  if (!cookieStore.has("sessionid")) {
    redirect(`/${locale}/login?next=${encodeURIComponent(`/${locale}/friends`)}`);
  }
  const rawAlias = (await searchParams)?.alias;
  const initialAlias = Array.isArray(rawAlias) ? rawAlias[0] ?? "" : rawAlias ?? "";

  return (
    <main className="sp-page sp-fr-page">
      <FriendsApp locale={locale} initialAlias={initialAlias} />
    </main>
  );
}
