import Link from "next/link";

import { GameCard } from "@/components/GameCard";
import { formatCount, getDictionary } from "@/i18n";
import { fetchCatalogueList } from "@/lib/api";

export default async function CataloguePage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ q?: string; page?: string }>;
}) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);
  const { q, page } = await searchParams;
  const currentPage = page ? Number(page) : 1;

  const result = await fetchCatalogueList({ q, page: currentPage });

  return (
    <main>
      <h1>{dict.catalogue.heading}</h1>
      <form action={`/${locale}/catalogue`} method="get">
        <label htmlFor="q">{dict.catalogue.searchLabel}</label>
        <input id="q" name="q" type="search" defaultValue={q ?? ""} />
        <button type="submit">{dict.catalogue.searchLabel}</button>
        {q ? (
          <Link href={`/${locale}/catalogue`}>{dict.catalogue.clearSearch}</Link>
        ) : null}
      </form>
      <p data-testid="result-count" role="status">
        {formatCount(dict.catalogue.resultCount, result.count)}
      </p>
      {result.results.length === 0 ? (
        <div>
          <p>{dict.catalogue.emptyHeading}</p>
          <p>{dict.catalogue.emptyBody}</p>
        </div>
      ) : (
        <>
          <ul className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(144px, 1fr))" }}>
            {result.results.map((game) => (
              <GameCard key={game.id} game={game} locale={locale} />
            ))}
          </ul>
          <nav aria-label={locale === "es" ? "Paginación" : "Pagination"}>
            {currentPage > 1 ? (
              <Link href={`/${locale}/catalogue?${new URLSearchParams({ ...(q ? { q } : {}), page: String(currentPage - 1) })}`}>
                {locale === "es" ? "Anterior" : "Previous"}
              </Link>
            ) : null}
            <span aria-current="page">{currentPage}</span>
            {result.has_next ? (
              <Link href={`/${locale}/catalogue?${new URLSearchParams({ ...(q ? { q } : {}), page: String(currentPage + 1) })}`}>
                {locale === "es" ? "Siguiente" : "Next"}
              </Link>
            ) : null}
          </nav>
        </>
      )}
    </main>
  );
}
