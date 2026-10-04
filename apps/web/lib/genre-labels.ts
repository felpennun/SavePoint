/**
 * Spanish names for the genre (tag) vocabulary shown in the catalogue filter,
 * its chips and the game detail page. The API serves the upstream English names
 * (IGDB and the curated labels); the Spanish interface translates them here by
 * their stable slug, and any slug without an entry falls back to the original
 * name, so a new upstream value never breaks the page.
 */
const GENRE_LABELS_ES: Record<string, string> = {
  // Curated tags (the "Género" filter)
  action: "Acción",
  adventure: "Aventura",
  anime: "Anime",
  arcade: "Arcade",
  "battle-royale": "Battle royale",
  "card-game": "Juego de cartas",
  casual: "Casual",
  comedy: "Comedia",
  "co-op": "Cooperativo",
  cyberpunk: "Ciberpunk",
  deckbuilder: "Construcción de mazos",
  educational: "Educativo",
  "family-friendly": "Apto para familias",
  fantasy: "Fantasía",
  fighting: "Lucha",
  "hack-and-slash": "Hack and slash",
  historical: "Histórico",
  horror: "Terror",
  indie: "Indie",
  jrpg: "JRPG",
  kids: "Infantil",
  metroidvania: "Metroidvania",
  mmo: "MMO",
  moba: "MOBA",
  multiplayer: "Multijugador",
  music: "Música",
  mystery: "Misterio",
  "open-world": "Mundo abierto",
  party: "Fiesta",
  pinball: "Pinball",
  "pixel-art": "Pixel art",
  platformer: "Plataformas",
  "point-and-click": "Point-and-click",
  puzzle: "Puzles",
  racing: "Carreras",
  retro: "Retro",
  roguelike: "Roguelike",
  romance: "Romance",
  rpg: "RPG",
  sandbox: "Sandbox",
  "sci-fi": "Ciencia ficción",
  shooter: "Disparos",
  "side-scroller": "Scroll lateral",
  simulation: "Simulación",
  singleplayer: "Un jugador",
  "souls-like": "Souls-like",
  "split-screen": "Pantalla dividida",
  sports: "Deportes",
  stealth: "Sigilo",
  "story-rich": "Narrativa profunda",
  strategy: "Estrategia",
  superhero: "Superhéroes",
  survival: "Supervivencia",
  tactical: "Táctico",
  trivia: "Preguntas y respuestas",
  "turn-based": "Por turnos",
  "visual-novel": "Novela visual",
  vr: "Realidad virtual",
  // IGDB genres (kept for filters opened from a shared URL)
  "card-board-game": "Cartas y juegos de mesa",
  "hack-and-slashbeat-em-up": "Hack and slash / Beat 'em up",
  platform: "Plataformas",
  quiztrivia: "Preguntas y respuestas",
  "real-time-strategy-rts": "Estrategia en tiempo real (RTS)",
  "role-playing-rpg": "Rol (RPG)",
  simulator: "Simulador",
  sport: "Deportes",
  "turn-based-strategy-tbs": "Estrategia por turnos (TBS)",
};

/** Name to show for a genre/tag: Spanish when the interface is Spanish and a translation exists. */
export function localizedGenreLabel(slug: string, name: string, locale: string): string {
  if (locale !== "es") return name;
  return GENRE_LABELS_ES[slug] ?? name;
}
