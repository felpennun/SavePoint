import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ResearchPanel } from "@/components/ResearchPanel";
import ResearchLoading from "@/app/[locale]/research/loading";
import { en } from "@/i18n/en";
import { es } from "@/i18n/es";
import {
  buildResearchExportHref,
  fetchResearchComparison,
  type ResearchComparison,
  type ResearchComparisonRow,
} from "@/lib/api";

function row(overrides: Partial<ResearchComparisonRow> = {}): ResearchComparisonRow {
  return {
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
    ...overrides,
  };
}

function comparison(overrides: Partial<ResearchComparison> = {}): ResearchComparison {
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
    rows: [row()],
    metric_definitions: [],
    timings: [],
    provenance: { simulation: true },
    limitations: ["Single published test run."],
    downloads: [
      { format: "json", run_id: "evaluation-400-test-2026-09-12-v15", available: true },
      { format: "csv", run_id: "evaluation-400-test-2026-09-12-v15", available: true },
      { format: "svg", run_id: "evaluation-400-test-2026-09-12-v15", available: true },
    ],
    ...overrides,
  };
}

function renderPanel(status: "empty" | "error" | "partial" | "populated", value = comparison()): string {
  return renderToStaticMarkup(
    <ResearchPanel locale="es" comparison={value} artifacts={status === "populated" ? { run: value.run, artifacts: [], provenance: {} } : null} labels={es.research} status={status} />,
  );
}

function occurrences(markup: string, value: string): number {
  return markup.split(value).length - 1;
}

afterEach(() => vi.unstubAllGlobals());

describe("ResearchPanel states and equivalence", () => {
  it("renders a supplied comparison in the localized panel without deriving values", () => {
    const markup = renderPanel("partial");

    expect(markup).toContain(es.research.heading);
    expect(markup).toContain("Content CBF");
    expect(markup).toContain("0.42");
    expect(markup).toContain("1250");
    expect(markup).toContain("<svg");
    expect(markup).toContain("<table");
    expect(markup).toContain(es.research.evidence.partial);
    expect(occurrences(markup, es.research.evidence.partial)).toBe(1);
    expect(markup).not.toMatch(/re-run|rerun|delete|eliminar/i);
  });

  it("keeps the SVG and semantic table equivalent in source order", () => {
    const second = row({
      algorithm_id: "collab-v1",
      algorithm_label: "Collaborative",
      cohort_id: "cold_start",
      cohort_label: "Cold start",
      metrics: {
        "ndcg@10": {
          metric_id: "ndcg@10",
          value: null,
          unit: "ratio",
          higher_is_better: true,
          unavailable_reason: "not_evaluable",
        },
      },
      timing: { duration_seconds: null, wall_ms: null, cpu_ms: null, unavailable_reason: "not_recorded" },
    });
    const value = comparison({ rows: [row(), second] });
    const markup = renderPanel("populated", value);

    expect(markup).toContain('viewBox="0 0 640 320"');
    expect(markup).toMatch(/<caption>Comparación/);
    expect(occurrences(markup, "Content CBF")).toBe(3);
    expect(occurrences(markup, "Collaborative")).toBe(2);
    expect(occurrences(markup, "0.42")).toBe(2);
    expect(occurrences(markup, es.research.evidence.unavailable)).toBeGreaterThanOrEqual(2);
    expect(markup).toContain('scope="col"');
    expect(markup).toContain('scope="row"');
    expect(markup).toContain('tabindex="0"');
  });

  it("renders an explanatory empty state without chart/table", () => {
    const markup = renderPanel("empty", comparison({ rows: [] }));

    expect(markup).toContain('data-research-state="empty"');
    expect(markup).toContain(es.research.emptyHeading);
    expect(markup).toContain(es.research.emptyBody);
    expect(markup).not.toContain("<svg");
    expect(markup).not.toContain("<table");
  });

  it("renders an alert error state and a partial state with one notice", () => {
    const errorMarkup = renderPanel("error");
    const partialMarkup = renderPanel("partial");

    expect(errorMarkup).toContain('role="alert"');
    expect(errorMarkup).toContain(es.research.errorHeading);
    expect(errorMarkup).not.toContain("<svg");
    expect(partialMarkup).toContain('data-research-state="partial"');
    expect(occurrences(partialMarkup, es.research.evidence.partial)).toBe(1);
  });

  it("uses localized GET filters with allowlisted options and an explicit apply", () => {
    const markup = renderPanel("populated");

    expect(markup).toMatch(/<form[^>]*method="get"[^>]*action="\/es\/research"|<form[^>]*action="\/es\/research"[^>]*method="get"/);
    expect(markup).toContain('aria-label="Filtros de investigación"');
    expect(markup).toContain('name="run"');
    expect(markup).toContain('name="algorithm"');
    expect(markup).toContain('name="cohort"');
    expect(markup).toContain('name="metric"');
    expect(markup).toContain('type="submit"');
    expect(markup).toContain(es.research.filters.apply);
    expect(markup).toContain('href="/es/research"');
  });

  it("renders loading with a polite status and skeletons", async () => {
    const element = await ResearchLoading({ params: Promise.resolve({ locale: "es" }) });
    const markup = renderToStaticMarkup(element);

    expect(markup).toContain('aria-busy="true"');
    expect(markup).toContain('role="status"');
    expect(markup).toContain(es.loading.generic);
    expect(occurrences(markup, "sp-skeleton")).toBe(1);
  });

  it("keeps Spanish and English research copy structurally in parity", () => {
    expect(Object.keys(es.research).sort()).toEqual(Object.keys(en.research).sort());
    expect(es.research.heading).not.toBe(en.research.heading);
    expect(es.research.downloads.json).not.toHaveLength(0);
    expect(en.research.downloads.json).not.toHaveLength(0);
  });

  it("preserves selected filters in same-origin export links", () => {
    const href = buildResearchExportHref({
      run: comparison().run,
      filters: { run_id: "run-1", algorithm_id: "algo-1", cohort_id: "cohort-1", metric_id: "metric-1" },
    }, "json");

    expect(href).toBe("/api/evaluation/exports/?run=evaluation-400-test-2026-09-12-v15&algorithm=algo-1&cohort=cohort-1&metric=metric-1&format=json");
    expect(href).not.toContain("same-origin.invalid");
  });

  it("sends one request with only known, single-value query filters", async () => {
    const fetchMock = vi.fn(async () => ({ status: 200, ok: true, json: async () => ({}) }));
    vi.stubGlobal("fetch", fetchMock);

    await fetchResearchComparison("sessionid=demo", {
      run: "run-1",
      algorithm: "algo-1",
      cohort: ["first", "duplicate"] as unknown as string,
      metric: "metric-1",
      unknown: "ignored",
    } as unknown as Parameters<typeof fetchResearchComparison>[1]);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const requestCalls = fetchMock.mock.calls as unknown as Array<[URL, RequestInit?]>;
    const requestUrl = String(requestCalls[0][0]);
    expect(requestUrl).toContain("run=run-1");
    expect(requestUrl).toContain("algorithm=algo-1");
    expect(requestUrl).toContain("metric=metric-1");
    expect(requestUrl).not.toContain("cohort=");
    expect(requestUrl).not.toContain("unknown=");
  });
});
