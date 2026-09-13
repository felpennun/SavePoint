/** Shared dictionary shape -- both es.ts and en.ts must satisfy this type
 * exactly (TypeScript structural typing already enforces key presence and
 * value shape at compile time; i18n.test.ts additionally proves runtime
 * key-set parity so a typo in one file can't silently diverge). */

export interface CountCopy {
  zero: string;
  one: string;
  many: (count: number) => string;
}

export interface Dictionary {
  nav: {
    home: string;
    catalogue: string;
    collection: string;
    recommendations: string;
    profile: string;
    sources: string;
    login: string;
    loginAria: string;
    logout: string;
    account: string;
    skipToContent: string;
    openMenu: string;
    closeMenu: string;
    search: string;
  };
  catalogue: {
    heading: string;
    searchLabel: string;
    clearSearch: string;
    emptyHeading: string;
    emptyBody: string;
    resultCount: CountCopy;
    gamesCount: CountCopy;
    filteredCount: CountCopy;
    viewFull: string;
    filters: {
      heading: string;
      platform: string;
      tag: string;
      year: string;
      minRating: string;
      anyOption: string;
      apply: string;
      clearAll: string;
      mobileToggle: string;
      unavailable: string;
      activeLabel: CountCopy;
      emptyHeading: string;
      emptyBody: string;
    };
    facet: {
      selectedCount: CountCopy;
      clear: string;
      searchInList: string;
    };
    chip: {
      tag: string;
      platform: string;
    };
  };
  card: {
    score: {
      label: string;
      aria: string;
      none: string;
      /** Tier names shown beside the ScorePill on the detail page,
       * coloured in the tier colour. */
      tiers: {
        essential: string;
        great: string;
        fair: string;
        poor: string;
        bad: string;
      };
    };
    rating: {
      aria: string;
    };
    platinum: {
      label: string;
    };
  };
  detail: {
    synopsis: {
      heading: string;
      showMore: string;
      showLess: string;
    };
    ratingBreakdown: string;
    ratingBreakdownExternalOnly: string;
    ratingBreakdownLocalOnly: string;
    igdbRating: string;
    tags: string;
    platforms: string;
    releaseDate: string;
    summary: string;
    summaryUnavailable: string;
    ratings: string;
    releases: string;
    editions: string;
    relatedContent: string;
    dlc: string;
    expansion: string;
    addToCollection: string;
    inCollection: string;
    attribution: string;
    seeSources: string;
  };
  recommendations: {
    nav: string;
    contentHeading: string;
    heading: string;
    intro: string;
    excludedNote: string;
    /** Heading for the algorithm_id + limitation disclosure block. */
    methodHeading: string;
    /** "{id}" -> the DTO's algorithm_id, so this heuristic is never
     * confused with popularity (REC-02) or the Phase 6 recommender. */
    methodAlgorithm: string;
    shelfHeading: string;
    /** "{tag}" -> the taste tag; per-shelf plain-language explainer. */
    shelfEvidence: string;
    emptyHeading: string;
    emptyBody: string;
    emptyCta: string;
    error: string;
    retry: string;
    dlc: {
      heading: string;
      intro: string;
      baseGameLabel: string;
    };
    contentSections: {
      weighted: { heading: string; description: string };
      multiplicative: { heading: string; description: string };
      twoStage: { heading: string; description: string };
      negative: { heading: string; description: string };
      weightedPop: { heading: string; description: string };
      multiplicativePop: { heading: string; description: string };
      twoStagePop: { heading: string; description: string };
      negativePop: { heading: string; description: string };
      recency: { heading: string; description: string };
      mmr: { heading: string; description: string };
      mmrPop: { heading: string; description: string };
      collaborative: { heading: string; description: string };
      hybrid: { heading: string; description: string };
      hybridMmr: { heading: string; description: string };
    };
    tagDescription: string;
    refreshPreparing: string;
    refreshUpdating: string;
    refreshNeedsCollectionChange: string;
  };
  social: {
    friends: {
      heading: string;
      searchHeading: string;
      searchLabel: string;
      search: string;
      received: string;
      sent: string;
      list: string;
      receivedEmpty: string;
      sentEmpty: string;
      emptyHeading: string;
      emptyBody: string;
      exactAliasEmpty: string;
      exactAliasEmptyBody: string;
      requestCount: CountCopy;
      friendCount: CountCopy;
      relationship: string;
      pending: string;
      none: string;
      accepted: string;
      blocked: string;
    };
    messages: {
      nav: string;
      heading: string;
      emptyHeading: string;
      emptyBody: string;
      markRead: string;
      markUnread: string;
      unreadCount: CountCopy;
      recommend: string;
      optionalMessage: string;
      send: string;
      sending: string;
      sent: string;
    };
    profile: {
      basicNotice: string;
    };
    privacy: {
      collectionEmpty: string;
      listEmpty: string;
      commentsHidden: string;
    };
    actions: {
      sendRequest: string;
      requestSent: string;
      acceptRequest: string;
      rejectRequest: string;
      removeFriendship: string;
      block: string;
      unblock: string;
      cancel: string;
      confirm: string;
      rejectConfirm: (alias: string) => string;
      removeConfirm: (alias: string) => string;
      blockConfirm: (alias: string) => string;
      accepted: string;
      rejected: string;
      removed: string;
      blocked: string;
      failed: string;
      retry: string;
    };
    errors: {
      load: string;
      mutation: string;
      retry: string;
    };
    cooldown: string;
    notFound: {
      heading: string;
      body: string;
    };
  };
  collection: {
    heading: string;
    subheading: string;
    emptyHeading: string;
    emptyBody: string;
    emptyCta: string;
    count: CountCopy;
    filterByStatus: string;
    allStatuses: string;
    filterByCopy: string;
    allCopyStates: string;
    withCopy: string;
    withoutCopy: string;
    filterByPlatinum: string;
    allPlatinumStates: string;
    platinumOnly: string;
    notPlatinum: string;
    statusEmptyGroup: string;
    showAll: string;
    statusSummaryCount: CountCopy;
    ownedCopyCount: CountCopy;
    sort: {
      label: string;
      recentlyUpdated: string;
      ratingDesc: string;
      titleAsc: string;
      releaseYear: string;
    };
  };
  account: {
    switcher: {
      label: string;
      change: string;
      current: string;
    };
    banner: string;
    list: {
      heading: string;
      intro: string;
    };
  };
  register: {
    heading: string;
    intro: string;
    username: string;
    password: string;
    passwordHint: string;
    confirmPassword: string;
    submit: string;
    pending: string;
    haveAccount: string;
    errorDuplicate: string;
    errorWeakPassword: string;
    weakPasswordIntro: string;
    errorGeneric: string;
    errorRateLimited: string;
  };
  home: {
    valueProposition: string;
    sampleHeading: string;
    newReleases: {
      heading: string;
    };
    signedIn: {
      continueHeading: string;
      continueEmpty: string;
    };
    loggedOut: {
      secondaryCta: string;
      registerCta: string;
    };
  };
  theme: {
    toggle: {
      switchToDark: string;
      switchToLight: string;
    };
  };
  common: {
    retry: string;
    showMore: string;
    showLess: string;
    coverMissing: string;
  };
  status: {
    legend: string;
    labels: {
      pending: string;
      playing: string;
      completed: string;
      abandoned: string;
    };
    save: string;
    saveSuccess: string;
  };
  rating: {
    unrated: string;
    save: string;
    saveSuccess: string;
  };
  errors: {
    generic: string;
    invalidCredentials: string;
    homepageSampleFailure: string;
    openFullCatalogue: string;
    retryCatalogue: string;
    retryGameDetails: string;
    retrySearch: string;
    retryStatusSave: string;
    retryRatingSave: string;
    retrySignIn: string;
  };
  loading: {
    generic: string;
  };
  provenance: {
    heading: string;
    notAvailable: string;
  };
}

/** Formats a count using the canonical zero/one/many rows (UI-SPEC
 * Copywriting Contract): always the explicit localized form, never a
 * concatenated number + untranslated noun. */
export function formatCount(copy: CountCopy, count: number): string {
  if (count === 0) return copy.zero;
  if (count === 1) return copy.one;
  return copy.many(count);
}
