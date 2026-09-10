import Link from "next/link";
import { notFound } from "next/navigation";

import { StatusPill, type BacklogStatus } from "@/components/StatusPill";
import { getDictionary } from "@/i18n";
import { fetchPublicProfile } from "@/lib/api";

const STATUSES: BacklogStatus[] = ["pending", "playing", "completed", "abandoned"];

const COPY = {
  es: {
    heading: (alias: string) => `Perfil de ${alias}`,
    empty: "Colección pública vacía",
    activity: "Actividad pública",
    summaryLabels: { pending: "pendientes", playing: "jugando", completed: "completados", abandoned: "abandonados" },
    note: "Solo se muestran los campos que expone el backend: alias, actividad y resumen. Sin datos privados ni valoraciones ajenas.",
  },
  en: {
    heading: (alias: string) => `${alias}'s profile`,
    empty: "Public collection empty",
    activity: "Public activity",
    summaryLabels: { pending: "pending", playing: "playing", completed: "completed", abandoned: "abandoned" },
    note: "Only the fields the backend exposes are shown: alias, activity and summary. No private data, no other users' ratings.",
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

  const summaryChips = STATUSES.map((status) => [status, profile.summary[status] ?? 0] as const).filter(
    ([, count]) => count > 0,
  );

  return (
    <main className="sp-page">
      <div className="sp-profile-head">
        <span className="sp-account-avatar sp-profile-avatar" aria-hidden="true">
          {initials(profile.alias)}
        </span>
        <div>
          <h1 className="sp-h1" style={{ margin: 0 }}>
            {copy.heading(profile.alias)}
          </h1>
          <p className="sp-mono sp-muted" style={{ margin: "var(--space-xs) 0 0" }}>
            /{locale}/profiles/{profile.alias}
          </p>
        </div>
      </div>

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

      <p className="sp-muted" style={{ maxWidth: "72ch", lineHeight: 1.6, marginTop: "var(--space-xl)" }}>
        {copy.note}
      </p>
    </main>
  );
}
