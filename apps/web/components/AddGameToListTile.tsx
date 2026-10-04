"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { GamePicker, type PickerWork } from "@/components/GamePicker";
import { apiFetch } from "@/lib/client-api";

const COPY = {
  es: { add: "Añadir juego", toList: "a esta lista", title: "Añadir juego a la lista", error: "No se pudo añadir el juego." },
  en: { add: "Add game", toList: "to this list", title: "Add a game to the list", error: "Couldn't add the game." },
} as const;

/** Dashed "Añadir juego a esta lista" tile that ends the grid of a custom list
 * (design artboard "Colección con listas"). It opens the same collection
 * search used to pick a favorite or to recommend a game. */
export function AddGameToListTile({
  locale,
  listId,
  works,
  excludedIds,
}: {
  locale: "es" | "en";
  listId: string;
  works: PickerWork[];
  excludedIds: string[];
}) {
  const copy = COPY[locale];
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function pick(workId: string | null) {
    if (!workId) return;
    setError(null);
    try {
      const response = await apiFetch(`/api/library/lists/${listId}/items/`, { method: "POST", body: { work_id: workId } });
      if (!response.ok) {
        setError(copy.error);
        return;
      }
      setOpen(false);
      router.refresh();
    } catch {
      setError(copy.error);
    }
  }

  return (
    <li>
      <button type="button" className="sp-coll-add-tile" onClick={() => setOpen(true)}>
        <span className="sp-coll-add-plus" aria-hidden="true">
          +
        </span>
        <span>
          {copy.add}
          <br />
          {copy.toList}
        </span>
        {error ? (
          <span role="status" className="sp-coll-add-error">
            {error}
          </span>
        ) : null}
      </button>
      <GamePicker
        open={open}
        title={copy.title}
        works={works}
        excludedIds={excludedIds}
        currentWorkId={null}
        locale={locale}
        onPick={pick}
        onClose={() => setOpen(false)}
      />
    </li>
  );
}
