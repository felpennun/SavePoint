"use client";

import Link from "next/link";
import { useState, type ComponentProps } from "react";

type LinkProps = ComponentProps<typeof Link>;

/**
 * A <Link> that starts loading its destination in full as soon as the pointer,
 * keyboard focus or a finger reaches it, so the click that follows usually
 * finds the page already in the router cache (see `staleTimes` in
 * next.config.ts). Without `eager` it does nothing until then, which suits
 * long grids of cards where prefetching every link in view would flood the
 * server; with `eager` it keeps Next's default prefetch for links in view and
 * only upgrades to a full prefetch on interaction.
 */
export function HoverPrefetchLink({
  eager = false,
  prefetch: _ignored,
  onMouseEnter,
  onFocus,
  onTouchStart,
  ...rest
}: LinkProps & { eager?: boolean }) {
  const [armed, setArmed] = useState(false);
  return (
    <Link
      {...rest}
      prefetch={armed ? true : eager ? undefined : false}
      onMouseEnter={(event) => {
        setArmed(true);
        onMouseEnter?.(event);
      }}
      onFocus={(event) => {
        setArmed(true);
        onFocus?.(event);
      }}
      onTouchStart={(event) => {
        setArmed(true);
        onTouchStart?.(event);
      }}
    />
  );
}
