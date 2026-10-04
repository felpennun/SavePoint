import Link from "next/link";
import { cookies } from "next/headers";

import { FilterBar } from "@/components/FilterBar";
import { localizedGenreLabel } from "@/lib/genre-labels";
import { FilterChip } from "@/components/FilterChip";
import { GameCard } from "@/components/GameCard";
import { ScrollTop } from "@/components/ScrollTop";
import { PaginationArrow, PaginationSpacer } from "@/components/PaginationArrow";
import { getDictionary } from "@/i18n";
import { fetchCatalogueList } from "@/lib/api";
import {
  type FilterOption,
  type CatalogueFacetOptions,
  REPEATED_FACET_KEYS,
  buildQuery,
  countActiveFilters,
  parseFilters,
  removeHref,
  restrictSelectedFilters,
  sortPlatformOptions,
} from "@/lib/catalogue-filters";

type RawParams = Record<string, string | string[] | undefined>;

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

function toQueryString(params: RawParams): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    for (const item of Array.isArray(value) ? value : value == null ? [] : [value]) {
      query.append(key, item);
    }
  }
  return query.toString();
}

/**
 * Catalogue (01.1-UI-SPEC Screen Contract 2, CAT-02). Server component,
 * searchParams-driven, every control submits via GET so each filtered view
 * is a shareable/bookmarkable URL — no client-only filter state. The
 * platform/tag checkbox options and the year-input bounds come from the
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
  const filters = parseFilters(sp, currentYear);
  const currentPage = Math.max(1, Number(first(sp.page)) || 1);
  const basePath = `/${locale}/catalogue`;
  const currentQuery = toQueryString(sp);
  const cookieHeader = (await cookies()).toString();

  let result: Awaited<ReturnType<typeof fetchCatalogueList>> | null = null;
  let failed = false;
  try {
    result = await fetchCatalogueList({
      q: filters.q,
      page: currentPage,
      platform: filters.platform,
      tag: filters.tag,
      edition: filters.edition,
      genre: filters.genre,
      franchise: filters.franchise,
      developer: filters.developer,
      publisher: filters.publisher,
      mode: filters.mode,
      year_from: filters.year_from,
      year_to: filters.year_to,
      date_from: filters.date_from,
      date_to: filters.date_to,
      min_rating: filters.min_rating,
      sort: filters.sort,
    }, cookieHeader);
  } catch {
    // A rejected filter (for example an out-of-range year) must not take the
    // toolbar down with it: load the plain catalogue for its filter options and
    // show "no games match" for the rejected combination instead.
    try {
      const base = await fetchCatalogueList({ page: 1 }, cookieHeader);
      result = { ...base, results: [], count: 0, has_next: false };
    } catch {
      failed = true;
    }
  }

  const platformOptions: FilterOption[] = sortPlatformOptions(
    result?.facets.platforms.map((p) => ({ value: p.slug, label: p.name })) ?? [],
  );
  const facetOptions: CatalogueFacetOptions = result
    ? {
        platforms: platformOptions,
        tags: result.facets.tags.map((facet) => ({ value: facet.slug, label: localizedGenreLabel(facet.slug, facet.name, locale) })).sort((a, b) => a.label.localeCompare(b.label, locale)),
        editions: result.facets.editions.map((facet) => ({ value: facet.slug, label: facet.name })),
        genres: result.facets.genres.map((facet) => ({ value: facet.slug, label: localizedGenreLabel(facet.slug, facet.name, locale) })).sort((a, b) => a.label.localeCompare(b.label, locale)),
        franchises: result.facets.franchises.map((facet) => ({ value: facet.slug, label: facet.name })),
        developers: result.facets.developers.map((facet) => ({ value: facet.slug, label: facet.name })),
        publishers: result.facets.publishers.map((facet) => ({ value: facet.slug, label: facet.name })),
        modes: result.facets.modes.map((facet) => ({ value: facet.slug, label: facet.name })),
      }
    : {};
  const yearRange = result?.facets.year_range;
  const visibleFilters = result ? restrictSelectedFilters(filters, facetOptions) : filters;
  const activeCount = countActiveFilters(visibleFilters);
  const facetLabels: Record<string, string> = locale === "en"
    ? { platform: "Platform", tag: "Genre", edition: "Edition", genre: "Genre", franchise: "Franchise", developer: "Developer", publisher: "Publisher", mode: "Mode" }
    : { platform: "Plataforma", tag: "Género", edition: "Edición", genre: "Género", franchise: "Franquicia", developer: "Desarrollador", publisher: "Editorial", mode: "Modo" };
  const facetValueLabels = Object.fromEntries(
    REPEATED_FACET_KEYS.map((key) => {
      const optionKey = `${key}s` as keyof CatalogueFacetOptions;
      return [key, new Map((facetOptions[optionKey] ?? []).map((option) => [option.value, option.label]))];
    }),
  ) as Record<string, Map<string, string>>;

  return (
    <main className="sp-page sp-fixed-page">
      <FilterBar
        filters={filters}
        locale={locale}
        basePath={basePath}
        activeCount={activeCount}
        facets={facetOptions}
        currentQuery={currentQuery}
        yearMin={yearRange?.min ?? 1950}
        yearMax={yearRange?.max ?? currentYear + 2}
        optionsUnavailable={failed}
      />

      <section aria-label={dict.catalogue.heading}>
        <ScrollTop watch={`${currentQuery}-${currentPage}`} />
        {activeCount > 0 ? (
            <div className="sp-chip-row" aria-label={dict.catalogue.filters.activeLabel.many(activeCount)}>
              {REPEATED_FACET_KEYS.flatMap((key) =>
                (visibleFilters[key] ?? []).map((value) => {
                  const label = `${facetLabels[key]}: ${facetValueLabels[key]?.get(value) ?? value}`;
                  return (
                    <FilterChip
                      key={`${key}-${value}`}
                      label={label}
                      removeHref={`${basePath}${removeHref(currentQuery, key, value)}`}
                      removeAriaLabel={`${locale === "es" ? "Quitar filtro" : "Remove filter"} ${label}`}
                    />
                  );
                }),
              )}
            </div>
          ) : null}
          {failed || !result ? (
        <div className="sp-empty sp-empty--error">
          <span className="sp-error-badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
            error
          </span>
          <p className="sp-h2" role="alert" style={{ margin: 0 }}>
            {dict.errors.retryCatalogue}
          </p>
          <Link href={basePath} className="sp-btn-primary">
            {dict.common.retry}
          </Link>
        </div>
          ) : (
        <>
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
                  <svg className="sp-empty-mark" width="40" height="40" viewBox="0 0 48 48" fill="none" aria-hidden="true">
                    <path d="M6 12a6 6 0 0 1 6-6h20l10 10v20a6 6 0 0 1-6 6H12a6 6 0 0 1-6-6V12Z" stroke="currentColor" strokeWidth="2.5" />
                    <path d="M24 15l8 9-8 9-8-9 8-9Z" fill="currentColor" />
                  </svg>
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
                  <GameCard key={game.id} game={game} locale={locale} score={game.display_rating ?? null} />
                ))}
              </ul>
              <nav className="sp-pagination" aria-label={locale === "es" ? "Paginación" : "Pagination"}>
                {currentPage > 1 ? (
                  <PaginationArrow
                    href={`${basePath}${buildQuery(visibleFilters, currentPage - 1)}`}
                    direction="prev"
                    label={locale === "es" ? "Anterior" : "Previous"}
                  />
                ) : (
                  <PaginationSpacer />
                )}
                <span aria-current="page" className="sp-pagination-current">
                  {currentPage}
                </span>
                {result.has_next ? (
                  <PaginationArrow
                    href={`${basePath}${buildQuery(visibleFilters, currentPage + 1)}`}
                    direction="next"
                    label={locale === "es" ? "Siguiente" : "Next"}
                  />
                ) : (
                  <PaginationSpacer />
                )}
              </nav>
            </>
          )}
        </>
          )}
      </section>
    </main>
  );
}
