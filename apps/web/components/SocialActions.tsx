"use client";

import { useEffect, useRef, useState } from "react";

import { apiFetch } from "@/lib/client-api";

export type SocialActionRelationship = "none" | "pending_sent" | "pending_received" | "friend" | "blocked";
export type SocialActionKey = "send" | "request_sent" | "accept" | "reject" | "remove" | "block" | "unblock";

export interface SocialActionDescriptor {
  key: SocialActionKey;
  label: string;
  variant: "primary" | "secondary" | "danger";
  requiresConfirmation: boolean;
}

const COPY = {
  es: {
    send: "Enviar solicitud de amistad",
    request_sent: "Solicitud enviada",
    accept: "Aceptar solicitud",
    reject: "Rechazar solicitud",
    remove: "Eliminar amistad",
    block: "Bloquear",
    unblock: "Desbloquear",
    cancel: "Cancelar",
    confirm: "Confirmar",
    error: "La acción no se pudo completar. Revisa el estado e inténtalo de nuevo.",
    retry: "Reintentar",
    accepted: "Solicitud aceptada.",
    rejected: "Solicitud rechazada.",
    removed: "Amistad eliminada.",
    blocked: "Cuenta bloqueada.",
    unblocked: "Cuenta desbloqueada.",
    sent: "Solicitud enviada.",
    rejectConfirm: (alias: string) => `¿Rechazar la solicitud de ${alias}? Podrá volver a enviarte una solicitud más adelante.`,
    removeConfirm: (alias: string) => `¿Eliminar a ${alias} de tus amistades? Perderá el acceso a tu colección, listas y comentarios permitidos, pero podrá solicitar amistad de nuevo.`,
    blockConfirm: (alias: string) => `¿Bloquear a ${alias}? Se cancelarán las solicitudes, se eliminará la amistad, se revocará el acceso y no podrá volver a enviarte solicitudes mientras esté bloqueado.`,
  },
  en: {
    send: "Send friend request",
    request_sent: "Request sent",
    accept: "Accept request",
    reject: "Reject request",
    remove: "Remove friendship",
    block: "Block",
    unblock: "Unblock",
    cancel: "Cancel",
    confirm: "Confirm",
    error: "The action could not be completed. Check the current state and try again.",
    retry: "Retry",
    accepted: "Request accepted.",
    rejected: "Request rejected.",
    removed: "Friendship removed.",
    blocked: "Account blocked.",
    unblocked: "Account unblocked.",
    sent: "Request sent.",
    rejectConfirm: (alias: string) => `Reject ${alias}'s request? They can send another request later.`,
    removeConfirm: (alias: string) => `Remove ${alias} from your friends? They will lose access to your permitted collection, lists, and comments, but can request friendship again.`,
    blockConfirm: (alias: string) => `Block ${alias}? Requests will be cancelled, the friendship removed, access revoked, and new requests prevented while blocked.`,
  },
} as const;

export function getSocialActionDescriptors(
  relationship: SocialActionRelationship,
  locale: string,
): SocialActionDescriptor[] {
  const copy = locale === "en" ? COPY.en : COPY.es;
  switch (relationship) {
    case "none":
      return [{ key: "send", label: copy.send, variant: "primary", requiresConfirmation: false }];
    case "pending_sent":
      return [{ key: "request_sent", label: copy.request_sent, variant: "secondary", requiresConfirmation: false }];
    case "pending_received":
      return [
        { key: "accept", label: copy.accept, variant: "primary", requiresConfirmation: false },
        { key: "reject", label: copy.reject, variant: "secondary", requiresConfirmation: true },
      ];
    case "friend":
      return [
        { key: "remove", label: copy.remove, variant: "secondary", requiresConfirmation: true },
        { key: "block", label: copy.block, variant: "danger", requiresConfirmation: true },
      ];
    case "blocked":
      return [{ key: "unblock", label: copy.unblock, variant: "secondary", requiresConfirmation: false }];
  }
}

export function buildSocialActionPath(action: SocialActionKey, alias: string, requestId?: string): string {
  const encodedAlias = encodeURIComponent(alias);
  if (action === "send") return "/api/social/requests/";
  if (action === "accept" || action === "reject") return `/api/social/requests/${requestId}/${action}/`;
  if (action === "remove" || action === "block") return `/api/social/friendships/${encodedAlias}/${action}/`;
  if (action === "unblock") return `/api/social/blocks/${encodedAlias}/unblock/`;
  return "";
}

function confirmationText(action: SocialActionKey, alias: string, locale: string): string | null {
  const copy = locale === "en" ? COPY.en : COPY.es;
  if (action === "reject") return copy.rejectConfirm(alias);
  if (action === "remove") return copy.removeConfirm(alias);
  if (action === "block") return copy.blockConfirm(alias);
  return null;
}

function successText(action: SocialActionKey, locale: string): string {
  const copy = locale === "en" ? COPY.en : COPY.es;
  const messages: Record<Exclude<SocialActionKey, "request_sent">, string> = {
    send: copy.sent,
    accept: copy.accepted,
    reject: copy.rejected,
    remove: copy.removed,
    block: copy.blocked,
    unblock: copy.unblocked,
  };
  return action === "request_sent" ? copy.request_sent : messages[action];
}

export function SocialActions({
  alias,
  relationship,
  locale,
  requestId,
  onSuccess,
}: {
  alias: string;
  relationship: SocialActionRelationship;
  locale: string;
  requestId?: string;
  onSuccess?: (action: SocialActionKey, alias: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [dialogAction, setDialogAction] = useState<SocialActionKey | null>(null);
  const [failedAction, setFailedAction] = useState<SocialActionKey | null>(null);
  const [error, setError] = useState(false);
  const [feedback, setFeedback] = useState("");
  const dialogRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!dialogAction) return;
    const dialog = dialogRef.current;
    const focusables = dialog?.querySelectorAll<HTMLElement>('button:not([disabled])');
    focusables?.[0]?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDialogAction(null);
        triggerRef.current?.focus();
        return;
      }
      if (event.key !== "Tab" || !dialog) return;
      const nodes = dialog.querySelectorAll<HTMLElement>('button:not([disabled])');
      if (!nodes.length) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [dialogAction]);

  async function run(action: SocialActionKey) {
    if (action === "request_sent") return;
    setBusy(true);
    setError(false);
    setFeedback("");
    try {
      const response = await apiFetch(buildSocialActionPath(action, alias, requestId), {
        method: "POST",
        ...(action === "send" ? { body: { alias } } : {}),
      });
      if (!response.ok) throw new Error("social_action_failed");
      setDialogAction(null);
      setBusy(false);
      const message = successText(action, locale);
      setFeedback(message);
      onSuccess?.(action, alias);
    } catch {
      setBusy(false);
      setFailedAction(action);
      setError(true);
    }
  }

  const descriptors = getSocialActionDescriptors(relationship, locale);
  const dialogCopy = dialogAction ? confirmationText(dialogAction, alias, locale) : null;
  const copy = locale === "en" ? COPY.en : COPY.es;

  return (
    <div className="flex flex-wrap items-center gap-2" data-social-actions={alias}>
      {descriptors.map((descriptor) => {
        if (descriptor.key === "request_sent") {
          return <span key={descriptor.key} role="status" className="sp-meta">{descriptor.label}</span>;
        }
        const className = descriptor.variant === "primary" ? "sp-btn-primary" : descriptor.variant === "danger" ? "sp-btn-danger" : "sp-btn-secondary";
        return (
          <button
            key={descriptor.key}
            type="button"
            className={className}
            disabled={busy}
            onClick={(event) => {
              if (descriptor.requiresConfirmation) {
                triggerRef.current = event.currentTarget;
                setDialogAction(descriptor.key);
              } else {
                void run(descriptor.key);
              }
            }}
          >
            {descriptor.label}
          </button>
        );
      })}
      {feedback ? <p role="status" aria-live="polite" style={{ flexBasis: "100%", margin: 0 }}>{feedback}</p> : null}
      {error ? (
        <div role="alert" style={{ flexBasis: "100%" }}>
          <span>{copy.error}</span>
          <button type="button" className="sp-link" disabled={busy} onClick={() => { if (failedAction) void run(failedAction); }}>{copy.retry}</button>
        </div>
      ) : null}
      {dialogCopy ? (
        <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby={`confirm-${alias}-${dialogAction}`} className="sp-surface" style={{ flexBasis: "100%" }}>
          <p id={`confirm-${alias}-${dialogAction}`} className="sp-lead">{dialogCopy}</p>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="sp-btn-secondary" disabled={busy} onClick={() => { setDialogAction(null); triggerRef.current?.focus(); }}>{copy.cancel}</button>
            <button type="button" className={dialogAction === "block" ? "sp-btn-danger" : "sp-btn-primary"} disabled={busy} onClick={() => { if (dialogAction) void run(dialogAction); }}>{copy.confirm}</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
