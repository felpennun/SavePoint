/**
 * English dictionary. Every key here MUST have an exact counterpart in
 * es.ts -- apps/web/tests/i18n.test.ts enforces parity.
 */

import type { Dictionary } from "./dictionary";

export const en: Dictionary = {
  nav: {
    home: "Home",
    catalogue: "Catalogue",
    collection: "Collection",
    profile: "Profile",
    sources: "Sources",
    login: "Log in",
    logout: "Log out",
    skipToContent: "Skip to content",
    openMenu: "Open menu",
    closeMenu: "Close menu",
  },
  catalogue: {
    heading: "Catalogue",
    searchLabel: "Search games",
    clearSearch: "Clear search",
    emptyHeading: "No games found",
    emptyBody: "Try another title or check the spelling.",
    resultCount: {
      zero: "0 results",
      one: "1 result",
      many: (count) => `${count} results`,
    },
  },
  collection: {
    heading: "Collection",
    emptyHeading: "Your collection is empty",
    emptyBody: "Add a status or a copy from a game page.",
    statusSummaryCount: {
      zero: "0",
      one: "1",
      many: (count) => `${count}`,
    },
    ownedCopyCount: {
      zero: "0 copies",
      one: "1 copy",
      many: (count) => `${count} copies`,
    },
  },
  status: {
    legend: "Status:",
    labels: {
      pending: "Pending",
      playing: "Playing",
      completed: "Completed",
      abandoned: "Abandoned",
    },
    save: "Save status",
    saveSuccess: "Status saved",
  },
  rating: {
    unrated: "Unrated",
    save: "Save rating",
    saveSuccess: "Rating saved",
  },
  errors: {
    generic: "We couldn't load this information. Try again.",
    invalidCredentials: "The username or password is incorrect. Check the details and try again.",
    homepageSampleFailure: "We couldn't load the catalogue sample. You can open the full catalogue.",
    openFullCatalogue: "Open full catalogue",
    retryCatalogue: "Retry catalogue",
    retryGameDetails: "Retry game details",
    retrySearch: "Retry search",
    retryStatusSave: "Retry status save",
    retryRatingSave: "Retry rating save",
    retrySignIn: "Retry sign-in",
  },
  loading: {
    generic: "Loading…",
  },
  provenance: {
    heading: "Provenance",
    notAvailable: "Not available",
  },
};
