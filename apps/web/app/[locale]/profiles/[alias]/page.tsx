import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { FriendProfile } from "@/components/FriendProfile";
import { parseProfileTab } from "@/lib/profile-navigation";

/** The detailed profile of a friend (or of the signed-in user): read-only, with
 * profile, collection, lists and comments. Visitors without a session sign in
 * first; people who are not friends are sent to the friends page. */
export default async function ProfilePage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string; alias: string }>;
  searchParams?: Promise<{ tab?: string | string[] }>;
}) {
  const { locale: rawLocale, alias } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const cookieStore = await cookies();
  if (!cookieStore.has("sessionid")) {
    redirect(`/${locale}/login?next=${encodeURIComponent(`/${locale}/profiles/${alias}`)}`);
  }
  const tab = parseProfileTab((await searchParams)?.tab);

  return (
    <main className="sp-page sp-pf-page">
      <FriendProfile locale={locale} alias={alias} initialTab={tab} />
    </main>
  );
}
