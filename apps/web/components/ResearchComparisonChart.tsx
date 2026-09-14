import type { ResearchComparisonRow } from "@/lib/api";

export function ResearchComparisonChart({
  rows,
  selectedMetricId,
  labels,
  notAvailable,
}: {
  rows: ResearchComparisonRow[];
  selectedMetricId: string;
  labels: {
    chartLabel: string;
    chartDescription: string;
    scaleLabel: string;
  };
  notAvailable: string;
}) {
  return (
    <figure className="sp-research-chart" aria-describedby="research-chart-description" data-testid="research-chart">
      <figcaption className="sp-research-chart-caption">
        <span>{labels.chartLabel}</span>
        <span id="research-chart-description" className="sp-muted">{labels.chartDescription}</span>
      </figcaption>
      <p className="sp-research-scale sp-mono">{labels.scaleLabel}</p>
      <svg
        aria-hidden="true"
        className="sp-research-svg"
        viewBox="0 0 640 320"
        preserveAspectRatio="xMinYMin meet"
        role="img"
      >
        <line x1="250" y1="8" x2="250" y2="304" stroke="var(--color-surface-border)" strokeWidth="1" />
        {rows.map((row, index) => {
          const metric = row.metrics[selectedMetricId];
          const value = metric?.value == null ? notAvailable : String(metric.value);
          const y = 28 + index * 32;
          return (
            <g key={`${row.algorithm_id}-${row.cohort_id}-${row.k}`} transform={`translate(0 ${y})`}>
              <text x="0" y="0" dominantBaseline="middle" className="sp-research-svg-label">
                {row.algorithm_label} · {row.cohort_label}
              </text>
              <line x1="250" y1="0" x2="570" y2="0" stroke="var(--color-accent-edge)" strokeWidth="2" />
              <circle cx="570" cy="0" r="5" fill="var(--color-accent)" />
              <text x="582" y="0" dominantBaseline="middle" className="sp-research-svg-value">
                {value}
              </text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}
