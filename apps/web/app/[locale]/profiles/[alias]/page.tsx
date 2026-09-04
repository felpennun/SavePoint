import Link from "next/link";
import { notFound } from "next/navigation";

import { fetchPublicProfile } from "@/lib/api";

const COPY = {
  es: {
    heading: (alias: string) => `Perfil de ${alias}`,
    empty: "Colección pública vacía",
  },
  en: {
    heading: (alias: string) => `${alias}'s profile`,
    empty: "Public collection empty",
  },
} as const;

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

  const profile = await fetchPublicProfile(alias);
  if (!profile) {
    notFound();
  }

  return (
    <main>
      <h1>{copy.heading(profile.alias)}</h1>
      {profile.activity.length === 0 ? (
        <p>{copy.empty}</p>
      ) : (
        <ul>
          {profile.activity.map((item) => (
            <li key={item.work_slug}>
              <Link href={`/${locale}/games/${item.work_slug}`}>{item.work_title}</Link> — {item.status}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
