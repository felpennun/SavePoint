"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

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
  };
}) {
  const [open, setOpen] = useState(false);
  const [alias, setAlias] = useState<string | null>(null);
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

  return (
    <div style={{ position: "relative" }}>
      <button
        ref={triggerRef}
        type="button"
        className="sp-btn-secondary sp-account-trigger"
        aria-label={triggerText}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <svg className="sp-account-avatar" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 21v-1a7 7 0 0 1 14 0v1" />
        </svg>
        <span className="hidden md:inline">{triggerText}</span>
        <span aria-hidden="true">▾</span>
      </button>
      {open ? (
        <div
          ref={panelRef}
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
          <button type="button" role="menuitem" className="sp-link" style={{ textAlign: "left" }} onClick={logout}>
            {labels.logout}
          </button>
        </div>
      ) : null}
    </div>
  );
}
