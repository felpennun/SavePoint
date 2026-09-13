"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { CoverImage } from "@/components/CoverImage";
import { apiFetch, getSocialUnreadCount, markSocialMessageRead, sendSocialRecommendation } from "@/lib/client-api";
import type { Cover, GameCard, SocialFriend, SocialMessage } from "@/lib/api";

const COPY = {
  es: {
    heading: "Mensajes de amigos",
    intro: "Recomendaciones privadas recibidas de tus amistades.",
    emptyHeading: "No tienes mensajes de amigos",
    emptyBody: "Cuando una amistad te recomiende un juego, aparecerá aquí.",
    loadError: "No se pudo cargar esta información. Inténtalo de nuevo.",
    retry: "Reintentar",
    from: "De",
    recommended: "te recomienda",
    markRead: "Marcar como leído",
    markedRead: "Mensaje marcado como leído.",
    read: "Leído",
    recommend: "Recomendar juego",
    friend: "Amistad",
    game: "Juego del catálogo",
    text: "Mensaje opcional",
    send: "Enviar recomendación",
    sent: "Recomendación enviada.",
    mutationError: "La acción no se pudo completar. Revisa el estado e inténtalo de nuevo.",
    cooldown: "Ya has recomendado un juego a esta amistad durante los últimos 7 días.",
    retryAfter: (seconds: number) => `El límite del servidor se renueva en ${seconds} segundos.`,
    noOptions: "Necesitas una amistad y un juego del catálogo para recomendar.",
  },
  en: {
    heading: "Messages from friends",
    intro: "Private recommendations received from your friends.",
    emptyHeading: "You have no messages from friends",
    emptyBody: "When a friend recommends a game, it will appear here.",
    loadError: "This information could not be loaded. Try again.",
    retry: "Retry",
    from: "From",
    recommended: "recommends",
    markRead: "Mark as read",
    markedRead: "Message marked as read.",
    read: "Read",
    recommend: "Recommend a game",
    friend: "Friend",
    game: "Catalogue game",
    text: "Optional message",
    send: "Send recommendation",
    sent: "Recommendation sent.",
    mutationError: "The action could not be completed. Check the state and try again.",
    cooldown: "You have already recommended a game to this friend during the last 7 days.",
    retryAfter: (seconds: number) => `The server limit resets in ${seconds} seconds.`,
    noOptions: "You need a friend and a catalogue game to recommend one.",
  },
} as const;

function isSocialMessage(value: unknown): value is SocialMessage {
  if (typeof value !== "object" || value === null) return false;
  const message = value as Partial<SocialMessage>;
  const work = message.work;
  return typeof message.id === "string"
    && typeof message.sender_alias === "string"
    && typeof message.recipient_alias === "string"
    && typeof message.text === "string"
    && typeof message.date === "string"
    && typeof message.read === "boolean"
    && typeof work === "object"
    && work !== null
    && typeof work.id === "string"
    && typeof work.title === "string"
    && typeof work.cover === "object"
    && work.cover !== null;
}

function safeCover(cover: Cover, title: string): Cover {
  return {
    url: typeof cover.url === "string" ? cover.url : null,
    is_placeholder: cover.is_placeholder === true,
    alt: typeof cover.alt === "string" ? cover.alt : title,
  };
}

function messageDate(value: string): string {
  return value.slice(0, 10);
}

function announceUnreadCount(count: number): void {
  window.dispatchEvent(new CustomEvent("savepoint:social-unread-count", { detail: { count } }));
}

export function SocialInbox({
  locale,
  initialMessages,
  friends = [],
  catalogue = [],
}: {
  locale: string;
  initialMessages: SocialMessage[];
  friends?: SocialFriend[];
  catalogue?: GameCard[];
}) {
  const copy = locale === "en" ? COPY.en : COPY.es;
  const [messages, setMessages] = useState(initialMessages);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [recipientAlias, setRecipientAlias] = useState(friends[0]?.alias ?? "");
  const [workId, setWorkId] = useState(catalogue[0]?.id ?? "");
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<"generic" | "cooldown" | null>(null);
  const [retryAfterSeconds, setRetryAfterSeconds] = useState<number | null>(null);

  async function reload() {
    setLoading(true);
    setLoadError(false);
    try {
      const response = await apiFetch("/api/social/messages/");
      if (!response.ok) throw new Error("social_inbox_failed");
      const body = (await response.json()) as { messages?: unknown };
      const next = Array.isArray(body.messages) ? body.messages.filter(isSocialMessage) : [];
      setMessages(next);
      const unread = await getSocialUnreadCount();
      if (unread !== null) announceUnreadCount(unread);
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }

  async function markRead(messageId: string) {
    const ok = await markSocialMessageRead(messageId);
    if (!ok) {
      setFeedback(copy.mutationError);
      return;
    }
    setMessages((current) => current.map((item) => item.id === messageId ? { ...item, read: true } : item));
    setFeedback(copy.markedRead);
    const unread = await getSocialUnreadCount();
    if (unread !== null) announceUnreadCount(unread);
  }

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!recipientAlias || !workId) return;
    setSending(true);
    setSendError(null);
    setRetryAfterSeconds(null);
    const result = await sendSocialRecommendation({ recipient_alias: recipientAlias, work_id: workId, text });
    if (result.kind === "ok") {
      setFeedback(copy.sent);
      setText("");
    } else if (result.kind === "cooldown") {
      setSendError("cooldown");
      setRetryAfterSeconds(result.retryAfterSeconds);
      setFeedback(copy.cooldown);
    } else {
      setSendError("generic");
      setFeedback(copy.mutationError);
    }
    setSending(false);
  }

  const unreadCount = messages.filter((item) => !item.read).length;
  const hasRecommendationOptions = friends.length > 0 && catalogue.length > 0;

  return (
    <main className="sp-page">
      <h1 className="sp-h1">{copy.heading}</h1>
      <p className="sp-lead">{copy.intro}</p>
      <p className="sp-meta" role="status" aria-live="polite" aria-atomic="true">
        {unreadCount} {locale === "en" ? "unread messages" : "mensajes sin leer"}
      </p>

      {hasRecommendationOptions ? (
        <section className="sp-surface" aria-labelledby="recommend-game-heading" style={{ marginTop: "var(--space-xl)" }}>
          <h2 id="recommend-game-heading" className="sp-h2" style={{ marginTop: 0 }}>{copy.recommend}</h2>
          <form onSubmit={send} className="grid gap-3">
            <div className="sp-field">
              <label htmlFor="recommend-friend">{copy.friend}</label>
              <select id="recommend-friend" value={recipientAlias} onChange={(event) => setRecipientAlias(event.target.value)} disabled={sending}>
                {friends.map((friend) => <option key={friend.alias} value={friend.alias}>{friend.alias}</option>)}
              </select>
            </div>
            <div className="sp-field">
              <label htmlFor="recommend-game">{copy.game}</label>
              <select id="recommend-game" value={workId} onChange={(event) => setWorkId(event.target.value)} disabled={sending}>
                {catalogue.map((game) => <option key={game.id} value={game.id}>{game.title}</option>)}
              </select>
            </div>
            <div className="sp-field">
              <label htmlFor="recommend-text">{copy.text}</label>
              <textarea id="recommend-text" maxLength={2000} value={text} onChange={(event) => setText(event.target.value)} disabled={sending} rows={3} />
            </div>
            {sendError === "cooldown" ? (
              <p role="alert" className="sp-lead">{copy.cooldown} {retryAfterSeconds === null ? null : copy.retryAfter(retryAfterSeconds)}</p>
            ) : (
              <button type="submit" className="sp-btn-primary" disabled={sending || !recipientAlias || !workId}>
                {sending ? `${copy.send}…` : copy.send}
              </button>
            )}
            {sendError === "generic" ? <button type="submit" className="sp-link" disabled={sending}>{copy.retry}</button> : null}
          </form>
          {!hasRecommendationOptions ? <p className="sp-muted">{copy.noOptions}</p> : null}
        </section>
      ) : null}

      <section aria-labelledby="received-messages-heading" style={{ marginTop: "var(--space-2xl)" }}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="received-messages-heading" className="sp-h2" style={{ marginTop: 0 }}>{copy.heading}</h2>
          <button type="button" className="sp-btn-secondary" onClick={() => void reload()} disabled={loading}>
            {loading ? `${copy.retry}…` : copy.retry}
          </button>
        </div>
        {loadError ? <p role="alert" className="sp-lead">{copy.loadError}</p> : null}
        {!loading && messages.length === 0 ? (
          <div className="sp-empty">
            <p className="sp-h2" style={{ margin: 0 }}>{copy.emptyHeading}</p>
            <p className="sp-lead" style={{ marginInline: "auto" }}>{copy.emptyBody}</p>
          </div>
        ) : (
          <ul className="grid gap-3" aria-live="polite" style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {messages.map((item) => {
              const catalogueGame = catalogue.find((game) => game.id === item.work.id);
              const gameHref = `/${locale}/games/${catalogueGame?.slug ?? item.work.id}`;
              const cover = safeCover(item.work.cover, item.work.title);
              return (
                <li key={item.id} className="sp-surface" style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-md)", alignItems: "flex-start" }}>
                  <div aria-hidden="true" style={{ width: "48px", flex: "0 0 48px" }}>
                    <div className="sp-account-avatar" style={{ display: "grid", placeItems: "center", fontSize: "var(--text-micro)", fontWeight: 600 }}>{item.sender_alias.slice(0, 2).toUpperCase()}</div>
                  </div>
                  <div className="min-w-0" style={{ flex: "1 1 18rem" }}>
                    <p className="sp-meta" style={{ margin: 0 }}>{copy.from} <strong style={{ overflowWrap: "anywhere" }}>{item.sender_alias}</strong> · {messageDate(item.date)}</p>
                    <p style={{ margin: "var(--space-sm) 0", overflowWrap: "anywhere" }}>{item.sender_alias} {copy.recommended} <Link href={gameHref}>{item.work.title}</Link>.</p>
                    {cover.url || cover.is_placeholder ? <div style={{ maxWidth: "96px", marginBottom: "var(--space-sm)" }}><div className="sp-cover"><CoverImage src={cover.url} alt={cover.alt} title={item.work.title} missingLabel={locale === "en" ? "Cover not available" : "Portada no disponible"} width={96} height={128} /></div></div> : null}
                    {item.text ? <p style={{ margin: 0, overflowWrap: "anywhere" }}>{item.text}</p> : null}
                    <div className="flex flex-wrap items-center gap-2" style={{ marginTop: "var(--space-md)" }}>
                      {item.read ? <span className="sp-muted">{copy.read}</span> : <button type="button" className="sp-btn-secondary" onClick={() => void markRead(item.id)}>{copy.markRead}</button>}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </main>
  );
}
