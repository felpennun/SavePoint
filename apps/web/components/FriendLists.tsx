"use client";

import { useMemo, useState } from "react";

import { GameCard } from "@/components/GameCard";
import { ScrollTop } from "@/components/ScrollTop";
import type { BacklogStatus } from "@/components/StatusPill";
import { getDictionary } from "@/i18n";
import type { Cover } from "@/lib/api";

interface FriendListItem {
  work_slug: string;
  title: string;
  cover: Cover;
}

export interface FriendListDto {
  name: string;
  slug: string;
  visibility: string | null;
  count: number;
  items: FriendListItem[];
}

/** The slice of the friend's collection used to dress a list's covers as full cards. */
export interface FriendListCollectionItem {
  game: { slug: string };
  year: number | null;
  platform: string;
  backlog_status: string | null;
  personal_rating: number | null;
  is_platinum: boolean;
  display_rating: number | null;
}

const STATUSES: BacklogStatus[] = ["pending", "playing", "completed", "abandoned"];
// Two rows of four games per page.
const PAGE_SIZE = 8;

const COPY = {
  es: { heading: "LISTAS", empty: "Lista vacía", noMatches: "Ningún juego coincide con la búsqueda.", pagination: "Paginación", previous: "Anterior", next: "Siguiente" },
  en: { heading: "LISTS", empty: "Empty list", noMatches: "No game matches the search.", pagination: "Pagination", previous: "Previous", next: "Next" },
} as const;

function normalize(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

/** "Listas" tab of a friend's profile: the lists on the left and, for the chosen
 * one, its games as the same cards the collection tab uses. */
export function FriendLists({
  locale,
  lists,
  collection,
}: {
  locale: "es" | "en";
  lists: FriendListDto[];
  /** The friend's collection when it is visible to the viewer, else empty. */
  collection: FriendListCollectionItem[];
}) {
  const copy = COPY[locale];
  const dict = getDictionary(locale);
  const [selected, setSelected] = useState(lists[0]?.slug ?? "");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const current = lists.find((list) => list.slug === selected) ?? lists[0];
  const bySlug = useMemo(() => new Map(collection.map((item) => [item.game.slug, item])), [collection]);

  if (!current) return null;

  const needle = normalize(query.trim());
  const items = current.items.filter((item) => !needle || normalize(item.title).includes(needle));
  const pageCount = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const visible = items.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  function choose(slug: string) {
    setSelected(slug);
    setQuery("");
    setPage(1);
  }

  return (
    <div className="sp-pf-lists-layout">
      <nav className="sp-pf-lists-side" aria-label={copy.heading}>
        <h3 className="sp-coll-side-title">{copy.heading}</h3>
        <ul className="sp-coll-side-list">
          {lists.map((list) => {
            const active = list.slug === current.slug;
            return (
              <li key={list.slug}>
                <button type="button" className={`sp-coll-side-row${active ? " is-on" : ""}`} aria-pressed={active} onClick={() => choose(list.slug)}>
                  <span className="sp-coll-side-name">
                    <span className="sp-coll-side-ellipsis">{list.name}</span>
                  </span>
                  <span className="sp-coll-side-count">{list.count}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="sp-pf-lists-main">
        {current.items.length === 0 ? (
          <p className="sp-meta">{copy.empty}</p>
        ) : (
          <>
            <div className="sp-filterbar sp-surface">
              <div className="sp-filterbar-row sp-filterbar-row--single">
                <div className="sp-search">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
                    <circle cx="11" cy="11" r="7" />
                    <path d="M16.5 16.5 21 21" />
                  </svg>
                  <label htmlFor="friend-list-q" className="visually-hidden">
                    {dict.catalogue.searchLabel}
                  </label>
                  <input
                    id="friend-list-q"
                    type="search"
                    placeholder={dict.catalogue.searchLabel}
                    value={query}
                    onChange={(event) => {
                      setQuery(event.target.value);
                      setPage(1);
                    }}
                  />
                </div>
              </div>
            </div>
            <div className="sp-pf-scroll">
              <ScrollTop watch={`${current.slug}-${currentPage}-${query}`} />
            {items.length === 0 ? (
              <p className="sp-meta" role="status">
                {copy.noMatches}
              </p>
            ) : (
              <ul className="sp-grid sp-pf-games">
                {visible.map((item) => {
                  const entry = bySlug.get(item.work_slug);
                  const status = entry?.backlog_status ?? "";
                  return (
                    <GameCard
                      key={item.work_slug}
                      locale={locale}
                      game={{
                        id: item.work_slug,
                        slug: item.work_slug,
                        title: item.title,
                        year: entry?.year ?? null,
                        platform_summary: entry?.platform ?? "",
                        cover: item.cover,
                      }}
                      status={(STATUSES as string[]).includes(status) ? (status as BacklogStatus) : undefined}
                      ratingHalfSteps={entry?.personal_rating ?? null}
                      score={entry?.display_rating ?? null}
                      isPlatinum={entry?.is_platinum ?? false}
                    />
                  );
                })}
              </ul>
            )}
            {pageCount > 1 ? (
              <nav className="sp-pagination" aria-label={copy.pagination}>
                {currentPage > 1 ? (
                  <button type="button" className="sp-pagination-arrow" aria-label={copy.previous} onClick={() => setPage(currentPage - 1)}>
                    ‹
                  </button>
                ) : (
                  <span className="sp-pagination-spacer" aria-hidden="true" />
                )}
                <span aria-current="page" className="sp-pagination-current">
                  {currentPage}
                </span>
                {currentPage < pageCount ? (
                  <button type="button" className="sp-pagination-arrow" aria-label={copy.next} onClick={() => setPage(currentPage + 1)}>
                    ›
                  </button>
                ) : (
                  <span className="sp-pagination-spacer" aria-hidden="true" />
                )}
              </nav>
            ) : null}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
