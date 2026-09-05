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
    recommendations: "Recommendations",
    profile: "Profile",
    sources: "Sources",
    login: "Log in",
    loginAria: "Log in",
    logout: "Log out",
    account: "Account",
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
    gamesCount: {
      zero: "0 games",
      one: "1 game",
      many: (count) => `${count} games`,
    },
    filteredCount: {
      zero: "0 games match",
      one: "1 game matches",
      many: (count) => `${count} games match`,
    },
    viewFull: "Showing a filtered view — {n} of {total} games",
    filters: {
      heading: "Filters",
      platform: "Platform",
      genre: "Genre",
      yearFrom: "Year from",
      yearTo: "Year to",
      minRating: "Minimum IGDB rating",
      anyOption: "Any",
      apply: "Apply filters",
      clearAll: "Clear all filters",
      mobileToggle: "Filters ({n} active)",
      unavailable: "Some filters are unavailable right now. Search still works.",
      activeLabel: {
        zero: "No filters",
        one: "1 filter",
        many: (count) => `${count} filters`,
      },
      emptyHeading: "No games match these filters",
      emptyBody: "Clear a filter or widen your search.",
    },
    sort: {
      label: "Sort by",
      relevance: "Relevance",
      titleAsc: "Title A–Z",
      titleDesc: "Title Z–A",
      releaseNewest: "Release date (newest)",
      releaseOldest: "Release date (oldest)",
      ratingDesc: "IGDB rating (high to low)",
    },
  },
  card: {
    score: {
      aria: "IGDB rating {n} out of 100",
      none: "No IGDB rating",
    },
    rating: {
      aria: "Your rating: {n} of 5",
    },
  },
  detail: {
    igdbRating: "IGDB rating",
    genres: "Genres",
    platforms: "Platforms",
    releaseDate: "Release date",
    addToCollection: "Add to collection",
    inCollection: "In your collection",
    attribution: "Data from IGDB.com",
    seeSources: "See all sources",
  },
  recommendations: {
    nav: "Recommendations",
    heading: "Recommended by your genres",
    intro:
      "Built from the genres of the games you've rated and completed. Not the demo popularity ranking.",
    excludedNote: "Games already in your collection are not shown.",
    shelfHeading: "Because you play a lot of {genre}",
    shelfExplainer: {
      zero: "0 games in your collection are {genre}.",
      one: "1 game in your collection is {genre}.",
      many: (count) => `${count} games in your collection are {genre}.`,
    },
    emptyHeading: "Not enough activity yet",
    emptyBody: "Rate or complete a few games and genre suggestions will appear here.",
    emptyCta: "Browse the catalogue",
    error: "We couldn't build your recommendations. Try again.",
  },
  collection: {
    heading: "Collection",
    subheading: "Every game you've marked, rated, or own a copy of.",
    emptyHeading: "Your collection is empty",
    emptyBody: "Browse the catalogue to add games.",
    emptyCta: "Browse the catalogue",
    count: {
      zero: "0 games in your collection",
      one: "1 game in your collection",
      many: (count) => `${count} games in your collection`,
    },
    filterByStatus: "Status",
    allStatuses: "All",
    statusEmptyGroup: "No games marked {status}.",
    showAll: "Show all",
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
    sort: {
      label: "Sort by",
      recentlyUpdated: "Recently updated",
      ratingDesc: "Your rating (high to low)",
      titleAsc: "Title A–Z",
      releaseYear: "Release year (newest)",
    },
  },
  account: {
    switcher: {
      label: "Simulated account",
      change: "Switch account",
      current: "Signed in as {alias} (simulated)",
    },
    banner: "Simulated account — this is a controlled demo, not a real user account.",
    list: {
      heading: "Choose a simulated account",
      intro: "Each account has its own preloaded collection and ratings.",
    },
  },
  register: {
    heading: "Create a simulated account",
    intro:
      "This creates a working account inside the controlled demo. It is not a public production account.",
    username: "Username",
    password: "Password",
    confirmPassword: "Confirm password",
    submit: "Create simulated account",
    pending: "Creating…",
    haveAccount: "Already have an account? Log in",
    errorDuplicate: "That username is taken. Try another.",
    errorWeakPassword: "Choose a stronger password and try again.",
    errorGeneric: "We couldn't create the account. Try again.",
    errorRateLimited: "Too many attempts. Wait a minute and try again.",
  },
  home: {
    valueProposition:
      "A controlled, reproducible personal video-game catalogue, with explainable recommendations.",
    sampleHeading: "A catalogue sample",
    signedIn: {
      greeting: "Welcome back, {alias}",
      continueHeading: "Pick up where you left off",
      recommendationsCta: "See your genre recommendations",
    },
    loggedOut: {
      primaryCta: "Log in",
      secondaryCta: "Browse the catalogue",
      registerCta: "Create a simulated account",
    },
  },
  theme: {
    toggle: {
      label: "Theme",
      dark: "Dark",
      light: "Light",
      switchToDark: "Switch to dark theme",
      switchToLight: "Switch to light theme",
    },
  },
  common: {
    retry: "Try again",
    showMore: "Show more",
    coverMissing: "Cover not available",
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
