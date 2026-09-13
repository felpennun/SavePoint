"use client";

import { useEffect, useState } from "react";

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

const COPY = {
  es: {
    heading: "Comentarios",
    empty: "Todavía no hay comentarios públicos.",
    yourComment: "Tu comentario",
    placeholder: "Escribe tu comentario sobre este juego…",
    visibility: "Visibilidad",
    public: "Público",
    private: "Privado",
    save: "Guardar comentario",
    saving: "Guardando…",
    saved: "Comentario guardado",
    delete: "Eliminar",
    deleting: "Eliminando…",
    edit: "Editar",
    cancel: "Cancelar",
    error: "No se pudo guardar el comentario. Inténtalo de nuevo.",
    loginRequired: "Inicia sesión para comentar.",
    loading: "Cargando comentarios…",
    you: "Tú",
  },
  en: {
    heading: "Comments",
    empty: "No public comments yet.",
    yourComment: "Your comment",
    placeholder: "Write your comment about this game…",
    visibility: "Visibility",
    public: "Public",
    private: "Private",
    save: "Save comment",
    saving: "Saving…",
    saved: "Comment saved",
    delete: "Delete",
    deleting: "Deleting…",
    edit: "Edit",
    cancel: "Cancel",
    error: "We couldn't save the comment. Try again.",
    loginRequired: "Log in to comment.",
    loading: "Loading comments…",
    you: "You",
  },
} as const;

/** Per-work comment section (LIB-03, D-04/D-05): at most one comment per
 * signed-in author, editable/deletable only by its own author; every other
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
  const [comments, setComments] = useState<CommentDto[]>([]);
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState("");
  const [visibility, setVisibility] = useState<Visibility>("public");
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const ownComment = comments.find((comment) => comment.is_own);
  const otherComments = comments.filter((comment) => !comment.is_own);

  useEffect(() => {
    let cancelled = false;
    apiFetch(`/api/library/entries/${workId}/comments/`)
      .then((response) => (response.ok ? response.json() : { comments: [] }))
      .then((body) => {
        if (cancelled) return;
        const list: CommentDto[] = Array.isArray(body?.comments) ? body.comments : [];
        setComments(list);
        const own = list.find((comment) => comment.is_own);
        if (own) {
          setText(own.text);
          setVisibility(own.visibility);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workId]);

  if (loading) return <p aria-live="polite">{copy.loading}</p>;

  async function saveComment() {
    setSaving(true);
    setFeedback(null);
    try {
      const response = ownComment
        ? await apiFetch(`/api/library/comments/${ownComment.id}/`, { method: "PATCH", body: { text, visibility } })
        : await apiFetch(`/api/library/entries/${workId}/comments/`, { method: "POST", body: { text, visibility } });
      if (!response.ok) {
        setFeedback(copy.error);
        return;
      }
      const saved = (await response.json()) as CommentDto;
      setComments((previous) => {
        const withoutOwn = previous.filter((comment) => !comment.is_own);
        return [...withoutOwn, { ...saved, is_own: true }];
      });
      setFeedback(copy.saved);
      setEditing(false);
    } catch {
      setFeedback(copy.error);
    } finally {
      setSaving(false);
    }
  }

  async function deleteComment() {
    if (!ownComment) return;
    setSaving(true);
    setFeedback(null);
    try {
      const response = await apiFetch(`/api/library/comments/${ownComment.id}/`, { method: "DELETE" });
      if (!response.ok && response.status !== 204) {
        setFeedback(copy.error);
        return;
      }
      setComments((previous) => previous.filter((comment) => !comment.is_own));
      setText("");
      setVisibility("public");
      setEditing(false);
    } catch {
      setFeedback(copy.error);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="sp-game-comments" aria-label={copy.heading}>
      <h2 className="sp-h2">{copy.heading}</h2>

      {isAuthenticated ? (
        ownComment && !editing ? (
          <div className="sp-copy-row">
            <p className="sp-eyebrow" style={{ margin: 0 }}>
              {copy.yourComment}
            </p>
            <p style={{ margin: 0 }}>{ownComment.text}</p>
            <div className="sp-filterbar-actions" style={{ marginLeft: 0, gap: "var(--space-sm)" }}>
              <button type="button" className="sp-copy-add sp-comment-edit" onClick={() => setEditing(true)}>
                {copy.edit}
              </button>
              <button type="button" className="sp-copy-remove sp-comment-remove" onClick={deleteComment} disabled={saving}>
                {saving ? copy.deleting : copy.delete}
              </button>
            </div>
          </div>
        ) : (
          <div className="sp-copy-row">
            <div className="sp-field">
              <label htmlFor={`comment-text-${workId}`}>{copy.yourComment}</label>
              <textarea
                id={`comment-text-${workId}`}
                value={text}
                placeholder={copy.placeholder}
                onChange={(event) => setText(event.target.value)}
                disabled={saving}
                rows={3}
                maxLength={2000}
              />
            </div>
            <div className="sp-field">
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
            <div className="sp-filterbar-actions" style={{ marginLeft: 0, gap: "var(--space-sm)" }}>
              <button type="button" className="sp-btn-primary" onClick={saveComment} disabled={saving || !text.trim()}>
                {saving ? copy.saving : copy.save}
              </button>
              {ownComment ? (
                <button
                  type="button"
                  className="sp-copy-add sp-comment-cancel"
                  onClick={() => {
                    setEditing(false);
                    setText(ownComment.text);
                    setVisibility(ownComment.visibility);
                  }}
                  disabled={saving}
                >
                  {copy.cancel}
                </button>
              ) : null}
            </div>
          </div>
        )
      ) : (
        <p className="sp-meta">{copy.loginRequired}</p>
      )}

      {feedback ? (
        <p role="status" data-testid="comment-feedback">
          {feedback}
        </p>
      ) : null}

      {otherComments.length === 0 ? (
        <p className="sp-meta" style={{ marginTop: "var(--space-md)" }}>
          {copy.empty}
        </p>
      ) : (
        <ul className="sp-profile-comments-list" style={{ marginTop: "var(--space-md)" }}>
          {otherComments.map((comment) => (
            <li key={comment.id}>
              <strong>{comment.author}</strong>
              <p>{comment.text}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
