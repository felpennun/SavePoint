export const PROFILE_TABS = ["profile", "collection", "lists", "comments"] as const;
export type ProfileTab = (typeof PROFILE_TABS)[number];

/** `?tab=` values accepted by the profile page; anything else opens the first tab. */
export function parseProfileTab(value: string | string[] | undefined): ProfileTab {
  const raw = Array.isArray(value) ? value[0] : value;
  return (PROFILE_TABS as readonly string[]).includes(raw ?? "") ? (raw as ProfileTab) : "profile";
}

export type ProfileNavigationSection = "profile" | "collection" | "list";

const LABELS = {
  es: { profile: "Perfil", collection: "Colección", lists: "Listas" },
  en: { profile: "Profile", collection: "Collection", lists: "Lists" },
} as const;

/** The local links shown on a profile sub-page (a list opened from the profile):
 * each opens the matching tab of the profile page. */
export function buildProfileNavigation(locale: string, alias: string, current: ProfileNavigationSection) {
  const labels = locale === "en" ? LABELS.en : LABELS.es;
  const base = `/${locale}/profiles/${encodeURIComponent(alias)}`;
  return [
    { href: base, label: labels.profile, current: current === "profile" },
    { href: `${base}?tab=collection`, label: labels.collection, current: current === "collection" },
    { href: `${base}?tab=lists`, label: labels.lists, current: current === "list" },
  ];
}
