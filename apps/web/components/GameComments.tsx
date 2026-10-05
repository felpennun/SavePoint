"use client";

import { useEffect, useRef, useState } from "react";

import { apiFetch } from "@/lib/client-api";

type Visibility = "public" | "private";

interface CommentDto {
  id: string;
  work_id: string;
  author: string;
  text: string;
  visibility: Visibility;
  is_own: boolean;
  created_at: string;
}

/** More comments than this are split into pages. */
const PAGE_SIZE = 10;

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

const COPY = {
  es: {
    heading: "Comentarios",
    empty: "Todavía no hay comentarios.",
    yourComment: "Tu comentario",
    placeholder: "Escribe tu comentario sobre este juego…",
    visibility: "Visibilidad",
    public: "Solo amigos",
    private: "Privado",
    save: "Guardar comentario",
    saving: "Guardando…",
    saved: "Comentario guardado",
    delete: "Eliminar",
    deleting: "Eliminando…",
    deleteAria: "Eliminar comentario",
    confirmTitle: "¿Eliminar este comentario?",
    confirmBody: "Esta acción no se puede deshacer.",
    edit: "Editar",
    cancel: "Cancelar",
    error: "No se pudo guardar el comentario. Inténtalo de nuevo.",
    loginRequired: "Inicia sesión para comentar.",
    notInCollection: "Añade el juego a tu colección (elige un estado) para poder comentarlo.",
    loading: "Cargando comentarios…",
    pagination: "Paginación de comentarios",
    previous: "Anterior",
    next: "Siguiente",
    you: "Tú",
  },
  en: {
    heading: "Comments",
    empty: "No comments yet.",
    yourComment: "Your comment",
    placeholder: "Write your comment about this game…",
    visibility: "Visibility",
    public: "Friends only",
    private: "Private",
    save: "Save comment",
    saving: "Saving…",
    saved: "Comment saved",
    delete: "Delete",
    deleting: "Deleting…",
    deleteAria: "Delete comment",
    confirmTitle: "Delete this comment?",
    confirmBody: "This cannot be undone.",
    edit: "Edit",
    cancel: "Cancel",
    error: "We couldn't save the comment. Try again.",
    loginRequired: "Log in to comment.",
    notInCollection: "Add the game to your collection (pick a status) to comment on it.",
    loading: "Loading comments…",
    pagination: "Comments pagination",
    previous: "Previous",
    next: "Next",
    you: "You",
  },
} as const;

/** Per-work comment section (LIB-03): a signed-in author may write several
 * comments, deletable only by their own author; every other
 * visible comment here is `public` by construction (the GET endpoint
 * already filters to public + the caller's own). */
export function GameComments({
  workId,
  locale,
  isAuthenticated,
}: {
  workId: string;
  locale: "es" | "en";
  isAuthenticated: boolean;
}) {
  const copy = COPY[locale];
  const [loading, setLoading] = useState(true);
  const [inCollection, setInCollection] = useState(false);
  const [comments, setComments] = useState<CommentDto[]>([]);
  const [text, setText] = useState("");
  const [visibility, setVisibility] = useState<Visibility>("public");
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const confirmRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = confirmRef.current;
    if (!dialog) return;
    if (confirmId !== null && !dialog.open) dialog.showModal();
    if (confirmId === null && dialog.open) dialog.close();
  }, [confirmId]);

  useEffect(() => {
    let cancelled = false;
    apiFetch(`/api/library/entries/${workId}/comments/`)
      .then((response) => (response.ok ? response.json() : { comments: [] }))
      .then((body) => {
        if (cancelled) return;
        const raw: Array<Partial<CommentDto> & { author_alias?: string; date?: string }> = Array.isArray(body?.comments)
          ? body.comments
          : [];
        // Own comments come with their id; other authors' use the shared allowlist.
        const list: CommentDto[] = raw.map((item, index) => ({
          id: item.id ?? `shared-${index}`,
          work_id: item.work_id ?? workId,
          author: item.author ?? item.author_alias ?? "",
          text: item.text ?? "",
          visibility: item.visibility ?? "public",
          is_own: Boolean(item.is_own),
          created_at: item.created_at ?? item.date ?? "",
        }));
        setComments(list);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    if (isAuthenticated) {
      apiFetch(`/api/library/entries/${workId}/configuration/`)
        .then((response) => (response.ok ? response.json() : null))
        .then((body: { in_collection?: unknown } | null) => {
          if (!cancelled) setInCollection(body?.in_collection === true);
        })
        .catch(() => {
          if (!cancelled) setInCollection(false);
        });
    } else {
      setInCollection(false);
    }
    return () => {
      cancelled = true;
    };
  }, [workId, isAuthenticated]);

  if (loading) return <p aria-live="polite">{copy.loading}</p>;

  async function saveComment() {
    setSaving(true);
    setFeedback(null);
    try {
      const response = await apiFetch(`/api/library/entries/${workId}/comments/`, { method: "POST", body: { text, visibility } });
      if (!response.ok) {
        const detail = (await response.json().catch(() => null)) as { detail?: unknown } | null;
        setFeedback(
          typeof detail?.detail === "string" && detail.detail.includes("not in your collection")
            ? copy.notInCollection
            : copy.error,
        );
        return;
      }
      const saved = (await response.json()) as CommentDto;
      const total = comments.length + 1;
      setComments((previous) => [...previous, { ...saved, is_own: true }]);
      setPage(Math.max(1, Math.ceil(total / PAGE_SIZE)));
      setFeedback(copy.saved);
      setText("");
    } catch {
      setFeedback(copy.error);
    } finally {
      setSaving(false);
    }
  }

  async function deleteComment() {
    if (confirmId === null) return;
    const id = confirmId;
    setConfirmId(null);
    setSaving(true);
    setFeedback(null);
    try {
      const response = await apiFetch(`/api/library/comments/${id}/`, { method: "DELETE" });
      if (!response.ok && response.status !== 204) {
        setFeedback(copy.error);
        return;
      }
      setComments((previous) => previous.filter((comment) => comment.id !== id));
    } catch {
      setFeedback(copy.error);
    } finally {
      setSaving(false);
    }
  }

  const pageCount = Math.max(1, Math.ceil(comments.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const visibleComments = comments.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  return (
    <section className="sp-game-comments" aria-label={copy.heading}>
      <h2 className="sp-h2">{copy.heading}</h2>

      {isAuthenticated && inCollection ? (
        <div className="sp-copy-row">
          <div className="sp-field">
            <textarea
              id={`comment-text-${workId}`}
              aria-label={copy.yourComment}
              value={text}
              placeholder={copy.placeholder}
              onChange={(event) => setText(event.target.value)}
              disabled={saving}
              rows={3}
              maxLength={2000}
            />
          </div>
          <div className="sp-comment-actions-row">
            <div className="sp-field sp-comment-visibility">
              <label htmlFor={`comment-visibility-${workId}`}>{copy.visibility}</label>
              <select
                id={`comment-visibility-${workId}`}
                value={visibility}
                onChange={(event) => setVisibility(event.target.value as Visibility)}
                disabled={saving}
              >
                <option value="public">{copy.public}</option>
                <option value="private">{copy.private}</option>
              </select>
            </div>
            <button type="button" className="sp-btn-primary" onClick={saveComment} disabled={saving || !text.trim()}>
              {saving ? copy.saving : copy.save}
            </button>
          </div>
        </div>
      ) : isAuthenticated ? (
        <p className="sp-meta">{copy.notInCollection}</p>
      ) : (
        <p className="sp-meta">{copy.loginRequired}</p>
      )}

      {feedback ? (
        <p role="status" data-testid="comment-feedback">
          {feedback}
        </p>
      ) : null}

      {comments.length === 0 ? (
        <p className="sp-meta" style={{ marginTop: "var(--space-md)" }}>
          {copy.empty}
        </p>
      ) : (
        <ul className="sp-comment-list" style={{ marginTop: "var(--space-md)" }}>
          {visibleComments.map((comment) => (
            <li key={comment.id} className={`sp-comment-item${comment.is_own ? " is-own" : ""}`}>
              <strong className="sp-comment-author">{comment.author || copy.you}</strong>
              <p className="sp-comment-text">
                {comment.text}
                {comment.is_own && comment.visibility === "private" ? (
                  <span className="sp-meta sp-comment-private"> · {copy.private}</span>
                ) : null}
              </p>
              {comment.is_own ? (
                <button
                  type="button"
                  className="sp-btn-clear sp-comment-remove"
                  aria-label={copy.deleteAria}
                  title={copy.deleteAria}
                  onClick={() => setConfirmId(comment.id)}
                  disabled={saving}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M3 6h18" />
                    <path d="M8 6V4h8v2" />
                    <path d="M6 6l1 14h10l1-14" />
                    <path d="M10 11v5M14 11v5" />
                  </svg>
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      {pageCount > 1 ? (
        <nav className="sp-pagination sp-comment-pagination" aria-label={copy.pagination}>
          {currentPage > 1 ? (
            <button
              type="button"
              className="sp-pagination-arrow"
              aria-label={copy.previous}
              onClick={() => setPage(currentPage - 1)}
            >
              <Chevron direction="prev" />
            </button>
          ) : (
            <span className="sp-pagination-spacer" aria-hidden="true" />
          )}
          <span aria-current="page" className="sp-pagination-current">
            {currentPage}
          </span>
          {currentPage < pageCount ? (
            <button
              type="button"
              className="sp-pagination-arrow"
              aria-label={copy.next}
              onClick={() => setPage(currentPage + 1)}
            >
              <Chevron direction="next" />
            </button>
          ) : (
            <span className="sp-pagination-spacer" aria-hidden="true" />
          )}
        </nav>
      ) : null}

      <dialog
        ref={confirmRef}
        className="sp-copy-dialog sp-confirm-dialog"
        aria-labelledby={`comment-confirm-title-${workId}`}
        onClose={() => setConfirmId(null)}
      >
        <div className="sp-copy-dialog-body">
          <h3 id={`comment-confirm-title-${workId}`}>{copy.confirmTitle}</h3>
          <p style={{ margin: 0 }}>{copy.confirmBody}</p>
          <div className="sp-copy-dialog-actions">
            <button type="button" className="sp-copy-cancel" onClick={() => setConfirmId(null)}>
              {copy.cancel}
            </button>
            <button type="button" className="sp-comment-confirm-delete" onClick={deleteComment} disabled={saving}>
              {copy.delete}
            </button>
          </div>
        </div>
      </dialog>
    </section>
  );
}
