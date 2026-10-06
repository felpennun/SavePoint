"use client";

import { useEffect } from "react";

/**
 * Turns a vertical mouse wheel into horizontal movement while the pointer
 * is over a `.sp-shelf-track` (the recommendation / new-releases shelves).
 * The scrollbar itself is hidden in CSS -- this is the affordance that
 * replaces it. One delegated capture-phase listener on `window` so it also
 * covers shelves rendered after client-side navigation and runs before any
 * page-level wheel handlers; renders nothing.
 *
 * While the pointer is over a shelf the wheel is fully captured for
 * horizontal scrolling -- it does not hand back to the page even at the
 * ends. The page only scrolls up/down when the pointer is outside a shelf.
 */
export function ShelfWheelScroll() {
  useEffect(() => {
    function onWheel(event: WheelEvent) {
      const target = event.target as Element | null;
      const track = target?.closest?.(".sp-shelf-track") as HTMLElement | null;
      if (!track) return;
      // Nothing to do if the shelf isn't actually overflowing.
      if (track.scrollWidth <= track.clientWidth) return;
      // Leave real horizontal gestures (trackpads, tilt wheels) alone.
      if (Math.abs(event.deltaX) > Math.abs(event.deltaY) || event.deltaY === 0) return;
      event.preventDefault();
      track.scrollLeft += event.deltaY;
    }
    window.addEventListener("wheel", onWheel, { passive: false, capture: true });
    return () => window.removeEventListener("wheel", onWheel, true);
  }, []);

  return null;
}
