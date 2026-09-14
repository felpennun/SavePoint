import type { ResearchComparison } from "@/lib/api";

type FilterLabels = {
  heading: string;
  formLabel: string;
  run: string;
  algorithm: string;
  cohort: string;
  metric: string;
  any: string;
  apply: string;
  reset: string;
};

function selectedValue(options: Array<{ id: string }>, value: string | undefined): string {
  return value && options.some((option) => option.id === value) ? value : "";
}

function FilterSelect({
  id,
  name,
  label,
  options,
  value,
  any,
}: {
  id: string;
  name: string;
  label: string;
  options: Array<{ id: string; label: string }>;
  value: string | undefined;
  any: string;
}) {
  return (
    <div className="sp-field">
      <label htmlFor={id}>{label}</label>
      <select id={id} name={name} defaultValue={selectedValue(options, value)}>
        <option value="">{any}</option>
        {options.map((option) => <option value={option.id} key={option.id}>{option.label}</option>)}
      </select>
    </div>
  );
}

export function ResearchFilters({
  locale,
  options,
  selected,
  labels,
}: {
  locale: string;
  options: ResearchComparison["filter_options"];
  selected: ResearchComparison["filters"];
  labels: FilterLabels;
}) {
  return (
    <section className="sp-surface sp-research-filters" aria-labelledby="research-filters-heading">
      <h2 id="research-filters-heading" className="sp-research-section-heading">{labels.heading}</h2>
      <form method="get" action={`/${locale}/research`} aria-label={labels.formLabel}>
        <div className="sp-research-filter-grid">
          <FilterSelect id="research-run" name="run" label={labels.run} options={options.runs} value={selected.run_id} any={labels.any} />
          <FilterSelect id="research-algorithm" name="algorithm" label={labels.algorithm} options={options.algorithms} value={selected.algorithm_id} any={labels.any} />
          <FilterSelect id="research-cohort" name="cohort" label={labels.cohort} options={options.cohorts} value={selected.cohort_id} any={labels.any} />
          <FilterSelect id="research-metric" name="metric" label={labels.metric} options={options.metrics} value={selected.metric_id} any={labels.any} />
        </div>
        <div className="sp-research-filter-actions">
          <button type="submit" className="sp-btn-primary">{labels.apply}</button>
          <a href={`/${locale}/research`} className="sp-btn-secondary">{labels.reset}</a>
        </div>
      </form>
    </section>
  );
}
