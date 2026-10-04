import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ClearFiltersButton } from "@/components/ClearFiltersButton";
import { CollectionSidebar, type SidebarRow } from "@/components/CollectionSidebar";
import { ScrollTop } from "@/components/ScrollTop";
import { SelectedListView } from "@/components/SelectedListView";
import { GameCard } from "@/components/GameCard";
import { PaginationArrow, PaginationSpacer } from "@/components/PaginationArrow";
import { FilterDropdown } from "@/components/FilterDropdown";
import { FilterDropdownScript } from "@/components/FilterDropdownScript";
import type { BacklogStatus } from "@/components/StatusPill";
import { formatCount, getDictionary } from "@/i18n";
import { fetchMyLibrary, fetchMyLists, type GameCard as GameCardData, type MyLibraryItem } from "@/lib/api";

type RawParams = Record<string, string | string[] | undefined>;
const STATUSES: BacklogStatus[] = ["pending", "playing", "completed", "abandoned"];
// Order of the states in the left selector (design artboard "Colección con listas").
const SIDEBAR_STATUS_ORDER: BacklogStatus[] = ["playing", "pending", "completed", "abandoned"];
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

  const lists = await fetchMyLists(cookieHeader);
  const rawStatus = first(sp.status);
  const activeStatus = STATUSES.includes(rawStatus as BacklogStatus) ? (rawStatus as BacklogStatus) : "all";
  const rawList = first(sp.list);
  const activeList = lists.find((list) => list.id === rawList) ?? null;
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
  if (activeList) {
    const listedIds = new Set(activeList.items.map((item) => item.work_id));
    items = items.filter((i) => listedIds.has(i.work_id));
  }
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
    const status =
      patch.status !== undefined
        ? patch.status
        : patch.list
          ? undefined
          : activeStatus !== "all"
            ? activeStatus
            : undefined;
    const list =
      patch.list !== undefined ? patch.list : patch.status ? undefined : activeList ? activeList.id : undefined;
    const sort = patch.sort !== undefined ? patch.sort : activeSort !== "recently_updated" ? activeSort : undefined;
    const copy = patch.copy !== undefined ? patch.copy : activeCopy !== "all" ? activeCopy : undefined;
    const platinum = patch.platinum !== undefined ? patch.platinum : activePlatinum !== "all" ? activePlatinum : undefined;
    const page = patch.page;
    const q = searchText || undefined;
    if (q) params.set("q", q);
    if (status) params.set("status", status);
    if (list) params.set("list", list);
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
    (activeSort !== "recently_updated" ? 1 : 0) +
    (activeCopy !== "all" ? 1 : 0) +
    (activePlatinum !== "all" ? 1 : 0);

  const activeSortSummary = activeSort === "recently_updated" ? undefined : sortLabels[activeSort];
  const activeCopySummary =
    activeCopy === "all" ? undefined : activeCopy === "with_copy" ? dict.collection.withCopy : dict.collection.withoutCopy;
  const activePlatinumSummary =
    activePlatinum === "all"
      ? undefined
      : activePlatinum === "platinum"
        ? dict.collection.platinumOnly
        : dict.collection.notPlatinum;

  const clearBarFiltersHref = (() => {
    const params = new URLSearchParams();
    if (activeStatus !== "all") params.set("status", activeStatus);
    if (activeList) params.set("list", activeList.id);
    const query = params.toString();
    return `${basePath}${query ? `?${query}` : ""}`;
  })();
  const sidebar = dict.collection.sidebar;
  const statusRows: SidebarRow[] = [
    {
      key: "all",
      label: sidebar.all,
      count: libraryTotal,
      href: buildHref({ status: "", list: "" }),
      active: activeStatus === "all" && !activeList,
      dot: "var(--color-text-muted)",
    },
    ...SIDEBAR_STATUS_ORDER.map((st) => ({
      key: st,
      label: sidebar.statuses[st],
      count: library.summary[st] ?? 0,
      href: buildHref({ status: st }),
      active: activeStatus === st && !activeList,
      dot: `var(--color-status-${st})`,
    })),
  ];
  const listRows: SidebarRow[] = lists.map((list) => ({
    key: list.id,
    label: list.name,
    count: list.items.length,
    href: buildHref({ list: list.id }),
    active: activeList?.id === list.id,
    caption: sidebar.visibility[list.visibility],
  }));

  return (
    <main className={libraryTotal > 0 ? "sp-coll-page" : "sp-page"}>
      {libraryTotal > 0 ? (
        <CollectionSidebar
          locale={locale}
          basePath={basePath}
          ariaLabel={sidebar.ariaLabel}
          statusHeading={sidebar.status}
          statusRows={statusRows}
          listsHeading={sidebar.lists}
          listRows={listRows}
          newListLabel={sidebar.newList}
          noListsLabel={sidebar.noLists}
        />
      ) : null}
      <div className={libraryTotal > 0 ? "sp-coll-main" : undefined}>
      {libraryTotal > 0 ? (
        <div className="sp-filterbar sp-surface">
          <form method="get" action={basePath} className="sp-filterbar-row sp-filterbar-row--single">
            {activeStatus !== "all" ? <input type="hidden" name="status" value={activeStatus} /> : null}
            {activeList ? <input type="hidden" name="list" value={activeList.id} /> : null}
            <div className="sp-search">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
                <circle cx="11" cy="11" r="7" />
                <path d="M16.5 16.5 21 21" />
              </svg>
              <label htmlFor="collection-q" className="visually-hidden">{dict.catalogue.searchLabel}</label>
              <input id="collection-q" name="q" type="search" placeholder={dict.catalogue.searchLabel} defaultValue={searchText} />
            </div>

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
                <ClearFiltersButton href={clearBarFiltersHref} label={dict.catalogue.filters.clearAll} />
              ) : null}
            </div>
          </form>
          <FilterDropdownScript />
        </div>
      ) : null}

      <section aria-label={dict.collection.heading}>
      <ScrollTop watch={buildHref({ page: String(currentPage) })} />
      {libraryTotal === 0 ? (
        <p role="status" className="sp-meta">
          {formatCount(dict.collection.count, total)}
        </p>
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
      ) : pageItems.length === 0 && !activeList ? (
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
          {activeList ? (
            <SelectedListView
              key={`${activeList.id}-${activeList.items.length}`}
              locale={locale}
              listId={activeList.id}
              listName={activeList.name}
              basePath={basePath}
              excludedIds={activeList.items.map((item) => item.work_id)}
              items={pageItems.map((item) => ({
                itemId: activeList.items.find((entry) => entry.work_id === item.work_id)?.id ?? "",
                workId: item.work_id,
                game: toCardData(item),
                score: item.display_rating ?? null,
                status: STATUSES.includes(item.status as BacklogStatus) ? (item.status as BacklogStatus) : undefined,
                ratingHalfSteps: item.rating_half_steps ?? null,
                ownedCopyCount: item.owned_copy_count,
                isPlatinum: item.is_platinum === true,
              }))}
              works={library.items.map((item) => ({
                work_id: item.work_id,
                work_title: item.work_title,
                cover: item.cover ?? { url: null, is_placeholder: true, alt: item.work_title },
              }))}
            />
          ) : (
          <ul className="sp-grid sp-collection-grid">
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
          )}
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
      </div>
    </main>
  );
}
