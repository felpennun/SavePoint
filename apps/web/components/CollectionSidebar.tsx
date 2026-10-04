import { HoverPrefetchLink } from "@/components/HoverPrefetchLink";

import { SidebarNewList } from "@/components/SidebarNewList";

export interface SidebarRow {
  key: string;
  label: string;
  count: number;
  href: string;
  active: boolean;
  /** CSS colour of the little square before a status label. */
  dot?: string;
  /** Small mono caption under a list name (its visibility). */
  caption?: string;
}

/**
 * Left selector of the collection page (design artboard "Colección con
 * listas"): the fixed states on top, the user's own lists below. Every row is
 * a plain link that sets `?status=` or `?list=` -- no client state -- and the
 * active one is marked with `aria-current`.
 */
export function CollectionSidebar({
  locale,
  basePath,
  ariaLabel,
  statusHeading,
  statusRows,
  listsHeading,
  listRows,
  newListLabel,
  noListsLabel,
}: {
  locale: "es" | "en";
  basePath: string;
  ariaLabel: string;
  statusHeading: string;
  statusRows: SidebarRow[];
  listsHeading: string;
  listRows: SidebarRow[];
  newListLabel: string;
  noListsLabel: string;
}) {
  return (
    <aside className="sp-coll-side" aria-label={ariaLabel}>
      <div className="sp-coll-side-inner">
      <div className="sp-coll-side-group">
        <h2 className="sp-coll-side-title">{statusHeading}</h2>
        <ul className="sp-coll-side-list">
          {statusRows.map((row) => (
            <li key={row.key}>
              <HoverPrefetchLink eager href={row.href} className={`sp-coll-side-row${row.active ? " is-on" : ""}`} aria-current={row.active ? "true" : undefined}>
                <span className="sp-coll-side-name">
                  <span className="sp-coll-side-dot" aria-hidden="true" style={{ background: row.dot }} />
                  {row.label}
                </span>
                <span className="sp-coll-side-count">{row.count}</span>
              </HoverPrefetchLink>
            </li>
          ))}
        </ul>
      </div>

      <div className="sp-coll-side-group">
        <SidebarNewList locale={locale} heading={listsHeading} newLabel={newListLabel} basePath={basePath} />
        {listRows.length === 0 ? (
          <p className="sp-coll-side-empty">{noListsLabel}</p>
        ) : (
          <ul className="sp-coll-side-list">
            {listRows.map((row) => (
              <li key={row.key}>
                <HoverPrefetchLink eager href={row.href} className={`sp-coll-side-row${row.active ? " is-on" : ""}`} aria-current={row.active ? "true" : undefined}>
                  <span className="sp-coll-side-name sp-coll-side-name--stack">
                    <span className="sp-coll-side-ellipsis">{row.label}</span>
                    {row.caption ? <span className="sp-coll-side-caption">{row.caption}</span> : null}
                  </span>
                  <span className="sp-coll-side-count">{row.count}</span>
                </HoverPrefetchLink>
              </li>
            ))}
          </ul>
        )}
      </div>
      </div>
    </aside>
  );
}
