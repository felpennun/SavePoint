"use client";

import { useEffect, useState } from "react";

import type { Release } from "@/lib/api";

const STATUSES = ["pending", "playing", "completed", "abandoned"] as const;
type Status = (typeof STATUSES)[number];

const COPY = {
  es: {
    statusLegend: "Estado:",
    statusLabels: { pending: "Pendiente", playing: "Jugando", completed: "Completado", abandoned: "Abandonado" },
    statusSave: "Guardar estado",
    statusSaving: "Guardando…",
    statusSuccess: "Estado guardado",
    ratingLabel: "Valoración",
    ratingUnrated: "Sin valorar",
    ratingSave: "Guardar valoración",
    ratingSaving: "Guardando…",
    ratingSuccess: "Valoración guardada",
    ratingClear: "Borrar valoración",
    copiesHeading: "Copias",
    copiesEmpty: "Sin copias registradas.",
    copyFormat: "Formato",
    copyPhysical: "Física",
    copyDigital: "Digital",
    copyRelease: "Edición/plataforma",
    copyEdition: "Edición (opcional)",
    copyAdd: "Añadir copia",
    copyAdding: "Añadiendo…",
    copyAdded: "Copia añadida",
    error: "No se pudo guardar. Inténtalo de nuevo.",
    loginRequired: "Inicia sesión para guardar estado, valoración o copias.",
    loading: "Cargando…",
  },
  en: {
    statusLegend: "Status:",
    statusLabels: { pending: "Pending", playing: "Playing", completed: "Completed", abandoned: "Abandoned" },
    statusSave: "Save status",
    statusSaving: "Saving…",
    statusSuccess: "Status saved",
    ratingLabel: "Rating",
    ratingUnrated: "Unrated",
    ratingSave: "Save rating",
    ratingSaving: "Saving…",
    ratingSuccess: "Rating saved",
    ratingClear: "Clear rating",
    copiesHeading: "Copies",
    copiesEmpty: "No copies registered.",
    copyFormat: "Format",
    copyPhysical: "Physical",
    copyDigital: "Digital",
    copyRelease: "Release/platform",
    copyEdition: "Edition (optional)",
    copyAdd: "Add copy",
    copyAdding: "Adding…",
    copyAdded: "Copy added",
    error: "We couldn't save that. Try again.",
    loginRequired: "Log in to save status, rating, or copies.",
    loading: "Loading…",
  },
} as const;

function readCookie(name: string): string | undefined {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

async function apiPost(path: string, body: unknown) {
  const csrfToken = readCookie("csrftoken");
  return fetch(path, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}) },
    body: JSON.stringify(body),
  });
}

interface OwnedCopyItem {
  id: string;
  release_id: string;
  edition_id: string | null;
  format: "physical" | "digital";
}

export function LibraryControls({
  workId,
  locale,
  isAuthenticated,
  releases,
}: {
  workId: string;
  locale: "es" | "en";
  isAuthenticated: boolean;
  releases: Release[];
}) {
  const copy = COPY[locale];
  const [loading, setLoading] = useState(isAuthenticated);

  const [status, setStatus] = useState<Status | "">("");
  const [statusPending, setStatusPending] = useState(false);
  const [statusFeedback, setStatusFeedback] = useState<string | null>(null);

  const [rating, setRating] = useState<number>(0); // half-steps, 0 = unrated
  const [ratingPending, setRatingPending] = useState(false);
  const [ratingFeedback, setRatingFeedback] = useState<string | null>(null);

  const [copies, setCopies] = useState<OwnedCopyItem[]>([]);
  const [releaseId, setReleaseId] = useState(releases[0]?.id ?? "");
  const [editionId, setEditionId] = useState("");
  const [format, setFormat] = useState<"physical" | "digital">("physical");
  const [copyPending, setCopyPending] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    Promise.all([
      fetch(`/api/library/entries/${workId}/status/`, { credentials: "same-origin" }).then((r) => r.json()),
      fetch(`/api/library/entries/${workId}/rating/`, { credentials: "same-origin" }).then((r) => r.json()),
      fetch(`/api/library/entries/${workId}/copies/`, { credentials: "same-origin" }).then((r) => r.json()),
    ])
      .then(([statusBody, ratingBody, copiesBody]) => {
        if (cancelled) return;
        if (statusBody.status) setStatus(statusBody.status);
        if (ratingBody.rating_half_steps) setRating(ratingBody.rating_half_steps);
        if (Array.isArray(copiesBody.copies)) setCopies(copiesBody.copies);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workId, isAuthenticated]);

  if (!isAuthenticated) {
    return <p>{copy.loginRequired}</p>;
  }
  if (loading) {
    return <p aria-live="polite">{copy.loading}</p>;
  }

  async function saveStatus() {
    if (!status) return;
    setStatusPending(true);
    setStatusFeedback(null);
    try {
      const response = await apiPost(`/api/library/entries/${workId}/status/`, { status });
      setStatusFeedback(response.ok ? copy.statusSuccess : copy.error);
    } catch {
      setStatusFeedback(copy.error);
    } finally {
      setStatusPending(false);
    }
  }

  async function saveRating(nextValue: number | null) {
    setRatingPending(true);
    setRatingFeedback(null);
    try {
      const response = await apiPost(`/api/library/entries/${workId}/rating/`, { rating_half_steps: nextValue });
      if (response.ok) {
        setRating(nextValue ?? 0);
        setRatingFeedback(copy.ratingSuccess);
      } else {
        setRatingFeedback(copy.error);
      }
    } catch {
      setRatingFeedback(copy.error);
    } finally {
      setRatingPending(false);
    }
  }

  async function addCopy() {
    if (!releaseId) return;
    setCopyPending(true);
    setCopyFeedback(null);
    try {
      const idempotencyKey = crypto.randomUUID();
      const response = await apiPost(`/api/library/entries/${workId}/copies/`, {
        release_id: releaseId,
        edition_id: editionId || null,
        format,
        idempotency_key: idempotencyKey,
      });
      if (response.ok) {
        const body = await response.json();
        setCopies((prev) => [body.copy, ...prev]);
        setCopyFeedback(copy.copyAdded);
      } else {
        setCopyFeedback(copy.error);
      }
    } catch {
      setCopyFeedback(copy.error);
    } finally {
      setCopyPending(false);
    }
  }

  const selectedRelease = releases.find((r) => r.id === releaseId);
  const ratingStars = (rating / 2).toFixed(1);

  return (
    <div>
      <fieldset>
        <legend>{copy.statusLegend}</legend>
        {STATUSES.map((value) => (
          <label key={value}>
            <input type="radio" name="status" value={value} checked={status === value} onChange={() => setStatus(value)} />
            {copy.statusLabels[value]}
          </label>
        ))}
        <button type="button" onClick={saveStatus} disabled={statusPending || !status}>
          {statusPending ? copy.statusSaving : copy.statusSave}
        </button>
        {statusFeedback ? (
          <p role="status" data-testid="status-feedback">
            {statusFeedback}
          </p>
        ) : null}
      </fieldset>

      <div>
        <label htmlFor="rating-range">
          {copy.ratingLabel}: {rating > 0 ? `${ratingStars}` : copy.ratingUnrated}
        </label>
        <input
          id="rating-range"
          type="range"
          min={1}
          max={10}
          step={1}
          value={rating || 1}
          onChange={(event) => setRating(Number(event.target.value))}
          aria-valuetext={ratingStars}
        />
        <button type="button" onClick={() => saveRating(rating || 1)} disabled={ratingPending}>
          {ratingPending ? copy.ratingSaving : copy.ratingSave}
        </button>
        <button type="button" onClick={() => saveRating(null)} disabled={ratingPending || rating === 0}>
          {copy.ratingClear}
        </button>
        {ratingFeedback ? (
          <p role="status" data-testid="rating-feedback">
            {ratingFeedback}
          </p>
        ) : null}
      </div>

      <div>
        <h3>{copy.copiesHeading}</h3>
        {copies.length === 0 ? <p>{copy.copiesEmpty}</p> : null}
        <ul>
          {copies.map((item) => (
            <li key={item.id}>
              {item.format === "physical" ? copy.copyPhysical : copy.copyDigital}
            </li>
          ))}
        </ul>
        {releases.length > 0 ? (
          <div>
            <label htmlFor="copy-release">{copy.copyRelease}</label>
            <select
              id="copy-release"
              value={releaseId}
              onChange={(event) => {
                setReleaseId(event.target.value);
                setEditionId("");
              }}
            >
              {releases.map((release) => (
                <option key={release.id} value={release.id}>
                  {release.platform ?? release.release_name}
                </option>
              ))}
            </select>

            {selectedRelease && selectedRelease.editions.length > 0 ? (
              <>
                <label htmlFor="copy-edition">{copy.copyEdition}</label>
                <select id="copy-edition" value={editionId} onChange={(event) => setEditionId(event.target.value)}>
                  <option value="">—</option>
                  {selectedRelease.editions.map((edition) => (
                    <option key={edition.id} value={edition.id}>
                      {edition.name}
                    </option>
                  ))}
                </select>
              </>
            ) : null}

            <label htmlFor="copy-format">{copy.copyFormat}</label>
            <select id="copy-format" value={format} onChange={(event) => setFormat(event.target.value as "physical" | "digital")}>
              <option value="physical">{copy.copyPhysical}</option>
              <option value="digital">{copy.copyDigital}</option>
            </select>

            <button type="button" onClick={addCopy} disabled={copyPending}>
              {copyPending ? copy.copyAdding : copy.copyAdd}
            </button>
            {copyFeedback ? (
              <p role="status" data-testid="copy-feedback">
                {copyFeedback}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
