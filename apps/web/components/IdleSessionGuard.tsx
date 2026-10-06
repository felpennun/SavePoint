"use client";

import { useEffect } from "react";
import {
  IDLE_CHECK_INTERVAL_MS,
  KEEPALIVE_INTERVAL_MS,
  LAST_ACTIVITY_KEY,
  isIdleExpired,
  signOutAndRedirect,
} from "@/lib/idle-session";

const ACTIVITY_EVENTS = ["pointerdown", "pointermove", "keydown", "wheel", "scroll", "touchstart"] as const;

function readStored(): number | null {
  try {
    const value = Number(window.localStorage.getItem(LAST_ACTIVITY_KEY));
    return Number.isFinite(value) && value > 0 ? value : null;
  } catch {
    return null;
  }
}

function writeStored(value: number): void {
  try {
    window.localStorage.setItem(LAST_ACTIVITY_KEY, String(value));
  } catch {
    /* storage unavailable: this tab's in-memory timestamp is used instead */
  }
}

/**
 * Closes the session after 30 minutes without interaction. Mounted only for
 * signed-in visitors; renders nothing. Activity is shared between tabs through
 * localStorage, and the idle check also runs when a sleeping tab or laptop
 * wakes up, because timers are paused while it is asleep.
 */
export function IdleSessionGuard({ locale }: { locale: "es" | "en" }) {
  useEffect(() => {
    let last = Date.now();
    let lastKeepalive = last;
    let signingOut = false;
    writeStored(last);

    function endSession() {
      if (signingOut) return;
      signingOut = true;
      void signOutAndRedirect(`/${locale}/login?idle=1`);
    }

    function onActivity() {
      const now = Date.now();
      // Event bursts (mouse moves) are collapsed to one write per second.
      if (now - last < 1000) return;
      last = now;
      writeStored(now);
      if (now - lastKeepalive >= KEEPALIVE_INTERVAL_MS) {
        lastKeepalive = now;
        fetch("/api/accounts/me/", { credentials: "same-origin", cache: "no-store" })
          .then((response) => {
            // 401/403: the server already dropped the session.
            if (response.status === 401 || response.status === 403) endSession();
          })
          .catch(() => {});
      }
    }

    function check() {
      const latest = Math.max(last, readStored() ?? 0);
      if (isIdleExpired(latest, Date.now())) endSession();
    }

    function onVisibility() {
      if (document.visibilityState === "visible") check();
    }

    for (const name of ACTIVITY_EVENTS) window.addEventListener(name, onActivity, { passive: true, capture: true });
    document.addEventListener("visibilitychange", onVisibility);
    const timer = window.setInterval(check, IDLE_CHECK_INTERVAL_MS);
    return () => {
      for (const name of ACTIVITY_EVENTS) window.removeEventListener(name, onActivity, true);
      document.removeEventListener("visibilitychange", onVisibility);
      window.clearInterval(timer);
    };
  }, [locale]);

  return null;
}
