import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { GameCard } from "@/components/GameCard";
import { StatusPill, type BacklogStatus } from "@/components/StatusPill";
import { formatCount, getDictionary } from "@/i18n";
import { fetchMyLibrary, type GameCard as GameCardData, type MyLibraryItem } from "@/lib/api";

type RawParams = Record<string, string | string[] | undefined>;
const STATUSES: BacklogStatus[] = ["pending", "playing", "completed", "abandoned"];
const SORTS = ["recently_updated", "rating_desc", "title_asc", "release_year"] as const;
type CollSort = (typeof SORTS)[number];
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
 * (URL-shareable); the backend filter wiring is Plan 03, so the list is
 * filtered/sorted in-page today.
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
  const currentPage = Math.max(1, Number(first(sp.page)) || 1);

  const total = library.items.length;

  let items = [...library.items];
  if (activeStatus !== "all") items = items.filter((i) => i.status === activeStatus);
  if (activeSort === "title_asc") {
    items.sort((a, b) => a.work_title.localeCompare(b.work_title, locale));
  } else if (activeSort === "rating_desc") {
    items.sort((a, b) => (b.rating_half_steps ?? -1) - (a.rating_half_steps ?? -1));
  } else if (activeSort === "release_year") {
    items.sort((a, b) => (b.year ?? 0) - (a.year ?? 0));
  }

  const pageCount = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const pageItems = items.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  const buildHref = (patch: Record<string, string | undefined>) => {
    const params = new URLSearchParams();
    const status = patch.status !== undefined ? patch.status : activeStatus !== "all" ? activeStatus : undefined;
    const sort = patch.sort !== undefined ? patch.sort : activeSort !== "recently_updated" ? activeSort : undefined;
    const page = patch.page;
    if (status) params.set("status", status);
    if (sort) params.set("sort", sort);
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

  return (
    <main className="sp-page">
      <h1 className="sp-h1">{dict.collection.heading}</h1>
      <p className="sp-lead">{dict.collection.subheading}</p>
      <p role="status" className="sp-meta">
        {formatCount(dict.collection.count, total)}
      </p>

      <form method="get" action={basePath} className="sp-surface sp-controls-row">
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
        <button type="submit" className="sp-btn-primary">
          {dict.catalogue.filters.apply}
        </button>
      </form>

      {total > 0 ? (
        <dl className="sp-summary-dl" aria-label={locale === "es" ? "Resumen por estado" : "Status summary"}>
          {STATUSES.map((s) => (
            <div key={s}>
              <dt>
                <StatusPill status={s} label={dict.status.labels[s]} />
              </dt>
              <dd>{formatCount(dict.collection.statusSummaryCount, library.summary[s] ?? 0)}</dd>
            </div>
          ))}
        </dl>
      ) : null}

      {total === 0 ? (
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
          <ul className="sp-grid" style={{ marginTop: "var(--space-lg)" }}>
            {pageItems.map((item) => (
              <GameCard
                key={item.work_id}
                game={toCardData(item)}
                locale={locale}
                status={STATUSES.includes(item.status as BacklogStatus) ? (item.status as BacklogStatus) : undefined}
                ratingHalfSteps={item.rating_half_steps}
                ownedCopyCount={item.owned_copy_count}
              />
            ))}
          </ul>
          {pageCount > 1 ? (
            <nav
              aria-label={locale === "es" ? "Paginación" : "Pagination"}
              style={{ display: "flex", gap: "var(--space-md)", alignItems: "center", justifyContent: "center", marginTop: "var(--space-xl)" }}
            >
              {currentPage > 1 ? (
                <Link href={buildHref({ page: String(currentPage - 1) })}>
                  {locale === "es" ? "Anterior" : "Previous"}
                </Link>
              ) : null}
              <span aria-current="page" style={{ color: "var(--color-accent-strong)", fontWeight: 600 }}>
                {currentPage}
              </span>
              {currentPage < pageCount ? (
                <Link href={buildHref({ page: String(currentPage + 1) })}>
                  {locale === "es" ? "Siguiente" : "Next"}
                </Link>
              ) : null}
            </nav>
          ) : null}
        </>
      )}
    </main>
  );
}
