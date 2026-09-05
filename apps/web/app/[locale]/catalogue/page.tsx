import Link from "next/link";

import { FilterBar } from "@/components/FilterBar";
import { FilterChip } from "@/components/FilterChip";
import { GameCard } from "@/components/GameCard";
import { formatCount, getDictionary } from "@/i18n";
import { fetchCatalogueList } from "@/lib/api";
import {
  type FilterOption,
  buildQuery,
  countActiveFilters,
  parseFilters,
} from "@/lib/catalogue-filters";

type RawParams = Record<string, string | string[] | undefined>;

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

/**
 * Catalogue (01.1-UI-SPEC Screen Contract 2, CAT-02). Server component,
 * searchParams-driven, every control submits via GET so each filtered view
 * is a shareable/bookmarkable URL — no client-only filter state. The
 * platform/genre `<select>` options and the year-input bounds come from the
 * API `facets` payload; if that payload is unavailable the FilterBar
 * degrades to search-only. Pagination carries the full query string.
 */
export default async function CataloguePage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<RawParams>;
}) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const dict = getDictionary(locale);
  const sp = await searchParams;

  const currentYear = new Date().getUTCFullYear();
  const flat: Record<string, string | undefined> = {};
  for (const key of ["q", "platform", "genre", "year_from", "year_to", "min_rating", "sort"]) {
    flat[key] = first(sp[key]);
  }
  const filters = parseFilters(flat, currentYear);
  const activeCount = countActiveFilters(filters);
  const currentPage = Math.max(1, Number(first(sp.page)) || 1);
  const basePath = `/${locale}/catalogue`;

  let result: Awaited<ReturnType<typeof fetchCatalogueList>> | null = null;
  let failed = false;
  try {
    result = await fetchCatalogueList({
      q: filters.q,
      page: currentPage,
      platform: filters.platform,
      genre: filters.genre,
      year_from: filters.year_from,
      year_to: filters.year_to,
      min_rating: filters.min_rating,
      sort: filters.sort,
    });
  } catch {
    failed = true;
  }

  const platformOptions: FilterOption[] =
    result?.facets.platforms.map((p) => ({ value: p.slug, label: p.name })) ?? [];
  const genreOptions: FilterOption[] =
    result?.facets.genres.map((g) => ({ value: g.slug, label: g.name })) ?? [];
  const platformLabels = new Map(platformOptions.map((o) => [o.value, o.label]));
  const genreLabels = new Map(genreOptions.map((o) => [o.value, o.label]));
  const yearRange = result?.facets.year_range;

  const chips: { key: string; label: string }[] = [];
  if (filters.q) chips.push({ key: "q", label: `${dict.catalogue.searchLabel}: ${filters.q}` });
  if (filters.platform)
    chips.push({
      key: "platform",
      label: `${dict.catalogue.filters.platform}: ${platformLabels.get(filters.platform) ?? filters.platform}`,
    });
  if (filters.genre)
    chips.push({
      key: "genre",
      label: `${dict.catalogue.filters.genre}: ${genreLabels.get(filters.genre) ?? filters.genre}`,
    });
  if (filters.year_from) chips.push({ key: "year_from", label: `${dict.catalogue.filters.yearFrom}: ${filters.year_from}` });
  if (filters.year_to) chips.push({ key: "year_to", label: `${dict.catalogue.filters.yearTo}: ${filters.year_to}` });
  if (filters.min_rating) chips.push({ key: "min_rating", label: `IGDB ${filters.min_rating}+` });

  function chipRemoveHref(dropKey: string): string {
    const next: Partial<typeof filters> = { ...filters };
    delete next[dropKey as keyof typeof next];
    return `${basePath}${buildQuery(next)}`;
  }

  return (
    <main className="sp-page">
      <h1 className="sp-h1">{dict.catalogue.heading}</h1>

      <FilterBar
        filters={filters}
        locale={locale}
        basePath={basePath}
        activeCount={activeCount}
        platformOptions={platformOptions}
        genreOptions={genreOptions}
        yearMin={yearRange?.min ?? 1958}
        yearMax={yearRange?.max ?? currentYear + 2}
        optionsUnavailable={failed}
      />

      {chips.length > 0 ? (
        <div className="sp-chip-row" aria-label={dict.catalogue.filters.heading}>
          {chips.map((c) => (
            <FilterChip
              key={c.key}
              label={c.label}
              removeHref={chipRemoveHref(c.key)}
              removeAriaLabel={`${locale === "es" ? "Quitar filtro" : "Remove filter"} ${c.label}`}
            />
          ))}
        </div>
      ) : null}

      {failed || !result ? (
        <div>
          <p role="alert">{dict.errors.retryCatalogue}</p>
          <Link href={basePath} className="sp-link">
            {dict.common.retry}
          </Link>
        </div>
      ) : (
        <>
          <p data-testid="result-count" role="status" className="sp-meta">
            {activeCount > 0
              ? formatCount(dict.catalogue.filteredCount, result.count)
              : formatCount(dict.catalogue.gamesCount, result.count)}
          </p>

          {result.results.length === 0 ? (
            <div className="sp-empty">
              {activeCount > 0 ? (
                <>
                  <p className="sp-h2" style={{ margin: 0 }}>
                    {dict.catalogue.filters.emptyHeading}
                  </p>
                  <p className="sp-lead" style={{ marginInline: "auto" }}>
                    {dict.catalogue.filters.emptyBody}
                  </p>
                  <a href={basePath} className="sp-link">
                    {dict.catalogue.filters.clearAll}
                  </a>
                </>
              ) : (
                <>
                  <p className="sp-h2" style={{ margin: 0 }}>
                    {dict.catalogue.emptyHeading}
                  </p>
                  <p className="sp-lead" style={{ marginInline: "auto" }}>
                    {dict.catalogue.emptyBody}
                  </p>
                </>
              )}
            </div>
          ) : (
            <>
              <ul className="sp-grid" style={{ marginTop: "var(--space-md)" }}>
                {result.results.map((game) => (
                  <GameCard key={game.id} game={game} locale={locale} score={game.total_rating ?? null} />
                ))}
              </ul>
              <nav aria-label={locale === "es" ? "Paginación" : "Pagination"} style={{ display: "flex", gap: "var(--space-md)", alignItems: "center", justifyContent: "center", marginTop: "var(--space-xl)" }}>
                {currentPage > 1 ? (
                  <Link href={`${basePath}${buildQuery(filters, currentPage - 1)}`}>
                    {locale === "es" ? "Anterior" : "Previous"}
                  </Link>
                ) : null}
                <span aria-current="page" style={{ color: "var(--color-accent-strong)", fontWeight: 600 }}>
                  {currentPage}
                </span>
                {result.has_next ? (
                  <Link href={`${basePath}${buildQuery(filters, currentPage + 1)}`}>
                    {locale === "es" ? "Siguiente" : "Next"}
                  </Link>
                ) : null}
              </nav>
            </>
          )}
        </>
      )}
    </main>
  );
}
