import Link from "next/link";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { CoverImage } from "@/components/CoverImage";
import { ProfileSettings } from "@/components/ProfileSettings";
import { StatusPill, type BacklogStatus } from "@/components/StatusPill";
import { getDictionary } from "@/i18n";
import { fetchAccountMe, fetchPublicProfile } from "@/lib/api";

const STATUSES: BacklogStatus[] = ["pending", "playing", "completed", "abandoned"];

const COPY = {
  es: {
    heading: (alias: string) => `Perfil de ${alias}`,
    empty: "Colección pública vacía",
    activity: "Actividad pública",
    summaryLabels: { pending: "pendientes", playing: "jugando", completed: "completados", abandoned: "abandonados" },
    note: "Solo se muestran los campos que expone el backend: alias, actividad y resumen. Sin datos privados ni valoraciones ajenas.",
    favoritesHeading: "Favoritos",
    commentsHeading: "Comentarios",
    listsHeading: "Listas",
    listEmpty: "Lista vacía",
  },
  en: {
    heading: (alias: string) => `${alias}'s profile`,
    empty: "Public collection empty",
    activity: "Public activity",
    summaryLabels: { pending: "pending", playing: "playing", completed: "completed", abandoned: "abandoned" },
    note: "Only the fields the backend exposes are shown: alias, activity and summary. No private data, no other users' ratings.",
    favoritesHeading: "Favorites",
    commentsHeading: "Comments",
    listsHeading: "Lists",
    listEmpty: "Empty list",
  },
} as const;

function initials(alias: string): string {
  return alias
    .split(/[\s._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("") || alias.slice(0, 2).toUpperCase();
}

/** PROF-02/INV-05: renders only the allowlisted fields the backend
 * returns -- never fetches or displays anything beyond `alias`,
 * `activity`, and `summary` (there is nothing else in the DTO to render
 * by construction). */
export default async function PublicProfilePage({
  params,
}: {
  params: Promise<{ locale: string; alias: string }>;
}) {
  const { locale: rawLocale, alias } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const copy = COPY[locale];
  const dict = getDictionary(locale);

  const profile = await fetchPublicProfile(alias);
  if (!profile) {
    notFound();
  }

  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((cookie) => `${cookie.name}=${cookie.value}`)
    .join("; ");
  const me = cookieStore.has("sessionid") ? await fetchAccountMe(cookieHeader) : null;
  const isOwner = me?.username === profile.alias;

  const summaryChips = STATUSES.map((status) => [status, profile.summary[status] ?? 0] as const).filter(
    ([, count]) => count > 0,
  );
  const favoriteSlots = profile.favorites.filter((slot) => slot !== null);

  return (
    <main className="sp-page">
      {isOwner ? (
        <div className="sp-surface" style={{ marginBottom: "var(--space-xl)" }}>
          <ProfileSettings locale={locale} />
        </div>
      ) : null}

      <div className="sp-profile-head">
        {profile.avatar_url ? (
          <CoverImage
            src={profile.avatar_url}
            alt={copy.heading(profile.alias)}
            title={profile.alias}
            missingLabel=""
            width={64}
            height={64}
          />
        ) : (
          <span className="sp-account-avatar sp-profile-avatar" aria-hidden="true">
            {initials(profile.alias)}
          </span>
        )}
        <div>
          <h1 className="sp-h1" style={{ margin: 0 }}>
            {copy.heading(profile.alias)}
          </h1>
          <p className="sp-mono sp-muted" style={{ margin: "var(--space-xs) 0 0" }}>
            /{locale}/profiles/{profile.alias}
          </p>
        </div>
      </div>

      {profile.bio ? <p className="sp-lead">{profile.bio}</p> : null}

      {favoriteSlots.length > 0 ? (
        <>
          <p className="sp-eyebrow" style={{ margin: "var(--space-xl) 0 var(--space-sm)" }}>
            {copy.favoritesHeading}
          </p>
          <ul className="sp-favorites-list">
            {favoriteSlots.map((slot) => (
              <li key={slot!.work_slug}>
                <Link href={`/${locale}/games/${slot!.work_slug}`} className="sp-link">
                  {slot!.work_title}
                </Link>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {summaryChips.length > 0 ? (
        <div className="sp-chip-row">
          {summaryChips.map(([status, count]) => (
            <span key={status} className="sp-chip">
              {count} {copy.summaryLabels[status]}
            </span>
          ))}
        </div>
      ) : null}

      <p className="sp-eyebrow" style={{ margin: "var(--space-xl) 0 var(--space-sm)" }}>
        {copy.activity}
      </p>
      {profile.activity.length === 0 ? (
        <p className="sp-lead">{copy.empty}</p>
      ) : (
        <ul className="sp-activity-list">
          {profile.activity.map((item) => {
            const status = STATUSES.includes(item.status as BacklogStatus)
              ? (item.status as BacklogStatus)
              : null;
            return (
              <li key={item.work_slug}>
                <Link href={`/${locale}/games/${item.work_slug}`} className="sp-link">
                  {item.work_title}
                </Link>
                {status ? <StatusPill status={status} label={dict.status.labels[status]} bare /> : null}
              </li>
            );
          })}
        </ul>
      )}

      {profile.comments.length > 0 ? (
        <>
          <p className="sp-eyebrow" style={{ margin: "var(--space-xl) 0 var(--space-sm)" }}>
            {copy.commentsHeading}
          </p>
          <ul className="sp-profile-comments-list">
            {profile.comments.map((comment, index) => (
              <li key={`${comment.work_slug}-${index}`}>
                <Link href={`/${locale}/games/${comment.work_slug}`} className="sp-link">
                  {comment.work_title}
                </Link>
                <p className="sp-meta">{comment.text}</p>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {profile.lists.length > 0 ? (
        <>
          <p className="sp-eyebrow" style={{ margin: "var(--space-xl) 0 var(--space-sm)" }}>
            {copy.listsHeading}
          </p>
          <div className="sp-profile-lists">
            {profile.lists.map((list, listIndex) => (
              <div className="sp-profile-list-card" key={`${list.name}-${listIndex}`}>
                <h3 className="sp-library-title">{list.name}</h3>
                {list.items.length === 0 ? (
                  <p className="sp-meta">{copy.listEmpty}</p>
                ) : (
                  <ol>
                    {list.items.map((item) => (
                      <li key={item.work_slug}>
                        <Link href={`/${locale}/games/${item.work_slug}`} className="sp-link">
                          {item.work_title}
                        </Link>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            ))}
          </div>
        </>
      ) : null}

      <p className="sp-muted" style={{ maxWidth: "72ch", lineHeight: 1.6, marginTop: "var(--space-xl)" }}>
        {copy.note}
      </p>
    </main>
  );
}
