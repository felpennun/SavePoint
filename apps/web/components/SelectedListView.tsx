"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { AddGameToListTile } from "@/components/AddGameToListTile";
import { GameCard } from "@/components/GameCard";
import type { PickerWork } from "@/components/GamePicker";
import type { BacklogStatus } from "@/components/StatusPill";
import type { GameCard as GameCardData } from "@/lib/api";
import { apiFetch } from "@/lib/client-api";

export interface ListViewItem {
  /** The list entry's own id (what the delete endpoint needs). */
  itemId: string;
  workId: string;
  game: GameCardData;
  score: number | null;
  status?: BacklogStatus;
  ratingHalfSteps: number | null;
  ownedCopyCount: number;
  isPlatinum: boolean;
}

const COPY = {
  es: {
    edit: "Editar lista",
    name: "Nombre de la lista",
    rename: "Cambiar nombre",
    saving: "Guardando…",
    removeGames: "Eliminar juegos",
    cancel: "Cancelar",
    confirmRemove: "Confirmar borrado",
    selected: (n: number) => (n === 1 ? "1 juego seleccionado" : `${n} juegos seleccionados`),
    deleteList: "Eliminar lista",
    toggle: (title: string) => `Marcar ${title} para quitarlo de la lista`,
    removeTitle: (n: number) => (n === 1 ? "¿Quitar 1 juego de la lista?" : `¿Quitar ${n} juegos de la lista?`),
    removeBody: "Los juegos seguirán en tu colección.",
    remove: "Quitar",
    deleteTitle: "¿Eliminar esta lista?",
    deleteBody: "Los juegos seguirán en tu colección.",
    delete: "Eliminar",
    error: "No se pudo completar la acción. Inténtalo de nuevo.",
  },
  en: {
    edit: "Edit list",
    name: "List name",
    rename: "Rename",
    saving: "Saving…",
    removeGames: "Remove games",
    cancel: "Cancel",
    confirmRemove: "Confirm removal",
    selected: (n: number) => (n === 1 ? "1 game selected" : `${n} games selected`),
    deleteList: "Delete list",
    toggle: (title: string) => `Mark ${title} to remove it from the list`,
    removeTitle: (n: number) => (n === 1 ? "Remove 1 game from the list?" : `Remove ${n} games from the list?`),
    removeBody: "The games stay in your collection.",
    remove: "Remove",
    deleteTitle: "Delete this list?",
    deleteBody: "The games stay in your collection.",
    delete: "Delete",
    error: "Couldn't complete the action. Try again.",
  },
} as const;

/** The selected custom list: its folded "Editar lista" panel (rename, delete the
 * list, and a remove-games mode that marks several covers and asks to confirm)
 * and the grid of its games, ending with the "add a game" tile. */
export function SelectedListView({
  locale,
  listId,
  listName,
  basePath,
  items,
  works,
  excludedIds,
}: {
  locale: "es" | "en";
  listId: string;
  listName: string;
  basePath: string;
  items: ListViewItem[];
  works: PickerWork[];
  excludedIds: string[];
}) {
  const copy = COPY[locale];
  const router = useRouter();
  const [name, setName] = useState(listName);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [removeMode, setRemoveMode] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [confirm, setConfirm] = useState<"games" | "list" | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => setName(listName), [listName]);
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (confirm && !dialog.open) dialog.showModal();
    if (!confirm && dialog.open) dialog.close();
  }, [confirm]);

  async function rename(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || name === listName || busy) return;
    setBusy(true);
    setFeedback(null);
    try {
      const response = await apiFetch(`/api/library/lists/${listId}/`, { method: "PATCH", body: { name } });
      if (!response.ok) {
        setFeedback(copy.error);
        return;
      }
      router.refresh();
    } catch {
      setFeedback(copy.error);
    } finally {
      setBusy(false);
    }
  }

  function leaveRemoveMode() {
    setRemoveMode(false);
    setSelected([]);
  }

  async function removeSelected() {
    setBusy(true);
    setFeedback(null);
    try {
      for (const item of items.filter((entry) => selected.includes(entry.workId))) {
        const response = await apiFetch(`/api/library/lists/${listId}/items/${item.itemId}/`, { method: "DELETE" });
        if (!response.ok && response.status !== 204) {
          setFeedback(copy.error);
          return;
        }
      }
      setConfirm(null);
      leaveRemoveMode();
      router.refresh();
    } catch {
      setFeedback(copy.error);
    } finally {
      setBusy(false);
    }
  }

  async function deleteList() {
    setBusy(true);
    setFeedback(null);
    try {
      const response = await apiFetch(`/api/library/lists/${listId}/`, { method: "DELETE" });
      if (!response.ok && response.status !== 204) {
        setFeedback(copy.error);
        return;
      }
      setConfirm(null);
      router.push(basePath);
      router.refresh();
    } catch {
      setFeedback(copy.error);
    } finally {
      setBusy(false);
    }
  }

  function toggle(workId: string) {
    setSelected((previous) => (previous.includes(workId) ? previous.filter((id) => id !== workId) : [...previous, workId]));
  }

  return (
    <>
      <details className="sp-coll-editor">
        <summary>{copy.edit}</summary>
        <div className="sp-coll-editor-body">
          <form className="sp-coll-editor-rename" onSubmit={rename}>
            <label htmlFor="coll-list-name" className="visually-hidden">
              {copy.name}
            </label>
            <input id="coll-list-name" value={name} onChange={(event) => setName(event.target.value)} maxLength={80} disabled={busy} />
            <button type="submit" className="sp-copy-add" disabled={busy || !name.trim() || name === listName}>
              {busy ? copy.saving : copy.rename}
            </button>
            <button type="button" className="sp-copy-remove sp-list-delete" onClick={() => setConfirm("list")} disabled={busy}>
              {copy.deleteList}
            </button>
          </form>

          <div className="sp-coll-editor-actions">
            {removeMode ? (
              <>
                <span className="sp-meta" role="status">
                  {copy.selected(selected.length)}
                </span>
                <button type="button" className="sp-copy-cancel" onClick={leaveRemoveMode} disabled={busy}>
                  {copy.cancel}
                </button>
                <button type="button" className="sp-comment-confirm-delete" onClick={() => setConfirm("games")} disabled={busy || selected.length === 0}>
                  {copy.confirmRemove}
                </button>
              </>
            ) : (
              <button type="button" className="sp-copy-remove" onClick={() => setRemoveMode(true)} disabled={items.length === 0}>
                {copy.removeGames}
              </button>
            )}
          </div>
          {feedback ? (
            <p role="status" className="sp-coll-editor-error">
              {feedback}
            </p>
          ) : null}
        </div>
      </details>

      <ul className="sp-grid sp-collection-grid">
        {items.map((item) => {
          const isSelected = selected.includes(item.workId);
          return (
            <GameCard
              key={item.workId}
              game={item.game}
              locale={locale}
              score={item.score}
              status={item.status}
              ratingHalfSteps={item.ratingHalfSteps}
              ownedCopyCount={item.ownedCopyCount}
              isPlatinum={item.isPlatinum}
              itemClassName={`sp-coll-card${removeMode ? " is-removing" : ""}${isSelected ? " is-selected" : ""}`}
              overlay={
                removeMode ? (
                  <button
                    type="button"
                    className="sp-coll-remove-toggle"
                    aria-pressed={isSelected}
                    aria-label={copy.toggle(item.game.title)}
                    onClick={() => toggle(item.workId)}
                  >
                    <span className="sp-coll-remove-badge" aria-hidden="true">
                      −
                    </span>
                  </button>
                ) : null
              }
            />
          );
        })}
        {removeMode ? null : <AddGameToListTile locale={locale} listId={listId} works={works} excludedIds={excludedIds} />}
      </ul>

      <dialog
        ref={dialogRef}
        className="sp-copy-dialog sp-confirm-dialog"
        aria-labelledby="coll-list-confirm-title"
        onClose={() => setConfirm(null)}
      >
        <div className="sp-copy-dialog-body">
          <h3 id="coll-list-confirm-title">{confirm === "list" ? copy.deleteTitle : copy.removeTitle(selected.length)}</h3>
          <p style={{ margin: 0 }}>{confirm === "list" ? copy.deleteBody : copy.removeBody}</p>
          <div className="sp-copy-dialog-actions">
            <button type="button" className="sp-copy-cancel" onClick={() => setConfirm(null)}>
              {copy.cancel}
            </button>
            <button
              type="button"
              className="sp-comment-confirm-delete"
              onClick={confirm === "list" ? deleteList : removeSelected}
              disabled={busy}
            >
              {confirm === "list" ? copy.delete : copy.remove}
            </button>
          </div>
        </div>
      </dialog>
    </>
  );
}
