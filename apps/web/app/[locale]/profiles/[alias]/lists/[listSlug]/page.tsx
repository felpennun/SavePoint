import Link from "next/link";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { CoverImage } from "@/components/CoverImage";
import { StatusPill, type BacklogStatus } from "@/components/StatusPill";
import { buildProfileNavigation } from "@/app/[locale]/profiles/[alias]/page";
import { fetchSharedList, type FriendCollectionItem } from "@/lib/api";

const STATUSES: BacklogStatus[] = ["pending", "playing", "completed", "abandoned"];

const COPY = {
  es: {
    navigation: "Navegación del perfil",
    empty: "Esta lista está vacía.",
    rating: (value: number) => `Valoración personal: ${value}/10`,
    cover: "Carátula no disponible",
  },
  en: {
    navigation: "Profile navigation",
    empty: "This list is empty.",
    rating: (value: number) => `Personal rating: ${value}/10`,
    cover: "Cover not available",
  },
} as const;

function ListRow({ item, locale, copy }: { item: FriendCollectionItem; locale: string; copy: { rating: (value: number) => string; cover: string } }) {
  const status = STATUSES.includes(item.backlog_status as BacklogStatus)
    ? (item.backlog_status as BacklogStatus)
    : null;
  const statusLabels = {
    pending: locale === "en" ? "Pending" : "Pendiente",
    playing: locale === "en" ? "Playing" : "Jugando",
    completed: locale === "en" ? "Completed" : "Completado",
    abandoned: locale === "en" ? "Abandoned" : "Abandonado",
  } as const;
  return (
    <li className="sp-activity-list-item">
      <div className="flex min-w-0 items-center gap-3">
        <CoverImage src={item.cover.url} alt={item.cover.alt} title={item.game.title} missingLabel={copy.cover} width={48} height={72} />
        <div className="min-w-0">
          <Link href={`/${locale}/games/${item.game.slug}`} className="sp-link" style={{ overflowWrap: "anywhere" }}>
            {item.game.title}
          </Link>
          <p className="sp-meta" style={{ margin: "var(--space-xs) 0 0", overflowWrap: "anywhere" }}>
            {[item.year, item.platform].filter(Boolean).join(" · ")}
          </p>
        </div>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        {status ? <StatusPill status={status} label={statusLabels[status]} bare /> : null}
        {item.personal_rating != null ? <span className="sp-meta">{copy.rating(item.personal_rating)}</span> : null}
      </div>
    </li>
  );
}

export default async function PublicListPage({
  params,
}: {
  params: Promise<{ locale: string; alias: string; listSlug: string }>;
}) {
  const { locale: rawLocale, alias, listSlug } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const copy = COPY[locale];
  const cookieHeader = (await cookies()).getAll().map((cookie) => `${cookie.name}=${cookie.value}`).join("; ");
  const list = await fetchSharedList(alias, listSlug, cookieHeader);
  if (!list) notFound();

  const navigation = buildProfileNavigation(locale, alias, "list");
  return (
    <main className="sp-page">
      <nav aria-label={copy.navigation} style={{ marginBottom: "var(--space-xl)" }}>
        <ul className="sp-mobile-nav" style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-sm)" }}>
          {navigation.map((item) => (
            <li key={item.href}>
              <Link href={item.href} aria-current={item.current ? "page" : undefined} className={item.current ? "sp-chip sp-chip--active" : "sp-chip"}>
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      <h1 className="sp-h1" style={{ overflowWrap: "anywhere" }}>{list.name}</h1>
      {list.items.length === 0 ? <p className="sp-lead">{copy.empty}</p> : (
        <section aria-labelledby="shared-list-items-heading">
          <h2 id="shared-list-items-heading" className="visually-hidden">{list.name}</h2>
          <ul className="sp-activity-list">
            {list.items.map((item) => <ListRow key={item.game.slug} item={item} locale={locale} copy={copy} />)}
          </ul>
        </section>
      )}
    </main>
  );
}
