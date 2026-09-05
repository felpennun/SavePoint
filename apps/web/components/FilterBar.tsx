import { getDictionary } from "@/i18n";
import {
  GENRE_OPTIONS,
  MIN_RATING_OPTIONS,
  PLATFORM_OPTIONS,
  SORT_KEYS,
  type CatalogueFilters,
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
  optionsUnavailable = false,
}: {
  filters: CatalogueFilters;
  locale: string;
  basePath: string;
  activeCount: number;
  optionsUnavailable?: boolean;
}) {
  const dict = getDictionary(locale);
  const f = dict.catalogue.filters;
  const s = dict.catalogue.sort;
  const sortLabels: Record<(typeof SORT_KEYS)[number], string> = {
    relevance: s.relevance,
    title_asc: s.titleAsc,
    title_desc: s.titleDesc,
    release_newest: s.releaseNewest,
    release_oldest: s.releaseOldest,
    rating_desc: s.ratingDesc,
  };
  const platformsUnavailable = optionsUnavailable || PLATFORM_OPTIONS.length === 0;
  const genresUnavailable = optionsUnavailable || GENRE_OPTIONS.length === 0;
  const currentYear = new Date().getUTCFullYear();

  return (
    <details className="sp-filterbar sp-surface" open>
      <summary>
        {f.mobileToggle.replace("{n}", String(activeCount))}
      </summary>
      <form method="get" action={basePath} className="sp-filterbar-body">
        <div className="sp-field">
          <label htmlFor="q">{dict.catalogue.searchLabel}</label>
          <input id="q" name="q" type="search" defaultValue={filters.q ?? ""} />
        </div>

        <div className="sp-field">
          <label htmlFor="platform">{f.platform}</label>
          <select id="platform" name="platform" defaultValue={filters.platform ?? ""} disabled={platformsUnavailable}>
            <option value="">{f.anyOption}</option>
            {PLATFORM_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        <div className="sp-field">
          <label htmlFor="genre">{f.genre}</label>
          <select id="genre" name="genre" defaultValue={filters.genre ?? ""} disabled={genresUnavailable}>
            <option value="">{f.anyOption}</option>
            {GENRE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        <div className="sp-field">
          <label htmlFor="year_from">{f.yearFrom}</label>
          <input id="year_from" name="year_from" type="number" min={1958} max={currentYear + 2} defaultValue={filters.year_from ?? ""} />
        </div>

        <div className="sp-field">
          <label htmlFor="year_to">{f.yearTo}</label>
          <input id="year_to" name="year_to" type="number" min={1958} max={currentYear + 2} defaultValue={filters.year_to ?? ""} />
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

        <div className="sp-field">
          <label htmlFor="sort">{s.label}</label>
          <select id="sort" name="sort" defaultValue={filters.sort}>
            {SORT_KEYS.map((k) => (
              <option key={k} value={k}>
                {sortLabels[k]}
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
