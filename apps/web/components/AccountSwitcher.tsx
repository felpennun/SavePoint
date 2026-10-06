"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { presetGradient } from "@/lib/avatar-presets";
import { getSocialUnreadCount } from "@/lib/client-api";
import { signOutAndRedirect } from "@/lib/idle-session";

export function buildMessagesHref(locale: string): string {
  return `/${locale}/friends`;
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
 * AccountSwitcher (01.1-UI-SPEC). Occupies the navbar right-end account slot
 * when the visitor is authenticated. The accessible trigger name always
 * includes the account label, including icon-only mobile. Panel = role="menu",
 * focus-trapped, Escape-closes, focus-returns -- reuses the MobileMenu
 * focus-management pattern. "Switch account" links to the existing
 * /{locale}/login entry point; Log out ends the session.
 */
export function AccountSwitcher({
  locale,
  labels,
}: {
  locale: string;
  labels: {
    label: string;
    editProfile: string;
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
  // The account photo shown in the trigger: an image, a built-in gradient, or
  // nothing (the generic person icon).
  const [photo, setPhoto] = useState<{ src: string; gradient?: string } | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();

  // Best-effort alias resolution; the trigger degrades gracefully to the
  // bare account label if the endpoint is absent.
  useEffect(() => {
    let cancelled = false;
    fetch("/api/accounts/me/", { credentials: "same-origin" })
      .then((r) => (r.ok ? r.json() : null))
      .then((body) => {
        if (cancelled) return;
        setAlias(body && typeof body.username === "string" ? body.username : null);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  // Load the account photo; the profile page asks for a refresh when it changes.
  useEffect(() => {
    let cancelled = false;
    const loadPhoto = () => {
      fetch("/api/accounts/me/profile/", { credentials: "same-origin" })
        .then((r) => (r.ok ? r.json() : null))
        .then((body) => {
          if (cancelled) return;
          if (!body) {
            setPhoto(null);
            return;
          }
          const src: string = body.avatar_image_url || (String(body.avatar_url || "").startsWith("https://") ? body.avatar_url : "");
          const gradient = presetGradient(body.avatar_preset);
          setPhoto(src || gradient ? { src, gradient } : null);
        })
        .catch(() => {});
    };
    loadPhoto();
    window.addEventListener("savepoint:profile-updated", loadPhoto);
    return () => {
      cancelled = true;
      window.removeEventListener("savepoint:profile-updated", loadPhoto);
    };
  }, [pathname]);

  // Close the menu when the user clicks or taps anywhere outside of it.
  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: PointerEvent) {
      const target = event.target as Node | null;
      if (target && (panelRef.current?.contains(target) || triggerRef.current?.contains(target))) return;
      setOpen(false);
    }
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  // The profile page renames the account without a full reload.
  useEffect(() => {
    const onRenamed = (event: Event) => {
      const next = (event as CustomEvent<{ username?: unknown }>).detail?.username;
      if (typeof next === "string") setAlias(next);
    };
    window.addEventListener("savepoint:username-changed", onRenamed);
    return () => window.removeEventListener("savepoint:username-changed", onRenamed);
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
    setOpen(false);
    // Full page load: after logging out nothing of the previous account (header,
    // photo, cached pages) may remain on screen.
    await signOutAndRedirect(`/${locale}`);
  }

  const triggerText = alias ? `${labels.label}: ${alias}` : labels.label;
  const messagesLabel = labels.messagesLabel ?? (locale === "es" ? "Mensajes de amigos" : "Messages from friends");
  const triggerLabel = labels.messagesLabel
    ? buildAccountTriggerLabel(triggerText, messagesLabel, unreadCount, labels.unreadLabel, labels.noUnreadLabel)
    : triggerText;

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
        {photo?.src ? (
          // eslint-disable-next-line @next/next/no-img-element -- own profile photo (own endpoint or the https URL the user set)
          <img
            className="sp-account-avatar sp-account-photo"
            src={photo.src}
            alt=""
            aria-hidden="true"
            onError={() => setPhoto(photo.gradient ? { src: "", gradient: photo.gradient } : null)}
          />
        ) : photo?.gradient ? (
          <span className="sp-account-avatar sp-account-photo" style={{ backgroundImage: photo.gradient }} aria-hidden="true" />
        ) : (
          <svg className="sp-account-avatar" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 21v-1a7 7 0 0 1 14 0v1" />
          </svg>
        )}
      </button>
      {open ? (
        <div
          ref={panelRef}
          id="account-menu"
          role="menu"
          aria-label={labels.listHeading}
          className="sp-account-menu"
        >
          {alias ? <p className="sp-account-menu-head">{labels.current.replace("{alias}", alias)}</p> : null}
          <Link href={`/${locale}/profile`} role="menuitem" className="sp-account-menu-item" onClick={() => setOpen(false)}>
            {labels.editProfile}
          </Link>
          <Link href={`/${locale}/login`} role="menuitem" className="sp-account-menu-item" onClick={() => setOpen(false)}>
            {labels.change}
          </Link>
          <button type="button" role="menuitem" className="sp-account-menu-item is-separated" onClick={logout}>
            {labels.logout}
          </button>
        </div>
      ) : null}
    </div>
  );
}
