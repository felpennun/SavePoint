import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import Link from "next/link";

import { SocialInbox } from "@/components/SocialInbox";
import { fetchCatalogueList, fetchSocialHubData, fetchSocialInbox, type GameCard } from "@/lib/api";

export default async function MessagesPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const loginRedirect = `/${locale}/login?next=${encodeURIComponent(`/${locale}/messages`)}`;
  const cookieStore = await cookies();
  if (!cookieStore.has("sessionid")) redirect(loginRedirect);
  const cookieHeader = cookieStore.getAll().map((cookie) => `${cookie.name}=${cookie.value}`).join("; ");

  let inbox;
  let social;
  try {
    [inbox, social] = await Promise.all([
      fetchSocialInbox(cookieHeader),
      fetchSocialHubData(cookieHeader),
    ]);
  } catch {
    return (
      <main className="sp-page">
        <h1 className="sp-h1">{locale === "en" ? "Messages from friends" : "Mensajes de amigos"}</h1>
        <p role="alert" className="sp-lead">{locale === "en" ? "This information could not be loaded. Try again." : "No se pudo cargar esta información. Inténtalo de nuevo."}</p>
        <Link className="sp-btn-primary" href={`/${locale}/messages`}>{locale === "en" ? "Retry" : "Reintentar"}</Link>
      </main>
    );
  }
  if (!inbox || !social) redirect(loginRedirect);
  let catalogue: GameCard[] = [];
  try {
    catalogue = (await fetchCatalogueList({ page: 1 }, cookieHeader)).results;
  } catch {
    // The private inbox remains useful when catalogue discovery is briefly unavailable.
  }
  return <SocialInbox locale={locale} initialMessages={inbox.messages} friends={social.friendships.friends} catalogue={catalogue} />;
}
