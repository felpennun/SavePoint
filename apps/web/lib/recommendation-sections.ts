/** Product shelves mapped to the backend's published algorithm catalogue. */

export const CONTENT_RECOMMENDATION_SECTIONS = [
  ["content-cbf-weighted-v1", "weighted"],
  ["content-cbf-mmr-pop-v2", "mmrPop"],
  ["recency-v1", "recency"],
] as const;
