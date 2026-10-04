"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { FilterDropdown } from "@/components/FilterDropdown";
import { FilterDropdownScript } from "@/components/FilterDropdownScript";
import { FriendLists } from "@/components/FriendLists";
import { ScrollTop } from "@/components/ScrollTop";

import { CoverImage } from "@/components/CoverImage";
import { GameCard } from "@/components/GameCard";
import type { BacklogStatus } from "@/components/StatusPill";
import { formatCount, getDictionary } from "@/i18n";
import { presetGradient } from "@/lib/avatar-presets";
import type { Cover } from "@/lib/api";
import { apiFetch } from "@/lib/client-api";
import { PROFILE_TABS, type ProfileTab } from "@/lib/profile-navigation";

type Locale = "es" | "en";

interface FavoriteDto {
  work_slug: string;
  title: string;
  year: number | null;
  cover: Cover;
}

interface CollectionItem {
  game: { slug: string; title: string };
  cover: Cover;
  year: number | null;
  platform: string;
  backlog_status: string | null;
  personal_rating: number | null;
  is_platinum: boolean;
  updated_at: string;
  display_rating: number | null;
}

const SORTS = ["recently_updated", "rating_desc", "title_asc", "release_year"] as const;
type CollectionSort = (typeof SORTS)[number];
const PLATINUM_FILTERS = ["all", "platinum", "not_platinum"] as const;

interface CollectionFilters {
  q: string;
  status: "all" | BacklogStatus;
  sort: CollectionSort;
  platinum: (typeof PLATINUM_FILTERS)[number];
}

const DEFAULT_FILTERS: CollectionFilters = { q: "", status: "all", sort: "recently_updated", platinum: "all" };

function normalizeForSearch(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

interface ListDto {
  name: string;
  slug: string;
  visibility: string | null;
  count: number;
  items: Array<{ work_slug: string; title: string; cover: Cover }>;
}

interface CommentDto {
  work_slug: string;
  title: string;
  cover: Cover;
  text: string;
  date: string;
}

interface ProfileDto {
  alias: string;
  relationship: "friend" | "self" | "none" | "pending_sent" | "pending_received";
  display_name: string;
  bio: string;
  avatar_url: string;
  avatar_image_url: string;
  avatar_preset: number | null;
  cover_image_url: string;
  member_since: string;
  favorites_visible: boolean;
  favorites: Array<FavoriteDto | null>;
  collection_visible: boolean;
  summary: { games: number; completed: number; playing: number; pending: number; abandoned: number } | null;
  collection: CollectionItem[];
  lists: ListDto[];
  comments: CommentDto[];
}

// Two rows of five games per page.
const PAGE_SIZE = 10;
const STATUSES: BacklogStatus[] = ["pending", "playing", "completed", "abandoned"];

const COPY = {
  es: {
    loading: "Cargando perfil…",
    unavailableTitle: "Perfil no disponible",
    unavailableBody: "Este perfil no existe o no puedes verlo.",
    toFriends: "Amistades",
    tabsLabel: "Secciones del perfil",
    tabs: { profile: "Perfil", collection: "Colección", lists: "Listas", comments: "Comentarios" },
    memberSince: (date: string) => `miembro desde ${date}`,
    games: (count: number) => `${count} ${count === 1 ? "juego" : "juegos"}`,
    recommend: "Recomendarle un juego",
    editProfile: "Editar perfil",
    fullName: "Nombre completo",
    username: "Nombre de usuario",
    bio: "Biografía",
    noBio: "Sin biografía.",
    favorites: "Favoritos",
    unavailable: {
      favorites: ["Favoritos no disponibles", (name: string) => `${name} no comparte sus favoritos.`],
      collection: ["Colección no disponible", (name: string) => `${name} no comparte su colección.`],
      lists: ["Sin listas disponibles", (name: string) => `${name} no tiene listas visibles para ti.`],
      comments: ["Sin comentarios disponibles", (name: string) => `${name} no tiene comentarios visibles para ti.`],
    },
    emptyCollection: "Todavía no tiene juegos en su colección.",
    noMatches: "Ningún juego coincide con los filtros.",
    summaryHeading: "RESUMEN",
    stats: { completed: "Completados", playing: "Jugando", pending: "Pendientes", abandoned: "Abandonados" },
    statsUnavailable: "No comparte su colección.",
    listItems: (count: number) => `${count} ${count === 1 ? "juego" : "juegos"}`,
    emptyList: "Lista vacía",
    pagination: "Paginación",
    previous: "Anterior",
    next: "Siguiente",
  },
  en: {
    loading: "Loading profile…",
    unavailableTitle: "Profile not available",
    unavailableBody: "This profile does not exist or you cannot see it.",
    toFriends: "Friends",
    tabsLabel: "Profile sections",
    tabs: { profile: "Profile", collection: "Collection", lists: "Lists", comments: "Comments" },
    memberSince: (date: string) => `member since ${date}`,
    games: (count: number) => `${count} ${count === 1 ? "game" : "games"}`,
    recommend: "Recommend a game",
    editProfile: "Edit profile",
    fullName: "Full name",
    username: "Username",
    bio: "Biography",
    noBio: "No biography.",
    favorites: "Favorites",
    unavailable: {
      favorites: ["Favorites not available", (name: string) => `${name} does not share their favorites.`],
      collection: ["Collection not available", (name: string) => `${name} does not share their collection.`],
      lists: ["No lists available", (name: string) => `${name} has no lists visible to you.`],
      comments: ["No comments available", (name: string) => `${name} has no comments visible to you.`],
    },
    emptyCollection: "No games in their collection yet.",
    noMatches: "No game matches the filters.",
    summaryHeading: "SUMMARY",
    stats: { completed: "Completed", playing: "Playing", pending: "Pending", abandoned: "Abandoned" },
    statsUnavailable: "Does not share their collection.",
    listItems: (count: number) => `${count} ${count === 1 ? "game" : "games"}`,
    emptyList: "Empty list",
    pagination: "Pagination",
    previous: "Previous",
    next: "Next",
  },
} as const;

function initialsOf(name: string): string {
  const parts = name.split(/[\s._-]+/).filter(Boolean).slice(0, 2);
  return (parts.map((part) => part[0]?.toUpperCase() ?? "").join("") || name.slice(0, 2).toUpperCase()).slice(0, 2);
}

function Unavailable({ title, body }: { title: string; body: string }) {
  return (
    <div className="sp-pf-unavailable" role="status">
      <span className="sp-pf-unavailable-icon" aria-hidden="true">
        <svg width="22" height="22" viewBox="0 0 256 256" fill="currentColor">
          <path d="M208 80h-32V56a48 48 0 0 0-96 0v24H48a16 16 0 0 0-16 16v112a16 16 0 0 0 16 16h160a16 16 0 0 0 16-16V96a16 16 0 0 0-16-16ZM96 56a32 32 0 0 1 64 0v24H96Zm112 152H48V96h160v112Z" />
        </svg>
      </span>
      <strong>{title}</strong>
      <span>{body}</span>
    </div>
  );
}

function Chevron({ direction }: { direction: "prev" | "next" }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={direction === "prev" ? { transform: "scaleX(-1)" } : undefined}
    >
      <path d="M9 5l7 7-7 7" />
    </svg>
  );
}

/** The detailed, read-only profile of a friend: the same layout as the editable
 * profile (cover, photo, name, tabs), with profile, collection, lists and
 * comments. Whatever the owner keeps private is announced as not available. */
export function FriendProfile({
  locale,
  alias,
  initialTab,
}: {
  locale: Locale;
  alias: string;
  initialTab: ProfileTab;
}) {
  const copy = COPY[locale];
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "ready" | "missing">("loading");
  const [profile, setProfile] = useState<ProfileDto | null>(null);
  const [tab, setTab] = useState<ProfileTab>(initialTab);
  const [page, setPage] = useState(1);
  const [photoFailed, setPhotoFailed] = useState(false);
  // The collection toolbar works like the real collection page: the controls
  // edit a draft, and "Apply filters" (or Enter in the search box) applies it.
  const [draft, setDraft] = useState<CollectionFilters>(DEFAULT_FILTERS);
  const [applied, setApplied] = useState<CollectionFilters>(DEFAULT_FILTERS);

  useEffect(() => {
    let cancelled = false;
    apiFetch(`/api/social/friends/${encodeURIComponent(alias)}/profile/`)
      .then(async (response) => {
        if (cancelled) return;
        if (!response.ok) {
          setStatus("missing");
          return;
        }
        const body = (await response.json()) as ProfileDto;
        if (body.relationship !== "friend" && body.relationship !== "self") {
          // Not a friend yet: the friends page shows the basic profile and the actions.
          router.replace(`/${locale}/friends?alias=${encodeURIComponent(alias)}`);
          return;
        }
        setProfile(body);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("missing");
      });
    return () => {
      cancelled = true;
    };
  }, [alias, locale, router]);

  // Filter dropdowns close on an outside click, Escape and when another opens.
  // (The shared inline script only runs on server-rendered pages.)
  useEffect(() => {
    const w = window as unknown as { __spFilterDropdownInit?: boolean };
    if (w.__spFilterDropdownInit) return;
    w.__spFilterDropdownInit = true;
    const openDropdowns = () => document.querySelectorAll("details.sp-dropdown[open]");
    document.addEventListener("click", (event) => {
      openDropdowns().forEach((d) => {
        if (!d.contains(event.target as Node)) d.removeAttribute("open");
      });
    });
    document.addEventListener(
      "toggle",
      (event) => {
        const el = event.target as HTMLDetailsElement | null;
        if (!(el && el.matches && el.matches("details.sp-dropdown") && el.open)) return;
        openDropdowns().forEach((d) => {
          if (d !== el) d.removeAttribute("open");
        });
      },
      true,
    );
    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      const open = document.querySelector("details.sp-dropdown[open]");
      if (!open) return;
      open.removeAttribute("open");
      (open.querySelector("summary") as HTMLElement | null)?.focus();
    });
  }, []);

  const filteredCollection = useMemo(() => {
    if (!profile) return [];
    let items = [...profile.collection];
    const needle = normalizeForSearch(applied.q.trim());
    if (needle) items = items.filter((item) => normalizeForSearch(item.game.title).includes(needle));
    if (applied.status !== "all") items = items.filter((item) => item.backlog_status === applied.status);
    if (applied.platinum === "platinum") items = items.filter((item) => item.is_platinum);
    if (applied.platinum === "not_platinum") items = items.filter((item) => !item.is_platinum);
    if (applied.sort === "title_asc") items.sort((a, b) => a.game.title.localeCompare(b.game.title, locale));
    else if (applied.sort === "rating_desc") items.sort((a, b) => (b.personal_rating ?? -1) - (a.personal_rating ?? -1));
    else if (applied.sort === "release_year") items.sort((a, b) => (b.year ?? 0) - (a.year ?? 0));
    else items.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
    return items;
  }, [profile, applied, locale]);

  const memberSince = useMemo(() => {
    if (!profile) return "";
    return new Intl.DateTimeFormat(locale, { month: "short", year: "numeric" }).format(new Date(profile.member_since));
  }, [profile, locale]);

  if (status === "loading") return <p aria-live="polite">{copy.loading}</p>;
  if (status === "missing" || !profile) {
    return (
      <div role="alert">
        <h1 className="sp-h1">{copy.unavailableTitle}</h1>
        <p>{copy.unavailableBody}</p>
        <Link href={`/${locale}/friends`} className="sp-btn-primary">
          {copy.toFriends}
        </Link>
      </div>
    );
  }

  const name = profile.display_name || profile.alias;
  const isSelf = profile.relationship === "self";
  const photoSrc =
    profile.avatar_image_url || (profile.avatar_url.startsWith("https://") ? profile.avatar_url : "");
  const gradient = presetGradient(profile.avatar_preset);
  const dict = getDictionary(locale);
  const pageCount = Math.max(1, Math.ceil(filteredCollection.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const visibleGames = filteredCollection.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  const sortLabels: Record<CollectionSort, string> = {
    recently_updated: dict.collection.sort.recentlyUpdated,
    rating_desc: dict.collection.sort.ratingDesc,
    title_asc: dict.collection.sort.titleAsc,
    release_year: dict.collection.sort.releaseYear,
  };
  const platinumLabels: Record<(typeof PLATINUM_FILTERS)[number], string> = {
    all: dict.collection.allPlatinumStates,
    platinum: dict.collection.platinumOnly,
    not_platinum: dict.collection.notPlatinum,
  };
  const activeFilterCount =
    (applied.q.trim() ? 1 : 0) +
    (applied.status !== "all" ? 1 : 0) +
    (applied.sort !== "recently_updated" ? 1 : 0) +
    (applied.platinum !== "all" ? 1 : 0);
  function applyFilters(event: React.FormEvent) {
    event.preventDefault();
    setApplied(draft);
    setPage(1);
  }
  function clearFilters() {
    setDraft(DEFAULT_FILTERS);
    setApplied(DEFAULT_FILTERS);
    setPage(1);
  }
  const counts: Record<ProfileTab, number | null> = {
    profile: null,
    collection: profile.collection_visible ? profile.collection.length : null,
    lists: profile.lists.length,
    comments: profile.comments.length,
  };
  const dateFormat = new Intl.DateTimeFormat(locale, { dateStyle: "medium" });

  function onTabKey(event: React.KeyboardEvent<HTMLButtonElement>, index: number) {
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    event.preventDefault();
    const next = PROFILE_TABS[(index + step + PROFILE_TABS.length) % PROFILE_TABS.length];
    setTab(next);
    document.getElementById(`fp-tab-${next}`)?.focus();
  }

  return (
    <div className={`sp-pf sp-pf--friend${tab === "collection" || tab === "lists" || tab === "comments" ? " is-fixed" : ""}`}>
      <div className="sp-pf-card">
        <div
          className="sp-pf-banner"
          style={profile.cover_image_url ? { backgroundImage: `url(${profile.cover_image_url})` } : undefined}
        />

        <div className="sp-pf-head">
          <div className="sp-pf-identity">
            <div className="sp-pf-avatar-wrap">
              <div className="sp-pf-avatar" style={gradient && !photoSrc ? { backgroundImage: gradient } : undefined} aria-hidden="true">
                {photoSrc && !photoFailed ? (
                  // eslint-disable-next-line @next/next/no-img-element -- the friend's photo (own endpoint or their https URL)
                  <img src={photoSrc} alt="" width={112} height={112} onError={() => setPhotoFailed(true)} />
                ) : (
                  <span>{initialsOf(name)}</span>
                )}
              </div>
            </div>
            <div className="sp-pf-who">
              <h1>{name}</h1>
              <span className="sp-pf-meta">
                @{profile.alias} · {copy.memberSince(memberSince)}
                {profile.summary ? ` · ${copy.games(profile.summary.games)}` : ""}
              </span>
            </div>
          </div>
          <div className="sp-pf-head-actions">
            <Link href={`/${locale}/friends`} className="sp-pf-action">
              {copy.toFriends}
            </Link>
            {isSelf ? (
              <Link href={`/${locale}/profile`} className="sp-pf-save">
                {copy.editProfile}
              </Link>
            ) : (
              <Link href={`/${locale}/friends?alias=${encodeURIComponent(profile.alias)}`} className="sp-pf-save">
                {copy.recommend}
              </Link>
            )}
          </div>
        </div>

        <div className="sp-pf-tabs" role="tablist" aria-label={copy.tabsLabel}>
          {PROFILE_TABS.map((id, index) => (
            <button
              key={id}
              id={`fp-tab-${id}`}
              type="button"
              role="tab"
              aria-selected={tab === id}
              aria-controls={`fp-panel-${id}`}
              tabIndex={tab === id ? 0 : -1}
              className={tab === id ? "is-on" : undefined}
              onClick={() => setTab(id)}
              onKeyDown={(event) => onTabKey(event, index)}
            >
              {copy.tabs[id]}
              {counts[id] !== null ? <span className="sp-pf-tab-count"> {counts[id]}</span> : null}
            </button>
          ))}
        </div>

        <div className={`sp-pf-body${tab === "profile" ? "" : " sp-pf-body--single"}`}>
          <div className="sp-pf-main" role="tabpanel" id={`fp-panel-${tab}`} aria-labelledby={`fp-tab-${tab}`}>
            {tab === "profile" ? (
              <>
                <div className="sp-pf-two">
                  <div className="sp-pf-field">
                    <span>{copy.fullName}</span>
                    <span className="sp-pf-value">{profile.display_name || "—"}</span>
                  </div>
                  <div className="sp-pf-field">
                    <span>{copy.username}</span>
                    <span className="sp-pf-value is-mono">@{profile.alias}</span>
                  </div>
                </div>
                <div className="sp-pf-field">
                  <span>{copy.bio}</span>
                  <span className="sp-pf-value is-text">{profile.bio || copy.noBio}</span>
                </div>
                <div className="sp-pf-field">
                  <span>{copy.favorites}</span>
                  {profile.favorites_visible ? (
                    <ol className="sp-pf-favs sp-pf-favs-view">
                      {profile.favorites.map((favorite, index) => (
                        <li key={index}>
                          {favorite ? (
                            <Link href={`/${locale}/games/${favorite.work_slug}`} className="sp-pf-fav is-filled" title={favorite.title}>
                              <CoverImage src={favorite.cover.url} alt="" title={favorite.title} missingLabel="" width={84} height={112} />
                              <span className="visually-hidden">{favorite.title}</span>
                            </Link>
                          ) : (
                            <span className="sp-pf-fav" aria-hidden="true" />
                          )}
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <Unavailable title={copy.unavailable.favorites[0]} body={copy.unavailable.favorites[1](name)} />
                  )}
                </div>
              </>
            ) : null}

            {tab === "collection" ? (
              !profile.collection_visible ? (
                <Unavailable title={copy.unavailable.collection[0]} body={copy.unavailable.collection[1](name)} />
              ) : profile.collection.length === 0 ? (
                <p className="sp-meta">{copy.emptyCollection}</p>
              ) : (
                <>
                  <div className="sp-filterbar sp-surface">
                    <form className="sp-filterbar-row sp-filterbar-row--single" onSubmit={applyFilters}>
                      <div className="sp-search">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
                          <circle cx="11" cy="11" r="7" />
                          <path d="M16.5 16.5 21 21" />
                        </svg>
                        <label htmlFor="friend-collection-q" className="visually-hidden">
                          {dict.catalogue.searchLabel}
                        </label>
                        <input
                          id="friend-collection-q"
                          type="search"
                          placeholder={dict.catalogue.searchLabel}
                          value={draft.q}
                          onChange={(event) => setDraft({ ...draft, q: event.target.value })}
                        />
                      </div>

                      <FilterDropdownScript />
                      <FilterDropdown
                        label={dict.collection.filterByStatus}
                        summary={draft.status === "all" ? undefined : dict.status.labels[draft.status]}
                      >
                        <ul className="sp-facet-options">
                          <li>
                            <label className="sp-facet-option">
                              <input type="radio" name="status" checked={draft.status === "all"} onChange={() => setDraft({ ...draft, status: "all" })} />
                              <span>{dict.collection.allStatuses}</span>
                            </label>
                          </li>
                          {STATUSES.map((value) => (
                            <li key={value}>
                              <label className="sp-facet-option">
                                <input type="radio" name="status" checked={draft.status === value} onChange={() => setDraft({ ...draft, status: value })} />
                                <span>{dict.status.labels[value]}</span>
                              </label>
                            </li>
                          ))}
                        </ul>
                      </FilterDropdown>

                      <FilterDropdown
                        label={dict.collection.sort.label}
                        summary={draft.sort === "recently_updated" ? undefined : sortLabels[draft.sort]}
                      >
                        <ul className="sp-facet-options">
                          {SORTS.map((value) => (
                            <li key={value}>
                              <label className="sp-facet-option">
                                <input type="radio" name="sort" checked={draft.sort === value} onChange={() => setDraft({ ...draft, sort: value })} />
                                <span>{sortLabels[value]}</span>
                              </label>
                            </li>
                          ))}
                        </ul>
                      </FilterDropdown>

                      <FilterDropdown
                        label={dict.collection.filterByPlatinum}
                        summary={draft.platinum === "all" ? undefined : platinumLabels[draft.platinum]}
                      >
                        <ul className="sp-facet-options">
                          {PLATINUM_FILTERS.map((value) => (
                            <li key={value}>
                              <label className="sp-facet-option">
                                <input type="radio" name="platinum" checked={draft.platinum === value} onChange={() => setDraft({ ...draft, platinum: value })} />
                                <span>{platinumLabels[value]}</span>
                              </label>
                            </li>
                          ))}
                        </ul>
                      </FilterDropdown>

                      <p role="status" className="sp-meta sp-filterbar-total">
                        {formatCount(dict.collection.count, filteredCollection.length)}
                      </p>

                      <div className="sp-filterbar-actions">
                        <button type="submit" className="sp-btn-primary">
                          {dict.catalogue.filters.apply}
                        </button>
                        {activeFilterCount > 0 ? (
                          <button
                            type="button"
                            className="sp-btn-clear"
                            aria-label={dict.catalogue.filters.clearAll}
                            title={dict.catalogue.filters.clearAll}
                            onClick={clearFilters}
                          >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                              <path d="M3 6h18" />
                              <path d="M8 6V4h8v2" />
                              <path d="M6 6l1 14h10l1-14" />
                              <path d="M10 11v5M14 11v5" />
                            </svg>
                          </button>
                        ) : null}
                      </div>
                    </form>
                  </div>
                  <div className="sp-pf-scroll">
                    <ScrollTop watch={`${currentPage}-${applied.q}-${applied.status}-${applied.sort}-${applied.platinum}`} />
                  {filteredCollection.length === 0 ? (
                    <p className="sp-meta" role="status">
                      {copy.noMatches}
                    </p>
                  ) : null}
                  <ul className="sp-grid sp-pf-games">
                    {visibleGames.map((item) => (
                      <GameCard
                        key={item.game.slug}
                        locale={locale}
                        game={{
                          id: item.game.slug,
                          slug: item.game.slug,
                          title: item.game.title,
                          year: item.year,
                          platform_summary: item.platform,
                          cover: item.cover,
                        }}
                        status={(STATUSES as string[]).includes(item.backlog_status ?? "") ? (item.backlog_status as BacklogStatus) : undefined}
                        ratingHalfSteps={item.personal_rating}
                        score={item.display_rating}
                        isPlatinum={item.is_platinum}
                      />
                    ))}
                  </ul>
                  {pageCount > 1 ? (
                    <nav className="sp-pagination" aria-label={copy.pagination}>
                      {currentPage > 1 ? (
                        <button type="button" className="sp-pagination-arrow" aria-label={copy.previous} onClick={() => setPage(currentPage - 1)}>
                          <Chevron direction="prev" />
                        </button>
                      ) : (
                        <span className="sp-pagination-spacer" aria-hidden="true" />
                      )}
                      <span aria-current="page" className="sp-pagination-current">
                        {currentPage}
                      </span>
                      {currentPage < pageCount ? (
                        <button type="button" className="sp-pagination-arrow" aria-label={copy.next} onClick={() => setPage(currentPage + 1)}>
                          <Chevron direction="next" />
                        </button>
                      ) : (
                        <span className="sp-pagination-spacer" aria-hidden="true" />
                      )}
                    </nav>
                  ) : null}
                  </div>
                </>
              )
            ) : null}

            {tab === "lists" ? (
              profile.lists.length === 0 ? (
                <Unavailable title={copy.unavailable.lists[0]} body={copy.unavailable.lists[1](name)} />
              ) : (
                <FriendLists
                  locale={locale}
                  lists={profile.lists}
                  collection={profile.collection_visible ? profile.collection : []}
                />
              )
            ) : null}

            {tab === "comments" ? (
              profile.comments.length === 0 ? (
                <Unavailable title={copy.unavailable.comments[0]} body={copy.unavailable.comments[1](name)} />
              ) : (
                <ul className="sp-pf-comments sp-pf-scroll">
                  {profile.comments.map((comment, index) => (
                    <li key={`${comment.work_slug}-${index}`}>
                      <Link href={`/${locale}/games/${comment.work_slug}`} className="sp-pf-comment-cover" tabIndex={-1} aria-hidden="true">
                        <CoverImage src={comment.cover.url} alt="" title={comment.title} missingLabel="" width={48} height={64} />
                      </Link>
                      <div className="sp-pf-comment-main">
                        <div className="sp-pf-comment-head">
                          <Link href={`/${locale}/games/${comment.work_slug}`}>{comment.title}</Link>
                          <span className="sp-pf-tab-count">{dateFormat.format(new Date(comment.date))}</span>
                        </div>
                        <p>{comment.text}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              )
            ) : null}
          </div>

          {tab === "profile" ? (
            <aside className="sp-pf-side">
              <div className="sp-pf-panel">
                <div className="sp-pf-eyebrow">{copy.summaryHeading}</div>
                {profile.summary ? (
                  <div className="sp-pf-stats">
                    {(["completed", "playing", "pending", "abandoned"] as const).map((key) => (
                      <div key={key}>
                        <strong>{profile.summary?.[key] ?? 0}</strong>
                        <span>{copy.stats[key]}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="sp-pf-note" style={{ margin: 0 }}>
                    {copy.statsUnavailable}
                  </p>
                )}
              </div>
            </aside>
          ) : null}
        </div>
      </div>
    </div>
  );
}
