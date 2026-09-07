"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface SelectableCollectionItem {
  workId: string;
  title: string;
}

function readCookie(name: string): string | undefined {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

async function ensureCsrfToken(): Promise<string | undefined> {
  const current = readCookie("csrftoken");
  if (current) return current;
  await fetch("/api/accounts/csrf/", { credentials: "same-origin" });
  return readCookie("csrftoken");
}

export function CollectionBulkActions({
  items,
  locale,
}: {
  items: SelectableCollectionItem[];
  locale: "es" | "en";
}) {
  const router = useRouter();
  const [selecting, setSelecting] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(false);
  const copy = locale === "es"
    ? {
        select: "Seleccionar juegos",
        cancel: "Cancelar selección",
        remove: "Eliminar seleccionados",
        empty: "No hay juegos visibles para seleccionar.",
        error: "No se pudieron eliminar todos los juegos.",
      }
    : {
        select: "Select games",
        cancel: "Cancel selection",
        remove: "Remove selected",
        empty: "There are no visible games to select.",
        error: "Not all games could be removed.",
      };

  function toggle(workId: string) {
    setSelected((current) => (current.includes(workId) ? current.filter((id) => id !== workId) : [...current, workId]));
  }

  async function removeSelected() {
    if (selected.length === 0) return;
    if (!window.confirm(locale === "es" ? "¿Eliminar los juegos seleccionados y su configuración?" : "Remove the selected games and their configuration?")) return;
    setPending(true);
    setError(false);
    try {
      const csrfToken = await ensureCsrfToken();
      const responses = await Promise.all(
        selected.map((workId) =>
          fetch(`/api/library/entries/${workId}/`, {
            method: "DELETE",
            credentials: "same-origin",
            headers: csrfToken ? { "X-CSRFToken": csrfToken } : undefined,
          }),
        ),
      );
      if (responses.some((response) => !response.ok)) {
        setError(true);
        return;
      }
      setSelected([]);
      setSelecting(false);
      router.refresh();
    } catch {
      setError(true);
    } finally {
      setPending(false);
    }
  }

  if (!selecting) {
    return (
      <button type="button" className="sp-btn-secondary" onClick={() => setSelecting(true)} disabled={items.length === 0}>
        {copy.select}
      </button>
    );
  }

  return (
    <div className="sp-bulk-selection">
      <button type="button" className="sp-btn-secondary" onClick={() => { setSelecting(false); setSelected([]); }} disabled={pending}>
        {copy.cancel}
      </button>
      {items.length === 0 ? <p className="sp-meta">{copy.empty}</p> : null}
      <div className="sp-selection-list">
        {items.map((item) => (
          <label key={item.workId} className="sp-choice">
            <input type="checkbox" checked={selected.includes(item.workId)} onChange={() => toggle(item.workId)} disabled={pending} />
            <span>{item.title}</span>
          </label>
        ))}
      </div>
      <button type="button" className="sp-btn-danger" onClick={removeSelected} disabled={pending || selected.length === 0}>
        {pending ? "…" : `${copy.remove} (${selected.length})`}
      </button>
      {error ? <p role="alert">{copy.error}</p> : null}
    </div>
  );
}
