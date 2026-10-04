"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/client-api";

const COPY = {
  es: { name: "Nombre de la lista", friends: "Amistades", private: "Privada", visibility: "Visibilidad", create: "Crear", creating: "Creando…", error: "No se pudo crear la lista." },
  en: { name: "List name", friends: "Friends", private: "Private", visibility: "Visibility", create: "Create", creating: "Creating…", error: "Couldn't create the list." },
} as const;

/** "MIS LISTAS" heading with its "+ NUEVA" button; the button opens a small
 * inline form and, once the list exists, jumps to it. */
export function SidebarNewList({
  locale,
  heading,
  newLabel,
  basePath,
}: {
  locale: "es" | "en";
  heading: string;
  newLabel: string;
  basePath: string;
}) {
  const copy = COPY[locale];
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [visibility, setVisibility] = useState<"public" | "private">("public");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const response = await apiFetch("/api/library/lists/", { method: "POST", body: { name, visibility } });
      if (!response.ok) {
        setError(copy.error);
        return;
      }
      const created = (await response.json()) as { id: string };
      setName("");
      setOpen(false);
      router.push(`${basePath}?list=${created.id}`);
      router.refresh();
    } catch {
      setError(copy.error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="sp-coll-side-titlerow">
        <h2 className="sp-coll-side-title">{heading}</h2>
        <button type="button" className="sp-coll-side-new" aria-expanded={open} onClick={() => setOpen((value) => !value)}>
          {newLabel}
        </button>
      </div>
      {open ? (
        <form className="sp-coll-side-newform" onSubmit={submit}>
          <label className="visually-hidden" htmlFor="coll-new-list-name">
            {copy.name}
          </label>
          <input
            id="coll-new-list-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder={copy.name}
            maxLength={80}
            disabled={busy}
            autoFocus
          />
          <label className="visually-hidden" htmlFor="coll-new-list-visibility">
            {copy.visibility}
          </label>
          <select
            id="coll-new-list-visibility"
            value={visibility}
            onChange={(event) => setVisibility(event.target.value as "public" | "private")}
            disabled={busy}
          >
            <option value="public">{copy.friends}</option>
            <option value="private">{copy.private}</option>
          </select>
          <button type="submit" className="sp-btn-primary" disabled={busy || !name.trim()}>
            {busy ? copy.creating : copy.create}
          </button>
          {error ? <p role="status" className="sp-coll-side-empty">{error}</p> : null}
        </form>
      ) : null}
    </>
  );
}
