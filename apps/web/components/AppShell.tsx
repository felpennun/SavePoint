"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { AccountSwitcher } from "@/components/AccountSwitcher";
import { BrandLockup } from "@/components/BrandLockup";
import { DemoAccountBanner } from "@/components/DemoAccountBanner";
import { LoginIconButton } from "@/components/LoginIconButton";
import { LanguageToggle } from "@/components/LanguageToggle";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getDictionary, type Dictionary } from "@/i18n";

interface NavItem {
  href: string;
  label: string;
}

function buildNavItems(dict: Dictionary, locale: string, isAuthenticated: boolean): NavItem[] {
  const base: NavItem[] = [
    { href: `/${locale}`, label: dict.nav.home },
    { href: `/${locale}/catalogue`, label: dict.nav.catalogue },
  ];
  if (isAuthenticated) {
    base.push({ href: `/${locale}/collection`, label: dict.nav.collection });
    base.push({ href: `/${locale}/recommendations`, label: dict.nav.recommendations });
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
      <ul className="flex items-center gap-6" style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {items.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              aria-current={isCurrent(pathname, item.href) ? "page" : undefined}
              style={{
                color: isCurrent(pathname, item.href) ? "var(--color-text-primary)" : "var(--color-text-secondary)",
                textDecoration: "none",
                fontWeight: isCurrent(pathname, item.href) ? 600 : 400,
                borderBottom: isCurrent(pathname, item.href) ? "2px solid var(--color-accent)" : "2px solid transparent",
                paddingBottom: "2px",
              }}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function MobileMenu({ items, dict }: { items: NavItem[]; dict: Dictionary }) {
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
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "var(--space-sm)" }}>
            {items.map((item) => (
              <li key={item.href}>
                <Link href={item.href} onClick={() => setOpen(false)}>
                  {item.label}
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
}: {
  children: ReactNode;
  locale: string;
  isAuthenticated: boolean;
}) {
  const dict = getDictionary(locale);
  const items = buildNavItems(dict, locale, isAuthenticated);

  return (
    <>
      <a href="#main-content" className="skip-link">
        {dict.nav.skipToContent}
      </a>
      <header className="border-b" style={{ borderColor: "var(--color-surface-border)", background: "var(--color-surface-raised)", position: "relative" }}>
        <div className="flex items-center justify-between gap-2 md:gap-4 px-3 md:px-4 py-3">
          <Link href={`/${locale}`} aria-label={dict.nav.home} className="min-w-0 [&>svg]:max-w-full" style={{ color: "var(--color-text-primary)", display: "inline-flex", alignItems: "center" }}>
            <BrandLockup />
          </Link>
          <div className="flex shrink-0 items-center gap-2 md:gap-4">
            <TopNavigation items={items} locale={locale} />
            <LanguageToggle locale={locale} />
            <ThemeToggle labels={dict.theme.toggle} />
            {isAuthenticated ? (
              <AccountSwitcher
                locale={locale}
                labels={{
                  label: dict.account.switcher.label,
                  change: dict.account.switcher.change,
                  current: dict.account.switcher.current,
                  logout: dict.nav.logout,
                  listHeading: dict.account.list.heading,
                }}
              />
            ) : (
              <LoginIconButton locale={locale} label={dict.nav.loginAria} />
            )}
            <MobileMenu items={items} dict={dict} />
          </div>
        </div>
      </header>
      {isAuthenticated ? <DemoAccountBanner text={dict.account.banner} /> : null}
      <div id="main-content">{children}</div>
    </>
  );
}
