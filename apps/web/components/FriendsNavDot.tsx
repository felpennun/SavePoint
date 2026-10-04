"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

import { getSocialUnreadCount } from "@/lib/client-api";

/** The red dot next to the "Friends" tab while there are unread notifications
 * (requests, recommendations, notices). It checks on every navigation and
 * follows the count the friends page publishes when notifications are read. */
export function FriendsNavDot({ locale }: { locale: string }) {
  const pathname = usePathname();
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    getSocialUnreadCount().then((value) => {
      if (!cancelled && value !== null) setCount(value);
    });
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  useEffect(() => {
    const onChange = (event: Event) => {
      const next = (event as CustomEvent<{ count?: unknown }>).detail?.count;
      if (typeof next === "number" && Number.isInteger(next) && next >= 0) setCount(next);
    };
    window.addEventListener("savepoint:social-unread-count", onChange);
    return () => window.removeEventListener("savepoint:social-unread-count", onChange);
  }, []);

  if (!count) return null;
  return (
    <>
      <span className="sp-nav-dot" aria-hidden="true" />
      <span className="visually-hidden">
        {locale === "es" ? ` (${count} sin leer)` : ` (${count} unread)`}
      </span>
    </>
  );
}
