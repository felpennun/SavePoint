"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { apiFetch } from "@/lib/client-api";

type Visibility = "public" | "private";

interface ListItemDto {
  id: string;
  work_id: string;
  work_slug: string;
  work_title: string;
  position: number;
}

interface ListDto {
  id: string;
  name: string;
  visibility: Visibility;
  version: number;
  items: ListItemDto[];
}

const COPY = {
  es: {
    heading: "Tus listas",
    empty: "Todavía no has creado ninguna lista.",
    newName: "Nombre de la nueva lista",
    newVisibility: "Visibilidad",
    public: "Pública",
    private: "Privada",
    create: "Crear lista",
    creating: "Creando…",
    delete: "Eliminar lista",
    deleting: "Eliminando…",
    addItem: "Añadir juego",
    addItemPlaceholder: "Elige un juego de tu colección",
    add: "Añadir",
    adding: "Añadiendo…",
    remove: "Quitar",
    moveUp: "Subir",
    moveDown: "Bajar",
    listEmpty: "Lista vacía. Añade juegos de tu colección.",
    conflict: "La lista cambió en otra pestaña; se ha recargado el orden actual.",
    error: "No se pudo completar la acción. Inténtalo de nuevo.",
    loading: "Cargando listas…",
  },
  en: {
    heading: "Your lists",
    empty: "You haven't created any lists yet.",
    newName: "New list name",
    newVisibility: "Visibility",
    public: "Public",
    private: "Private",
    create: "Create list",
    creating: "Creating…",
    delete: "Delete list",
    deleting: "Deleting…",
    addItem: "Add game",
    addItemPlaceholder: "Pick a game from your collection",
    add: "Add",
    adding: "Adding…",
    remove: "Remove",
    moveUp: "Move up",
    moveDown: "Move down",
    listEmpty: "Empty list. Add games from your collection.",
    conflict: "The list changed in another tab; the current order was reloaded.",
    error: "Couldn't complete the action. Try again.",
    loading: "Loading lists…",
  },
} as const;

/** Custom lists CRUD + reorder (LIB-04, D-06/D-07). Reorder uses
 * up/down buttons rather than drag-and-drop -- keyboard- and
 * screen-reader-operable by construction, and it maps directly onto the
 * backend's optimistic `expected_version` + full `item_ids` contract. */
export function CustomLists({
  locale,
  collectionItems,
}: {
  locale: "es" | "en";
  collectionItems: { work_id: string; work_title: string }[];
}) {
  const copy = COPY[locale];
  const [loading, setLoading] = useState(true);
  const [lists, setLists] = useState<ListDto[]>([]);
  const [newName, setNewName] = useState("");
  const [newVisibility, setNewVisibility] = useState<Visibility>("public");
  const [creating, setCreating] = useState(false);
  const [busyListId, setBusyListId] = useState<string | null>(null);
  const [pickerByList, setPickerByList] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch("/api/library/lists/")
      .then((response) => (response.ok ? response.json() : { lists: [] }))
      .then((body) => {
        if (!cancelled) setLists(Array.isArray(body?.lists) ? body.lists : []);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <p aria-live="polite">{copy.loading}</p>;

  async function reloadList(listId: string) {
    const response = await apiFetch(`/api/library/lists/${listId}/`);
    if (response.ok) {
      const fresh = (await response.json()) as ListDto;
      setLists((previous) => previous.map((list) => (list.id === listId ? fresh : list)));
    }
  }

  async function createList() {
    if (!newName.trim()) return;
    setCreating(true);
    setFeedback(null);
    try {
      const response = await apiFetch("/api/library/lists/", {
        method: "POST",
        body: { name: newName, visibility: newVisibility },
      });
      if (!response.ok) {
        setFeedback(copy.error);
        return;
      }
      const created = (await response.json()) as ListDto;
      setLists((previous) => [...previous, created]);
      setNewName("");
    } catch {
      setFeedback(copy.error);
    } finally {
      setCreating(false);
    }
  }

  async function deleteList(listId: string) {
    setBusyListId(listId);
    try {
      const response = await apiFetch(`/api/library/lists/${listId}/`, { method: "DELETE" });
      if (!response.ok && response.status !== 204) {
        setFeedback(copy.error);
        return;
      }
      setLists((previous) => previous.filter((list) => list.id !== listId));
    } catch {
      setFeedback(copy.error);
    } finally {
      setBusyListId(null);
    }
  }

  async function addItem(listId: string) {
    const workId = pickerByList[listId];
    if (!workId) return;
    setBusyListId(listId);
    try {
      const response = await apiFetch(`/api/library/lists/${listId}/items/`, { method: "POST", body: { work_id: workId } });
      if (!response.ok) {
        setFeedback(copy.error);
        return;
      }
      await reloadList(listId);
      setPickerByList((previous) => ({ ...previous, [listId]: "" }));
    } catch {
      setFeedback(copy.error);
    } finally {
      setBusyListId(null);
    }
  }

  async function removeItem(listId: string, itemId: string) {
    setBusyListId(listId);
    try {
      const response = await apiFetch(`/api/library/lists/${listId}/items/${itemId}/`, { method: "DELETE" });
      if (!response.ok && response.status !== 204) {
        setFeedback(copy.error);
        return;
      }
      await reloadList(listId);
    } catch {
      setFeedback(copy.error);
    } finally {
      setBusyListId(null);
    }
  }

  async function reorder(list: ListDto, fromIndex: number, direction: -1 | 1) {
    const toIndex = fromIndex + direction;
    if (toIndex < 0 || toIndex >= list.items.length) return;
    const reordered = [...list.items];
    [reordered[fromIndex], reordered[toIndex]] = [reordered[toIndex], reordered[fromIndex]];
    const itemIds = reordered.map((item) => item.id);

    setBusyListId(list.id);
    try {
      const response = await apiFetch(`/api/library/lists/${list.id}/reorder/`, {
        method: "POST",
        body: { expected_version: list.version, item_ids: itemIds },
      });
      if (response.status === 409) {
        setFeedback(copy.conflict);
        await reloadList(list.id);
        return;
      }
      if (!response.ok) {
        setFeedback(copy.error);
        return;
      }
      const updated = (await response.json()) as ListDto;
      setLists((previous) => previous.map((existing) => (existing.id === list.id ? updated : existing)));
    } catch {
      setFeedback(copy.error);
    } finally {
      setBusyListId(null);
    }
  }

  return (
    <section className="sp-custom-lists" aria-label={copy.heading}>
      <h2 className="sp-h2">{copy.heading}</h2>

      <div className="sp-copy-row">
        <div className="sp-field">
          <label htmlFor="new-list-name">{copy.newName}</label>
          <input id="new-list-name" value={newName} onChange={(event) => setNewName(event.target.value)} disabled={creating} />
        </div>
        <div className="sp-field">
          <label htmlFor="new-list-visibility">{copy.newVisibility}</label>
          <select
            id="new-list-visibility"
            value={newVisibility}
            onChange={(event) => setNewVisibility(event.target.value as Visibility)}
            disabled={creating}
          >
            <option value="public">{copy.public}</option>
            <option value="private">{copy.private}</option>
          </select>
        </div>
        <button type="button" className="sp-btn-primary" onClick={createList} disabled={creating || !newName.trim()}>
          {creating ? copy.creating : copy.create}
        </button>
      </div>

      {feedback ? (
        <p role="status" data-testid="lists-feedback">
          {feedback}
        </p>
      ) : null}

      {lists.length === 0 ? (
        <p className="sp-meta">{copy.empty}</p>
      ) : (
        <div className="sp-profile-lists">
          {lists.map((list) => {
            const busy = busyListId === list.id;
            const usedWorkIds = new Set(list.items.map((item) => item.work_id));
            const pickableItems = collectionItems.filter((item) => !usedWorkIds.has(item.work_id));
            return (
              <div className="sp-profile-list-card" key={list.id}>
                <div className="sp-section-heading-row">
                  <h3 className="sp-library-title">{list.name}</h3>
                  <button type="button" className="sp-copy-remove sp-list-delete" onClick={() => deleteList(list.id)} disabled={busy}>
                    {busy ? copy.deleting : copy.delete}
                  </button>
                </div>

                {list.items.length === 0 ? (
                  <p className="sp-meta">{copy.listEmpty}</p>
                ) : (
                  <ol className="sp-list-items">
                    {list.items.map((item, index) => (
                      <li key={item.id}>
                        <Link href={`/${locale}/games/${item.work_slug}`} className="sp-link">
                          {item.work_title}
                        </Link>
                        <span className="sp-list-item-actions">
                          <button
                            type="button"
                            className="sp-copy-add sp-list-item-up"
                            aria-label={copy.moveUp}
                            onClick={() => reorder(list, index, -1)}
                            disabled={busy || index === 0}
                          >
                            ↑
                          </button>
                          <button
                            type="button"
                            className="sp-copy-add sp-list-item-down"
                            aria-label={copy.moveDown}
                            onClick={() => reorder(list, index, 1)}
                            disabled={busy || index === list.items.length - 1}
                          >
                            ↓
                          </button>
                          <button
                            type="button"
                            className="sp-copy-remove sp-list-item-remove"
                            onClick={() => removeItem(list.id, item.id)}
                            disabled={busy}
                          >
                            {copy.remove}
                          </button>
                        </span>
                      </li>
                    ))}
                  </ol>
                )}

                {pickableItems.length > 0 ? (
                  <div className="sp-field">
                    <label htmlFor={`add-item-${list.id}`}>{copy.addItem}</label>
                    <select
                      id={`add-item-${list.id}`}
                      value={pickerByList[list.id] ?? ""}
                      onChange={(event) => setPickerByList((previous) => ({ ...previous, [list.id]: event.target.value }))}
                      disabled={busy}
                    >
                      <option value="">{copy.addItemPlaceholder}</option>
                      {pickableItems.map((item) => (
                        <option key={item.work_id} value={item.work_id}>
                          {item.work_title}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className="sp-copy-add sp-list-item-add"
                      onClick={() => addItem(list.id)}
                      disabled={busy || !pickerByList[list.id]}
                    >
                      {busy ? copy.adding : copy.add}
                    </button>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
