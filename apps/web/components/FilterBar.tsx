import { getDictionary } from "@/i18n";
import { FacetMenu } from "@/components/FacetMenu";
import { FilterDropdown } from "@/components/FilterDropdown";
import { FilterDropdownScript } from "@/components/FilterDropdownScript";
import {
  MIN_RATING_OPTIONS,
  type CatalogueFilters,
  type FilterOption,
} from "@/lib/catalogue-filters";

/**
 * FilterBar (01.1-UI-SPEC Screen Contract 2 / First-Party Component
 * Contracts; redesigned 2026-09-12 -- moved from a sidebar to a thin bar
 * above the results grid). A single <form method="get"> -- every control
 * is URL-shareable. Server component, no client state beyond the shared
 * <FilterDropdownScript> enhancement. Every filter besides free-text search
 * lives behind its own popover so the bar stays one row on desktop and
 * wraps onto as few rows as possible on narrow viewports; each popover
 * degrades to an always-openable native <details> without JavaScript.
 * Year and rating open straight onto a flat, single-select option list
 * (same `.sp-facet-options` markup as platform/tag) -- never a `<select>`
 * nested inside the popover. Year is a single exact value, not a range.
 * Degrades to search-only if an option list is empty.
 */
export function FilterBar({
  filters,
  locale,
  basePath,
  activeCount,
  platformOptions,
  tagOptions,
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
  tagOptions: FilterOption[];
  currentQuery: string;
  yearMin?: number;
  yearMax?: number;
  optionsUnavailable?: boolean;
}) {
  const dict = getDictionary(locale);
  const f = dict.catalogue.filters;
  const platformsUnavailable = optionsUnavailable || platformOptions.length === 0;
  const tagsUnavailable = optionsUnavailable || tagOptions.length === 0;
  const currentYear = new Date().getUTCFullYear();
  const yearCeiling = yearMax ?? currentYear + 2;
  // A single exact year, newest first (2026-09-12: was a year_from/year_to
  // range) -- a flat list, same as platform/tag, not a nested control.
  const yearOptions = Array.from({ length: Math.max(0, yearCeiling - yearMin + 1) }, (_, i) => yearCeiling - i);

  const ratingSummary = filters.min_rating ? `${filters.min_rating}+` : undefined;

  return (
    <div className="sp-filterbar sp-surface">
      <form method="get" action={basePath} className="sp-filterbar-row">
        <div className="sp-search">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="M16.5 16.5 21 21" />
          </svg>
          <label htmlFor="q" className="visually-hidden">
            {dict.catalogue.searchLabel}
          </label>
          <input id="q" name="q" type="search" placeholder={dict.catalogue.searchLabel} defaultValue={filters.q ?? ""} />
        </div>

        <FacetMenu
          name="platform"
          label={f.platform}
          options={platformOptions}
          selected={filters.platform}
          locale={locale}
          currentQuery={currentQuery}
          unavailable={platformsUnavailable}
        />

        <FacetMenu
          name="tag"
          label={f.tag}
          options={tagOptions}
          selected={filters.tag}
          locale={locale}
          currentQuery={currentQuery}
          unavailable={tagsUnavailable}
        />

        <FilterDropdown label={f.year} summary={filters.year}>
          <ul className="sp-facet-options">
            <li>
              <label className="sp-facet-option">
                <input type="radio" name="year" value="" defaultChecked={!filters.year} />
                <span>{f.anyOption}</span>
              </label>
            </li>
            {yearOptions.map((y) => (
              <li key={y}>
                <label className="sp-facet-option">
                  <input type="radio" name="year" value={y} defaultChecked={filters.year === String(y)} />
                  <span>{y}</span>
                </label>
              </li>
            ))}
          </ul>
        </FilterDropdown>

        <FilterDropdown label={f.minRating} summary={ratingSummary}>
          <ul className="sp-facet-options">
            <li>
              <label className="sp-facet-option">
                <input type="radio" name="min_rating" value="" defaultChecked={!filters.min_rating} />
                <span>{f.anyOption}</span>
              </label>
            </li>
            {MIN_RATING_OPTIONS.map((v) => (
              <li key={v}>
                <label className="sp-facet-option">
                  <input type="radio" name="min_rating" value={v} defaultChecked={filters.min_rating === v} />
                  <span>{v}+</span>
                </label>
              </li>
            ))}
          </ul>
        </FilterDropdown>

        <div className="sp-filterbar-actions">
          <button type="submit" className="sp-btn-primary">
            {f.apply}
          </button>
          {activeCount > 0 ? (
            <a href={basePath} className="sp-link">
              {f.clearAll}
            </a>
          ) : null}
          {activeCount > 0 ? <span className="sp-filterbar-count">{f.activeLabel.many(activeCount)}</span> : null}
        </div>

        {platformsUnavailable || tagsUnavailable ? (
          <p className="sp-muted sp-filterbar-note">{f.unavailable}</p>
        ) : null}
      </form>
      <FilterDropdownScript />
    </div>
  );
}
