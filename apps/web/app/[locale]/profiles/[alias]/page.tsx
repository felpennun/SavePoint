import Link from "next/link";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { CoverImage } from "@/components/CoverImage";
import { ProfileSettings } from "@/components/ProfileSettings";
import { StatusPill, type BacklogStatus } from "@/components/StatusPill";
import { getDictionary } from "@/i18n";
import {
  fetchAccountMe,
  fetchPublicProfile,
  fetchSharedCollection,
  type FriendCollectionItem,
  type ProtectedPublicProfile,
} from "@/lib/api";

const STATUSES: BacklogStatus[] = ["pending", "playing", "completed", "abandoned"];

const COPY = {
  es: {
    heading: (alias: string) => `Perfil de ${alias}`,
    empty: "Esta colección no tiene juegos visibles.",
    activity: "Actividad pública",
    summaryLabels: { pending: "pendientes", playing: "jugando", completed: "completados", abandoned: "abandonados" },
    note: "Solo se muestran los campos que expone el backend: alias, actividad y resumen. Sin datos privados ni valoraciones ajenas.",
    favoritesHeading: "Favoritos",
    commentsHeading: "Comentarios",
    listsHeading: "Listas",
    listEmpty: "Lista vacía",
    basicNote: "Solo puedes ver el perfil básico hasta que se acepte la amistad.",
    actions: {
      login: "Inicia sesión para enviar una solicitud de amistad",
      send_friend_request: "Enviar solicitud de amistad",
      request_sent: "Solicitud enviada",
      review_friend_request: "Revisar solicitud de amistad",
    },
    profileNav: "Navegación del perfil",
    profile: "Perfil",
    collection: "Colección",
    lists: "Listas",
    personalRating: (rating: number) => `Valoración personal: ${rating}/10`,
  },
  en: {
    heading: (alias: string) => `${alias}'s profile`,
    empty: "This collection has no visible games.",
    activity: "Public activity",
    summaryLabels: { pending: "pending", playing: "playing", completed: "completed", abandoned: "abandoned" },
    note: "Only the fields the backend exposes are shown: alias, activity and summary. No private data, no other users' ratings.",
    favoritesHeading: "Favorites",
    commentsHeading: "Comments",
    listsHeading: "Lists",
    listEmpty: "Empty list",
    basicNote: "You can only see the basic profile until the friendship is accepted.",
    actions: {
      login: "Log in to send a friend request",
      send_friend_request: "Send friend request",
      request_sent: "Request sent",
      review_friend_request: "Review friend request",
    },
    profileNav: "Profile navigation",
    profile: "Profile",
    collection: "Collection",
    lists: "Lists",
    personalRating: (rating: number) => `Personal rating: ${rating}/10`,
  },
} as const;

export type ProfileNavigationSection = "profile" | "collection" | "list";

export function buildProfileNavigation(
  locale: string,
  alias: string,
  current: ProfileNavigationSection,
) {
  const copy = locale === "en" ? COPY.en : COPY.es;
  const base = `/${locale}/profiles/${encodeURIComponent(alias)}`;
  return [
    { href: base, label: copy.profile, current: current === "profile" },
    { href: `${base}#collection`, label: copy.collection, current: current === "collection" },
    { href: `${base}#lists`, label: copy.lists, current: current === "list" },
  ];
}

function initials(alias: string): string {
  return alias
    .split(/[\s._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("") || alias.slice(0, 2).toUpperCase();
}

function isBacklogStatus(value: string | null): value is BacklogStatus {
  return value !== null && STATUSES.includes(value as BacklogStatus);
}

function CollectionRow({
  item,
  locale,
  labels,
}: {
  item: FriendCollectionItem;
  locale: string;
  labels: { personalRating: (rating: number) => string };
}) {
  const dict = getDictionary(locale);
  return (
    <li className="sp-activity-list-item">
      <div className="flex min-w-0 items-center gap-3">
        <CoverImage
          src={item.cover.url}
          alt={item.cover.alt}
          title={item.game.title}
          missingLabel={dict.common.coverMissing}
          width={48}
          height={72}
        />
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
        {isBacklogStatus(item.backlog_status) ? (
          <StatusPill status={item.backlog_status} label={dict.status.labels[item.backlog_status]} bare />
        ) : null}
        {item.personal_rating != null ? <span className="sp-meta">{labels.personalRating(item.personal_rating)}</span> : null}
      </div>
    </li>
  );
}

function ProfileNavigation({
  locale,
  alias,
  current,
}: {
  locale: string;
  alias: string;
  current: ProfileNavigationSection;
}) {
  const copy = locale === "en" ? COPY.en : COPY.es;
  return (
    <nav aria-label={copy.profileNav} style={{ marginBottom: "var(--space-xl)" }}>
      <ul className="sp-mobile-nav" style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-sm)" }}>
        {buildProfileNavigation(locale, alias, current).map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              aria-current={item.current ? "page" : undefined}
              className={item.current ? "sp-chip sp-chip--active" : "sp-chip"}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

/** The API's explicit projection discriminator is the only branch that
 * decides whether protected content can be rendered. A missing collection is
 * an empty protected projection, never a reason to reveal basic fields. */
export default async function PublicProfilePage({
  params,
}: {
  params: Promise<{ locale: string; alias: string }>;
}) {
  const { locale: rawLocale, alias } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const copy = COPY[locale];
  const dict = getDictionary(locale);
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((cookie) => `${cookie.name}=${cookie.value}`)
    .join("; ");

  const profile = await fetchPublicProfile(alias, cookieHeader);
  if (!profile) notFound();

  const isOwner = profile.kind === "protected" && cookieStore.has("sessionid")
    ? (await fetchAccountMe(cookieHeader))?.username === profile.alias
    : false;
  const protectedProfile: ProtectedPublicProfile | null = profile.kind === "protected" ? profile : null;
  const collection = protectedProfile ? await fetchSharedCollection(profile.alias, cookieHeader) : null;
  const summaryChips = protectedProfile
    ? STATUSES.map((status) => [status, protectedProfile.summary[status] ?? 0] as const).filter(([, count]) => count > 0)
    : [];
  const favoriteSlots = protectedProfile ? protectedProfile.favorites.filter((slot) => slot !== null) : [];

  return (
    <main className="sp-page">
      <div className="sp-profile-head">
        {profile.avatar_url ? (
          <CoverImage
            src={profile.avatar_url}
            alt={copy.heading(profile.alias)}
            title={profile.alias}
            missingLabel={dict.common.coverMissing}
            width={64}
            height={64}
          />
        ) : (
          <span className="sp-account-avatar sp-profile-avatar" aria-hidden="true">
            {initials(profile.alias)}
          </span>
        )}
        <div className="min-w-0">
          <h1 className="sp-h1" style={{ margin: 0, overflowWrap: "anywhere" }}>
            {copy.heading(profile.alias)}
          </h1>
          <p className="sp-mono sp-muted" style={{ margin: "var(--space-xs) 0 0", overflowWrap: "anywhere" }}>
            /{locale}/profiles/{profile.alias}
          </p>
        </div>
      </div>

      {profile.bio ? <p className="sp-lead">{profile.bio}</p> : null}

      {profile.kind === "basic" ? (
        <section className="sp-surface" aria-label={copy.profile} style={{ marginBottom: "var(--space-xl)" }}>
          <p className="sp-lead">{copy.basicNote}</p>
          {profile.action === "login" ? (
            <Link href={`/${locale}/login?next=${encodeURIComponent(`/${locale}/profiles/${profile.alias}`)}`} className="sp-btn-primary">
              {copy.actions.login}
            </Link>
          ) : profile.action === "request_sent" ? (
            <p role="status" className="sp-meta">{copy.actions.request_sent}</p>
          ) : (
            <Link href={`/${locale}/friends?alias=${encodeURIComponent(profile.alias)}`} className="sp-btn-primary">
              {copy.actions[profile.action]}
            </Link>
          )}
        </section>
      ) : (
        <>
          <ProfileNavigation locale={locale} alias={profile.alias} current="profile" />
          {isOwner ? (
            <div className="sp-surface" style={{ marginBottom: "var(--space-xl)" }}>
              <ProfileSettings locale={locale} />
            </div>
          ) : null}

          <section id="collection" aria-labelledby="profile-collection-heading">
            <p id="profile-collection-heading" className="sp-eyebrow" style={{ margin: "var(--space-xl) 0 var(--space-sm)" }}>
              {copy.activity}
            </p>
            {!collection || collection.items.length === 0 ? (
              <p className="sp-lead">{copy.empty}</p>
            ) : (
              <ul className="sp-activity-list">
                {collection.items.map((item) => <CollectionRow key={item.game.slug} item={item} locale={locale} labels={copy} />)}
              </ul>
            )}
          </section>

          {favoriteSlots.length > 0 ? (
            <section aria-labelledby="profile-favorites-heading">
              <p id="profile-favorites-heading" className="sp-eyebrow" style={{ margin: "var(--space-xl) 0 var(--space-sm)" }}>
                {copy.favoritesHeading}
              </p>
              <ul className="sp-favorites-list">
                {favoriteSlots.map((slot) => (
                  <li key={slot!.work_slug}>
                    <Link href={`/${locale}/games/${slot!.work_slug}`} className="sp-link">{slot!.work_title}</Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {summaryChips.length > 0 ? (
            <div className="sp-chip-row" aria-label={copy.activity}>
              {summaryChips.map(([status, count]) => (
                <span key={status} className="sp-chip">{count} {copy.summaryLabels[status]}</span>
              ))}
            </div>
          ) : null}

          {profile.comments.length > 0 ? (
            <section aria-labelledby="profile-comments-heading">
              <p id="profile-comments-heading" className="sp-eyebrow" style={{ margin: "var(--space-xl) 0 var(--space-sm)" }}>
                {copy.commentsHeading}
              </p>
              <ul className="sp-profile-comments-list">
                {profile.comments.map((comment, index) => (
                  <li key={`${comment.work_slug}-${index}`}>
                    <Link href={`/${locale}/games/${comment.work_slug}`} className="sp-link">{comment.work_title}</Link>
                    <p className="sp-meta">{comment.text}</p>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section id="lists" aria-labelledby="profile-lists-heading">
            <p id="profile-lists-heading" className="sp-eyebrow" style={{ margin: "var(--space-xl) 0 var(--space-sm)" }}>
              {copy.listsHeading}
            </p>
            {profile.lists.length === 0 ? <p className="sp-meta">{copy.listEmpty}</p> : (
              <div className="sp-profile-lists">
                {profile.lists.map((list, listIndex) => (
                  <div className="sp-profile-list-card" key={`${list.name}-${listIndex}`}>
                    <h2 className="sp-library-title" style={{ overflowWrap: "anywhere" }}>{list.name}</h2>
                    {list.items.length === 0 ? <p className="sp-meta">{copy.listEmpty}</p> : (
                      <ol>
                        {list.items.map((item) => (
                          <li key={item.work_slug}>
                            <Link href={`/${locale}/games/${item.work_slug}`} className="sp-link">{item.work_title}</Link>
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
          <p className="sp-muted" style={{ maxWidth: "72ch", lineHeight: 1.6, marginTop: "var(--space-xl)" }}>{copy.note}</p>
        </>
      )}
    </main>
  );
}
