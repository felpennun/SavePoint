import { en } from "./en";
import { es } from "./es";
import type { Dictionary } from "./dictionary";

export type { CountCopy, Dictionary } from "./dictionary";
export { formatCount } from "./dictionary";

const DICTIONARIES: Record<"es" | "en", Dictionary> = { es, en };

export function getDictionary(locale: string): Dictionary {
  return DICTIONARIES[locale === "en" ? "en" : "es"];
}
