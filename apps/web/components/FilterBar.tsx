import { getDictionary } from "@/i18n";
import { FacetMenu } from "@/components/FacetMenu";
import {
  MIN_RATING_OPTIONS,
  type CatalogueFilters,
  type FilterOption,
} from "@/lib/catalogue-filters";

/**
 * FilterBar (01.1-UI-SPEC Screen Contract 2 / First-Party Component
 * Contracts). A single <form method="get"> -- every control is
 * URL-shareable. Server component, no client state. Inline above the grid
 * on desktop; a <details> disclosure on mobile (CSS in globals.css keeps
 * the DOM order identical). Degrades to search-only if an option list is
 * empty.
 */
export function FilterBar({
  filters,
  locale,
  basePath,
  activeCount,
  platformOptions,
  genreOptions,
  currentQuery,
  yearMin = 1958,
  yearMax,
  optionsUnavailable = false,
}: {
  filters: CatalogueFilters;
  locale: string;
  basePath: string;
  activeCount: number;
  platformOptions: FilterOption[];
  genreOptions: FilterOption[];
  currentQuery: string;
  yearMin?: number;
  yearMax?: number;
  optionsUnavailable?: boolean;
}) {
  const dict = getDictionary(locale);
  const f = dict.catalogue.filters;
  const platformsUnavailable = optionsUnavailable || platformOptions.length === 0;
  const genresUnavailable = optionsUnavailable || genreOptions.length === 0;
  const currentYear = new Date().getUTCFullYear();
  const yearCeiling = yearMax ?? currentYear + 2;

  return (
    <details className="sp-filterbar sp-surface" open>
      <summary>
        {f.mobileToggle.replace("{n}", String(activeCount))}
      </summary>
      <div className="sp-filterbar-head">
        <span className="sp-filterbar-title">{locale === "es" ? "Filtros" : "Filters"}</span>
        {activeCount > 0 ? (
          <span className="sp-filterbar-count">{f.activeLabel.many(activeCount)}</span>
        ) : null}
      </div>
      <form method="get" action={basePath} className="sp-filterbar-body">
        <div className="sp-field">
          <label htmlFor="q">{dict.catalogue.searchLabel}</label>
          <div className="sp-search">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="M16.5 16.5 21 21" />
            </svg>
            <input id="q" name="q" type="search" defaultValue={filters.q ?? ""} />
          </div>
        </div>

        <FacetMenu
          name="platform"
          label={f.platform}
          options={platformOptions}
          selected={filters.platform}
          semanticsText={dict.catalogue.facet.platformSemantics}
          locale={locale}
          currentQuery={currentQuery}
          unavailable={platformsUnavailable}
        />

        <FacetMenu
          name="genre"
          label={f.genre}
          options={genreOptions}
          selected={filters.genre}
          semanticsText={dict.catalogue.facet.genreSemantics}
          locale={locale}
          currentQuery={currentQuery}
          unavailable={genresUnavailable}
        />

        <div className="sp-field">
          <label htmlFor="year_from">{f.yearFrom}</label>
          <input id="year_from" name="year_from" type="number" min={yearMin} max={yearCeiling} defaultValue={filters.year_from ?? ""} />
        </div>

        <div className="sp-field">
          <label htmlFor="year_to">{f.yearTo}</label>
          <input id="year_to" name="year_to" type="number" min={yearMin} max={yearCeiling} defaultValue={filters.year_to ?? ""} />
        </div>

        <div className="sp-field">
          <label htmlFor="min_rating">{f.minRating}</label>
          <select id="min_rating" name="min_rating" defaultValue={filters.min_rating ?? ""}>
            <option value="">{f.anyOption}</option>
            {MIN_RATING_OPTIONS.map((v) => (
              <option key={v} value={v}>
                {v}+
              </option>
            ))}
          </select>
        </div>

        <div className="sp-filterbar-actions">
          <button type="submit" className="sp-btn-primary">
            {f.apply}
          </button>
          {activeCount > 0 ? (
            <a href={basePath} className="sp-link">
              {f.clearAll}
            </a>
          ) : null}
        </div>

        {platformsUnavailable || genresUnavailable ? (
          <p className="sp-muted" style={{ gridColumn: "1 / -1", margin: 0 }}>
            {f.unavailable}
          </p>
        ) : null}
      </form>
    </details>
  );
}
