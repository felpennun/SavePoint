"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { PlatinumMedalIcon } from "@/components/PlatinumBadge";
import type { Release } from "@/lib/api";

const STATUSES = ["pending", "playing", "completed", "abandoned"] as const;
type Status = (typeof STATUSES)[number];
type CopyFormat = "physical" | "digital";

const COPY = {
  es: {
    configHeading: "Tu configuración",
    statusLegend: "Estado",
    statusLabels: { pending: "Pendiente", playing: "Jugando", completed: "Completado", abandoned: "Abandonado" },
    statusNone: "Sin estado",
    platinumLabel: "Marcar como platinado",
    platinumOnLabel: "Platinado (pulsa para desmarcar)",
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
    copyAdd: "Añadir copia",
    copyDialogNew: "Añadir copia",
    copyDialogEdit: "Editar copia",
    copySave: "Guardar copia",
    copyCancel: "Cancelar",
    copyUnknown: "Copia",
    copyAddAria: "Añadir copia",
    copyRemoveAria: "Eliminar copia",
    copyConfirmTitle: "¿Eliminar esta copia?",
    copyConfirmBody: "Esta acción no se puede deshacer.",
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
    statusNone: "No status",
    platinumLabel: "Mark as platinum",
    platinumOnLabel: "Platinum (press to unmark)",
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
    copyAdd: "Add copy",
    copyDialogNew: "Add copy",
    copyDialogEdit: "Edit copy",
    copySave: "Save copy",
    copyCancel: "Cancel",
    copyUnknown: "Copy",
    copyAddAria: "Add copy",
    copyRemoveAria: "Remove copy",
    copyConfirmTitle: "Remove this copy?",
    copyConfirmBody: "This cannot be undone.",
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
  // The copy form lives in a modal dialog so it never lengthens the page.
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingIsNew, setEditingIsNew] = useState(false);
  const editSnapshot = useRef<OwnedCopyItem | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  // Removing a copy (the "-" button) asks for confirmation first.
  const [confirmIndex, setConfirmIndex] = useState<number | null>(null);
  const confirmRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = confirmRef.current;
    if (!dialog) return;
    if (confirmIndex !== null && !dialog.open) dialog.showModal();
    if (confirmIndex === null && dialog.open) dialog.close();
  }, [confirmIndex]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (editingIndex !== null && !dialog.open) dialog.showModal();
    if (editingIndex === null && dialog.open) dialog.close();
  }, [editingIndex]);

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

  function copyName(item: OwnedCopyItem): string {
    const release = releases.find((candidate) => candidate.id === item.release_id);
    const platform = release?.platform ?? release?.release_name ?? copy.copyUnknown;
    const edition = release?.editions.find((candidate) => candidate.id === item.edition_id)?.name;
    return [platform, item.format === "physical" ? copy.copyPhysical : copy.copyDigital, edition]
      .filter(Boolean)
      .join(" · ");
  }

  function openNewCopy() {
    editSnapshot.current = null;
    setCopies((previous) => [...previous, newCopy(releases)]);
    setEditingIsNew(true);
    setEditingIndex(copies.length);
  }

  function openCopy(index: number) {
    editSnapshot.current = copies[index] ?? null;
    setEditingIsNew(false);
    setEditingIndex(index);
  }

  function cancelCopyEdit() {
    if (editingIndex === null) return;
    const index = editingIndex;
    if (editingIsNew) {
      setCopies((previous) => previous.filter((_, itemIndex) => itemIndex !== index));
    } else if (editSnapshot.current) {
      const snapshot = editSnapshot.current;
      setCopies((previous) => previous.map((item, itemIndex) => (itemIndex === index ? snapshot : item)));
    }
    setEditingIndex(null);
  }

  function askToRemoveEditedCopy() {
    if (editingIndex === null || editingIsNew) return;
    const index = editingIndex;
    const snapshot = editSnapshot.current;
    if (snapshot) {
      setCopies((previous) => previous.map((item, itemIndex) => (itemIndex === index ? snapshot : item)));
    }
    setEditingIndex(null);
    setConfirmIndex(index);
  }

  async function saveCopyEdit() {
    if (await saveConfiguration()) setEditingIndex(null);
  }

  async function removeConfirmedCopy() {
    if (confirmIndex === null) return;
    const remaining = copies.filter((_, itemIndex) => itemIndex !== confirmIndex);
    setConfirmIndex(null);
    await saveConfiguration(remaining);
  }

  async function saveConfiguration(copiesToSave: OwnedCopyItem[] = copies): Promise<boolean> {
    setSaving(true);
    setFeedback(null);
    try {
      const response = await apiPost(`/api/library/entries/${workId}/configuration/`, {
        status: status || null,
        rating_half_steps: rating || null,
        is_platinum: isPlatinum,
        copies: copiesToSave.map(
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
        return false;
      }
      const body = await response.json();
      setStatus(body.status ?? "");
      setRating(body.rating_half_steps ?? 0);
      setCopies(Array.isArray(body.copies) ? body.copies : []);
      setIsPlatinum(Boolean(body.is_platinum));
      setFeedback(copy.success);
      router.refresh();
      return true;
    } catch {
      setFeedback(copy.error);
      return false;
    } finally {
      setSaving(false);
    }
  }

  function renderCopyFields(item: OwnedCopyItem, index: number) {
    const selectedRelease = releases.find((release) => release.id === item.release_id);
    return (
      <div className="sp-copy-row">
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
  }

  return (
    <section className="sp-library-controls" aria-label={copy.configHeading}>
      <h3 className="sp-library-title">{copy.configHeading}</h3>
      <div className="sp-library-section sp-status-row">
        <div className="sp-field sp-status-select">
          <label htmlFor={`status-${workId}`}>{copy.statusLegend}</label>
          <select
            id={`status-${workId}`}
            value={status}
            onChange={(event) => setStatus(event.target.value as Status | "")}
            disabled={saving}
          >
            <option value="">{copy.statusNone}</option>
            {STATUSES.map((value) => (
              <option key={value} value={value}>
                {copy.statusLabels[value]}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className={`sp-platinum-button${isPlatinum ? " is-on" : ""}`}
          aria-pressed={isPlatinum}
          aria-label={isPlatinum ? copy.platinumOnLabel : copy.platinumLabel}
          title={isPlatinum ? copy.platinumOnLabel : copy.platinumLabel}
          onClick={() => setIsPlatinum((previous) => !previous)}
          disabled={saving}
        >
          <PlatinumMedalIcon />
        </button>
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
          <span className="sp-copy-heading-tools">
            <span className="sp-meta">{copies.length}</span>
            {releases.length > 0 ? (
              <button
                type="button"
                className="sp-copy-icon-button sp-copy-add-button"
                aria-label={copy.copyAddAria}
                title={copy.copyAddAria}
                onClick={openNewCopy}
                disabled={saving}
              >
                +
              </button>
            ) : null}
          </span>
        </div>
        {copies.length === 0 ? <p className="sp-meta">{copy.copiesEmpty}</p> : null}
        <ul className="sp-copy-list">
          {copies.map((item, index) => (
            <li key={item.id ?? item.idempotency_key ?? index}>
              <button type="button" className="sp-copy-item" onClick={() => openCopy(index)} disabled={saving}>
                {copyName(item)}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <dialog
        ref={dialogRef}
        className="sp-copy-dialog"
        aria-labelledby={`copy-dialog-title-${workId}`}
        onClose={() => {
          if (editingIndex !== null) cancelCopyEdit();
        }}
      >
        {editingIndex !== null && copies[editingIndex] ? (
          <div className="sp-copy-dialog-body">
            <h3 id={`copy-dialog-title-${workId}`}>{editingIsNew ? copy.copyDialogNew : copy.copyDialogEdit}</h3>
            {renderCopyFields(copies[editingIndex], editingIndex)}
            <div className="sp-copy-dialog-actions">
              {!editingIsNew ? (
                <button type="button" className="sp-copy-remove" onClick={askToRemoveEditedCopy} disabled={saving}>
                  {copy.removeCopy}
                </button>
              ) : null}
              <button type="button" className="sp-copy-cancel" onClick={cancelCopyEdit} disabled={saving}>
                {copy.copyCancel}
              </button>
              <button type="button" className="sp-btn-primary" onClick={saveCopyEdit} disabled={saving}>
                {saving ? copy.saving : copy.copySave}
              </button>
            </div>
          </div>
        ) : null}
      </dialog>

      <dialog
        ref={confirmRef}
        className="sp-copy-dialog sp-confirm-dialog"
        aria-labelledby={`copy-confirm-title-${workId}`}
        onClose={() => setConfirmIndex(null)}
      >
        <div className="sp-copy-dialog-body">
          <h3 id={`copy-confirm-title-${workId}`}>{copy.copyConfirmTitle}</h3>
          <p style={{ margin: 0 }}>
            {confirmIndex !== null && copies[confirmIndex] ? copyName(copies[confirmIndex]) : copy.copyConfirmBody}
          </p>
          <div className="sp-copy-dialog-actions">
            <button type="button" className="sp-copy-cancel" onClick={() => setConfirmIndex(null)}>
              {copy.copyCancel}
            </button>
            <button type="button" className="sp-comment-confirm-delete" onClick={removeConfirmedCopy} disabled={saving}>
              {copy.removeCopy}
            </button>
          </div>
        </div>
      </dialog>

      <div className="sp-library-save">
        <button type="button" className="sp-btn-primary" onClick={() => void saveConfiguration()} disabled={saving}>
          {saving ? copy.saving : copy.save}
        </button>
        {feedback ? <p role="status" data-testid="status-feedback">{feedback}</p> : null}
      </div>
    </section>
  );
}
