import Link from "next/link";

import { fetchCatalogueList } from "@/lib/api";

const COPY = {
  es: { heading: "Catálogo", empty: "No encontramos juegos", searchLabel: "Buscar juegos" },
  en: { heading: "Catalogue", empty: "No games found", searchLabel: "Search games" },
} as const;

export default async function CataloguePage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ q?: string; page?: string }>;
}) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const copy = COPY[locale];
  const { q, page } = await searchParams;

  const result = await fetchCatalogueList({ q, page: page ? Number(page) : undefined });

  return (
    <main>
      <h1>{copy.heading}</h1>
      <form action={`/${locale}/catalogue`} method="get">
        <label htmlFor="q">{copy.searchLabel}</label>
        <input id="q" name="q" type="search" defaultValue={q ?? ""} />
        <button type="submit">{copy.searchLabel}</button>
      </form>
      <p data-testid="result-count">{result.count}</p>
      {result.results.length === 0 ? (
        <p>{copy.empty}</p>
      ) : (
        <ul>
          {result.results.map((game) => (
            <li key={game.id}>
              <Link href={`/${locale}/games/${game.slug}`}>
                {game.title}
                {game.year ? ` (${game.year})` : ""} — {game.platform_summary}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
