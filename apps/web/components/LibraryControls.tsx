"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import type { Release } from "@/lib/api";

const STATUSES = ["pending", "playing", "completed", "abandoned"] as const;
type Status = (typeof STATUSES)[number];
type CopyFormat = "physical" | "digital";

const COPY = {
  es: {
    configHeading: "Tu configuración",
    statusLegend: "Estado",
    statusLabels: { pending: "Pendiente", playing: "Jugando", completed: "Completado", abandoned: "Abandonado" },
    platinumLabel: "Marcar como platinado",
    ratingLabel: "Tu valoración",
    ratingUnrated: "Sin valorar",
    starLabel: "{n} de 5 estrellas",
    copiesHeading: "Copias que tienes",
    copiesEmpty: "Todavía no has añadido ninguna copia.",
    copyFormat: "Formato",
    copyPhysical: "Física",
    copyDigital: "Digital",
    copyRelease: "Plataforma",
    copyEdition: "Edición (opcional)",
    copyPurchaseDate: "Fecha de compra (opcional)",
    copyPrice: "Precio (opcional)",
    copyCurrency: "Moneda",
    copyStore: "Tienda (opcional)",
    copyConservation: "Estado de conservación",
    copyConservationNone: "—",
    copyConservationLabels: { new: "Nuevo", good: "Bueno", fair: "Aceptable", poor: "Deficiente", damaged: "Dañado" },
    copyStorageLocation: "Ubicación (opcional)",
    copyAdd: "Añadir otra copia",
    save: "Guardar configuración",
    saving: "Guardando configuración…",
    success: "Configuración guardada",
    removeCopy: "Eliminar",
    error: "No se pudo guardar la configuración. Inténtalo de nuevo.",
    loginRequired: "Inicia sesión para guardar estado, valoración o copias.",
    loading: "Cargando configuración…",
  },
  en: {
    configHeading: "Your setup",
    statusLegend: "Status",
    statusLabels: { pending: "Pending", playing: "Playing", completed: "Completed", abandoned: "Abandoned" },
    platinumLabel: "Mark as platinum",
    ratingLabel: "Your rating",
    ratingUnrated: "Unrated",
    starLabel: "{n} of 5 stars",
    copiesHeading: "Copies you own",
    copiesEmpty: "You have not added any copies yet.",
    copyFormat: "Format",
    copyPhysical: "Physical",
    copyDigital: "Digital",
    copyRelease: "Platform",
    copyEdition: "Edition (optional)",
    copyPurchaseDate: "Purchase date (optional)",
    copyPrice: "Price (optional)",
    copyCurrency: "Currency",
    copyStore: "Store (optional)",
    copyConservation: "Conservation state",
    copyConservationNone: "—",
    copyConservationLabels: { new: "New", good: "Good", fair: "Fair", poor: "Poor", damaged: "Damaged" },
    copyStorageLocation: "Storage location (optional)",
    copyAdd: "Add another copy",
    save: "Save configuration",
    saving: "Saving configuration…",
    success: "Configuration saved",
    removeCopy: "Remove",
    error: "We couldn't save the configuration. Try again.",
    loginRequired: "Log in to save status, rating, or copies.",
    loading: "Loading configuration…",
  },
} as const;

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

async function apiPost(path: string, body: unknown) {
  const csrfToken = await ensureCsrfToken();
  return fetch(path, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}) },
    body: JSON.stringify(body),
  });
}

type ConservationState = "new" | "good" | "fair" | "poor" | "damaged";
const CONSERVATION_STATES: ConservationState[] = ["new", "good", "fair", "poor", "damaged"];

interface OwnedCopyItem {
  id?: string;
  release_id: string;
  edition_id: string | null;
  format: CopyFormat;
  idempotency_key?: string;
  purchase_date: string | null;
  price: string | null;
  currency: string | null;
  store: string | null;
  conservation_state: ConservationState | null;
  storage_location: string | null;
}

function newCopy(releases: Release[]): OwnedCopyItem {
  const idempotencyKey =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return {
    release_id: releases[0]?.id ?? "",
    edition_id: null,
    format: "physical",
    idempotency_key: idempotencyKey,
    purchase_date: null,
    price: null,
    currency: null,
    store: null,
    conservation_state: null,
    storage_location: null,
  };
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
  const router = useRouter();
  const [loading, setLoading] = useState(isAuthenticated);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [status, setStatus] = useState<Status | "">("");
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [copies, setCopies] = useState<OwnedCopyItem[]>([]);
  const [isPlatinum, setIsPlatinum] = useState(false);

  /** While the pointer or keyboard focus is over the stars, preview that
   * value; otherwise show the saved rating. Both are in half-steps (1..10). */
  const displayRating = hoverRating || rating;

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    Promise.all([
      fetch(`/api/library/entries/${workId}/status/`, { credentials: "same-origin" }).then((r) => r.json()),
      fetch(`/api/library/entries/${workId}/rating/`, { credentials: "same-origin" }).then((r) => r.json()),
      fetch(`/api/library/entries/${workId}/copies/`, { credentials: "same-origin" }).then((r) => r.json()),
      // is_platinum has no bespoke endpoint of its own -- it rides the
      // combined configuration/ GET alongside status/rating/copies, which
      // are still fetched individually above for backward compatibility.
      fetch(`/api/library/entries/${workId}/configuration/`, { credentials: "same-origin" }).then((r) => r.json()),
    ])
      .then(([statusBody, ratingBody, copiesBody, configurationBody]) => {
        if (cancelled) return;
        setStatus(statusBody.status ?? "");
        setRating(ratingBody.rating_half_steps ?? 0);
        if (Array.isArray(copiesBody.copies)) setCopies(copiesBody.copies);
        setIsPlatinum(Boolean(configurationBody.is_platinum));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workId, isAuthenticated]);

  if (!isAuthenticated) return <p>{copy.loginRequired}</p>;
  if (loading) return <p aria-live="polite">{copy.loading}</p>;

  function updateCopy(index: number, patch: Partial<OwnedCopyItem>) {
    setCopies((previous) => previous.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)));
  }

  async function saveConfiguration() {
    setSaving(true);
    setFeedback(null);
    try {
      const response = await apiPost(`/api/library/entries/${workId}/configuration/`, {
        status: status || null,
        rating_half_steps: rating || null,
        is_platinum: isPlatinum,
        copies: copies.map(
          ({ id, release_id, edition_id, format, idempotency_key, purchase_date, price, currency, store, conservation_state, storage_location }) => ({
            ...(id ? { id } : { idempotency_key }),
            release_id,
            edition_id,
            format,
            purchase_date,
            price,
            currency,
            store,
            conservation_state: format === "digital" ? null : conservation_state,
            storage_location: format === "digital" ? null : storage_location,
          }),
        ),
      });
      if (!response.ok) {
        setFeedback(copy.error);
        return;
      }
      const body = await response.json();
      setStatus(body.status ?? "");
      setRating(body.rating_half_steps ?? 0);
      setCopies(Array.isArray(body.copies) ? body.copies : []);
      setIsPlatinum(Boolean(body.is_platinum));
      setFeedback(copy.success);
      router.refresh();
    } catch {
      setFeedback(copy.error);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="sp-library-controls" aria-label={copy.configHeading}>
      <h3 className="sp-library-title">{copy.configHeading}</h3>
      <fieldset className="sp-library-section">
        <legend>{copy.statusLegend}</legend>
        <div className="sp-status-options">
          {STATUSES.map((value) => (
            <label key={value} className="sp-choice">
              <input type="radio" name={`status-${workId}`} value={value} checked={status === value} onChange={() => setStatus(value)} />
              <span>{copy.statusLabels[value]}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="sp-library-section">
        <label className="sp-choice sp-platinum-toggle">
          <input
            type="checkbox"
            checked={isPlatinum}
            onChange={(event) => setIsPlatinum(event.target.checked)}
            disabled={saving}
          />
          <span>{copy.platinumLabel}</span>
        </label>
      </div>

      <div className="sp-library-section">
        <div className="sp-section-heading-row">
          <h3>{copy.ratingLabel}</h3>
          <span className="sp-rating-value">
            {displayRating > 0
              ? `${(displayRating / 2).toFixed(1).replace(".", locale === "es" ? "," : ".")} / 5`
              : copy.ratingUnrated}
          </span>
        </div>
        <div
          className="sp-interactive-stars"
          role="group"
          aria-label={copy.ratingLabel}
          onMouseLeave={() => setHoverRating(0)}
        >
          {Array.from({ length: 5 }, (_, index) => (
            <span className="sp-star-unit" key={index}>
              <span
                className={`sp-star-glyph${displayRating >= (index + 1) * 2 ? " is-filled" : ""}${
                  displayRating === index * 2 + 1 ? " is-half" : ""
                }`}
                aria-hidden="true"
              >
                ★
              </span>
              {[1, 2].map((half) => {
                const halfStep = index * 2 + half;
                const value = halfStep / 2;
                const label = copy.starLabel.replace("{n}", value.toFixed(1));
                return (
                  <button
                    key={halfStep}
                    type="button"
                    className={`sp-star-half-button${half === 1 ? " is-left" : " is-right"}`}
                    aria-label={label}
                    aria-pressed={rating === halfStep}
                    onClick={() => setRating(rating === halfStep ? 0 : halfStep)}
                    onMouseEnter={() => setHoverRating(halfStep)}
                    onFocus={() => setHoverRating(halfStep)}
                    onBlur={() => setHoverRating(0)}
                    disabled={saving}
                  />
                );
              })}
            </span>
          ))}
        </div>
      </div>

      <div className="sp-library-section">
        <div className="sp-section-heading-row">
          <h3>{copy.copiesHeading}</h3>
          <span className="sp-meta">{copies.length}</span>
        </div>
        {copies.length === 0 ? <p className="sp-meta">{copy.copiesEmpty}</p> : null}
        <div className="sp-copy-list">
          {copies.map((item, index) => {
            const selectedRelease = releases.find((release) => release.id === item.release_id);
            return (
              <div className="sp-copy-row" key={item.id ?? item.idempotency_key ?? index}>
                <button
                  type="button"
                  className="sp-copy-remove"
                  onClick={() => setCopies((previous) => previous.filter((_, itemIndex) => itemIndex !== index))}
                  disabled={saving}
                >
                  {copy.removeCopy}
                </button>
                <div className="sp-field">
                  <label htmlFor={`copy-release-${index}`}>{copy.copyRelease}</label>
                  <select
                    id={`copy-release-${index}`}
                    value={item.release_id}
                    onChange={(event) => updateCopy(index, { release_id: event.target.value, edition_id: null })}
                    disabled={releases.length === 0 || saving}
                  >
                    {releases.map((release) => (
                      <option key={release.id} value={release.id}>
                        {release.platform ?? release.release_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="sp-field">
                  <label htmlFor={`copy-format-${index}`}>{copy.copyFormat}</label>
                  <select
                    id={`copy-format-${index}`}
                    value={item.format}
                    onChange={(event) => {
                      const format = event.target.value as CopyFormat;
                      updateCopy(
                        index,
                        format === "digital"
                          ? { format, conservation_state: null, storage_location: null }
                          : { format },
                      );
                    }}
                    disabled={saving}
                  >
                    <option value="physical">{copy.copyPhysical}</option>
                    <option value="digital">{copy.copyDigital}</option>
                  </select>
                </div>
                {selectedRelease && selectedRelease.editions.length > 0 ? (
                  <div className="sp-field">
                    <label htmlFor={`copy-edition-${index}`}>{copy.copyEdition}</label>
                    <select
                      id={`copy-edition-${index}`}
                      value={item.edition_id ?? ""}
                      onChange={(event) => updateCopy(index, { edition_id: event.target.value || null })}
                      disabled={saving}
                    >
                      <option value="">—</option>
                      {selectedRelease.editions.map((edition) => (
                        <option key={edition.id} value={edition.id}>
                          {edition.name}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : null}

                <div className="sp-field">
                  <label htmlFor={`copy-purchase-date-${index}`}>{copy.copyPurchaseDate}</label>
                  <input
                    id={`copy-purchase-date-${index}`}
                    type="date"
                    value={item.purchase_date ?? ""}
                    onChange={(event) => updateCopy(index, { purchase_date: event.target.value || null })}
                    disabled={saving}
                  />
                </div>
                <div className="sp-field">
                  <label htmlFor={`copy-price-${index}`}>{copy.copyPrice}</label>
                  <input
                    id={`copy-price-${index}`}
                    type="number"
                    min="0"
                    step="0.01"
                    inputMode="decimal"
                    value={item.price ?? ""}
                    onChange={(event) => updateCopy(index, { price: event.target.value || null })}
                    disabled={saving}
                  />
                </div>
                <div className="sp-field">
                  <label htmlFor={`copy-currency-${index}`}>{copy.copyCurrency}</label>
                  <input
                    id={`copy-currency-${index}`}
                    type="text"
                    maxLength={3}
                    placeholder="EUR"
                    value={item.currency ?? ""}
                    onChange={(event) => updateCopy(index, { currency: event.target.value.toUpperCase() || null })}
                    disabled={saving}
                  />
                </div>
                <div className="sp-field">
                  <label htmlFor={`copy-store-${index}`}>{copy.copyStore}</label>
                  <input
                    id={`copy-store-${index}`}
                    type="text"
                    value={item.store ?? ""}
                    onChange={(event) => updateCopy(index, { store: event.target.value || null })}
                    disabled={saving}
                  />
                </div>
                {item.format === "physical" ? (
                  <>
                    <div className="sp-field">
                      <label htmlFor={`copy-conservation-${index}`}>{copy.copyConservation}</label>
                      <select
                        id={`copy-conservation-${index}`}
                        value={item.conservation_state ?? ""}
                        onChange={(event) =>
                          updateCopy(index, { conservation_state: (event.target.value || null) as ConservationState | null })
                        }
                        disabled={saving}
                      >
                        <option value="">{copy.copyConservationNone}</option>
                        {CONSERVATION_STATES.map((state) => (
                          <option key={state} value={state}>
                            {copy.copyConservationLabels[state]}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="sp-field">
                      <label htmlFor={`copy-storage-location-${index}`}>{copy.copyStorageLocation}</label>
                      <input
                        id={`copy-storage-location-${index}`}
                        type="text"
                        value={item.storage_location ?? ""}
                        onChange={(event) => updateCopy(index, { storage_location: event.target.value || null })}
                        disabled={saving}
                      />
                    </div>
                  </>
                ) : null}
              </div>
            );
          })}
        </div>
        {releases.length > 0 ? (
          <button type="button" className="sp-copy-add" onClick={() => setCopies((previous) => [...previous, newCopy(releases)])} disabled={saving}>
            {copy.copyAdd}
          </button>
        ) : null}
      </div>

      <div className="sp-library-save">
        <button type="button" className="sp-btn-primary" onClick={saveConfiguration} disabled={saving}>
          {saving ? copy.saving : copy.save}
        </button>
        {feedback ? <p role="status" data-testid="configuration-feedback">{feedback}</p> : null}
      </div>
    </section>
  );
}
