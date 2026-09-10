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
    search: "Search by name",
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
    facet: {
      selectedCount: {
        zero: "Any",
        one: "1 selected",
        many: (count) => `${count} selected`,
      },
      clear: "Clear",
      searchInList: "Filter this list",
    },
    chip: {
      genre: "Genre: {value}",
      platform: "Platform: {value}",
    },
  },
  card: {
    score: {
      label: "Rating",
      aria: "Rating {n} out of 100",
      none: "No rating",
    },
    rating: {
      aria: "Your rating: {n} of 5",
    },
  },
  detail: {
    synopsis: {
      heading: "Summary",
      showMore: "Show more",
      showLess: "Show less",
    },
    ratingBreakdown: "Based on ratings from {igdb} IGDB users and {savepoint} SavePoint users.",
    ratingBreakdownExternalOnly: "Based on ratings from {igdb} IGDB users.",
    ratingBreakdownLocalOnly: "Based on ratings from {savepoint} SavePoint users.",
    summary: "Synopsis",
    summaryUnavailable: "No synopsis is available for this game.",
    ratings: "Ratings",
    releases: "Releases and editions",
    editions: "Editions",
    relatedContent: "Related content",
    dlc: "DLC",
    expansion: "Expansion",
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
    heading: "Recommended by your genres and ratings",
    intro:
      "Built from the genres of the games you've rated and completed, prioritising the catalogue's highest-rated games. Not the demo popularity ranking.",
    excludedNote: "Games already in your collection are not shown.",
    methodHeading: "How these are generated",
    methodAlgorithm:
      "Algorithm: {id} — a deterministic genre heuristic ordered by catalogue rating, not the demo popularity ranking and not a trained model.",
    shelfHeading: "Because you play a lot of {genre}",
    shelfEvidence:
      "These games share the {genre} genre with titles you've rated or set a status on.",
    cardEvidence: "Shares your genres: {genres}",
    contentCardEvidence: "Matches your taste in {reasons}.",
    emptyHeading: "Not enough activity yet",
    emptyBody: "Add games to your collection and, if you like, rate them or set their status to start receiving recommendations.",
    emptyCta: "Browse the catalogue",
    error: "We couldn't load your recommendations. Try again.",
    retry: "Reload recommendations",
    contentHeading: "Recommended for you",
    contentSections: {
      weighted: {
        heading: "Content match",
        description: "Combines content similarity, your ratings, and quality and popularity signals.",
      },
      multiplicative: {
        heading: "Balanced content match",
        description: "Combines signals so that a very low match in one dimension cannot be fully offset by another.",
      },
      twoStage: {
        heading: "Two-stage content match",
        description: "First finds content-similar works, then orders them with scalar signals.",
      },
      negative: {
        heading: "Content match with your preferences in mind",
        description: "Boosts what you rate positively and reduces genres you have rated negatively several times.",
      },
      weightedPop: {
        heading: "Content and popularity match",
        description: "Combines content, rating-confidence, and PopScore; missing PopScore uses the minimum.",
      },
      multiplicativePop: {
        heading: "Balanced match with popularity",
        description: "Multiplies affinity and quality, adjusting popularity between a 15% penalty and a 15% boost.",
      },
      twoStagePop: {
        heading: "Two-stage match with popularity",
        description: "Similarity chooses the band; rating-confidence and PopScore order works within it.",
      },
      negativePop: {
        heading: "Match with preferences and popularity",
        description: "Boosts your preferences and catalogue activity while retaining the negative-similarity penalty.",
      },
      recency: {
        heading: "Recent matches for you",
        description: "Uses the same personalised signals and adds release-date recency.",
      },
      mmr: {
        heading: "Diverse content matches",
        description: "Starts from Weighted and reduces repetition between very similar games.",
      },
      mmrPop: {
        heading: "Diverse matches with popularity",
        description: "Starts from Weighted-Pop and balances relevance, PopScore, and variety.",
      },
      collaborative: {
        heading: "Matches from similar users",
        description: "Learns from users with similar ratings and prioritizes works they rated positively.",
      },
      hybrid: {
        heading: "Hybrid affinity",
        description: "Combines Weighted content affinity with ratings from similar users.",
      },
      hybridMmr: {
        heading: "Diverse hybrid affinity",
        description: "Combines content and collaborative affinity with MMR to reduce repetition between very similar games.",
      },
    },
    genreDescription: "A heuristic based on the genres in your activity and the catalogue rating.",
    refreshPreparing: "We are preparing your recommendations.",
    refreshUpdating: "We are updating your recommendations; you are seeing the previous version for now.",
    refreshNeedsCollectionChange: "Update your collection to refresh your recommendations.",
    dlc: {
      heading: "For games you own",
      intro: "Downloadable content for games already in your collection.",
      baseGameLabel: "DLC for {game}",
    },
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
    filterByCopy: "Copies",
    allCopyStates: "With and without copies",
    withCopy: "With a copy",
    withoutCopy: "Without a copy",
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
    passwordHint:
      "At least 8 characters. Avoid common passwords, all-numeric passwords, or ones close to your username. Any character is allowed, including spaces and symbols.",
    confirmPassword: "Confirm password",
    submit: "Create simulated account",
    pending: "Creating…",
    haveAccount: "Already have an account? Log in",
    errorDuplicate: "That username is taken. Try another.",
    errorWeakPassword: "Choose a stronger password and try again.",
    weakPasswordIntro: "The password does not meet the requirements:",
    errorGeneric: "We couldn't create the account. Try again.",
    errorRateLimited: "Too many attempts. Wait a minute and try again.",
  },
  home: {
    valueProposition:
      "A controlled, reproducible personal video-game catalogue, with explainable recommendations.",
    sampleHeading: "A catalogue sample",
    newReleases: {
      heading: "New releases",
      explainer: "Recently released games from the governed corpus.",
    },
    signedIn: {
      greeting: "Welcome back, {alias}",
      continueHeading: "Pick up where you left off",
      recommendationsCta: "See your genre recommendations",
    },
    loggedOut: {
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
    showLess: "Show less",
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
