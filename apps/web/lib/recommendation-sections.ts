/** Product shelves mapped to the backend's published algorithm catalogue. */

export const CONTENT_RECOMMENDATION_SECTIONS = [
  ["content-cbf-weighted-v1", "weighted"],
  ["content-cbf-multiplicative-v1", "multiplicative"],
  ["content-cbf-twostage-v1", "twoStage"],
  ["content-cbf-neg-v1", "negative"],
  ["content-cbf-weighted-pop-v1", "weightedPop"],
  ["content-cbf-multiplicative-pop-v1", "multiplicativePop"],
  ["content-cbf-twostage-pop-v1", "twoStagePop"],
  ["content-cbf-neg-pop-v1", "negativePop"],
  ["recency-v1", "recency"],
  ["content-cbf-mmr-v1", "mmr"],
  ["content-cbf-mmr-pop-v1", "mmrPop"],
  ["cf-user-knn-v1", "collaborative"],
  ["hybrid-weighted-cf-v1", "hybrid"],
  ["hybrid-mmr-v1", "hybridMmr"],
] as const;
