import { getDictionary } from "@/i18n";
import { FacetMenu } from "@/components/FacetMenu";
import { FilterDropdown } from "@/components/FilterDropdown";
import { FilterDropdownScript } from "@/components/FilterDropdownScript";
import {
  MIN_RATING_OPTIONS,
  type CatalogueFacetOptions,
  type CatalogueFilters,
  type FilterOption,
  type RepeatedFacetKey,
} from "@/lib/catalogue-filters";

const FACET_ORDER: Array<{
  name: RepeatedFacetKey;
  optionKey: keyof CatalogueFacetOptions;
  label: { es: string; en: string };
}> = [
  { name: "platform", optionKey: "platforms", label: { es: "Plataforma", en: "Platform" } },
  { name: "tag", optionKey: "tags", label: { es: "Etiquetas", en: "Tags" } },
  { name: "edition", optionKey: "editions", label: { es: "Edición", en: "Edition" } },
  { name: "genre", optionKey: "genres", label: { es: "Género", en: "Genre" } },
  { name: "franchise", optionKey: "franchises", label: { es: "Franquicia", en: "Franchise" } },
  { name: "developer", optionKey: "developers", label: { es: "Desarrollador", en: "Developer" } },
  { name: "publisher", optionKey: "publishers", label: { es: "Editorial", en: "Publisher" } },
  { name: "mode", optionKey: "modes", label: { es: "Modo", en: "Mode" } },
];

/**
 * GET-based catalogue toolbar. Every visible facet uses the local API's
 * allowlisted vocabulary and native controls, so it remains usable without
 * JavaScript and its query can be copied as a reproducible URL.
 */
export function FilterBar({
  filters,
  locale,
  basePath,
  activeCount,
  facets = {},
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
  facets?: CatalogueFacetOptions;
  /** Kept as a compatibility bridge for callers from the previous toolbar. */
  platformOptions?: FilterOption[];
  tagOptions?: FilterOption[];
  currentQuery: string;
  yearMin?: number;
  yearMax?: number;
  optionsUnavailable?: boolean;
}) {
  const dict = getDictionary(locale);
  const f = dict.catalogue.filters;
  const optionLists: CatalogueFacetOptions = {
    ...facets,
    platforms: facets.platforms ?? platformOptions ?? [],
    tags: facets.tags ?? tagOptions ?? [],
  };
  const currentYear = new Date().getUTCFullYear();
  const yearCeiling = yearMax ?? currentYear + 2;
  const yearSummary = [filters.year_from, filters.year_to].filter(Boolean).join(" – ") || undefined;
  const unavailable = optionsUnavailable;

  return (
    <div className="sp-filterbar sp-surface">
      <form method="get" action={basePath} className="sp-filterbar-row">
        <div className="sp-search">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="M16.5 16.5 21 21" />
          </svg>
          <label htmlFor="q" className="visually-hidden">{dict.catalogue.searchLabel}</label>
          <input id="q" name="q" type="search" placeholder={dict.catalogue.searchLabel} defaultValue={filters.q ?? ""} />
        </div>

        {FACET_ORDER.map(({ name, optionKey, label }) => (
          <FacetMenu
            key={name}
            name={name}
            label={name === "platform" ? f.platform : name === "tag" ? f.tag : label[locale === "en" ? "en" : "es"]}
            options={optionLists[optionKey] ?? []}
            selected={filters[name] ?? []}
            locale={locale}
            currentQuery={currentQuery}
            unavailable={unavailable}
          />
        ))}

        <FilterDropdown label={f.year} summary={yearSummary}>
          <div className="sp-dropdown-fields">
            <label htmlFor="year-from">{locale === "en" ? "From year" : "Desde año"}</label>
            <input id="year-from" name="year_from" type="number" min={yearMin} max={yearCeiling} defaultValue={filters.year_from ?? ""} />
            <label htmlFor="year-to">{locale === "en" ? "To year" : "Hasta año"}</label>
            <input id="year-to" name="year_to" type="number" min={yearMin} max={yearCeiling} defaultValue={filters.year_to ?? ""} />
          </div>
        </FilterDropdown>

        <FilterDropdown label={f.minRating} summary={filters.min_rating ? `${filters.min_rating}+` : undefined}>
          <ul className="sp-facet-options">
            <li><label className="sp-facet-option"><input type="radio" name="min_rating" value="" defaultChecked={!filters.min_rating} /><span>{f.anyOption}</span></label></li>
            {MIN_RATING_OPTIONS.map((value) => (
              <li key={value}><label className="sp-facet-option"><input type="radio" name="min_rating" value={value} defaultChecked={filters.min_rating === value} /><span>{value}+</span></label></li>
            ))}
          </ul>
        </FilterDropdown>

        <div className="sp-filterbar-actions">
          <button type="submit" className="sp-btn-primary">{f.apply}</button>
          {activeCount > 0 ? <a href={basePath} className="sp-link">{f.clearAll}</a> : null}
          {activeCount > 0 ? <span className="sp-filterbar-count">{f.activeLabel.many(activeCount)}</span> : null}
        </div>

        {unavailable ? <p className="sp-muted sp-filterbar-note">{f.unavailable}</p> : null}
      </form>
      <FilterDropdownScript />
    </div>
  );
}
