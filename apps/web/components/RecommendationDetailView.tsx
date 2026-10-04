"use client";

import Link from "next/link";

import { GameCard } from "@/components/GameCard";
import { CoverImage } from "@/components/CoverImage";
import { getDictionary } from "@/i18n";
import type { ContentRecommendationItem } from "@/lib/api";
import { localizedGenreLabel } from "@/lib/genre-labels";

type WeightKey = "content" | "quality" | "popularity" | "recency" | "relevance" | "diversity";

/** The real weights of the published algorithms (see recommendations/content/variants.py).
 * The MMR variant scores 0.80 x relevance - 0.20 x similarity to what is already
 * selected, and its relevance is the weighted-pop-v2 blend (content 0.4375, rating 0.25,
 * PopScore 0.3125); so its effective weights are 0.35 / 0.20 / 0.25 and 0.20 for variety. */
const ALGORITHM_WEIGHTS: Record<string, { code: string; weights: Array<[WeightKey, number]> }> = {
  "content-cbf-weighted-v1": {
    code: "WEIGHTED",
    weights: [
      ["content", 0.7],
      ["quality", 0.3],
    ],
  },
  "recency-v1": {
    code: "RECENCY",
    weights: [
      ["recency", 0.4],
      ["content", 0.2],
      ["quality", 0.2],
      ["popularity", 0.2],
    ],
  },
  "content-cbf-mmr-pop-v2": {
    code: "MMR-POP",
    weights: [
      ["content", 0.35],
      ["quality", 0.2],
      ["popularity", 0.25],
      ["diversity", 0.2],
    ],
  },
};

const SEGMENT_COLORS = ["var(--color-accent)", "var(--color-accent-edge)", "var(--color-secondary-mid)", "var(--color-text-muted)"];

const COPY = {
  es: {
    rail: "ALGORITMO",
    railLabel: "Algoritmos de recomendación",
    rank: "#",
    game: "JUEGO",
    why: "POR QUÉ",
    affinity: "AFINIDAD",
    weights: {
      content: "PARECIDO A LO TUYO",
      quality: "NOTA DEL JUEGO",
      popularity: "POPULARIDAD",
      recency: "FECHA DE SALIDA",
      relevance: "RELEVANCIA",
      diversity: "VARIEDAD",
    },
    recencyReason: "NOVEDAD",
    weightsLabel: "Peso de cada señal en el cálculo",
  },
  en: {
    rail: "ALGORITHM",
    railLabel: "Recommendation algorithms",
    rank: "#",
    game: "GAME",
    why: "WHY",
    affinity: "AFFINITY",
    weights: {
      content: "SIMILAR TO YOURS",
      quality: "GAME SCORE",
      popularity: "POPULARITY",
      recency: "RELEASE DATE",
      relevance: "RELEVANCE",
      diversity: "VARIETY",
    },
    recencyReason: "NEW",
    weightsLabel: "Weight of each signal in the calculation",
  },
} as const;

export interface DetailSection {
  algorithmId: string;
  heading: string;
  description: string;
  items: ContentRecommendationItem[];
}

function weightsCode(algorithmId: string): string {
  const entry = ALGORITHM_WEIGHTS[algorithmId];
  if (!entry) return algorithmId;
  return `${entry.code} · ${entry.weights.map(([, value]) => value.toFixed(2)).join("/")}`;
}

/** The recommendations page (artboard 1c): a rail to pick the algorithm and,
 * for the chosen one only, either its shelf (scrolling row of covers) or the
 * detailed view with the weight of each signal, its description and a table
 * with rank, game, why and affinity. The rail is the same in both views. */
export function RecommendationDetailView({
  sections,
  selectedId,
  onSelect,
  locale,
  mode,
  onToggleMode,
  toggleLabel,
  toggleText,
}: {
  sections: DetailSection[];
  selectedId: string;
  onSelect: (algorithmId: string) => void;
  locale: "es" | "en";
  mode: "shelf" | "detail";
  /** Switches between the shelf and the detailed view (button inside the frame). */
  onToggleMode: () => void;
  toggleLabel: string;
  toggleText: string;
}) {
  const copy = COPY[locale];
  const dict = getDictionary(locale);
  const selected = sections.find((section) => section.algorithmId === selectedId) ?? sections[0];
  if (!selected) return null;
  const weights = ALGORITHM_WEIGHTS[selected.algorithmId]?.weights;

  return (
    <div className="sp-reco-layout">
      <nav className="sp-reco-rail" aria-label={copy.railLabel}>
        <span className="sp-reco-rail-title">{copy.rail}</span>
        {sections.map((section) => {
          const active = section.algorithmId === selected.algorithmId;
          return (
            <button
              key={section.algorithmId}
              type="button"
              className={`sp-reco-rail-item${active ? " is-on" : ""}`}
              aria-pressed={active}
              onClick={() => onSelect(section.algorithmId)}
            >
              <span>{section.heading}</span>
              <span className="sp-reco-rail-code">{weightsCode(section.algorithmId)}</span>
            </button>
          );
        })}
      </nav>

      <section
        className={`sp-reco-detail${mode === "detail" ? " sp-reco-detail--table" : ""}`}
        aria-labelledby="reco-detail-title"
      >
        <div className="sp-reco-intro">
          <div className="sp-reco-intro-head">
            <h2 id="reco-detail-title">{selected.heading}</h2>
            <button
              type="button"
              className={`sp-view-toggle${mode === "detail" ? " is-on" : ""}`}
              aria-pressed={mode === "detail"}
              aria-label={toggleLabel}
              title={toggleLabel}
              onClick={onToggleMode}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" />
                <rect x="13.5" y="3.5" width="7" height="7" rx="1.5" />
                <rect x="3.5" y="13.5" width="7" height="7" rx="1.5" />
                <rect x="13.5" y="13.5" width="7" height="7" rx="1.5" />
              </svg>
              <span className="sp-view-toggle-text">{toggleText}</span>
            </button>
          </div>
          {weights ? (
            <>
              <div className="sp-reco-weights-bar" role="img" aria-label={copy.weightsLabel}>
                {weights.map(([key, value], index) => (
                  <span key={key} style={{ flex: Math.round(value * 100), background: SEGMENT_COLORS[index] }} />
                ))}
              </div>
              <ul className="sp-reco-weights-legend">
                {weights.map(([key, value], index) => (
                  <li key={key} style={{ color: index === 0 ? "var(--color-accent-strong)" : undefined }}>
                    <span aria-hidden="true" style={{ color: SEGMENT_COLORS[index] }}>
                      ■
                    </span>{" "}
                    {copy.weights[key]} {value.toFixed(2)}
                  </li>
                ))}
              </ul>
            </>
          ) : null}
          <p>{selected.description}</p>
        </div>

        {mode === "shelf" ? (
          <ol className="sp-shelf-track" key={selected.algorithmId}>
            {selected.items.map((item) => (
              <GameCard
                key={item.work_id}
                game={{
                  id: item.work_id,
                  slug: item.slug,
                  title: item.title,
                  year: item.year,
                  platform_summary: item.platform_summary,
                  cover: item.cover,
                }}
                locale={locale}
                score={item.display_rating}
              />
            ))}
          </ol>
        ) : (
        <div className="sp-reco-tablewrap">
        <table className="sp-reco-table">
          <thead>
            <tr>
              <th scope="col">{copy.rank}</th>
              <th scope="col" aria-label={copy.game} />
              <th scope="col">{copy.game}</th>
              <th scope="col" className="sp-reco-why-col">
                {copy.why}
              </th>
              <th scope="col" className="sp-reco-affinity-col">
                {copy.affinity}
              </th>
            </tr>
          </thead>
          <tbody>
            {selected.items.map((item, index) => {
              const reasons = item.contributions
                .slice(0, 2)
                .map((entry) => localizedGenreLabel(entry.tag, entry.tag, locale).toUpperCase());
              if (reasons.length === 0 && selected.algorithmId === "recency-v1") reasons.push(copy.recencyReason);
              const affinity = Math.max(0, Math.min(1, item.score));
              const meta = [item.year, item.platform_summary, item.display_rating]
                .filter((part) => part !== null && part !== "")
                .join(" · ");
              return (
                <tr key={item.work_id}>
                  <td className="sp-reco-rank">{String(index + 1).padStart(2, "0")}</td>
                  <td className="sp-reco-cover">
                    <Link href={`/${locale}/games/${item.slug}`} tabIndex={-1} aria-hidden="true">
                      <CoverImage
                        src={item.cover.url}
                        alt=""
                        title={item.title}
                        missingLabel={dict.common.coverMissing}
                        width={60}
                        height={80}
                      />
                    </Link>
                  </td>
                  <td className="sp-reco-game">
                    <Link href={`/${locale}/games/${item.slug}`}>{item.title}</Link>
                    <span>{meta}</span>
                  </td>
                  <td className="sp-reco-why-col">
                    <span className="sp-reco-tags">
                      {reasons.map((reason) => (
                        <span key={reason} className="sp-reco-tag">
                          + {reason}
                        </span>
                      ))}
                    </span>
                  </td>
                  <td className="sp-reco-affinity-col">
                    <span className="sp-reco-score">{affinity.toFixed(2)}</span>
                    <span className="sp-reco-meter" aria-hidden="true">
                      <span style={{ width: `${Math.round(affinity * 100)}%` }} />
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>
        )}
      </section>
    </div>
  );
}
