import { getDictionary } from "@/i18n";
import { FilterDropdown } from "@/components/FilterDropdown";
import { type FilterOption, type RepeatedFacetKey, removeHref } from "@/lib/catalogue-filters";

type FacetName = RepeatedFacetKey;

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
  unavailable = false,
}: {
  name: FacetName;
  label: string;
  options: FilterOption[];
  selected: string[];
  locale: string;
  unavailable?: boolean;
}) {
  const dict = getDictionary(locale);
  const isUnavailable = unavailable || options.length === 0;
  const selectedCountLabel = selected.length > 0 ? String(selected.length) : undefined;

  return (
    <FilterDropdown label={label} summary={selectedCountLabel} unavailable={isUnavailable} className="sp-facet">
      {isUnavailable ? (
        <p className="sp-muted" role="status">
          {dict.catalogue.filters.unavailable}
        </p>
      ) : (
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
      )}
    </FilterDropdown>
  );
}

export function facetChipHref(currentQuery: string, name: FacetName, value: string): string {
  return removeHref(currentQuery, name, value);
}
