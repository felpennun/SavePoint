import type { Dictionary } from "@/i18n";
import type { ResearchArtifacts, ResearchComparison } from "@/lib/api";

import { ResearchComparisonChart } from "@/components/ResearchComparisonChart";
import { ResearchComparisonTable } from "@/components/ResearchComparisonTable";
import { ResearchEvidenceDetails } from "@/components/ResearchEvidenceDetails";
import { ResearchExports } from "@/components/ResearchExports";
import { ResearchFilters } from "@/components/ResearchFilters";

export type ResearchPanelStatus = "empty" | "error" | "partial" | "populated";

export function ResearchPanel({
  locale,
  comparison,
  artifacts,
  labels,
  status = comparison.rows.length === 0 ? "empty" : artifacts ? "populated" : "partial",
}: {
  locale: string;
  comparison: ResearchComparison;
  artifacts: ResearchArtifacts | null;
  labels: Dictionary["research"];
  status?: ResearchPanelStatus;
}) {
  return <ResearchPanelContent locale={locale} comparison={comparison} artifacts={artifacts} status={status} labels={labels} />;
}

export function ResearchPanelContent({
  locale,
  comparison,
  artifacts,
  status,
  labels,
}: {
  locale: string;
  comparison: ResearchComparison;
  artifacts: ResearchArtifacts | null;
  status: ResearchPanelStatus;
  labels: Dictionary["research"];
}) {
  const isError = status === "error";
  return (
    <main className="sp-page sp-research-page" data-testid="research-panel" data-research-state={status}>
      <header className="sp-research-header">
        <div>
          <p className="sp-eyebrow">{labels.viewerBadge}</p>
          <h1 className="sp-h1">{labels.heading}</h1>
          <p className="sp-lead">{labels.intro}</p>
        </div>
      </header>
      <ResearchFilters locale={locale} options={comparison.filter_options} selected={comparison.filters} labels={labels.filters} />
      {isError ? (
        <section className="sp-empty sp-empty--error" role="alert">
          <h2 className="sp-research-section-heading">{labels.errorHeading}</h2>
          <p>{labels.errorBody}</p>
        </section>
      ) : status === "empty" ? (
        <section className="sp-empty" data-testid="research-empty">
          <h2 className="sp-research-section-heading">{labels.emptyHeading}</h2>
          <p>{labels.emptyBody}</p>
        </section>
      ) : (
        <>
          {status === "partial" ? <p className="sp-research-partial" role="status">{labels.evidence.partial}</p> : null}
          <section aria-labelledby="research-comparison-heading" className="sp-research-comparison">
            <h2 id="research-comparison-heading" className="sp-research-section-heading">{labels.comparison.heading}</h2>
            <ResearchComparisonChart rows={comparison.rows} selectedMetricId={comparison.selected_metric_id} labels={labels.comparison} notAvailable={labels.evidence.unavailable} />
            <ResearchComparisonTable rows={comparison.rows} selectedMetricId={comparison.selected_metric_id} labels={labels.comparison} notAvailable={labels.evidence.unavailable} />
          </section>
          <ResearchEvidenceDetails run={comparison.run} comparison={comparison} artifacts={artifacts} labels={labels.evidence} notAvailable={labels.evidence.unavailable} partial={status === "partial"} />
          <ResearchExports comparison={comparison} labels={labels.downloads} />
        </>
      )}
    </main>
  );
}
