import Link from "next/link";

import type { PopularityResultItem } from "@/lib/api";

const COPY = {
  es: {
    heading: "Populares en SavePoint",
    explainer:
      "Orden calculado a partir de las señales de popularidad importadas de IGDB. No es una recomendación personalizada.",
  },
  en: {
    heading: "Popular on SavePoint",
    explainer: "Order calculated from the popularity signals imported from IGDB. Not a personalized recommendation.",
  },
} as const;

/**
 * REC-02: always labels itself as a simple aggregate baseline -- never
 * "recommended for you" or any personalization claim the demo doesn't
 * actually implement.
 */
export function RecommendationStrip({
  results,
  locale,
}: {
  results: PopularityResultItem[];
  locale: "es" | "en";
}) {
  const copy = COPY[locale];
  if (results.length === 0) return null;

  return (
    <section aria-label={copy.heading}>
      <h2>{copy.heading}</h2>
      <p>{copy.explainer}</p>
      <ol>
        {results.map((item) => (
          <li key={item.work_id}>
            <Link href={`/${locale}/games/${item.slug}`}>{item.title}</Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
