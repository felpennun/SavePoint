import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import Link from "next/link";

import { SocialHub } from "@/components/SocialHub";
import { fetchSocialHubData } from "@/lib/api";

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
  const loginRedirect = `/${locale}/login?next=${encodeURIComponent(`/${locale}/friends`)}`;
  if (!cookieStore.has("sessionid")) redirect(loginRedirect);
  const cookieHeader = cookieStore.getAll().map((cookie) => `${cookie.name}=${cookie.value}`).join("; ");
  const rawAlias = (await searchParams)?.alias;
  const initialAlias = Array.isArray(rawAlias) ? rawAlias[0] ?? "" : rawAlias ?? "";
  try {
    const data = await fetchSocialHubData(cookieHeader);
    if (!data) redirect(loginRedirect);
    return <SocialHub locale={locale} initialRequests={data.requests} initialFriends={data.friendships} initialAlias={initialAlias} />;
  } catch {
    return (
      <main className="sp-page">
        <h1 className="sp-h1">{locale === "en" ? "Friends" : "Amistades"}</h1>
        <p role="alert" className="sp-lead">{locale === "en" ? "This information could not be loaded. Try again." : "No se pudo cargar esta información. Inténtalo de nuevo."}</p>
        <Link className="sp-btn-primary" href={`/${locale}/friends`}>{locale === "en" ? "Retry" : "Reintentar"}</Link>
      </main>
    );
  }
}
