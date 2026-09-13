/**
 * Personal "platinum" mark overlaid on a game's cover -- Collection page
 * only (the caller decides whether to render this at all; GameCard never
 * fetches is_platinum itself). A diagonal corner ribbon with a piped edge
 * (CSS, see .sp-platinum-ribbon) plus a spiked medal seal centred on it,
 * with two ribbon tails hanging below it and a trophy stamped in the
 * middle -- all clipped by the cover's own `overflow: hidden` (see
 * .sp-cover), so nothing needs its own rounding.
 */

const MEDAL_VIEWBOX_W = 44;
const MEDAL_VIEWBOX_H = 58;
const MEDAL_CENTER = MEDAL_VIEWBOX_W / 2;
// A sunburst of sharp points reads as "medal seal", not "flower" -- an
// earlier rounded-scallop version (overlapping bump circles) looked like
// petals however finely spaced. A star polygon alternating an outer
// (spike tip) and inner (valley) radius gives proper points instead.
const SPIKE_COUNT = 20;

/** Point string for an alternating outer/inner-radius star polygon
 * centred on the medal -- the classic sunburst-seal silhouette. */
function starPoints(outerRadius: number, innerRadius: number): string {
  const total = SPIKE_COUNT * 2;
  return Array.from({ length: total }, (_, index) => {
    const angle = (index / total) * 2 * Math.PI - Math.PI / 2;
    const radius = index % 2 === 0 ? outerRadius : innerRadius;
    const x = MEDAL_CENTER + radius * Math.cos(angle);
    const y = MEDAL_CENTER + radius * Math.sin(angle);
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
}

export function PlatinumBadge({ label }: { label: string }) {
  return (
    <div className="sp-platinum-badge" aria-hidden={false} role="img" aria-label={label} title={label}>
      <span className="sp-platinum-ribbon" />
      <span className="sp-platinum-medal">
        <svg
          viewBox={`0 0 ${MEDAL_VIEWBOX_W} ${MEDAL_VIEWBOX_H}`}
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          {/* Ribbon tails, drawn first so the seal above overlaps and
              hides their top edge -- they read as hanging out from behind
              the medal, notched piped-edge duotone matching the rest.
              Each tail is rotated outward from its top attachment point
              so the pair splays apart rather than hanging parallel. */}
          <g transform="rotate(14 17 29)">
            <path d="M10.9 28 L23.1 28 L23.1 54 L17 46.5 L10.9 54 Z" fill="var(--color-accent)" />
            <path d="M13.1 30.8 L20.9 30.8 L20.9 50.3 L17 44.8 L13.1 50.3 Z" fill="var(--color-platinum-medal-fill)" />
          </g>
          <g transform="rotate(-14 27 29)">
            <path d="M20.9 28 L33.1 28 L33.1 54 L27 46.5 L20.9 54 Z" fill="var(--color-accent)" />
            <path d="M23.1 30.8 L30.9 30.8 L30.9 50.3 L27 44.8 L23.1 50.3 Z" fill="var(--color-platinum-medal-fill)" />
          </g>
          {/* Seal border spikes -- the brand-logo purple (BrandLockup's
              own checkpoint-marker colour). Inner/outer radii kept close
              together for a subtler point than a sharp sunburst. */}
          <polygon points={starPoints(20, 17)} fill="var(--color-accent)" />
          {/* Seal face -- the fixed darker purple, spiked to match the
              border ring above (an inner ring of it stays visible all the
              way round). */}
          <polygon points={starPoints(17, 14.5)} fill="var(--color-platinum-medal-fill)" />
          {/* Detailed cup-and-handles trophy stamp, black-outlined gold,
              matching the reference icon's look (rim, tapered bowl,
              looped handles, stepped base, a highlight streak and two
              shading strokes under the rim) -- scaled around the medal
              centre to fill the seal face without crossing its valleys
              (radius 14.5): the trophy's own bounding-box corners sit
              ~23.2 units from centre pre-scale, so 0.58 keeps them at
              ~13.5, just inside. */}
          <g transform={`translate(${MEDAL_CENTER} ${MEDAL_CENTER}) scale(0.58) translate(${-MEDAL_CENTER} ${-MEDAL_CENTER})`}>
            <g
              stroke="var(--color-platinum-medal-outline)"
              strokeWidth="0.9"
              strokeLinejoin="round"
              fill="var(--color-platinum-medal-trophy)"
            >
              <path d="M31.7 11.8 C38.5 11 41 20 35.3 23 C33.6 23.9 31.8 23.6 30.6 22.5 L31.8 20.6 C32.6 21.2 33.8 21.3 34.8 20.7 C38.3 18.7 37.2 12.8 31.2 13.6 Z" />
              <path d="M12.3 11.8 C5.5 11 3 20 8.7 23 C10.4 23.9 12.2 23.6 13.4 22.5 L12.2 20.6 C11.4 21.2 10.2 21.3 9.2 20.7 C5.7 18.7 6.8 12.8 12.8 13.6 Z" />
              <rect x={14} y={30} width={16} height={3} rx={0.8} />
              <rect x={16.5} y={27.3} width={11} height={3} rx={0.6} />
              <path d="M19.5 27.3 L24.5 27.3 L23.3 21 L20.7 21 Z" />
              <path d="M12 10 L32 10 C32 10 31.6 19 27.5 22.5 C25.8 23.9 23.3 24.5 22 24.5 C20.7 24.5 18.2 23.9 16.5 22.5 C12.4 19 12 10 12 10 Z" />
              <rect x={11.5} y={8.6} width={21} height={2.4} rx={1.2} />
            </g>
            {/* Rim shading + bowl highlight, over the trophy fill. */}
            <path
              d="M16 11 L19.2 10.3 M28 11 L24.8 10.3"
              stroke="var(--color-platinum-medal-outline)"
              strokeWidth="0.7"
              strokeLinecap="round"
            />
            <path
              d="M15.6 11.5 C14.4 14.5 14.7 18.3 16.6 21.2"
              stroke="var(--color-platinum-medal-trophy-light)"
              strokeWidth="1.4"
              fill="none"
              strokeLinecap="round"
            />
          </g>
        </svg>
      </span>
    </div>
  );
}
