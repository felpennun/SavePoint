"use client";

import { useEffect, useState } from "react";

const STATUSES = ["pending", "playing", "completed", "abandoned"] as const;
type Status = (typeof STATUSES)[number];

const COPY = {
  es: {
    legend: "Estado:",
    labels: { pending: "Pendiente", playing: "Jugando", completed: "Completado", abandoned: "Abandonado" },
    save: "Guardar estado",
    saving: "Guardando…",
    success: "Estado guardado",
    error: "No se pudo guardar el estado. Inténtalo de nuevo.",
    loginRequired: "Inicia sesión para guardar un estado.",
    loading: "Cargando…",
  },
  en: {
    legend: "Status:",
    labels: { pending: "Pending", playing: "Playing", completed: "Completed", abandoned: "Abandoned" },
    save: "Save status",
    saving: "Saving…",
    success: "Status saved",
    error: "We couldn't save the status. Try again.",
    loginRequired: "Log in to save a status.",
    loading: "Loading…",
  },
} as const;

function readCookie(name: string): string | undefined {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

export default function StatusControl({
  workId,
  locale,
  isAuthenticated,
}: {
  workId: string;
  locale: "es" | "en";
  isAuthenticated: boolean;
}) {
  const copy = COPY[locale];
  const [selected, setSelected] = useState<Status | "">("");
  const [loading, setLoading] = useState(isAuthenticated);
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    // Read the persisted value fresh on every mount (i.e. every page load/
    // reload) -- never trust client-side state as the source of truth for
    // what was actually saved.
    fetch(`/api/library/entries/${workId}/status/`, { credentials: "same-origin" })
      .then((response) => (response.ok ? response.json() : { status: null }))
      .then((body: { status: Status | null }) => {
        if (!cancelled && body.status) setSelected(body.status);
      })
      .catch(() => {
        // Reload failure isn't fatal -- the fieldset still renders with no
        // pre-selected value, and saving a new status still works.
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

  async function handleSave() {
    if (!selected) return;
    setPending(true);
    setFeedback(null);
    try {
      const csrfToken = readCookie("csrftoken");
      const response = await fetch(`/api/library/entries/${workId}/status/`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        body: JSON.stringify({ status: selected }),
      });
      if (!response.ok) {
        setFeedback({ kind: "error", message: copy.error });
        return;
      }
      setFeedback({ kind: "success", message: copy.success });
    } catch {
      setFeedback({ kind: "error", message: copy.error });
    } finally {
      setPending(false);
    }
  }

  return (
    <fieldset>
      <legend>{copy.legend}</legend>
      {STATUSES.map((status) => (
        <label key={status}>
          <input
            type="radio"
            name="status"
            value={status}
            checked={selected === status}
            onChange={() => setSelected(status)}
          />
          {copy.labels[status]}
        </label>
      ))}
      <button type="button" onClick={handleSave} disabled={pending || !selected}>
        {pending ? copy.saving : copy.save}
      </button>
      {feedback ? (
        <p role={feedback.kind === "error" ? "alert" : "status"} data-testid="status-feedback">
          {feedback.message}
        </p>
      ) : null}
    </fieldset>
  );
}
