import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ResearchPanel } from "@/components/ResearchPanel";
import { es } from "@/i18n/es";
import type { ResearchComparison } from "@/lib/api";

function comparison(): ResearchComparison {
  return {
    run: {
      run_id: "evaluation-400-test-2026-09-12-v15",
      status: "succeeded",
      published_at: "2026-09-12T10:00:00Z",
      protocol_version: 15,
      corpus_version: "2026.09.2",
      split: "test",
      commit_sha: "abc123",
      feature_set_version: "fs-v9",
      seed_count: 2,
      artifact_sha256: "artifact-hash",
      cohort_sha256: "cohort-hash",
      protocol_sha256: "protocol-hash",
      snapshot_sha256: "snapshot-hash",
      popscore_snapshot_sha256: "popscore-hash",
      split_manifest_sha256: "split-hash",
    },
    filters: { run_id: "evaluation-400-test-2026-09-12-v15", metric_id: "ndcg@10" },
    filter_options: {
      runs: [{ id: "evaluation-400-test-2026-09-12-v15", label: "v15" }],
      algorithms: [{ id: "content-cbf-v1", label: "Content CBF" }],
      cohorts: [{ id: "active_history_10_to_20", label: "Active history" }],
      metrics: [{ id: "ndcg@10", label: "nDCG@10" }],
      formats: [{ id: "json", label: "JSON" }],
    },
    selected_metric_id: "ndcg@10",
    rows: [{
      algorithm_id: "content-cbf-v1",
      algorithm_label: "Content CBF",
      cohort_id: "active_history_10_to_20",
      cohort_label: "Active history",
      k: 10,
      evaluable_count: 79,
      population_count: 240,
      metrics: {
        "ndcg@10": {
          metric_id: "ndcg@10",
          value: 0.42,
          unit: "ratio",
          higher_is_better: true,
          unavailable_reason: null,
        },
      },
      timing: { duration_seconds: 1.25, wall_ms: 1250, cpu_ms: null, unavailable_reason: null },
      not_evaluable_reason: null,
    }],
    metric_definitions: [],
    timings: [],
    provenance: { simulation: true },
    limitations: ["Single published test run."],
    downloads: [
      { format: "json", run_id: "evaluation-400-test-2026-09-12-v15", available: true },
      { format: "csv", run_id: "evaluation-400-test-2026-09-12-v15", available: true },
      { format: "svg", run_id: "evaluation-400-test-2026-09-12-v15", available: true },
    ],
  };
}

describe("ResearchPanel tracer", () => {
  it("renders a supplied comparison in the localized panel without deriving values", () => {
    const markup = renderToStaticMarkup(
      <ResearchPanel locale="es" comparison={comparison()} artifacts={null} labels={es.research} status="partial" />,
    );

    expect(markup).toContain(es.research.heading);
    expect(markup).toContain("Content CBF");
    expect(markup).toContain("0.42");
    expect(markup).toContain("1250");
    expect(markup).toContain("<svg");
    expect(markup).toContain("<table");
    expect(markup).toContain(es.research.evidence.partial);
  });
});
