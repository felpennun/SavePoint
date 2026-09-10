import { formatCount, getDictionary } from "@/i18n";
import { type FilterOption, removeHref } from "@/lib/catalogue-filters";

type FacetName = "tag" | "platform";

function withoutFacet(currentQuery: string, name: FacetName): string {
  const params = new URLSearchParams(currentQuery.startsWith("?") ? currentQuery.slice(1) : currentQuery);
  params.delete(name);
  const query = params.toString();
  return query ? `?${query}` : "";
}

/**
 * A native, server-rendered disclosure for a repeated GET parameter. The
 * inline keyboard enhancement only adds Escape-to-close on desktop; the
 * checkbox list and form remain fully usable without JavaScript.
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
    <>
      <details
        className="sp-facet"
        aria-disabled={isUnavailable ? "true" : undefined}
        {...(isUnavailable ? { disabled: true } : {})}
      >
        <summary>
          <span>{label}</span>
          <span className="sp-facet-count">{selectedCountLabel}</span>
          <svg className="sp-facet-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
            <path d="m6 9 6 6 6-6" />
          </svg>
        </summary>
        <div className="sp-surface">
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
              <a href={clearHref} className="sp-link">
                {dict.catalogue.facet.clear}
              </a>
            </>
          )}
        </div>
      </details>
      <script
        dangerouslySetInnerHTML={{
          __html: `(() => {
            const script = document.currentScript;
            const details = script && script.previousElementSibling;
            if (!details || details.getAttribute("aria-disabled") === "true") return;
            const summary = details.querySelector("summary");
            details.addEventListener("keydown", (event) => {
              if (event.key === "Escape" && window.matchMedia("(min-width: 48rem)").matches) {
                details.open = false;
                summary && summary.focus();
              }
            });
          })();`,
        }}
      />
    </>
  );
}

export function facetChipHref(currentQuery: string, name: FacetName, value: string): string {
  return removeHref(currentQuery, name, value);
}
