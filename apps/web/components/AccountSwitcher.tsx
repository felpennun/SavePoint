"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { getSocialUnreadCount } from "@/lib/client-api";

export function buildMessagesHref(locale: string): string {
  return `/${locale}/messages`;
}

export function buildAccountTriggerLabel(
  accountLabel: string,
  messagesLabel: string,
  unreadCount: number | null,
  unreadLabel: (count: number) => string = (count) => `${count} mensajes sin leer`,
  noUnreadLabel = "Sin mensajes pendientes",
): string {
  if (unreadCount === null) return `${accountLabel}; ${messagesLabel}: estado pendiente`;
  return `${accountLabel}; ${messagesLabel}: ${unreadCount > 0 ? unreadLabel(unreadCount) : noUnreadLabel}`;
}

/**
 * AccountSwitcher (01.1-UI-SPEC, AUTH-02). Occupies the navbar right-end
 * account slot when the visitor is authenticated. The accessible trigger
 * name always includes "simulated"/"simulada", including icon-only mobile.
 * Panel = role="menu", focus-trapped,
 * Escape-closes, focus-returns -- reuses the MobileMenu focus-management
 * pattern. Lists the way to pick another simulated account plus Log out.
 * The preloaded-account list itself is wired by Plan 04/08; until then
 * "Switch account" links to the existing /{locale}/login entry point.
 */
export function AccountSwitcher({
  locale,
  labels,
}: {
  locale: string;
  labels: {
    label: string;
    change: string;
    current: string;
    logout: string;
    listHeading: string;
    messagesLabel?: string;
    unreadLabel?: (count: number) => string;
    noUnreadLabel?: string;
    unreadLoadingLabel?: string;
  };
}) {
  const [open, setOpen] = useState(false);
  const [alias, setAlias] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState<number | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Best-effort alias resolution; the trigger degrades gracefully to the
  // bare "Simulated account" label if the endpoint is absent (Plan 04/08).
  useEffect(() => {
    let cancelled = false;
    fetch("/api/accounts/me/", { credentials: "same-origin" })
      .then((r) => (r.ok ? r.json() : null))
      .then((body) => {
        if (!cancelled && body && typeof body.username === "string") setAlias(body.username);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const refreshUnread = async () => {
      const count = await getSocialUnreadCount();
      if (!cancelled && count !== null) setUnreadCount(count);
    };
    void refreshUnread();
    const onUnreadChange = (event: Event) => {
      const count = (event as CustomEvent<{ count?: unknown }>).detail?.count;
      if (typeof count === "number" && Number.isInteger(count) && count >= 0) setUnreadCount(count);
    };
    window.addEventListener("savepoint:social-unread-count", onUnreadChange);
    return () => {
      cancelled = true;
      window.removeEventListener("savepoint:social-unread-count", onUnreadChange);
    };
  }, []);

  useEffect(() => {
    if (!open) return;
    const node = panelRef.current;
    const focusables = node?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])');
    focusables?.[0]?.focus();

    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
        return;
      }
      if (event.key !== "Tab" || !node) return;
      const list = node.querySelectorAll<HTMLElement>('a[href], button:not([disabled])');
      if (list.length === 0) return;
      const first = list[0];
      const last = list[list.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  async function logout() {
    try {
      await fetch("/api/accounts/csrf/", { credentials: "same-origin" });
      const csrfToken = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="))
        ?.split("=")[1];
      await fetch("/api/accounts/logout/", {
        method: "POST",
        credentials: "same-origin",
        headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
      });
    } catch {
      /* fall through to a hard navigation regardless */
    }
    setOpen(false);
    router.push(`/${locale}`);
    router.refresh();
  }

  const triggerText = alias ? `${labels.label}: ${alias}` : labels.label;
  const messagesLabel = labels.messagesLabel ?? (locale === "es" ? "Mensajes de amigos" : "Messages from friends");
  const triggerLabel = labels.messagesLabel
    ? buildAccountTriggerLabel(triggerText, messagesLabel, unreadCount, labels.unreadLabel, labels.noUnreadLabel)
    : triggerText;
  const unreadText = unreadCount === null
    ? (labels.unreadLoadingLabel ?? (locale === "es" ? "Comprobando mensajes pendientes" : "Checking pending messages"))
    : unreadCount > 0
      ? (labels.unreadLabel?.(unreadCount) ?? buildAccountTriggerLabel("", "", unreadCount).replace(/^; : /, ""))
      : (labels.noUnreadLabel ?? (locale === "es" ? "Sin mensajes pendientes" : "No pending messages"));

  return (
    <div style={{ position: "relative" }}>
      <button
        ref={triggerRef}
        type="button"
        className="sp-btn-secondary sp-icon-btn sp-account-trigger"
        aria-label={triggerLabel}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls="account-menu"
        onClick={() => setOpen((v) => !v)}
      >
        <svg className="sp-account-avatar" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21v-1a7 7 0 0 1 14 0v1" />
        </svg>
        {labels.messagesLabel && unreadCount !== null && unreadCount > 0 ? (
          <span
            aria-hidden="true"
            style={{ position: "absolute", top: 0, right: 0, width: "0.55rem", height: "0.55rem", borderRadius: "999px", background: "var(--color-danger)", border: "2px solid var(--color-surface-overlay)" }}
          />
        ) : null}
      </button>
      {open ? (
        <div
          ref={panelRef}
          id="account-menu"
          role="menu"
          aria-label={labels.listHeading}
          className="sp-surface"
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 4px)",
            zIndex: 40,
            minWidth: "16rem",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-sm)",
          }}
        >
          {alias ? (
            <p className="sp-muted" style={{ margin: 0 }}>
              {labels.current.replace("{alias}", alias)}
            </p>
          ) : null}
          <Link href={`/${locale}/login`} role="menuitem" onClick={() => setOpen(false)}>
            {labels.change}
          </Link>
          {labels.messagesLabel ? (
            <Link href={buildMessagesHref(locale)} role="menuitem" onClick={() => setOpen(false)}>
              {messagesLabel} <span className="sp-muted">({unreadText})</span>
            </Link>
          ) : null}
          <button type="button" role="menuitem" className="sp-link" style={{ textAlign: "left" }} onClick={logout}>
            {labels.logout}
          </button>
        </div>
      ) : null}
    </div>
  );
}
