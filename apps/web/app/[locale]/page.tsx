import Link from "next/link";

import { GameCard } from "@/components/GameCard";
import { getDictionary } from "@/i18n";
import { fetchCatalogueList } from "@/lib/api";

const COPY = {
  es: {
    valueProposition: "Catálogo de videojuegos personal, controlado y reproducible, con recomendaciones explicables.",
    sampleHeading: "Una muestra del catálogo",
    sampleFailure: "No se pudo cargar la muestra del catálogo. Puedes abrir el catálogo completo.",
  },
  en: {
    valueProposition: "A controlled, reproducible personal video-game catalogue, with explainable recommendations.",
    sampleHeading: "A catalogue sample",
    sampleFailure: "We couldn't load the catalogue sample. You can open the full catalogue.",
  },
} as const;

/** D-01/D-04: a realistic homepage with branding, value proposition,
 * representative content, and a visible login entry -- no guided tour;
 * actions and states are self-explanatory. */
export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);
  const copy = COPY[locale];

  let sample: Awaited<ReturnType<typeof fetchCatalogueList>>["results"] = [];
  let sampleFailed = false;
  try {
    const result = await fetchCatalogueList({ page: 1 });
    sample = result.results.slice(0, 8);
  } catch {
    sampleFailed = true;
  }

  return (
    <main>
      <h1>SavePoint</h1>
      <p>{copy.valueProposition}</p>
      <nav>
        <Link href={`/${locale}/login`}>{dict.nav.login}</Link>
        {" · "}
        <Link href={`/${locale}/catalogue`}>{dict.nav.catalogue}</Link>
      </nav>

      <section aria-label={copy.sampleHeading}>
        <h2>{copy.sampleHeading}</h2>
        {sampleFailed ? (
          <div>
            <p role="alert">{copy.sampleFailure}</p>
            <Link href={`/${locale}/catalogue`}>{dict.errors.openFullCatalogue}</Link>
          </div>
        ) : (
          <ul className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(144px, 1fr))" }}>
            {sample.map((game) => (
              <GameCard key={game.id} game={game} locale={locale} />
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
