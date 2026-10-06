"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

/** A recommendation rail with explicit controls as well as native touch,
 * trackpad and keyboard scrolling. The wheel is handled by ShelfWheelScroll. */
export function RecommendationShelfTrack({
  children,
  locale,
  label,
}: {
  children: ReactNode;
  locale: "es" | "en";
  label: string;
}) {
  const trackRef = useRef<HTMLOListElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const updateControls = useCallback(() => {
    const track = trackRef.current;
    if (!track) return;
    setCanScrollLeft(track.scrollLeft > 1);
    setCanScrollRight(track.scrollLeft + track.clientWidth < track.scrollWidth - 1);
  }, []);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    updateControls();
    track.addEventListener("scroll", updateControls, { passive: true });
    const resizeObserver = new ResizeObserver(updateControls);
    resizeObserver.observe(track);
    return () => {
      track.removeEventListener("scroll", updateControls);
      resizeObserver.disconnect();
    };
  }, [updateControls]);

  function scroll(direction: -1 | 1) {
    const track = trackRef.current;
    if (!track) return;
    track.scrollBy({ left: direction * Math.max(track.clientWidth * 0.8, 200), behavior: "smooth" });
  }

  const previousLabel = locale === "es" ? "Desplazar recomendaciones a la izquierda" : "Scroll recommendations left";
  const nextLabel = locale === "es" ? "Desplazar recomendaciones a la derecha" : "Scroll recommendations right";

  return (
    <div className="sp-recommendation-track">
      <div className="sp-recommendation-track-controls">
        <button
          type="button"
          className="sp-recommendation-track-button"
          aria-label={previousLabel}
          title={previousLabel}
          disabled={!canScrollLeft}
          onClick={() => scroll(-1)}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m14.5 5-7 7 7 7" /></svg>
        </button>
        <button
          type="button"
          className="sp-recommendation-track-button"
          aria-label={nextLabel}
          title={nextLabel}
          disabled={!canScrollRight}
          onClick={() => scroll(1)}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9.5 5 7 7-7 7" /></svg>
        </button>
      </div>
      <ol ref={trackRef} className="sp-shelf-track" aria-label={label}>
        {children}
      </ol>
    </div>
  );
}
