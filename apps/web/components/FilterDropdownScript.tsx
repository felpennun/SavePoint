"use client";

import { useEffect } from "react";

const OPEN_SELECTOR = "details.sp-dropdown[open]";

/**
 * One shared enhancement for every `.sp-dropdown` on the page (FilterDropdown,
 * FacetMenu): clicking anywhere outside an open dropdown closes it, Escape
 * closes the focused one, and opening one closes any other that was already
 * open. Every dropdown is a plain <details>/<summary>, so without JavaScript
 * each still opens and closes on its own.
 *
 * It is a client effect (not an inline <script>): inline scripts do not run
 * when the page is reached through client-side navigation, which left the
 * panels stuck open. Mount it once next to the dropdowns; a second mount just
 * adds a second, harmless set of listeners that is removed on unmount.
 */
export function FilterDropdownScript() {
  useEffect(() => {
    const closeAll = (except?: Element | null) => {
      document.querySelectorAll(OPEN_SELECTOR).forEach((details) => {
        if (details !== except) details.removeAttribute("open");
      });
    };

    const onPointerDown = (event: Event) => {
      const target = event.target as Node | null;
      document.querySelectorAll(OPEN_SELECTOR).forEach((details) => {
        if (!target || !details.contains(target)) details.removeAttribute("open");
      });
    };
    const onToggle = (event: Event) => {
      const element = event.target as HTMLDetailsElement | null;
      if (element?.matches?.("details.sp-dropdown") && element.open) closeAll(element);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      const open = document.querySelector(OPEN_SELECTOR);
      if (!open) return;
      open.removeAttribute("open");
      open.querySelector("summary")?.focus();
    };

    document.addEventListener("pointerdown", onPointerDown, true);
    document.addEventListener("toggle", onToggle, true);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown, true);
      document.removeEventListener("toggle", onToggle, true);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  return null;
}
