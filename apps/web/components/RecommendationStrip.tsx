import Link from "next/link";

import type { PopularityResultItem } from "@/lib/api";

const COPY = {
  es: {
    heading: "Populares en la demo",
    explainer:
      "Orden calculado a partir de interacciones agregadas de esta demo. No es una recomendación personalizada.",
  },
  en: {
    heading: "Popular in this demo",
    explainer: "Order calculated from aggregate interactions in this demo. Not a personalized recommendation.",
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
