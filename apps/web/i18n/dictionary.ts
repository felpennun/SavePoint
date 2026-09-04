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
    profile: string;
    sources: string;
    login: string;
    logout: string;
    skipToContent: string;
    openMenu: string;
    closeMenu: string;
  };
  catalogue: {
    heading: string;
    searchLabel: string;
    clearSearch: string;
    emptyHeading: string;
    emptyBody: string;
    resultCount: CountCopy;
  };
  collection: {
    heading: string;
    emptyHeading: string;
    emptyBody: string;
    statusSummaryCount: CountCopy;
    ownedCopyCount: CountCopy;
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
