import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ClearFiltersButton } from "@/components/ClearFiltersButton";
import { CustomLists } from "@/components/CustomLists";
import { GameCard } from "@/components/GameCard";
import { PaginationArrow, PaginationSpacer } from "@/components/PaginationArrow";
import { FilterDropdown } from "@/components/FilterDropdown";
import { FilterDropdownScript } from "@/components/FilterDropdownScript";
import { StatusPill, type BacklogStatus } from "@/components/StatusPill";
import { formatCount, getDictionary } from "@/i18n";
import { fetchMyLibrary, type GameCard as GameCardData, type MyLibraryItem } from "@/lib/api";

type RawParams = Record<string, string | string[] | undefined>;
const STATUSES: BacklogStatus[] = ["pending", "playing", "completed", "abandoned"];
// Display order for the per-status count summary only (2026-09-12, author
// request) -- distinct from STATUSES, which still drives the filter
// dropdown's option order.
const STATUS_SUMMARY_ORDER: BacklogStatus[] = ["completed", "playing", "pending", "abandoned"];
const SORTS = ["recently_updated", "rating_desc", "title_asc", "release_year"] as const;
type CollSort = (typeof SORTS)[number];
const COPY_FILTERS = ["all", "with_copy", "without_copy"] as const;
type CopyFilter = (typeof COPY_FILTERS)[number];
const PLATINUM_FILTERS = ["all", "platinum", "not_platinum"] as const;
type PlatinumFilter = (typeof PLATINUM_FILTERS)[number];
const PAGE_SIZE = 50;

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

function toCardData(item: MyLibraryItem): GameCardData {
  return {
    id: item.work_id,
    slug: item.work_slug,
    title: item.work_title,
    year: item.year ?? null,
    platform_summary: item.platform_summary ?? "",
    cover: item.cover ?? { url: null, is_placeholder: true, alt: item.work_title },
  };
}

/**
 * Collection (01.1-UI-SPEC Screen Contract 6, redesign). The signed-in
 * user's own library: every work they've marked, rated, or own a copy of.
 * NOT the recommendations page, NOT the public profile. Same comfortable
 * ~156px grid as the catalogue (D-UI-2), per-card status + personal
 * rating + owned-copies chip. Status filter + sort are GET-only
 * (URL-shareable); filtering and sorting are applied in-page after the
 * owner-scoped API response.
 */
export default async function CollectionPage({
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
  const basePath = `/${locale}/collection`;

  const cookieStore = await cookies();
  if (!cookieStore.has("sessionid")) {
    redirect(`/${locale}/login?next=${encodeURIComponent(`/${locale}/collection`)}`);
  }
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  let library;
  try {
    library = await fetchMyLibrary(cookieHeader);
  } catch {
    redirect(`/${locale}/login?next=${encodeURIComponent(`/${locale}/collection`)}`);
  }

  const rawStatus = first(sp.status);
  const activeStatus = STATUSES.includes(rawStatus as BacklogStatus) ? (rawStatus as BacklogStatus) : "all";
  const rawSort = first(sp.sort);
  const activeSort: CollSort = (SORTS as readonly string[]).includes(rawSort ?? "") ? (rawSort as CollSort) : "recently_updated";
  const rawCopy = first(sp.copy);
  const activeCopy: CopyFilter = (COPY_FILTERS as readonly string[]).includes(rawCopy ?? "") ? (rawCopy as CopyFilter) : "all";
  const rawPlatinum = first(sp.platinum);
  const activePlatinum: PlatinumFilter = (PLATINUM_FILTERS as readonly string[]).includes(rawPlatinum ?? "")
    ? (rawPlatinum as PlatinumFilter)
    : "all";
  const currentPage = Math.max(1, Number(first(sp.page)) || 1);
  const searchText = (first(sp.q) ?? "").trim().slice(0, 100);
  const normalizeForSearch = (value: string) =>
    value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

  let items = [...library.items];
  if (searchText) {
    const needle = normalizeForSearch(searchText);
    items = items.filter((i) => normalizeForSearch(i.work_title).includes(needle));
  }
  if (activeStatus !== "all") items = items.filter((i) => i.status === activeStatus);
  if (activeCopy === "with_copy") items = items.filter((i) => i.owned_copy_count > 0);
  if (activeCopy === "without_copy") items = items.filter((i) => i.owned_copy_count === 0);
  if (activePlatinum === "platinum") items = items.filter((i) => i.is_platinum === true);
  if (activePlatinum === "not_platinum") items = items.filter((i) => !i.is_platinum);
  if (activeSort === "title_asc") {
    items.sort((a, b) => a.work_title.localeCompare(b.work_title, locale));
  } else if (activeSort === "rating_desc") {
    items.sort((a, b) => (b.rating_half_steps ?? -1) - (a.rating_half_steps ?? -1));
  } else if (activeSort === "release_year") {
    items.sort((a, b) => (b.year ?? 0) - (a.year ?? 0));
  } else if (activeSort === "recently_updated") {
    // Default sort -- MyLibraryView returns `updated_at`; fall back to a
    // stable no-op only if an older API response omits it.
    items.sort((a, b) => (b.updated_at ?? "").localeCompare(a.updated_at ?? ""));
  }

  // The count belongs to the visible, filtered collection. The status
  // summary below remains the complete owner-scoped breakdown.
  const libraryTotal = library.items.length;
  const total = items.length;

  const pageCount = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const pageItems = items.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  const buildHref = (patch: Record<string, string | undefined>) => {
    const params = new URLSearchParams();
    const status = patch.status !== undefined ? patch.status : activeStatus !== "all" ? activeStatus : undefined;
    const sort = patch.sort !== undefined ? patch.sort : activeSort !== "recently_updated" ? activeSort : undefined;
    const copy = patch.copy !== undefined ? patch.copy : activeCopy !== "all" ? activeCopy : undefined;
    const platinum = patch.platinum !== undefined ? patch.platinum : activePlatinum !== "all" ? activePlatinum : undefined;
    const page = patch.page;
    const q = searchText || undefined;
    if (q) params.set("q", q);
    if (status) params.set("status", status);
    if (sort) params.set("sort", sort);
    if (copy) params.set("copy", copy);
    if (platinum) params.set("platinum", platinum);
    if (page && page !== "1") params.set("page", page);
    const s = params.toString();
    return `${basePath}${s ? `?${s}` : ""}`;
  };

  const sortLabels: Record<CollSort, string> = {
    recently_updated: dict.collection.sort.recentlyUpdated,
    rating_desc: dict.collection.sort.ratingDesc,
    title_asc: dict.collection.sort.titleAsc,
    release_year: dict.collection.sort.releaseYear,
  };

  const activeFilterCount =
    (searchText ? 1 : 0) +
    (activeStatus !== "all" ? 1 : 0) +
    (activeSort !== "recently_updated" ? 1 : 0) +
    (activeCopy !== "all" ? 1 : 0) +
    (activePlatinum !== "all" ? 1 : 0);

  const activeStatusSummary = activeStatus === "all" ? undefined : dict.status.labels[activeStatus];
  const activeSortSummary = activeSort === "recently_updated" ? undefined : sortLabels[activeSort];
  const activeCopySummary =
    activeCopy === "all" ? undefined : activeCopy === "with_copy" ? dict.collection.withCopy : dict.collection.withoutCopy;
  const activePlatinumSummary =
    activePlatinum === "all"
      ? undefined
      : activePlatinum === "platinum"
        ? dict.collection.platinumOnly
        : dict.collection.notPlatinum;

  return (
    <main className="sp-page">
      {libraryTotal > 0 ? (
        <div className="sp-filterbar sp-surface">
          <form method="get" action={basePath} className="sp-filterbar-row sp-filterbar-row--single">
            <div className="sp-search">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
                <circle cx="11" cy="11" r="7" />
                <path d="M16.5 16.5 21 21" />
              </svg>
              <label htmlFor="collection-q" className="visually-hidden">{dict.catalogue.searchLabel}</label>
              <input id="collection-q" name="q" type="search" placeholder={dict.catalogue.searchLabel} defaultValue={searchText} />
            </div>

            <FilterDropdown label={dict.collection.filterByStatus} summary={activeStatusSummary}>
              <ul className="sp-facet-options">
                <li>
                  <label className="sp-facet-option">
                    <input type="radio" name="status" value="" defaultChecked={activeStatus === "all"} />
                    <span>{dict.collection.allStatuses}</span>
                  </label>
                </li>
                {STATUSES.map((s) => (
                  <li key={s}>
                    <label className="sp-facet-option">
                      <input type="radio" name="status" value={s} defaultChecked={activeStatus === s} />
                      <span>{dict.status.labels[s]}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </FilterDropdown>

            <FilterDropdown label={dict.collection.sort.label} summary={activeSortSummary}>
              <ul className="sp-facet-options">
                {SORTS.map((s) => (
                  <li key={s}>
                    <label className="sp-facet-option">
                      <input type="radio" name="sort" value={s} defaultChecked={activeSort === s} />
                      <span>{sortLabels[s]}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </FilterDropdown>

            <FilterDropdown label={dict.collection.filterByCopy} summary={activeCopySummary}>
              <ul className="sp-facet-options">
                {[
                  ["all", dict.collection.allCopyStates],
                  ["with_copy", dict.collection.withCopy],
                  ["without_copy", dict.collection.withoutCopy],
                ].map(([value, text]) => (
                  <li key={value}>
                    <label className="sp-facet-option">
                      <input type="radio" name="copy" value={value} defaultChecked={activeCopy === value} />
                      <span>{text}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </FilterDropdown>

            <FilterDropdown label={dict.collection.filterByPlatinum} summary={activePlatinumSummary}>
              <ul className="sp-facet-options">
                {[
                  ["all", dict.collection.allPlatinumStates],
                  ["platinum", dict.collection.platinumOnly],
                  ["not_platinum", dict.collection.notPlatinum],
                ].map(([value, text]) => (
                  <li key={value}>
                    <label className="sp-facet-option">
                      <input type="radio" name="platinum" value={value} defaultChecked={activePlatinum === value} />
                      <span>{text}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </FilterDropdown>

            <p role="status" className="sp-meta sp-filterbar-total">
              {formatCount(dict.collection.count, total)}
            </p>

            <div className="sp-filterbar-actions">
              <button type="submit" className="sp-btn-primary">
                {dict.catalogue.filters.apply}
              </button>
              {activeFilterCount > 0 ? (
                <ClearFiltersButton href={basePath} label={dict.catalogue.filters.clearAll} />
              ) : null}
            </div>
          </form>
          <FilterDropdownScript />
        </div>
      ) : null}

      <section aria-label={dict.collection.heading}>
      {libraryTotal === 0 ? (
        <p role="status" className="sp-meta">
          {formatCount(dict.collection.count, total)}
        </p>
      ) : null}

      {libraryTotal > 0 ? (
        <dl className="sp-summary-dl" aria-label={locale === "es" ? "Resumen por estado" : "Status summary"}>
          {STATUS_SUMMARY_ORDER.map((s) => (
            <div key={s}>
              <dt>
                <StatusPill status={s} label={dict.status.labels[s]} bare />
              </dt>
              <dd>{formatCount(dict.collection.statusSummaryCount, library.summary[s] ?? 0)}</dd>
            </div>
          ))}
        </dl>
      ) : null}

      {libraryTotal === 0 ? (
        <div className="sp-empty">
          <p className="sp-h2" style={{ margin: 0 }}>
            {dict.collection.emptyHeading}
          </p>
          <p className="sp-lead" style={{ marginInline: "auto" }}>
            {dict.collection.emptyBody}
          </p>
          <Link href={`/${locale}/catalogue`} className="sp-btn-primary">
            {dict.collection.emptyCta}
          </Link>
        </div>
      ) : pageItems.length === 0 ? (
        <div className="sp-empty">
          <p className="sp-lead" style={{ marginInline: "auto" }}>
            {dict.collection.statusEmptyGroup.replace(
              "{status}",
              activeStatus === "all" ? "" : dict.status.labels[activeStatus],
            )}
          </p>
          <Link href={basePath} className="sp-link">
            {dict.collection.showAll}
          </Link>
        </div>
      ) : (
        <>
          <ul className="sp-grid sp-collection-grid" style={{ marginTop: "var(--space-lg)" }}>
            {pageItems.map((item) => (
              <GameCard
                key={item.work_id}
                game={toCardData(item)}
                locale={locale}
                score={item.display_rating}
                status={STATUSES.includes(item.status as BacklogStatus) ? (item.status as BacklogStatus) : undefined}
                ratingHalfSteps={item.rating_half_steps}
                ownedCopyCount={item.owned_copy_count}
                isPlatinum={item.is_platinum}
              />
            ))}
          </ul>
          {pageCount > 1 ? (
            <nav className="sp-pagination" aria-label={locale === "es" ? "Paginación" : "Pagination"}>
              {currentPage > 1 ? (
                <PaginationArrow
                  href={buildHref({ page: String(currentPage - 1) })}
                  direction="prev"
                  label={locale === "es" ? "Anterior" : "Previous"}
                />
              ) : (
                <PaginationSpacer />
              )}
              <span aria-current="page" className="sp-pagination-current">
                {currentPage}
              </span>
              {currentPage < pageCount ? (
                <PaginationArrow
                  href={buildHref({ page: String(currentPage + 1) })}
                  direction="next"
                  label={locale === "es" ? "Siguiente" : "Next"}
                />
              ) : (
                <PaginationSpacer />
              )}
            </nav>
          ) : null}
        </>
      )}
      </section>

      {libraryTotal > 0 ? (
        <CustomLists
          locale={locale}
          collectionItems={library.items.map((item) => ({ work_id: item.work_id, work_title: item.work_title }))}
        />
      ) : null}
    </main>
  );
}
