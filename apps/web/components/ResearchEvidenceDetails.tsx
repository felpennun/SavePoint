import type { Dictionary } from "@/i18n";
import type { ResearchArtifacts, ResearchComparison, ResearchRunSummary } from "@/lib/api";

function valueOf(value: number | string | boolean | null | undefined, notAvailable: string): string {
  return value == null || value === "" ? notAvailable : String(value);
}

function EvidenceRow({ label, value }: { label: string; value: string }) {
  return <div className="sp-research-evidence-row"><dt>{label}</dt><dd className="sp-mono">{value}</dd></div>;
}

export function ResearchEvidenceDetails({
  run,
  comparison,
  artifacts,
  labels,
  notAvailable,
}: {
  run: ResearchRunSummary;
  comparison: ResearchComparison;
  artifacts: ResearchArtifacts | null;
  labels: Dictionary["research"]["evidence"];
  notAvailable: string;
}) {
  const provenance = artifacts?.provenance ?? comparison.provenance;
  return (
    <section className="sp-research-details-grid" aria-labelledby="research-evidence-heading">
      <div className="sp-surface">
        <h2 id="research-evidence-heading" className="sp-research-section-heading">{labels.heading}</h2>
        <dl className="sp-research-evidence-list">
          <EvidenceRow label={labels.run} value={valueOf(run.run_id, notAvailable)} />
          <EvidenceRow label={labels.status} value={valueOf(run.status, notAvailable)} />
          <EvidenceRow label={labels.publishedAt} value={valueOf(run.published_at, notAvailable)} />
          <EvidenceRow label={labels.protocol} value={valueOf(run.protocol_version, notAvailable)} />
          <EvidenceRow label={labels.corpus} value={valueOf(run.corpus_version, notAvailable)} />
          <EvidenceRow label={labels.split} value={valueOf(run.split, notAvailable)} />
          <EvidenceRow label={labels.commit} value={valueOf(run.commit_sha, notAvailable)} />
          <EvidenceRow label={labels.featureSet} value={valueOf(run.feature_set_version, notAvailable)} />
          <EvidenceRow label={labels.seedCount} value={valueOf(run.seed_count, notAvailable)} />
          <EvidenceRow label={labels.artifactHash} value={valueOf(run.artifact_sha256, notAvailable)} />
          <EvidenceRow label={labels.cohortHash} value={valueOf(run.cohort_sha256, notAvailable)} />
          <EvidenceRow label={labels.protocolHash} value={valueOf(run.protocol_sha256, notAvailable)} />
          <EvidenceRow label={labels.snapshotHash} value={valueOf(run.snapshot_sha256, notAvailable)} />
          <EvidenceRow label={labels.popscoreHash} value={valueOf(run.popscore_snapshot_sha256, notAvailable)} />
          <EvidenceRow label={labels.splitManifestHash} value={valueOf(run.split_manifest_sha256, notAvailable)} />
        </dl>
      </div>
      <div className="sp-surface">
        <h2 className="sp-research-section-heading">{labels.provenanceHeading}</h2>
        <dl className="sp-research-evidence-list">
          {Object.entries(provenance).map(([key, value]) => (
            <EvidenceRow key={key} label={key} value={valueOf(value, notAvailable)} />
          ))}
        </dl>
        <h3 className="sp-research-subheading">{labels.limitationsHeading}</h3>
        <ul className="sp-research-limitations">
          {comparison.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
        </ul>
      </div>
    </section>
  );
}
