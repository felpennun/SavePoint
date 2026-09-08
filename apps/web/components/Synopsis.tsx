"use client";

import { useEffect, useRef, useState } from "react";

/** A text-only, progressively enhanced synopsis with a six-line clamp. */
export function Synopsis({
  text,
  labels,
}: {
  text: string;
  labels: { heading: string; showMore: string; showLess: string };
}) {
  const paragraphRef = useRef<HTMLParagraphElement>(null);
  const [mounted, setMounted] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [isLong, setIsLong] = useState(false);

  useEffect(() => {
    const paragraph = paragraphRef.current;
    setIsLong(Boolean(paragraph && paragraph.scrollHeight > paragraph.clientHeight + 1));
    setMounted(true);
  }, [text]);

  if (!text.trim()) return null;

  const clampStyle = expanded
    ? undefined
    : {
        display: "-webkit-box",
        WebkitBoxOrient: "vertical" as const,
        WebkitLineClamp: 6,
        overflow: "hidden",
      };

  return (
    <section aria-labelledby="game-synopsis-heading">
      <h2 id="game-synopsis-heading" className="sp-h2">
        {labels.heading}
      </h2>
      <p ref={paragraphRef} className="sp-detail-summary" style={clampStyle}>
        {text}
      </p>
      {mounted && isLong ? (
        <button
          type="button"
          className="sp-link"
          aria-expanded={expanded}
          onClick={() => setExpanded((current) => !current)}
        >
          {expanded ? labels.showLess : labels.showMore}
        </button>
      ) : null}
      <noscript>
        <details>
          <summary className="sp-link">{labels.showMore}</summary>
          <p className="sp-detail-summary">{text}</p>
        </details>
      </noscript>
    </section>
  );
}
