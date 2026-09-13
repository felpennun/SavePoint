import { formatCount, getDictionary } from "@/i18n";
import { FilterDropdown } from "@/components/FilterDropdown";
import { type FilterOption, type RepeatedFacetKey, removeHref } from "@/lib/catalogue-filters";

type FacetName = RepeatedFacetKey;

function withoutFacet(currentQuery: string, name: FacetName): string {
  const params = new URLSearchParams(currentQuery.startsWith("?") ? currentQuery.slice(1) : currentQuery);
  params.delete(name);
  const query = params.toString();
  return query ? `?${query}` : "";
}

/**
 * A repeated-GET-parameter checkbox list, rendered as one popover in the
 * filter toolbar via <FilterDropdown> (outside-click/Escape handled once,
 * document-wide, by <FilterDropdownScript> in the toolbar that hosts this).
 * The checkbox list and form remain fully usable without JavaScript.
 */
export function FacetMenu({
  name,
  label,
  options,
  selected,
  locale,
  currentQuery,
  unavailable = false,
}: {
  name: FacetName;
  label: string;
  options: FilterOption[];
  selected: string[];
  locale: string;
  currentQuery: string;
  unavailable?: boolean;
}) {
  const dict = getDictionary(locale);
  const isUnavailable = unavailable || options.length === 0;
  const selectedCountLabel = formatCount(dict.catalogue.facet.selectedCount, selected.length);
  const clearHref = withoutFacet(currentQuery, name);

  return (
    <FilterDropdown label={label} summary={selectedCountLabel} unavailable={isUnavailable} className="sp-facet">
      {isUnavailable ? (
        <p className="sp-muted" role="status">
          {dict.catalogue.filters.unavailable}
        </p>
      ) : (
        <>
          <ul className="sp-facet-options">
            {options.map((option) => (
              <li key={option.value}>
                <label className="sp-facet-option">
                  <input
                    type="checkbox"
                    name={name}
                    value={option.value}
                    defaultChecked={selected.includes(option.value)}
                    disabled={isUnavailable}
                  />
                  <span>{option.label}</span>
                </label>
              </li>
            ))}
          </ul>
          <div className="sp-filterbar-actions">
            <button type="submit" className="sp-btn-primary">
              {dict.catalogue.filters.apply}
            </button>
            <a href={clearHref} className="sp-link">
              {dict.catalogue.facet.clear}
            </a>
          </div>
        </>
      )}
    </FilterDropdown>
  );
}

export function facetChipHref(currentQuery: string, name: FacetName, value: string): string {
  return removeHref(currentQuery, name, value);
}
