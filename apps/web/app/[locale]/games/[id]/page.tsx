import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { fetchGameDetail } from "@/lib/api";

import StatusControl from "./StatusControl";

const COPY = {
  es: { notAvailable: "No disponible", provenance: "Procedencia" },
  en: { notAvailable: "Not available", provenance: "Provenance" },
} as const;

export default async function GameDetailPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale: rawLocale, id } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const copy = COPY[locale];

  const game = await fetchGameDetail(id);
  if (!game) {
    notFound();
  }

  const cookieStore = await cookies();
  const isAuthenticated = cookieStore.has("sessionid");

  return (
    <main>
      <h1>{game.title}</h1>
      <p>{game.year ?? copy.notAvailable}</p>

      {game.cover.is_placeholder ? (
        <p data-testid="cover-placeholder">placeholder</p>
      ) : (
        // eslint-disable-next-line @next/next/no-img-element -- Plan 01-08 (UI wave) replaces with next/image + UI-SPEC CoverImage component.
        <img src={game.cover.url ?? undefined} alt={game.cover.alt} width={280} height={373} />
      )}

      <section aria-label={locale === "es" ? "Ediciones y plataformas" : "Releases and platforms"}>
        <ul>
          {game.releases.map((release) => (
            <li key={release.id}>
              {release.platform ?? copy.notAvailable}
              {release.editions.length > 0 ? ` — ${release.editions.join(", ")}` : ""}
            </li>
          ))}
        </ul>
      </section>

      {game.related_content.length > 0 ? (
        <section aria-label={locale === "es" ? "Contenido relacionado" : "Related content"}>
          <ul>
            {game.related_content.map((related) => (
              // Identity only, no action affordance -- D-11 non-actionable child content.
              <li key={related.id}>
                {related.title} ({related.relation})
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <StatusControl workId={game.id} locale={locale} isAuthenticated={isAuthenticated} />

      {game.provenance ? (
        <section aria-label={copy.provenance}>
          <h2>{copy.provenance}</h2>
          <p>
            {game.provenance.source} · {game.provenance.licence} ·{" "}
            {new Date(game.provenance.retrieved_at).toISOString().slice(0, 10)}
          </p>
        </section>
      ) : null}
    </main>
  );
}
