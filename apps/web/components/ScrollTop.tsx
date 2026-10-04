"use client";

import { useEffect, useRef } from "react";

/**
 * Sends the scrolling area it sits in back to the top whenever `watch` changes
 * (a new page of games, another list...). On desktop the games scroll inside
 * their own container, which would otherwise keep its position; where nothing
 * scrolls inside (phones) the page itself goes back to the top. Nothing
 * happens on the first render.
 */
export function ScrollTop({ watch }: { watch: string | number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const previous = useRef(watch);

  useEffect(() => {
    if (previous.current === watch) return;
    previous.current = watch;
    let element = ref.current?.parentElement ?? null;
    while (element) {
      const scrollable = element.scrollHeight > element.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(element).overflowY);
      if (scrollable) {
        element.scrollTop = 0;
        return;
      }
      element = element.parentElement;
    }
    window.scrollTo({ top: 0 });
  }, [watch]);

  return <span ref={ref} hidden aria-hidden="true" />;
}
