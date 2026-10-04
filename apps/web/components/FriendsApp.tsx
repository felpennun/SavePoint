"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { CoverImage } from "@/components/CoverImage";
import { GamePicker } from "@/components/GamePicker";
import { apiFetch } from "@/lib/client-api";
import type { Cover } from "@/lib/api";

type Locale = "es" | "en";
type Relationship = "none" | "pending_sent" | "pending_received" | "friend" | "blocked" | "self";
type NotifTab = "all" | "rec" | "req";

interface FriendDto {
  alias: string;
  display_name: string;
  has_avatar_image: boolean;
}

interface RequestDto {
  id: string;
  sender_alias: string;
  receiver_alias: string;
}

interface SearchAccount {
  alias: string;
  avatar_url: string;
  display_name: string;
  relationship: Relationship;
}

interface FavoriteDto {
  work_id: string;
  work_slug: string;
  title: string;
  year: number | null;
  platform_summary: string;
  cover: Cover;
}

interface CardDto {
  alias: string;
  relationship: Relationship;
  request_id?: string;
  display_name?: string;
  bio?: string;
  avatar_url?: string;
  avatar_image_url?: string;
  favorites_visible?: boolean;
  collection_visible?: boolean;
  favorites?: Array<FavoriteDto | null>;
  summary?: { games: number; completed: number; playing: number; pending: number; abandoned: number } | null;
  owned_work_ids?: string[] | null;
}

interface NotifDto {
  id: string;
  kind: "request" | "rec" | "accepted" | "rec_added";
  actor: { alias: string; name: string; is_friend: boolean };
  work: { id: string; title: string; slug: string } | null;
  note: string;
  state: string;
  read: boolean;
  date: string;
  request_id?: string;
  message_id?: string;
}

interface OwnGame {
  work_id: string;
  work_title: string;
  cover: Cover;
}

const AVATAR_HUES = ["#5c4f9e", "#3f5f86", "#6b3540", "#3d6a52", "#7a5a2d", "#4a5470"];

const COPY = {
  es: {
    heading: "Amistades",
    loading: "Cargando amistades…",
    loadError: "No se pudo cargar esta información. Inténtalo de nuevo.",
    retry: "Reintentar",
    searchHeading: "BUSCAR PERSONA",
    searchPlaceholder: "nombre de usuario",
    searchHint: "Escribe el nombre de usuario completo.",
    noResultTitle: "Nadie con ese nombre de usuario exacto.",
    noResultBody: "Comprueba el nombre completo e inténtalo de nuevo.",
    friendsHeading: (n: number) => `AMISTADES · ${n}`,
    sentHeading: (n: number) => `ENVIADAS · ${n}`,
    pendingBadge: "PENDIENTE",
    friendsEmpty: "Todavía no tienes amistades. Busca un nombre de usuario exacto para enviar una solicitud.",
    actions: {
      send: "Enviar solicitud",
      sent: "Solicitud enviada",
      accept: "Aceptar solicitud",
      view: "Ver perfil",
      cancel: "Cancelar solicitud",
      self: "Eres tú",
    },
    friendBadge: "AMISTAD",
    recommend: "Recomendarle un juego",
    recommendTo: (name: string) => `Recomendar a ${name}`,
    close: "Cerrar",
    pickGame: "Juego de tu colección",
    chooseGame: "Elegir juego",
    changeGame: "Cambiar",
    pickerTitle: (name: string) => `Recomendar a ${name}`,
    alreadyHas: (name: string) => `${name} ya tiene este juego en su colección.`,
    note: "Nota",
    optional: "(opcional)",
    notePlaceholder: "Por qué crees que le va a gustar",
    send: "Enviar recomendación",
    sending: "Enviando…",
    sentConfirm: (game: string, name: string) => `✓ Enviaste ${game} a ${name}. Le llegará como notificación.`,
    cooldown: (days: number) =>
      `Ya le recomendaste un juego esta semana. Podrás volver a hacerlo en ${days} ${days === 1 ? "día" : "días"}.`,
    sendError: "No se pudo enviar la recomendación. Inténtalo de nuevo.",
    favorites: "Favoritos",
    favoritesOf: (filled: number) => `${filled} DE 5`,
    favoritesHidden: "Esta persona no comparte sus favoritos.",
    collectionHidden: "Esta persona no comparte su colección.",
    summary: { completed: "completados", playing: "jugando", pending: "pendientes" },
    removeFriend: "Eliminar amistad",
    block: "Bloquear",
    confirmRemoveTitle: (name: string) => `¿Eliminar a ${name} de tus amistades?`,
    confirmBlockTitle: (name: string) => `¿Bloquear a ${name}?`,
    confirmBody: "Dejaréis de ver el contenido compartido y se ocultarán vuestras recomendaciones.",
    confirm: "Confirmar",
    cancelDialog: "Cancelar",
    basicProfile: "perfil básico",
    lock: {
      none: (alias: string) => [`Agrega a @${alias} para ver su perfil`, "Sus favoritos, su colección y sus listas solo son visibles para sus amistades. Mientras tanto ves su nombre de usuario y su avatar."],
      pending_sent: (_alias: string) => ["Solicitud enviada", "Cuando la acepte verás sus favoritos y podréis enviaros recomendaciones."],
      pending_received: (alias: string) => [`@${alias} quiere añadirte`, "Acepta la solicitud para ver su perfil y que vea el tuyo."],
      self: (_alias: string) => ["Este es tu perfil", "Así te ven tus amistades. Puedes cambiarlo desde Editar perfil."],
    },
    editProfile: "Editar perfil",
    pickPerson: "Elige una amistad de la lista o busca a alguien por su nombre de usuario.",
    notifications: "Notificaciones",
    markAll: "Marcar como leídas",
    unread: "Sin leer",
    tabs: { all: "Todas", rec: "Recomendaciones", req: "Solicitudes" },
    empty: "Nada nuevo por aquí.",
    kindText: {
      request: "quiere añadirte como amistad",
      rec: "te recomienda",
      accepted: "aceptó tu solicitud de amistad",
      rec_added: "añadió a pendientes tu recomendación:",
    },
    notifActions: {
      request: ["Aceptar", "Rechazar"],
      rec: ["Añadir a pendientes", "Descartar"],
    },
    done: {
      accepted: "✓ AHORA SOIS AMISTADES",
      rejected: "SOLICITUD RECHAZADA",
      added: "✓ AÑADIDO A PENDIENTES",
      dismissed: "RECOMENDACIÓN DESCARTADA",
    } as Record<string, string>,
    when: {
      now: "ahora",
      minutes: (n: number) => `hace ${n} min`,
      hours: (n: number) => `hace ${n} h`,
      yesterday: "ayer",
      days: (n: number) => `hace ${n} días`,
    },
    actionError: "No se pudo completar la acción. Inténtalo de nuevo.",
  },
  en: {
    heading: "Friends",
    loading: "Loading friends…",
    loadError: "This information could not be loaded. Try again.",
    retry: "Retry",
    searchHeading: "FIND A PERSON",
    searchPlaceholder: "username",
    searchHint: "Type the complete username.",
    noResultTitle: "Nobody with that exact username.",
    noResultBody: "Check the complete name and try again.",
    friendsHeading: (n: number) => `FRIENDS · ${n}`,
    sentHeading: (n: number) => `SENT · ${n}`,
    pendingBadge: "PENDING",
    friendsEmpty: "You do not have any friends yet. Search for an exact username to send a request.",
    actions: {
      send: "Send request",
      sent: "Request sent",
      accept: "Accept request",
      view: "View profile",
      cancel: "Cancel request",
      self: "That is you",
    },
    friendBadge: "FRIEND",
    recommend: "Recommend a game",
    recommendTo: (name: string) => `Recommend to ${name}`,
    close: "Close",
    pickGame: "Game from your collection",
    chooseGame: "Choose a game",
    changeGame: "Change",
    pickerTitle: (name: string) => `Recommend to ${name}`,
    alreadyHas: (name: string) => `${name} already has this game in their collection.`,
    note: "Note",
    optional: "(optional)",
    notePlaceholder: "Why you think they will like it",
    send: "Send recommendation",
    sending: "Sending…",
    sentConfirm: (game: string, name: string) => `✓ You sent ${game} to ${name}. It will arrive as a notification.`,
    cooldown: (days: number) =>
      `You already recommended a game this week. You can do it again in ${days} ${days === 1 ? "day" : "days"}.`,
    sendError: "The recommendation could not be sent. Try again.",
    favorites: "Favorites",
    favoritesOf: (filled: number) => `${filled} OF 5`,
    favoritesHidden: "This person does not share their favorites.",
    collectionHidden: "This person does not share their collection.",
    summary: { completed: "completed", playing: "playing", pending: "pending" },
    removeFriend: "Remove friend",
    block: "Block",
    confirmRemoveTitle: (name: string) => `Remove ${name} from your friends?`,
    confirmBlockTitle: (name: string) => `Block ${name}?`,
    confirmBody: "You will stop seeing each other's shared content and your recommendations will be hidden.",
    confirm: "Confirm",
    cancelDialog: "Cancel",
    basicProfile: "basic profile",
    lock: {
      none: (alias: string) => [`Add @${alias} to see their profile`, "Their favorites, collection and lists are only visible to their friends. Meanwhile you see their username and avatar."],
      pending_sent: (_alias: string) => ["Request sent", "Once they accept it you will see their favorites and you can send each other recommendations."],
      pending_received: (alias: string) => [`@${alias} wants to add you`, "Accept the request to see their profile and let them see yours."],
      self: (_alias: string) => ["This is your profile", "This is how your friends see you. You can change it from Edit profile."],
    },
    editProfile: "Edit profile",
    pickPerson: "Pick a friend from the list or search for someone by username.",
    notifications: "Notifications",
    markAll: "Mark as read",
    unread: "Unread",
    tabs: { all: "All", rec: "Recommendations", req: "Requests" },
    empty: "Nothing new here.",
    kindText: {
      request: "wants to add you as a friend",
      rec: "recommends",
      accepted: "accepted your friend request",
      rec_added: "added your recommendation to their backlog:",
    },
    notifActions: {
      request: ["Accept", "Reject"],
      rec: ["Add to backlog", "Dismiss"],
    },
    done: {
      accepted: "✓ YOU ARE NOW FRIENDS",
      rejected: "REQUEST REJECTED",
      added: "✓ ADDED TO BACKLOG",
      dismissed: "RECOMMENDATION DISMISSED",
    } as Record<string, string>,
    when: {
      now: "now",
      minutes: (n: number) => `${n} min ago`,
      hours: (n: number) => `${n} h ago`,
      yesterday: "yesterday",
      days: (n: number) => `${n} days ago`,
    },
    actionError: "The action could not be completed. Try again.",
  },
} as const;

function initialsOf(name: string): string {
  const parts = name.split(/[\s._-]+/).filter(Boolean).slice(0, 2);
  return (parts.map((part) => part[0]?.toUpperCase() ?? "").join("") || name.slice(0, 2).toUpperCase()).slice(0, 2);
}

function hueOf(alias: string): string {
  let hash = 0;
  for (const char of alias) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return AVATAR_HUES[hash % AVATAR_HUES.length];
}


function relativeTime(iso: string, copy: (typeof COPY)[Locale]): string {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (minutes < 1) return copy.when.now;
  if (minutes < 60) return copy.when.minutes(minutes);
  const hours = Math.round(minutes / 60);
  if (hours < 24) return copy.when.hours(hours);
  const days = Math.round(hours / 24);
  return days === 1 ? copy.when.yesterday : copy.when.days(days);
}

function Avatar({
  alias,
  name,
  size,
  imageSrc,
}: {
  alias: string;
  name: string;
  size: number;
  imageSrc?: string;
}) {
  const [failed, setFailed] = useState(false);
  const showImage = Boolean(imageSrc) && !failed;
  return (
    <span
      className="sp-fr-avatar"
      aria-hidden="true"
      style={{
        width: size,
        height: size,
        fontSize: size > 40 ? 18 : 12,
        backgroundImage: `linear-gradient(150deg, ${hueOf(alias)}, var(--fr-line))`,
      }}
    >
      {showImage ? (
        // eslint-disable-next-line @next/next/no-img-element -- own-origin profile photo
        <img src={imageSrc} alt="" width={size} height={size} onError={() => setFailed(true)} />
      ) : (
        initialsOf(name)
      )}
    </span>
  );
}

function publishUnread(count: number) {
  window.dispatchEvent(new CustomEvent("savepoint:social-unread-count", { detail: { count } }));
}

/** The friends page (artboard 2d): search and the friend list on the left, the
 * selected person's profile in the middle and the notifications on the right. */
export function FriendsApp({ locale, initialAlias }: { locale: Locale; initialAlias: string }) {
  const copy = COPY[locale];
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [friends, setFriends] = useState<FriendDto[]>([]);
  const [requests, setRequests] = useState<{ received: RequestDto[]; sent: RequestDto[] }>({ received: [], sent: [] });
  const [notifs, setNotifs] = useState<NotifDto[]>([]);
  const [ownGames, setOwnGames] = useState<OwnGame[]>([]);
  const [selected, setSelected] = useState<string | null>(initialAlias.trim() || null);
  const [card, setCard] = useState<CardDto | null>(null);
  const [cardLoading, setCardLoading] = useState(false);
  const [query, setQuery] = useState(initialAlias.trim());
  const [searchResult, setSearchResult] = useState<SearchAccount | null>(null);
  const [searched, setSearched] = useState(false);
  const [notifTab, setNotifTab] = useState<NotifTab>("all");
  const [feedback, setFeedback] = useState<string | null>(null);

  // Recommend panel.
  const [recOpen, setRecOpen] = useState(false);
  const [recGame, setRecGame] = useState<OwnGame | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [recNote, setRecNote] = useState("");
  const [recBusy, setRecBusy] = useState(false);
  const [recMessage, setRecMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(null);

  // Confirmation for removing / blocking a friend.
  const [confirmAction, setConfirmAction] = useState<"remove" | "block" | null>(null);
  const confirmRef = useRef<HTMLDialogElement>(null);

  const loadSocial = useCallback(async () => {
    const [friendsResponse, requestsResponse, notificationsResponse] = await Promise.all([
      apiFetch("/api/social/friendships/"),
      apiFetch("/api/social/requests/"),
      apiFetch("/api/social/notifications/"),
    ]);
    if (!friendsResponse.ok || !requestsResponse.ok || !notificationsResponse.ok) throw new Error("social");
    const friendsBody = await friendsResponse.json();
    const requestsBody = await requestsResponse.json();
    const notificationsBody = await notificationsResponse.json();
    setFriends(friendsBody.friends ?? []);
    setRequests({ received: requestsBody.received ?? [], sent: requestsBody.sent ?? [] });
    setNotifs(notificationsBody.notifications ?? []);
    if (typeof notificationsBody.unread === "number") publishUnread(notificationsBody.unread);
  }, []);

  const loadCard = useCallback(async (alias: string) => {
    setCardLoading(true);
    try {
      const response = await apiFetch(`/api/social/friends/${encodeURIComponent(alias)}/`);
      setCard(response.ok ? ((await response.json()) as CardDto) : null);
    } catch {
      setCard(null);
    } finally {
      setCardLoading(false);
    }
  }, []);

  const runSearch = useCallback(async (alias: string) => {
    const response = await apiFetch(`/api/social/search/?alias=${encodeURIComponent(alias)}`);
    if (!response.ok) {
      setSearchResult(null);
      setSearched(true);
      return;
    }
    const body = await response.json();
    setSearchResult((body.results?.[0] as SearchAccount | undefined) ?? null);
    setSearched(true);
  }, []);

  // First load.
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      loadSocial(),
      apiFetch("/api/library/entries/")
        .then((response) => (response.ok ? response.json() : null))
        .then((body) => {
          if (!cancelled && body && Array.isArray(body.items)) {
            setOwnGames(
              body.items.map((item: { work_id: string; work_title: string; cover: Cover }) => ({
                work_id: item.work_id,
                work_title: item.work_title,
                cover: item.cover,
              })),
            );
          }
        }),
    ])
      .then(() => {
        if (!cancelled) setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [loadSocial]);

  // Preselect the first friend when nothing was requested in the URL.
  useEffect(() => {
    if (status === "ready" && selected === null && friends.length > 0) setSelected(friends[0].alias);
  }, [status, selected, friends]);

  useEffect(() => {
    if (selected) void loadCard(selected);
    else setCard(null);
    setRecOpen(false);
    setRecGame(null);
    setRecNote("");
    setPickerOpen(false);
    setRecMessage(null);
  }, [selected, loadCard]);

  // Exact-alias search while typing (debounced).
  useEffect(() => {
    const alias = query.trim().replace(/^@/, "");
    if (!alias) {
      setSearchResult(null);
      setSearched(false);
      return;
    }
    const timer = window.setTimeout(() => {
      void runSearch(alias).catch(() => {});
    }, 350);
    return () => window.clearTimeout(timer);
  }, [query, runSearch]);

  useEffect(() => {
    const dialog = confirmRef.current;
    if (!dialog) return;
    if (confirmAction && !dialog.open) dialog.showModal();
    if (!confirmAction && dialog.open) dialog.close();
  }, [confirmAction]);

  async function refreshAfterAction(aliasToSelect?: string) {
    try {
      await loadSocial();
      const trimmed = query.trim().replace(/^@/, "");
      if (trimmed) await runSearch(trimmed);
      const target = aliasToSelect ?? selected;
      if (aliasToSelect) setSelected(aliasToSelect);
      else if (target) await loadCard(target);
    } catch {
      setFeedback(copy.actionError);
    }
  }

  async function act(path: string, body?: unknown, aliasToSelect?: string): Promise<boolean> {
    setFeedback(null);
    try {
      const response = await apiFetch(path, { method: "POST", body });
      if (!response.ok) {
        setFeedback(copy.actionError);
        return false;
      }
      await refreshAfterAction(aliasToSelect);
      return true;
    } catch {
      setFeedback(copy.actionError);
      return false;
    }
  }

  const sendRequest = (alias: string) => act("/api/social/requests/", { alias });
  const cancelRequest = (requestId: string) => act(`/api/social/requests/${requestId}/cancel/`);
  const acceptRequest = (requestId: string, alias: string) =>
    act(`/api/social/requests/${requestId}/accept/`, undefined, alias);
  const rejectRequest = (requestId: string) => act(`/api/social/requests/${requestId}/reject/`);

  async function markAllRead() {
    await act("/api/social/notifications/read-all/");
  }

  async function sendRecommendation() {
    if (!card || !recGame) return;
    setRecBusy(true);
    setRecMessage(null);
    try {
      const response = await apiFetch("/api/social/recommendations/", {
        method: "POST",
        body: { recipient_alias: card.alias, work_id: recGame.work_id, text: recNote.trim() },
      });
      if (response.status === 429) {
        const body = (await response.json().catch(() => null)) as { retry_after_seconds?: number } | null;
        const days = Math.max(1, Math.ceil((body?.retry_after_seconds ?? 86400) / 86400));
        setRecMessage({ kind: "error", text: copy.cooldown(days) });
        return;
      }
      if (!response.ok) {
        setRecMessage({ kind: "error", text: copy.sendError });
        return;
      }
      setRecMessage({ kind: "ok", text: copy.sentConfirm(recGame.work_title, firstName) });
      setRecOpen(false);
      setRecGame(null);
      setRecNote("");
    } catch {
      setRecMessage({ kind: "error", text: copy.sendError });
    } finally {
      setRecBusy(false);
    }
  }

  async function confirmFriendAction() {
    const action = confirmAction;
    setConfirmAction(null);
    if (!action || !card) return;
    const ok = await act(
      action === "remove"
        ? `/api/social/friendships/${encodeURIComponent(card.alias)}/remove/`
        : `/api/social/friendships/${encodeURIComponent(card.alias)}/block/`,
    );
    if (ok) setSelected(null);
  }

  const shownTab = (tab: NotifTab, item: NotifDto): boolean =>
    tab === "all" ||
    (tab === "rec" && (item.kind === "rec" || item.kind === "rec_added")) ||
    (tab === "req" && (item.kind === "request" || item.kind === "accepted"));
  const visibleNotifs = useMemo(() => notifs.filter((item) => shownTab(notifTab, item)), [notifs, notifTab]);

  const cardName = card ? card.display_name || card.alias : "";
  const firstName = cardName.split(" ")[0] || cardName;
  const isFriendCard = card?.relationship === "friend";
  const alreadyHas = Boolean(recGame && card?.owned_work_ids?.includes(recGame.work_id));

  if (status === "loading") return <p aria-live="polite">{copy.loading}</p>;
  if (status === "error") {
    return (
      <div role="alert">
        <p>{copy.loadError}</p>
        <button type="button" className="sp-btn-primary" onClick={() => window.location.reload()}>
          {copy.retry}
        </button>
      </div>
    );
  }

  // ---- left column: search result
  const searchAlias = query.trim().replace(/^@/, "");
  const result = searchResult;
  const resultRequestId = result
    ? result.relationship === "pending_received"
      ? requests.received.find((item) => item.sender_alias === result.alias)?.id
      : result.relationship === "pending_sent"
        ? requests.sent.find((item) => item.receiver_alias === result.alias)?.id
        : undefined
    : undefined;

  function resultAction() {
    if (!result) return;
    if (result.relationship === "none") void sendRequest(result.alias);
    else if (result.relationship === "pending_received" && resultRequestId) void acceptRequest(resultRequestId, result.alias);
  }

  const resultLabel: Record<string, [string, boolean]> = {
    none: [copy.actions.send, true],
    pending_sent: [copy.actions.sent, false],
    pending_received: [copy.actions.accept, true],
    friend: [copy.actions.view, true],
    self: [copy.actions.self, false],
  };

  // ---- center: lock text for non-friends
  const lock =
    card && card.relationship !== "friend" && card.relationship in copy.lock
      ? copy.lock[card.relationship as keyof typeof copy.lock](card.alias)
      : null;

  function lockAction() {
    if (!card) return;
    if (card.relationship === "none") void sendRequest(card.alias);
    else if (card.relationship === "pending_sent" && card.request_id) void cancelRequest(card.request_id);
    else if (card.relationship === "pending_received" && card.request_id) void acceptRequest(card.request_id, card.alias);
  }
  const lockLabel: Record<string, string> = {
    none: copy.actions.send,
    pending_sent: copy.actions.cancel,
    pending_received: copy.actions.accept,
  };

  const favorites = card?.favorites ?? [];
  const filledFavorites = favorites.filter(Boolean).length;
  const summary = card?.summary;

  return (
    <div className="sp-fr">
      <div className="sp-fr-card">
        <div className="sp-fr-grid">
          {/* ---- left: search + friends ---- */}
          <aside className="sp-fr-left">
            <div className="sp-fr-block">
              <label className="sp-fr-eyebrow" htmlFor="fr-search">
                {copy.searchHeading}
              </label>
              <div className="sp-fr-search">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
                  <circle cx="11" cy="11" r="7" />
                  <path d="M16.5 16.5 21 21" />
                </svg>
                <span aria-hidden="true">@</span>
                <input
                  id="fr-search"
                  type="search"
                  value={query}
                  autoComplete="off"
                  spellCheck={false}
                  placeholder={copy.searchPlaceholder}
                  onChange={(event) => setQuery(event.target.value)}
                />
              </div>
              <span className="sp-fr-hint">{copy.searchHint}</span>
            </div>

            <div aria-live="polite">
              {result ? (
                <div className="sp-fr-result">
                  {(() => {
                    const identity = (
                      <>
                        <Avatar
                          alias={result.alias}
                          name={result.display_name || result.alias}
                          size={40}
                          imageSrc={
                            friends.find((friend) => friend.alias === result.alias)?.has_avatar_image
                              ? `/api/accounts/profiles/${encodeURIComponent(result.alias)}/avatar/`
                              : undefined
                          }
                        />
                        <span className="sp-fr-who">
                          <span>{result.display_name || result.alias}</span>
                          <span className="sp-fr-mono">@{result.alias}</span>
                        </span>
                      </>
                    );
                    const profileHref = `/${locale}/profiles/${encodeURIComponent(result.alias)}`;
                    // A friend opens the detailed profile; anyone else is only
                    // shown, with the one action that applies (send a request).
                    return result.relationship === "friend" ? (
                      <>
                        <Link href={profileHref} className="sp-fr-result-head">
                          {identity}
                        </Link>
                        <Link href={profileHref} className="sp-fr-btn is-on">
                          {copy.actions.view}
                        </Link>
                      </>
                    ) : (
                      <>
                        <div className="sp-fr-result-head is-static">{identity}</div>
                        <button
                          type="button"
                          className={`sp-fr-btn${resultLabel[result.relationship]?.[1] ? " is-on" : ""}`}
                          disabled={!resultLabel[result.relationship]?.[1]}
                          onClick={resultAction}
                        >
                          {resultLabel[result.relationship]?.[0] ?? copy.actions.send}
                        </button>
                      </>
                    );
                  })()}
                </div>
              ) : searched && searchAlias ? (
                <div className="sp-fr-noresult">
                  <span>{copy.noResultTitle}</span>
                  <span>{copy.noResultBody}</span>
                </div>
              ) : null}
            </div>

            <div className="sp-fr-scroll sp-fr-scroll--friends">
            <div className="sp-fr-block">
              <span className="sp-fr-eyebrow sp-fr-eyebrow-pad">{copy.friendsHeading(friends.length)}</span>
              {friends.length === 0 ? <p className="sp-fr-hint sp-fr-pad">{copy.friendsEmpty}</p> : null}
              {friends.map((friend) => (
                <button
                  key={friend.alias}
                  type="button"
                  className={`sp-fr-row${selected === friend.alias ? " is-on" : ""}`}
                  aria-current={selected === friend.alias ? "true" : undefined}
                  onClick={() => setSelected(friend.alias)}
                >
                  <Avatar
                    alias={friend.alias}
                    name={friend.display_name || friend.alias}
                    size={34}
                    imageSrc={
                      friend.has_avatar_image ? `/api/accounts/profiles/${encodeURIComponent(friend.alias)}/avatar/` : undefined
                    }
                  />
                  <span className="sp-fr-who">
                    <span>{friend.display_name || friend.alias}</span>
                    <span className="sp-fr-mono">@{friend.alias}</span>
                  </span>
                </button>
              ))}
            </div>

            {requests.sent.length > 0 ? (
              <div className="sp-fr-block">
                <span className="sp-fr-eyebrow sp-fr-eyebrow-pad">{copy.sentHeading(requests.sent.length)}</span>
                {requests.sent.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`sp-fr-row${selected === item.receiver_alias ? " is-on" : ""}`}
                    onClick={() => setSelected(item.receiver_alias)}
                  >
                    <Avatar alias={item.receiver_alias} name={item.receiver_alias} size={34} />
                    <span className="sp-fr-who is-muted">
                      <span>{item.receiver_alias}</span>
                      <span className="sp-fr-mono">@{item.receiver_alias}</span>
                    </span>
                    <span className="sp-fr-pending">{copy.pendingBadge}</span>
                  </button>
                ))}
              </div>
            ) : null}
            </div>
          </aside>

          {/* ---- center: profile ---- */}
          <section className="sp-fr-center" aria-label={copy.heading}>
            {feedback ? (
              <p role="alert" className="sp-fr-error">
                {feedback}
              </p>
            ) : null}
            {!selected ? (
              <p className="sp-fr-empty">{copy.pickPerson}</p>
            ) : cardLoading && !card ? (
              <p aria-live="polite">{copy.loading}</p>
            ) : !card ? (
              <p className="sp-fr-empty">{copy.noResultTitle}</p>
            ) : isFriendCard ? (
              <div className="sp-fr-profile">
                <div className="sp-fr-hero">
                  <Link
                    href={`/${locale}/profiles/${encodeURIComponent(card.alias)}`}
                    className="sp-fr-hero-photo"
                    tabIndex={-1}
                    aria-hidden="true"
                  >
                    <Avatar alias={card.alias} name={cardName} size={52} imageSrc={card.avatar_image_url || card.avatar_url || undefined} />
                  </Link>
                  <div className="sp-fr-hero-main">
                    <div className="sp-fr-hero-title">
                      <h1>
                        <Link href={`/${locale}/profiles/${encodeURIComponent(card.alias)}`} title={cardName}>
                          {cardName}
                        </Link>
                      </h1>
                      <span className="sp-fr-badge">{copy.friendBadge}</span>
                    </div>
                    <Link href={`/${locale}/profiles/${encodeURIComponent(card.alias)}`} className="sp-fr-mono sp-fr-profile-link">
                      @{card.alias}
                    </Link>
                    <div className="sp-fr-hero-actions">
                      <button type="button" className="sp-fr-btn is-on" aria-expanded={recOpen} onClick={() => setRecOpen((open) => !open)}>
                        {copy.recommend}
                      </button>
                    </div>
                  </div>
                </div>

                {recOpen ? (
                  <div className="sp-fr-recpanel">
                    <div className="sp-fr-recpanel-head">
                      <span>{copy.recommendTo(firstName)}</span>
                      <button type="button" className="sp-fr-x" aria-label={copy.close} onClick={() => setRecOpen(false)}>
                        ✕
                      </button>
                    </div>
                    <div className="sp-fr-recpick">
                      <span id="fr-rec-game-label">{copy.pickGame}</span>
                      {recGame ? (
                        <div className="sp-fr-recgame">
                          <span className="sp-fr-recgame-cover">
                            <CoverImage src={recGame.cover.url} alt="" title={recGame.work_title} missingLabel="" width={36} height={48} />
                          </span>
                          <span className="sp-fr-recgame-title">{recGame.work_title}</span>
                          <button type="button" className="sp-fr-btn is-on" aria-describedby="fr-rec-game-label" onClick={() => setPickerOpen(true)}>
                            {copy.changeGame}
                          </button>
                        </div>
                      ) : (
                        <div>
                          <button type="button" className="sp-fr-btn is-on" aria-describedby="fr-rec-game-label" onClick={() => setPickerOpen(true)}>
                            {copy.chooseGame}
                          </button>
                        </div>
                      )}
                      {alreadyHas ? <span className="sp-fr-warn">{copy.alreadyHas(firstName)}</span> : null}
                    </div>
                    <label className="sp-fr-note">
                      <span>
                        {copy.note} <em>{copy.optional}</em>
                      </span>
                      <textarea
                        rows={2}
                        value={recNote}
                        maxLength={2000}
                        placeholder={copy.notePlaceholder}
                        onChange={(event) => setRecNote(event.target.value)}
                      />
                    </label>
                    <div className="sp-fr-recpanel-foot">
                      <button type="button" className="sp-fr-btn is-on" disabled={!recGame || recBusy} onClick={sendRecommendation}>
                        {recBusy ? copy.sending : copy.send}
                      </button>
                    </div>
                  </div>
                ) : null}
                {recMessage ? (
                  <div role="status" className={`sp-fr-banner${recMessage.kind === "error" ? " is-error" : ""}`}>
                    {recMessage.text}
                  </div>
                ) : null}

                <div className="sp-fr-favs-block">
                  <div className="sp-fr-favs-head">
                    <h2>{copy.favorites}</h2>
                    <span className="sp-fr-mono">{copy.favoritesOf(filledFavorites)}</span>
                  </div>
                  {card.favorites_visible === false ? (
                    <p className="sp-fr-hint">{copy.favoritesHidden}</p>
                  ) : (
                    <ol className="sp-fr-favs">
                      {favorites.map((favorite, index) => (
                        <li key={index}>
                          {favorite ? (
                            <Link href={`/${locale}/games/${favorite.work_slug}`} className="sp-fr-fav">
                              <span className="sp-fr-fav-cover">
                                <CoverImage
                                  src={favorite.cover.url}
                                  alt=""
                                  title={favorite.title}
                                  missingLabel=""
                                  width={160}
                                  height={213}
                                />
                              </span>
                              <span className="sp-fr-fav-title">{favorite.title}</span>
                              <span className="sp-fr-mono sp-fr-fav-meta">{favorite.year ?? ""}</span>
                            </Link>
                          ) : (
                            <span className="sp-fr-fav is-empty" aria-hidden="true">
                              <span className="sp-fr-fav-cover" />
                            </span>
                          )}
                        </li>
                      ))}
                    </ol>
                  )}
                </div>

                {summary ? (
                  <div className="sp-fr-summary">
                    <span>{`${summary.completed} ${copy.summary.completed}`}</span>
                    <span>{`${summary.playing} ${copy.summary.playing}`}</span>
                    <span>{`${summary.pending} ${copy.summary.pending}`}</span>
                  </div>
                ) : (
                  <p className="sp-fr-hint">{copy.collectionHidden}</p>
                )}

                <div className="sp-fr-manage">
                  <button type="button" className="sp-fr-link" onClick={() => setConfirmAction("remove")}>
                    {copy.removeFriend}
                  </button>
                  <button type="button" className="sp-fr-link is-danger" onClick={() => setConfirmAction("block")}>
                    {copy.block}
                  </button>
                </div>
              </div>
            ) : (
              <div className="sp-fr-profile">
                <div className="sp-fr-hero is-basic">
                  <Avatar alias={card.alias} name={card.alias} size={64} />
                  <div className="sp-fr-hero-main">
                    <h1>@{card.alias}</h1>
                    <span className="sp-fr-mono">{copy.basicProfile}</span>
                  </div>
                </div>
                <div className="sp-fr-lock">
                  <div className="sp-fr-lock-blur" aria-hidden="true">
                    {[0, 1, 2, 3, 4].map((index) => (
                      <span key={index} />
                    ))}
                  </div>
                  <div className="sp-fr-lock-over">
                    <span className="sp-fr-lock-icon" aria-hidden="true">
                      <svg width="22" height="22" viewBox="0 0 256 256" fill="currentColor">
                        <path d="M208 80h-32V56a48 48 0 0 0-96 0v24H48a16 16 0 0 0-16 16v112a16 16 0 0 0 16 16h160a16 16 0 0 0 16-16V96a16 16 0 0 0-16-16ZM96 56a32 32 0 0 1 64 0v24H96Zm112 152H48V96h160v112Z" />
                      </svg>
                    </span>
                    <span className="sp-fr-lock-title">{lock?.[0]}</span>
                    <span className="sp-fr-lock-body">{lock?.[1]}</span>
                    {card.relationship === "self" ? (
                      <Link href={`/${locale}/profile`} className="sp-fr-btn is-on">
                        {copy.editProfile}
                      </Link>
                    ) : lockLabel[card.relationship] ? (
                      <button type="button" className="sp-fr-btn is-on" onClick={lockAction}>
                        {lockLabel[card.relationship]}
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* ---- right: notifications ---- */}
          <aside className="sp-fr-right" aria-label={copy.notifications}>
            <div className="sp-fr-notif-head">
              <h2>{copy.notifications}</h2>
              <button type="button" className="sp-fr-markall" onClick={markAllRead}>
                {copy.markAll}
              </button>
            </div>
            <div className="sp-fr-tabs" role="tablist" aria-label={copy.notifications}>
              {(["all", "rec", "req"] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  aria-selected={notifTab === tab}
                  className={notifTab === tab ? "is-on" : undefined}
                  onClick={() => setNotifTab(tab)}
                >
                  {copy.tabs[tab]}
                </button>
              ))}
            </div>
            <div className="sp-fr-scroll sp-fr-scroll--notifs">
            <ul className="sp-fr-notifs">
              {visibleNotifs.map((item) => {
                const actionable = (item.kind === "request" || item.kind === "rec") && !item.state;
                const doneLabel = item.state ? copy.done[item.state] : undefined;
                const labels = item.kind === "request" ? copy.notifActions.request : copy.notifActions.rec;
                return (
                  <li key={item.id} className={`sp-fr-notif${item.read ? "" : " is-unread"}`}>
                    <div className="sp-fr-notif-main">
                      <Avatar
                        alias={item.actor.alias}
                        name={item.actor.name}
                        size={32}
                        imageSrc={
                          friends.find((friend) => friend.alias === item.actor.alias)?.has_avatar_image
                            ? `/api/accounts/profiles/${encodeURIComponent(item.actor.alias)}/avatar/`
                            : undefined
                        }
                      />
                      <div className="sp-fr-notif-text">
                        <span>
                          {item.read ? null : <span className="visually-hidden">{copy.unread}. </span>}
                          <strong>{item.actor.name}</strong> {copy.kindText[item.kind]}
                          {item.work ? (
                            <>
                              {" "}
                              <strong>{item.work.title}</strong>
                            </>
                          ) : null}
                        </span>
                        <span className="sp-fr-mono sp-fr-when">{relativeTime(item.date, copy)}</span>
                      </div>
                      <span className="sp-fr-dot" aria-hidden="true" />
                    </div>
                    {item.note ? <span className="sp-fr-notif-note">{item.note}</span> : null}
                    {actionable ? (
                      <div className="sp-fr-notif-actions">
                        <button
                          type="button"
                          className="is-primary"
                          onClick={() =>
                            item.kind === "request"
                              ? void acceptRequest(item.request_id as string, item.actor.alias)
                              : void act(`/api/social/messages/${item.message_id}/respond/`, { response: "added" })
                          }
                        >
                          {labels[0]}
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            item.kind === "request"
                              ? void rejectRequest(item.request_id as string)
                              : void act(`/api/social/messages/${item.message_id}/respond/`, { response: "dismissed" })
                          }
                        >
                          {labels[1]}
                        </button>
                      </div>
                    ) : null}
                    {doneLabel ? (
                      <span className={`sp-fr-done${item.state === "accepted" || item.state === "added" ? " is-ok" : ""}`}>
                        {doneLabel}
                      </span>
                    ) : null}
                  </li>
                );
              })}
            </ul>
            {visibleNotifs.length === 0 ? <span className="sp-fr-hint sp-fr-pad">{copy.empty}</span> : null}
            </div>
          </aside>
        </div>
      </div>

      <GamePicker
        open={pickerOpen}
        title={copy.pickerTitle(firstName)}
        works={ownGames}
        currentWorkId={recGame?.work_id ?? null}
        locale={locale}
        onPick={(workId) => {
          const chosen = ownGames.find((game) => game.work_id === workId);
          if (chosen) setRecGame(chosen);
          setPickerOpen(false);
        }}
        onClose={() => setPickerOpen(false)}
      />

      <dialog
        ref={confirmRef}
        className="sp-copy-dialog sp-confirm-dialog"
        aria-labelledby="fr-confirm-title"
        onClose={() => setConfirmAction(null)}
      >
        <div className="sp-copy-dialog-body">
          <h3 id="fr-confirm-title">
            {confirmAction === "block" ? copy.confirmBlockTitle(cardName) : copy.confirmRemoveTitle(cardName)}
          </h3>
          <p style={{ margin: 0 }}>{copy.confirmBody}</p>
          <div className="sp-copy-dialog-actions">
            <button type="button" className="sp-copy-cancel" onClick={() => setConfirmAction(null)}>
              {copy.cancelDialog}
            </button>
            <button type="button" className="sp-comment-confirm-delete" onClick={confirmFriendAction}>
              {copy.confirm}
            </button>
          </div>
        </div>
      </dialog>
    </div>
  );
}
