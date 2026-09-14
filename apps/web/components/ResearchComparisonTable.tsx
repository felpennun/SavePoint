import type { ResearchComparisonRow } from "@/lib/api";

function displayValue(value: number | string | null | undefined, notAvailable: string): string {
  return value == null ? notAvailable : String(value);
}

export function ResearchComparisonTable({
  rows,
  selectedMetricId,
  labels,
  notAvailable,
}: {
  rows: ResearchComparisonRow[];
  selectedMetricId: string;
  labels: {
    tableCaption: string;
    algorithm: string;
    cohort: string;
    evaluable: string;
    metric: string;
    wallTime: string;
    cpuTime: string;
    scrollHelp: string;
  };
  notAvailable: string;
}) {
  return (
    <div
      className="sp-research-table-scroll"
      tabIndex={0}
      aria-label={labels.scrollHelp}
      data-testid="research-table-scroll"
    >
      <table className="sp-research-table" data-testid="research-table">
        <caption>{labels.tableCaption}</caption>
        <thead>
          <tr>
            <th scope="col">{labels.algorithm}</th>
            <th scope="col">{labels.cohort}</th>
            <th scope="col">{labels.evaluable}</th>
            <th scope="col">{labels.metric}</th>
            <th scope="col">{labels.wallTime}</th>
            <th scope="col">{labels.cpuTime}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const metric = row.metrics[selectedMetricId];
            return (
              <tr key={`${row.algorithm_id}-${row.cohort_id}-${row.k}`}>
                <th scope="row">{row.algorithm_label}</th>
                <td>{row.cohort_label}</td>
                <td className="sp-mono">{displayValue(row.evaluable_count, notAvailable)}</td>
                <td className="sp-mono">{displayValue(metric?.value, notAvailable)}</td>
                <td className="sp-mono">{displayValue(row.timing.wall_ms, notAvailable)}</td>
                <td className="sp-mono">{displayValue(row.timing.cpu_ms, notAvailable)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="sp-muted sp-research-scroll-help">{labels.scrollHelp}</p>
    </div>
  );
}
