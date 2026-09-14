import { buildResearchExportHref, type ResearchComparison, type ResearchDownload } from "@/lib/api";

const formatLabels = {
  csv: "csv",
  json: "json",
  svg: "svg",
} as const;

export function ResearchExports({
  comparison,
  labels,
}: {
  comparison: ResearchComparison;
  labels: {
    heading: string;
    exportEvidence: string;
    csv: string;
    json: string;
    svg: string;
    noActions: string;
  };
}) {
  const names = { csv: labels.csv, json: labels.json, svg: labels.svg };
  return (
    <section className="sp-surface sp-research-exports" aria-labelledby="research-downloads-heading">
      <h2 id="research-downloads-heading" className="sp-research-section-heading">{labels.heading}</h2>
      <div className="sp-research-export-actions">
        {comparison.downloads.filter((download): download is ResearchDownload => download.available).map((download) => (
          <a
            href={buildResearchExportHref(comparison, download.format)}
            className={download.format === "json" ? "sp-btn-primary" : "sp-btn-secondary"}
            key={download.format}
            download
          >
            {download.format === "json" ? labels.exportEvidence : names[formatLabels[download.format]]}
          </a>
        ))}
      </div>
      <p className="sp-muted">{labels.noActions}</p>
    </section>
  );
}
