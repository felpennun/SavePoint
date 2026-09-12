import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { CustomLists } from "@/components/CustomLists";
import { GameCard } from "@/components/GameCard";
import { PaginationArrow } from "@/components/PaginationArrow";
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
const PAGE_SIZE = 48;

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
  const currentPage = Math.max(1, Number(first(sp.page)) || 1);

  let items = [...library.items];
  if (activeStatus !== "all") items = items.filter((i) => i.status === activeStatus);
  if (activeCopy === "with_copy") items = items.filter((i) => i.owned_copy_count > 0);
  if (activeCopy === "without_copy") items = items.filter((i) => i.owned_copy_count === 0);
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
    const page = patch.page;
    if (status) params.set("status", status);
    if (sort) params.set("sort", sort);
    if (copy) params.set("copy", copy);
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

  const activeStatusSummary = activeStatus === "all" ? undefined : dict.status.labels[activeStatus];
  const activeSortSummary = activeSort === "recently_updated" ? undefined : sortLabels[activeSort];
  const activeCopySummary =
    activeCopy === "all" ? undefined : activeCopy === "with_copy" ? dict.collection.withCopy : dict.collection.withoutCopy;

  return (
    <main className="sp-page">
      {libraryTotal > 0 ? (
        <div className="sp-filterbar sp-surface">
          <form method="get" action={basePath} className="sp-filterbar-row">
            <FilterDropdown label={dict.collection.filterByStatus} summary={activeStatusSummary}>
              <div className="sp-field">
                <label htmlFor="status">{dict.collection.filterByStatus}</label>
                <select id="status" name="status" defaultValue={activeStatus === "all" ? "" : activeStatus}>
                  <option value="">{dict.collection.allStatuses}</option>
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {dict.status.labels[s]}
                    </option>
                  ))}
                </select>
              </div>
            </FilterDropdown>

            <FilterDropdown label={dict.collection.sort.label} summary={activeSortSummary}>
              <div className="sp-field">
                <label htmlFor="sort">{dict.collection.sort.label}</label>
                <select id="sort" name="sort" defaultValue={activeSort}>
                  {SORTS.map((s) => (
                    <option key={s} value={s}>
                      {sortLabels[s]}
                    </option>
                  ))}
                </select>
              </div>
            </FilterDropdown>

            <FilterDropdown label={dict.collection.filterByCopy} summary={activeCopySummary}>
              <div className="sp-field">
                <label htmlFor="copy">{dict.collection.filterByCopy}</label>
                <select id="copy" name="copy" defaultValue={activeCopy}>
                  <option value="all">{dict.collection.allCopyStates}</option>
                  <option value="with_copy">{dict.collection.withCopy}</option>
                  <option value="without_copy">{dict.collection.withoutCopy}</option>
                </select>
              </div>
            </FilterDropdown>

            <div className="sp-filterbar-actions">
              <button type="submit" className="sp-btn-primary">
                {dict.catalogue.filters.apply}
              </button>
            </div>
          </form>
          <FilterDropdownScript />
        </div>
      ) : null}

      <section aria-label={dict.collection.heading}>
      <p role="status" className="sp-meta">
        {formatCount(dict.collection.count, total)}
      </p>

      {libraryTotal > 0 ? (
        <a href="/api/library/export/collection.csv" className="sp-link" download>
          {locale === "es" ? "Exportar colección a CSV" : "Export collection to CSV"}
        </a>
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
              ) : null}
              <span aria-current="page" className="sp-pagination-current">
                {currentPage}
              </span>
              {currentPage < pageCount ? (
                <PaginationArrow
                  href={buildHref({ page: String(currentPage + 1) })}
                  direction="next"
                  label={locale === "es" ? "Siguiente" : "Next"}
                />
              ) : null}
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
