"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { CoverImage } from "@/components/CoverImage";
import type { Cover } from "@/lib/api";

export interface PickerWork {
  work_id: string;
  work_title: string;
  cover: Cover;
}

const COPY = {
  es: { search: "Buscar en tu colección", empty: "No hay juegos que coincidan.", close: "Cerrar", coverMissing: "Portada no disponible" },
  en: { search: "Search your collection", empty: "No games match.", close: "Close", coverMissing: "Cover not available" },
} as const;

const MAX_ROWS = 60;

function normalize(value: string): string {
  return value.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

/** Modal list of the games in the user's collection with a search box, used to
 * choose one game (a favorite, or the game to recommend to a friend). */
export function GamePicker({
  open,
  title,
  works,
  excludedIds = [],
  currentWorkId,
  locale,
  removeLabel,
  onPick,
  onClose,
}: {
  open: boolean;
  title: string;
  works: PickerWork[];
  /** Games that cannot be chosen again (the current one is always offered). */
  excludedIds?: string[];
  currentWorkId: string | null;
  locale: "es" | "en";
  /** When set, a button with this label lets the user clear the current choice. */
  removeLabel?: string;
  onPick: (workId: string | null) => void;
  onClose: () => void;
}) {
  const copy = COPY[locale];
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      setQuery("");
      dialog.showModal();
    }
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const visible = useMemo(() => {
    const needle = normalize(query.trim());
    return works
      .filter((work) => !excludedIds.includes(work.work_id) || work.work_id === currentWorkId)
      .filter((work) => !needle || normalize(work.work_title).includes(needle))
      .slice(0, MAX_ROWS);
  }, [works, excludedIds, currentWorkId, query]);

  return (
    <dialog
      ref={dialogRef}
      className="sp-copy-dialog sp-pf-picker-dialog"
      aria-labelledby="game-picker-title"
      onClose={onClose}
    >
      <div className="sp-copy-dialog-body">
        <h3 id="game-picker-title">{title}</h3>
        <div className="sp-field">
          <label htmlFor="game-picker-search" className="visually-hidden">
            {copy.search}
          </label>
          <input
            id="game-picker-search"
            type="search"
            value={query}
            placeholder={copy.search}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        {visible.length === 0 ? (
          <p className="sp-meta" style={{ margin: 0 }}>
            {copy.empty}
          </p>
        ) : (
          <ul className="sp-pf-picker-list">
            {visible.map((work) => (
              <li key={work.work_id}>
                <button
                  type="button"
                  className={`sp-pf-picker-row${work.work_id === currentWorkId ? " is-current" : ""}`}
                  onClick={() => onPick(work.work_id)}
                >
                  <span className="sp-pf-picker-cover">
                    <CoverImage
                      src={work.cover.url}
                      alt=""
                      title={work.work_title}
                      missingLabel={copy.coverMissing}
                      width={36}
                      height={48}
                    />
                  </span>
                  <span>{work.work_title}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
        <div className="sp-copy-dialog-actions">
          {removeLabel && currentWorkId ? (
            <button type="button" className="sp-copy-remove" onClick={() => onPick(null)}>
              {removeLabel}
            </button>
          ) : null}
          <button type="button" className="sp-copy-cancel" onClick={onClose}>
            {copy.close}
          </button>
        </div>
      </div>
    </dialog>
  );
}
