"use client";

import { GamePicker, type PickerWork } from "@/components/GamePicker";
import type { Cover } from "@/lib/api";

export interface EligibleWork extends PickerWork {
  work_slug: string;
  cover: Cover;
}

const COPY = {
  es: { title: (slot: number) => `Favorito ${slot}`, remove: "Quitar de favoritos" },
  en: { title: (slot: number) => `Favorite ${slot}`, remove: "Remove from favorites" },
} as const;

/** The picker for one of the five favorite slots: games already used in
 * another slot are not offered, and the current choice can be removed. */
export function ProfileFavoritePicker({
  slot,
  works,
  takenWorkIds,
  currentWorkId,
  locale,
  onPick,
  onClose,
}: {
  slot: number | null;
  works: EligibleWork[];
  takenWorkIds: string[];
  currentWorkId: string | null;
  locale: "es" | "en";
  onPick: (workId: string | null) => void;
  onClose: () => void;
}) {
  const copy = COPY[locale];
  return (
    <GamePicker
      open={slot !== null}
      title={slot !== null ? copy.title(slot) : ""}
      works={works}
      excludedIds={takenWorkIds}
      currentWorkId={currentWorkId}
      locale={locale}
      removeLabel={copy.remove}
      onPick={onPick}
      onClose={onClose}
    />
  );
}
