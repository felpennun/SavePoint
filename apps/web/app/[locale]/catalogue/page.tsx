import Link from "next/link";

import { FilterBar } from "@/components/FilterBar";
import { FilterChip } from "@/components/FilterChip";
import { GameCard } from "@/components/GameCard";
import { PaginationArrow } from "@/components/PaginationArrow";
import { getDictionary } from "@/i18n";
import { fetchCatalogueList } from "@/lib/api";
import {
  type FilterOption,
  buildQuery,
  countActiveFilters,
  parseFilters,
  removeHref,
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

  let result: Awaited<ReturnType<typeof fetchCatalogueList>> | null = null;
  let failed = false;
  try {
    result = await fetchCatalogueList({
      q: filters.q,
      page: currentPage,
      platform: filters.platform,
      tag: filters.tag,
      // A single exact year (2026-09-12: was a year_from/year_to range in
      // the UI) still maps onto the API's range contract as one point.
      year_from: filters.year,
      year_to: filters.year,
      min_rating: filters.min_rating,
      sort: filters.sort,
    });
  } catch {
    failed = true;
  }

  const platformOptions: FilterOption[] =
    sortPlatformOptions(result?.facets.platforms.map((p) => ({ value: p.slug, label: p.name })) ?? []);
  const tagOptions: FilterOption[] =
    result?.facets.tags.map((tag) => ({ value: tag.slug, label: tag.name })) ?? [];
  const yearRange = result?.facets.year_range;
  const platformSlugs = new Set(platformOptions.map((option) => option.value));
  const tagSlugs = new Set(tagOptions.map((option) => option.value));
  const visibleFilters = {
    ...filters,
    platform: filters.platform.filter((value) => platformSlugs.has(value)),
    tag: filters.tag.filter((value) => tagSlugs.has(value)),
  };
  const activeCount = countActiveFilters(visibleFilters);
  const platformLabels = new Map(platformOptions.map((option) => [option.value, option.label]));
  const tagLabels = new Map(tagOptions.map((option) => [option.value, option.label]));

  return (
    <main className="sp-page">
      <FilterBar
        filters={filters}
        locale={locale}
        basePath={basePath}
        activeCount={activeCount}
        platformOptions={platformOptions}
        tagOptions={tagOptions}
        currentQuery={currentQuery}
        yearMin={yearRange?.min ?? 1958}
        yearMax={yearRange?.max ?? currentYear + 2}
        optionsUnavailable={failed}
      />

      <section aria-label={dict.catalogue.heading}>
        {activeCount > 0 ? (
            <div className="sp-chip-row" aria-label={dict.catalogue.filters.activeLabel.many(activeCount)}>
              {visibleFilters.tag.map((value) => {
                const label = dict.catalogue.chip.tag.replace("{value}", tagLabels.get(value) ?? value);
                return (
                  <FilterChip
                    key={`tag-${value}`}
                    label={label}
                    removeHref={`${basePath}${removeHref(currentQuery, "tag", value)}`}
                    removeAriaLabel={`${locale === "es" ? "Quitar filtro" : "Remove filter"} ${label}`}
                  />
                );
              })}
              {visibleFilters.platform.map((value) => {
                const label = dict.catalogue.chip.platform.replace("{value}", platformLabels.get(value) ?? value);
                return (
                  <FilterChip
                    key={`platform-${value}`}
                    label={label}
                    removeHref={`${basePath}${removeHref(currentQuery, "platform", value)}`}
                    removeAriaLabel={`${locale === "es" ? "Quitar filtro" : "Remove filter"} ${label}`}
                  />
                );
              })}
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
                ) : null}
                <span aria-current="page" className="sp-pagination-current">
                  {currentPage}
                </span>
                {result.has_next ? (
                  <PaginationArrow
                    href={`${basePath}${buildQuery(visibleFilters, currentPage + 1)}`}
                    direction="next"
                    label={locale === "es" ? "Siguiente" : "Next"}
                  />
                ) : null}
              </nav>
            </>
          )}
        </>
          )}
      </section>
    </main>
  );
}
