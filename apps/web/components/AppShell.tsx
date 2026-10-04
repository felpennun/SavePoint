"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { AccountSwitcher } from "@/components/AccountSwitcher";
import { BrandLockup } from "@/components/BrandLockup";
import { FriendsNavDot } from "@/components/FriendsNavDot";
import { LoginIconButton } from "@/components/LoginIconButton";
import { LanguageToggle } from "@/components/LanguageToggle";
import { ShelfWheelScroll } from "@/components/ShelfWheelScroll";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getDictionary, type Dictionary } from "@/i18n";

interface NavItem {
  href: string;
  label: string;
}

function buildNavItems(dict: Dictionary, locale: string, isAuthenticated: boolean, canViewResearch: boolean): NavItem[] {
  const base: NavItem[] = [
    { href: `/${locale}`, label: dict.nav.home },
    { href: `/${locale}/catalogue`, label: dict.nav.catalogue },
  ];
  if (isAuthenticated) {
    base.push({ href: `/${locale}/collection`, label: dict.nav.collection });
    base.push({ href: `/${locale}/recommendations`, label: dict.nav.recommendations });
    base.push({ href: `/${locale}/friends`, label: locale === "es" ? "Amistades" : "Friends" });
  }
  if (canViewResearch) {
    base.push({ href: `/${locale}/research`, label: dict.nav.research });
  }
  base.push({ href: `/${locale}/sources`, label: dict.nav.sources });
  return base;
}

function isCurrent(pathname: string, href: string): boolean {
  return pathname === href || (href.split("/").length > 2 && pathname.startsWith(`${href}/`));
}

/** Same DOM order/content as MobileMenu's list -- only CSS visibility
 * differs between breakpoints, never a JS-computed different tree, so
 * screen-reader/keyboard order never diverges from the visual layout. */
export function TopNavigation({ items, locale }: { items: NavItem[]; locale: string }) {
  const pathname = usePathname();
  return (
    <nav aria-label={locale === "es" ? "Principal" : "Main"} className="hidden md:block">
      <ul className="flex items-center" style={{ listStyle: "none", margin: 0, padding: 0, gap: "22px" }}>
        {items.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              aria-current={isCurrent(pathname, item.href) ? "page" : undefined}
              style={{
                fontSize: "14px",
                color: isCurrent(pathname, item.href) ? "var(--color-text-primary)" : "var(--color-text-muted)",
                textDecoration: "none",
                fontWeight: isCurrent(pathname, item.href) ? 600 : 400,
                borderBottom: isCurrent(pathname, item.href) ? "2px solid var(--color-accent)" : "2px solid transparent",
                paddingBottom: "3px",
              }}
            >
              {item.label}
              {item.href.endsWith("/friends") ? <FriendsNavDot locale={locale} /> : null}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

/** Name search in the header. A plain GET form that lands on the
 * catalogue with `?q=` -- shareable, works without JavaScript. Hidden
 * below md, where the catalogue's own FilterBar search takes over. */
export function NavSearch({ locale, label }: { locale: string; label: string }) {
  return (
    <form
      role="search"
      method="get"
      action={`/${locale}/catalogue`}
      className="sp-navsearch hidden md:flex"
    >
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
        <circle cx="11" cy="11" r="7" />
        <path d="M16.5 16.5 21 21" />
      </svg>
      <input type="search" name="q" aria-label={label} placeholder={label} />
    </form>
  );
}

export function MobileMenu({ items, dict, locale }: { items: NavItem[]; dict: Dictionary; locale: string }) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();

  // Close on route change (behavior: "cierra con ... ruta").
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  // Focus trap + Escape-to-close + focus-return (behavior: "atrapa foco,
  // cierra con Escape ... y devuelve foco").
  useEffect(() => {
    if (!open) return;

    const dialogNode = dialogRef.current;
    const focusables = dialogNode?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])');
    focusables?.[0]?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
        return;
      }
      if (event.key !== "Tab" || !dialogNode) return;
      const focusable = dialogNode.querySelectorAll<HTMLElement>('a[href], button:not([disabled])');
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  return (
    <div className="md:hidden">
      <button
        ref={triggerRef}
        type="button"
        className="sp-btn-secondary"
        aria-expanded={open}
        aria-controls="mobile-menu"
        onClick={() => setOpen((value) => !value)}
      >
        {open ? dict.nav.closeMenu : dict.nav.openMenu}
      </button>
      {open ? (
        <div
          id="mobile-menu"
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          aria-label={dict.nav.openMenu}
          className="sp-surface"
          style={{ position: "absolute", left: "var(--space-md)", right: "var(--space-md)", zIndex: 40, marginTop: "var(--space-sm)" }}
        >
          <ul className="sp-mobile-nav">
            {items.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={isCurrent(pathname, item.href) ? "page" : undefined}
                  onClick={() => setOpen(false)}
                >
                  {item.label}
                  {item.href.endsWith("/friends") ? <FriendsNavDot locale={locale} /> : null}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function AppShell({
  children,
  locale,
  isAuthenticated,
  canViewResearch = false,
}: {
  children: ReactNode;
  locale: string;
  isAuthenticated: boolean;
  canViewResearch?: boolean;
}) {
  const dict = getDictionary(locale);
  const items = buildNavItems(dict, locale, isAuthenticated, canViewResearch);

  return (
    <>
      <a href="#main-content" className="skip-link">
        {dict.nav.skipToContent}
      </a>
      <header className="sp-navbar border-b" style={{ borderColor: "var(--color-surface-border)", background: "var(--color-surface-overlay)", position: "relative" }}>
        <div
          className="sp-navbar-inner flex items-center justify-between gap-2 md:gap-4 py-3 px-4 md:px-6"
          style={{ maxWidth: "1180px", margin: "0 auto" }}
        >
          <div className="flex min-w-0 items-center gap-4 md:gap-7">
            <Link href={`/${locale}`} aria-label={dict.nav.home} className="min-w-0 [&>svg]:max-w-full" style={{ color: "var(--color-text-primary)", display: "inline-flex", alignItems: "center" }}>
              <BrandLockup />
            </Link>
            <TopNavigation items={items} locale={locale} />
          </div>
          <div className="flex shrink-0 items-center gap-2 md:gap-4">
            <NavSearch locale={locale} label={dict.nav.search} />
            <LanguageToggle locale={locale} />
            <ThemeToggle labels={dict.theme.toggle} />
            {isAuthenticated ? (
              <AccountSwitcher
                locale={locale}
                labels={{
                  label: dict.account.switcher.label,
                  editProfile: dict.account.switcher.editProfile,
                  change: dict.account.switcher.change,
                  current: dict.account.switcher.current,
                  logout: dict.nav.logout,
                  listHeading: dict.account.list.heading,
                  messagesLabel: locale === "es" ? "Notificaciones" : "Notifications",
                  unreadLabel: (count: number) => locale === "es" ? `${count} sin leer` : `${count} unread`,
                  noUnreadLabel: locale === "es" ? "Nada pendiente" : "Nothing pending",
                  unreadLoadingLabel: locale === "es" ? "Comprobando notificaciones" : "Checking notifications",
                }}
              />
            ) : (
              <LoginIconButton locale={locale} label={dict.nav.loginAria} />
            )}
            <MobileMenu items={items} dict={dict} locale={locale} />
          </div>
        </div>
      </header>
      <div id="main-content" tabIndex={-1}>
        {children}
      </div>
      <ShelfWheelScroll />
    </>
  );
}
