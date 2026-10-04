import { cookies } from "next/headers";
import Link from "next/link";

import { CoverImage } from "@/components/CoverImage";
import { StatusPill, type BacklogStatus } from "@/components/StatusPill";
import { getDictionary } from "@/i18n";
import {
  fetchCatalogueStats,
  getNewReleases,
  fetchMyLibrary,
  type Cover,
  type GameCard,
  type MyLibraryItem,
} from "@/lib/api";

const STATUSES: BacklogStatus[] = ["pending", "playing", "completed", "abandoned"];
function pickRandom<T>(items: T[]): T | null {
  return items.length > 0 ? items[Math.floor(Math.random() * items.length)] : null;
}

const COPY = {
  es: {
    headline: "Tu biblioteca de juegos, siempre al día.",
    lead:
      "Guarda lo que quieres jugar, lo que estás jugando y lo que ya terminaste. Cuanto más valoras, mejores son las sugerencias.",
    createAccount: "Crear cuenta gratis",
    exploreCatalogue: "Explorar el catálogo",
    myCollection: "Ir a mi colección",
    sampleNote: "Voy por Ciudad Lágrimas. Falta la llave simple.",
    sampleStatus: "JUGANDO",
    yourRating: (value: number) => `TU NOTA ${value}/10`,
    features: [
      ["01", "Tu colección, a tu manera", "Marca cada juego como pendiente, jugando, completado o abandonado, ponle nota y guarda tus copias. Crea listas propias, como «Para el Steam Deck»."],
      ["02", "Recomendaciones que se explican", "Te sugerimos juegos según los géneros y etiquetas de lo que ya tienes valorado, y puedes ver por qué aparece cada uno. Sin cajas negras: el mismo algoritmo da siempre el mismo resultado."],
      ["03", "Compartir, solo si quieres", "Tu colección es privada hasta que decidas lo contrario. Añade a tus amistades, mira sus favoritos y recomiéndales juegos de tu colección."],
    ],
    stats: {
      games: "juegos en el catálogo",
      rated: "con nota de IGDB",
      platforms: "plataformas, clásicas y actuales",
      years: (since: number | null) => (since ? `años de videojuegos, desde ${since}` : "años de videojuegos"),
    },
    dataFrom: "Datos de juegos: IGDB · Metodología en",
    sources: "Fuentes",
  },
  en: {
    headline: "Your game library, always up to date.",
    lead:
      "Save what you want to play, what you are playing and what you have finished. The more you rate, the better the suggestions get.",
    createAccount: "Create a free account",
    exploreCatalogue: "Explore the catalogue",
    myCollection: "Go to my collection",
    sampleNote: "Up to the City of Tears. Still missing the simple key.",
    sampleStatus: "PLAYING",
    yourRating: (value: number) => `YOUR RATING ${value}/10`,
    features: [
      ["01", "Your collection, your way", "Mark each game as pending, playing, completed or abandoned, rate it and keep track of your copies. Create your own lists, such as “For the Steam Deck”."],
      ["02", "Recommendations that explain themselves", "We suggest games based on the genres and tags of what you have already rated, and you can see why each one shows up. No black boxes: the same algorithm always gives the same result."],
      ["03", "Share only if you want to", "Your collection is private until you decide otherwise. Add your friends, see their favorites and recommend games from your collection."],
    ],
    stats: {
      games: "games in the catalogue",
      rated: "with an IGDB score",
      platforms: "platforms, classic and current",
      years: (since: number | null) => (since ? `years of video games, since ${since}` : "years of video games"),
    },
    dataFrom: "Game data: IGDB · Methodology in",
    sources: "Sources",
  },
} as const;

function formatCount(value: number, locale: "es" | "en"): string {
  return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, locale === "es" ? " " : ",");
}

interface Showcase {
  slug: string;
  title: string;
  cover: Cover;
  status: BacklogStatus | null;
  /** "TU NOTA 10/10 · PC, SWITCH" style line, or the platforms alone. */
  meta: string;
  note: string | null;
}

/** Home (artboard 3c, "Cómo funciona"): the same page with and without a
 * session. Only the calls to action and the showcase card change: a signed-in
 * user sees a random game of their collection, anyone else a random well-rated
 * game as the example of what a collection entry looks like. */
export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const copy = COPY[locale];
  const dict = getDictionary(locale);
  const cookieStore = await cookies();
  const isAuthenticated = cookieStore.has("sessionid");
  const cookieHeader = cookieStore
    .getAll()
    .map((cookie) => `${cookie.name}=${cookie.value}`)
    .join("; ");

  // The example game of the anonymous showcase is one of the new releases (the
  // "Novedades" snapshot: recent games with an IGDB score and PopScore), a
  // different one on every visit. The figures band comes from the catalogue stats.
  let topGame: GameCard | null = null;
  try {
    const newReleases = await getNewReleases();
    topGame = pickRandom(newReleases.filter((game) => !game.cover.is_placeholder)) ?? pickRandom(newReleases);
  } catch {
    // The page still reads well without the example game.
  }
  let catalogueStats: Awaited<ReturnType<typeof fetchCatalogueStats>> = null;
  try {
    catalogueStats = await fetchCatalogueStats();
  } catch {
    catalogueStats = null;
  }

  // A signed-in user sees a different game of their own collection on every visit.
  let current: MyLibraryItem | null = null;
  if (isAuthenticated) {
    try {
      const library = await fetchMyLibrary(cookieHeader);
      const withCover = library.items.filter((item) => !item.cover.is_placeholder);
      current = pickRandom(withCover.length > 0 ? withCover : library.items);
    } catch {
      current = null;
    }
  }

  const showcase: Showcase | null = current
    ? {
        slug: current.work_slug,
        title: current.work_title,
        cover: current.cover,
        status: (STATUSES as string[]).includes(current.status) ? (current.status as BacklogStatus) : null,
        meta: [
          current.rating_half_steps ? copy.yourRating(current.rating_half_steps) : null,
          current.platform_summary ? current.platform_summary.toUpperCase() : null,
        ]
          .filter(Boolean)
          .join(" · "),
        note: null,
      }
    : topGame
      ? {
          slug: topGame.slug,
          title: topGame.title,
          cover: topGame.cover,
          status: "playing",
          meta: [topGame.platform_summary ? topGame.platform_summary.toUpperCase() : null].filter(Boolean).join(" · "),
          note: copy.sampleNote,
        }
      : null;

  const yearsCovered =
    catalogueStats?.first_year != null && catalogueStats.last_year != null
      ? catalogueStats.last_year - catalogueStats.first_year
      : null;
  const stats: Array<[string, string]> = [
    [catalogueStats ? formatCount(catalogueStats.games, locale) : "—", copy.stats.games],
    [catalogueStats ? formatCount(catalogueStats.rated, locale) : "—", copy.stats.rated],
    [catalogueStats ? formatCount(catalogueStats.platforms, locale) : "—", copy.stats.platforms],
    [
      yearsCovered !== null ? String(yearsCovered) : "—",
      copy.stats.years(catalogueStats?.first_year ?? null),
    ],
  ];

  return (
    <main className="sp-page sp-home-page">
      <div className="sp-home">
        <section className="sp-home-hero">
          <div className="sp-home-hero-text">
            <h1>{copy.headline}</h1>
            <p>{copy.lead}</p>
            <div className="sp-home-actions">
              {isAuthenticated ? (
                <>
                  <Link href={`/${locale}/collection`} className="sp-home-btn is-primary">
                    {copy.myCollection}
                  </Link>
                  <Link href={`/${locale}/catalogue`} className="sp-home-btn">
                    {copy.exploreCatalogue}
                  </Link>
                </>
              ) : (
                <>
                  <Link href={`/${locale}/register`} className="sp-home-btn is-primary">
                    {copy.createAccount}
                  </Link>
                  <Link href={`/${locale}/catalogue`} className="sp-home-btn">
                    {copy.exploreCatalogue}
                  </Link>
                </>
              )}
            </div>
          </div>

          {showcase ? (
            <Link href={`/${locale}/games/${showcase.slug}`} className="sp-home-showcase">
              <span className="sp-home-showcase-cover">
                <CoverImage
                  src={showcase.cover.url}
                  alt=""
                  title={showcase.title}
                  missingLabel={dict.common.coverMissing}
                  width={120}
                  height={160}
                />
              </span>
              <span className="sp-home-showcase-body">
                <span className="sp-home-showcase-head">
                  <strong>{showcase.title}</strong>
                  {showcase.status ? <StatusPill status={showcase.status} label={dict.status.labels[showcase.status]} /> : null}
                </span>
                {showcase.note ? <span className="sp-home-showcase-note">{showcase.note}</span> : null}
                {showcase.meta ? <span className="sp-home-showcase-meta">{showcase.meta}</span> : null}
              </span>
            </Link>
          ) : null}
        </section>

        <section className="sp-home-features" aria-label={copy.features[0][1]}>
          {copy.features.map(([number, title, body]) => (
            <div key={number} className="sp-home-feature">
              <span className="sp-home-feature-n">{number}</span>
              <h2>{title}</h2>
              <p>{body}</p>
            </div>
          ))}
        </section>

        <section className="sp-home-stats">
          {stats.map(([value, label]) => (
            <div key={label}>
              <strong>{value}</strong>
              <span>{label}</span>
            </div>
          ))}
        </section>

        <div className="sp-home-foot">
          <span>
            {copy.dataFrom}{" "}
            <Link href={`/${locale}/sources`} className="sp-home-foot-link">
              {copy.sources}
            </Link>
          </span>
          <span className="sp-home-foot-lang">
            <Link href="/es" aria-current={locale === "es" ? "page" : undefined}>
              ES
            </Link>
            {" / "}
            <Link href="/en" aria-current={locale === "en" ? "page" : undefined}>
              EN
            </Link>
          </span>
        </div>
      </div>
    </main>
  );
}
