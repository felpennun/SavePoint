"use client";

import { useState } from "react";

import { apiFetch } from "@/lib/client-api";
import type { SocialAccount, SocialFriend, SocialFriendshipRequest, SocialFriends, SocialRelationship, SocialRequests } from "@/lib/api";
import { SocialActions, type SocialActionKey } from "@/components/SocialActions";

export const SOCIAL_SECTIONS = ["received", "sent", "friends"] as const;

export function buildSocialSearchUrl(alias: string): string {
  const params = new URLSearchParams();
  params.set("alias", alias.trim());
  return `/api/social/search/?${params.toString()}`;
}

const COPY = {
  es: {
    heading: "Amistades",
    searchHeading: "Buscar una amistad",
    searchLabel: "Alias exacto",
    search: "Buscar alias",
    received: "Solicitudes recibidas",
    sent: "Solicitudes enviadas",
    friends: "Amistades",
    receivedEmpty: "No tienes solicitudes recibidas.",
    sentEmpty: "No tienes solicitudes enviadas.",
    friendsEmpty: "Aún no tienes amistades",
    friendsEmptyBody: "Busca un alias exacto para enviar una solicitud.",
    noResult: "No se encontró ese alias exacto.",
    noResultBody: "Comprueba el alias completo e inténtalo de nuevo.",
    loadError: "No se pudo cargar esta información. Inténtalo de nuevo.",
    retry: "Reintentar",
    request: "solicitud",
    requests: "solicitudes",
    friend: "amistad",
    friendsCount: "amistades",
    relationship: "Estado de la relación",
    pending: "Solicitud pendiente",
    none: "Sin relación",
    friendStatus: "Amistad aceptada",
    blocked: "Cuenta bloqueada",
  },
  en: {
    heading: "Friends",
    searchHeading: "Find a friend",
    searchLabel: "Exact alias",
    search: "Search alias",
    received: "Received requests",
    sent: "Sent requests",
    friends: "Friends",
    receivedEmpty: "You have no received requests.",
    sentEmpty: "You have no sent requests.",
    friendsEmpty: "You do not have any friends yet",
    friendsEmptyBody: "Search for an exact alias to send a request.",
    noResult: "That exact alias was not found.",
    noResultBody: "Check the complete alias and try again.",
    loadError: "This information could not be loaded. Try again.",
    retry: "Retry",
    request: "request",
    requests: "requests",
    friend: "friend",
    friendsCount: "friends",
    relationship: "Relationship status",
    pending: "Request pending",
    none: "No relationship",
    friendStatus: "Accepted friendship",
    blocked: "Account blocked",
  },
} as const;

function countLabel(locale: string, count: number, singular: string, plural: string): string {
  return `${count} ${locale === "en" ? (count === 1 ? singular : plural) : (count === 1 ? singular : plural)}`;
}

function initials(alias: string): string {
  return alias.split(/[\s._-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase() ?? "").join("") || alias.slice(0, 2).toUpperCase();
}

function relationshipLabel(relationship: SocialRelationship, copy: { friendStatus: string; blocked: string; pending: string; none: string }): string {
  if (relationship === "friend") return copy.friendStatus;
  if (relationship === "blocked") return copy.blocked;
  if (relationship === "pending_sent" || relationship === "pending_received") return copy.pending;
  return copy.none;
}

function Avatar({ alias, avatarUrl }: { alias: string; avatarUrl?: string }) {
  return avatarUrl ? <img src={avatarUrl} alt="" width={40} height={40} className="sp-account-avatar" /> : <span className="sp-account-avatar" aria-hidden="true">{initials(alias)}</span>;
}

function RequestRow({ request, received, locale, onSuccess }: { request: SocialFriendshipRequest; received: boolean; locale: string; onSuccess: (action: SocialActionKey, alias: string) => void }) {
  const alias = received ? request.sender_alias : request.receiver_alias;
  return (
    <li className="sp-surface" data-testid={`social-request-${request.id}`} style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "var(--space-md)" }}>
      <Avatar alias={alias} />
      <div className="min-w-0" style={{ flex: "1 1 12rem" }}>
        <strong style={{ overflowWrap: "anywhere" }}>{alias}</strong>
        <p className="sp-meta" style={{ margin: "var(--space-xs) 0 0" }}>{request.created_at.slice(0, 10)}</p>
      </div>
      {received ? <SocialActions alias={alias} relationship="pending_received" requestId={request.id} locale={locale} onSuccess={onSuccess} /> : <SocialActions alias={alias} relationship="pending_sent" locale={locale} onSuccess={onSuccess} />}
    </li>
  );
}

function FriendRow({ friend, locale, onSuccess }: { friend: SocialFriend; locale: string; onSuccess: (action: SocialActionKey, alias: string) => void }) {
  return (
    <li className="sp-surface" data-testid={`social-friend-${friend.alias}`} style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "var(--space-md)" }}>
      <Avatar alias={friend.alias} />
      <strong className="min-w-0" style={{ flex: "1 1 12rem", overflowWrap: "anywhere" }}>{friend.alias}</strong>
      <SocialActions alias={friend.alias} relationship="friend" locale={locale} onSuccess={onSuccess} />
    </li>
  );
}

export function SocialHub({
  locale,
  initialRequests,
  initialFriends,
  initialAlias = "",
}: {
  locale: string;
  initialRequests: SocialRequests;
  initialFriends: SocialFriends;
  initialAlias?: string;
}) {
  const copy = locale === "en" ? COPY.en : COPY.es;
  const [requests, setRequests] = useState(initialRequests);
  const [friendships, setFriendships] = useState(initialFriends);
  const [alias, setAlias] = useState(initialAlias);
  const [searchResult, setSearchResult] = useState<SocialAccount | null>(null);
  const [searchError, setSearchError] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [searching, setSearching] = useState(false);
  const [feedback, setFeedback] = useState("");

  async function search(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const exactAlias = alias.trim();
    if (!exactAlias) return;
    setSearching(true);
    setHasSearched(true);
    setSearchError(false);
    setSearchResult(null);
    try {
      const response = await apiFetch(buildSocialSearchUrl(exactAlias));
      if (!response.ok) throw new Error("social_search_failed");
      const body = (await response.json()) as { results?: SocialAccount[] };
      setSearchResult(body.results?.[0] ?? null);
    } catch {
      setSearchError(true);
    } finally {
      setSearching(false);
    }
  }

  function handleSuccess(action: SocialActionKey, targetAlias: string) {
    setFeedback(action === "accept" ? (locale === "en" ? "Request accepted." : "Solicitud aceptada.") : action === "reject" ? (locale === "en" ? "Request rejected." : "Solicitud rechazada.") : action === "remove" ? (locale === "en" ? "Friendship removed." : "Amistad eliminada.") : action === "block" ? (locale === "en" ? "Account blocked." : "Cuenta bloqueada.") : action === "send" ? (locale === "en" ? "Request sent." : "Solicitud enviada.") : (locale === "en" ? "Action completed." : "Acción completada."));
    if (action === "accept") {
      const accepted = requests.received.find((item) => item.sender_alias === targetAlias);
      setRequests((current) => ({ ...current, received: current.received.filter((item) => item.sender_alias !== targetAlias) }));
      setFriendships((current) => current.friends.some((item) => item.alias === targetAlias) ? current : { friends: [...current.friends, { alias: targetAlias, relationship: "friend" }] });
      if (!accepted) return;
    } else if (action === "reject") {
      setRequests((current) => ({ ...current, received: current.received.filter((item) => item.sender_alias !== targetAlias) }));
    } else if (action === "remove" || action === "block") {
      setFriendships((current) => ({ friends: current.friends.filter((item) => item.alias !== targetAlias) }));
    } else if (action === "send" && searchResult) {
      setSearchResult({ ...searchResult, relationship: "pending_sent" });
    } else if (action === "unblock" && searchResult) {
      setSearchResult({ ...searchResult, relationship: "none" });
    }
  }

  function renderCount(count: number, kind: "request" | "friend") {
    if (kind === "friend") return countLabel(locale, count, copy.friend, copy.friendsCount);
    return countLabel(locale, count, copy.request, copy.requests);
  }

  return (
    <main className="sp-page">
      <h1 className="sp-h1">{copy.heading}</h1>
      <section className="sp-surface" aria-labelledby="social-search-heading" style={{ marginBottom: "var(--space-xl)" }}>
        <h2 id="social-search-heading" className="sp-h2" style={{ marginTop: 0 }}>{copy.searchHeading}</h2>
        <form role="search" onSubmit={search} className="flex flex-wrap items-end gap-2">
          <div className="sp-field" style={{ flex: "1 1 16rem" }}>
            <label htmlFor="social-alias">{copy.searchLabel}</label>
            <input id="social-alias" name="alias" type="text" autoComplete="off" value={alias} onChange={(event) => {
              setAlias(event.target.value);
              setHasSearched(false);
              setSearchResult(null);
            }} />
          </div>
          <button type="submit" className="sp-btn-primary" disabled={searching || !alias.trim()}>{copy.search}</button>
        </form>
        {searchError ? <p role="alert" className="sp-lead">{copy.loadError} <button type="button" className="sp-link" onClick={() => void search(new Event("submit") as unknown as React.FormEvent<HTMLFormElement>)}>{copy.retry}</button></p> : null}
        {!searching && hasSearched && !searchError && alias.trim() && searchResult === null ? <p className="sp-muted">{copy.noResult} {copy.noResultBody}</p> : null}
        {searchResult ? (
          <div className="sp-surface" style={{ marginTop: "var(--space-md)", display: "flex", flexWrap: "wrap", alignItems: "center", gap: "var(--space-md)" }}>
            <Avatar alias={searchResult.alias} avatarUrl={searchResult.avatar_url} />
            <div className="min-w-0" style={{ flex: "1 1 12rem" }}>
              <strong style={{ overflowWrap: "anywhere" }}>{searchResult.alias}</strong>
              <p className="sp-meta" style={{ margin: "var(--space-xs) 0 0" }}>{copy.relationship}: {relationshipLabel(searchResult.relationship, copy)}</p>
            </div>
            <SocialActions alias={searchResult.alias} relationship={searchResult.relationship} requestId={requests.received.find((request) => request.sender_alias === searchResult.alias)?.id} locale={locale} onSuccess={handleSuccess} />
          </div>
        ) : null}
      </section>

      <p role="status" aria-live="polite" aria-atomic="true">{feedback}</p>

      <div className="grid gap-6 md:grid-cols-3">
        <section aria-labelledby="social-received-heading">
          <h2 id="social-received-heading" className="sp-h2">{copy.received}</h2>
          <p className="sp-meta">{renderCount(requests.received.length, "request")}</p>
          {requests.received.length === 0 ? <p className="sp-lead">{copy.receivedEmpty}</p> : <ul className="grid gap-3">{requests.received.map((request) => <RequestRow key={request.id} request={request} received locale={locale} onSuccess={handleSuccess} />)}</ul>}
        </section>
        <section aria-labelledby="social-sent-heading">
          <h2 id="social-sent-heading" className="sp-h2">{copy.sent}</h2>
          <p className="sp-meta">{renderCount(requests.sent.length, "request")}</p>
          {requests.sent.length === 0 ? <p className="sp-lead">{copy.sentEmpty}</p> : <ul className="grid gap-3">{requests.sent.map((request) => <RequestRow key={request.id} request={request} received={false} locale={locale} onSuccess={handleSuccess} />)}</ul>}
        </section>
        <section aria-labelledby="social-friends-heading">
          <h2 id="social-friends-heading" className="sp-h2">{copy.friends}</h2>
          <p className="sp-meta">{renderCount(friendships.friends.length, "friend")}</p>
          {friendships.friends.length === 0 ? <div><p className="sp-lead">{copy.friendsEmpty}</p><p className="sp-lead">{copy.friendsEmptyBody}</p></div> : <ul className="grid gap-3">{friendships.friends.map((friend) => <FriendRow key={friend.alias} friend={friend} locale={locale} onSuccess={handleSuccess} />)}</ul>}
        </section>
      </div>
    </main>
  );
}
