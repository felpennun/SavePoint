"use client";

import { useState } from "react";

/**
 * CoverImage (01.1-UI-SPEC). Tiny client wrapper around <img> that swaps
 * to the first-party placeholder block on `onError` -- covers ADR-006's
 * 30-day IGDB image-removal window where a hotlinked cover can 404 at any
 * time. A fixed 3:4 box (.sp-cover on the parent) plus explicit
 * width/height reserve layout so a missing/slow cover causes no shift.
 */
export function CoverImage({
  src,
  alt,
  title,
  missingLabel,
  width = 156,
  height = 208,
}: {
  src: string | null | undefined;
  alt: string;
  /** Title text shown inside the placeholder block. */
  title: string;
  /** Localized "Cover not available" (dict.common.coverMissing). */
  missingLabel: string;
  width?: number;
  height?: number;
}) {
  const [failed, setFailed] = useState(false);
  const showPlaceholder = !src || failed;

  if (showPlaceholder) {
    return (
      <div className="sp-cover-placeholder" data-testid="cover-placeholder">
        <span>{title}</span>
        <span className="visually-hidden">{missingLabel}</span>
      </div>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element -- lawful hotlinked cover, ADR-006 approved host only; onError needs a native <img>
    <img
      src={src}
      alt={alt}
      width={width}
      height={height}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
