"use client";

import { useEffect } from "react";

const LINE_HEIGHT_PX = 40;

/** Wheel delta in pixels, whatever unit the browser reports it in. */
function wheelPixels(event: WheelEvent, track: HTMLElement): number {
  if (event.deltaMode === 1) return event.deltaY * LINE_HEIGHT_PX;
  if (event.deltaMode === 2) return event.deltaY * track.clientWidth;
  return event.deltaY;
}

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
 *
 * The tracks use `scroll-snap-type: x proximity` for touch. A wheel notch is
 * usually ~100px, less than half a card, so the snap pulled every notch back
 * to the starting card and the shelf looked frozen. The first wheel input
 * marks the track (`data-wheel`, see globals.css) to switch the snap off; a
 * touch gesture switches it back on.
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
      track.dataset.wheel = "";
      track.scrollLeft += wheelPixels(event, track);
    }
    function onTouchStart(event: TouchEvent) {
      const target = event.target as Element | null;
      const track = target?.closest?.(".sp-shelf-track") as HTMLElement | null;
      if (track) delete track.dataset.wheel;
    }
    window.addEventListener("wheel", onWheel, { passive: false, capture: true });
    window.addEventListener("touchstart", onTouchStart, { passive: true, capture: true });
    return () => {
      window.removeEventListener("wheel", onWheel, true);
      window.removeEventListener("touchstart", onTouchStart, true);
    };
  }, []);

  return null;
}
