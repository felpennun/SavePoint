import { fetchSources } from "@/lib/api";

const COPY = {
  es: {
    heading: "Fuentes y metodología",
    unavailable: "Fuentes no disponibles",
    reload: "Recargar fuentes",
    dataset: "Conjunto de datos",
    license: "Licencia",
    retrieved: "Fecha de recuperación",
    checksum: "Checksum SHA-256",
    records: "Juegos importados",
    covers: "Carátulas aprobadas",
    coverPolicy:
      "Política de carátulas: sólo se muestran imágenes con autor, licencia, URL de licencia y URL de fuente completos; cualquier otra usa el placeholder propio.",
    offline: "El catálogo funciona sin conexión al proveedor externo: los datos ya están importados en la base de datos local.",
  },
  en: {
    heading: "Sources & methodology",
    unavailable: "Sources unavailable",
    reload: "Reload sources",
    dataset: "Dataset",
    license: "Licence",
    retrieved: "Retrieval date",
    checksum: "SHA-256 checksum",
    records: "Games imported",
    covers: "Approved covers",
    coverPolicy:
      "Cover policy: only images with complete author, licence, licence URL, and source URL are shown; anything else uses the first-party placeholder.",
    offline: "The catalogue works without a connection to the external provider: the data is already imported into the local database.",
  },
} as const;

export default async function SourcesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  const locale = rawLocale === "en" ? "en" : "es";
  const copy = COPY[locale];

  const sources = await fetchSources();
  const num = (value: number) => new Intl.NumberFormat(locale).format(value);
  let sourceHref = "";
  if (sources) {
    try {
      sourceHref = new URL(sources.source_url).origin;
    } catch {
      sourceHref = sources.source_url;
    }
  }
  const coverPct = sources && sources.total_asset_candidate_count > 0
    ? Math.round((sources.approved_asset_count / sources.total_asset_candidate_count) * 100)
    : null;

  if (!sources) {
    return (
      <main className="sp-page">
        <h1 className="sp-h1">{copy.heading}</h1>
        <div className="sp-empty sp-empty--error" role="alert">
          <p className="sp-h2" style={{ margin: 0 }}>
            {copy.unavailable}
          </p>
          <a href={`/${locale}/sources`} className="sp-btn-primary">
            {copy.reload}
          </a>
        </div>
      </main>
    );
  }

  return (
    <main className="sp-page">
      <h1 className="sp-h1">{copy.heading}</h1>
      <p className="sp-lead">{copy.offline}</p>

      <dl className="sp-spec-table">
        <div className="sp-spec-row">
          <dt>{copy.dataset}</dt>
          <dd>
            {sources.source.toUpperCase()} —{" "}
            <a href={sourceHref} className="sp-link" target="_blank" rel="noopener noreferrer">
              {sourceHref.replace(/^https?:\/\//, "")}
            </a>
          </dd>
        </div>
        <div className="sp-spec-row">
          <dt>{copy.license}</dt>
          <dd>{sources.licence}</dd>
        </div>
        <div className="sp-spec-row">
          <dt>{copy.retrieved}</dt>
          <dd className="sp-mono">{new Date(sources.retrieved_at).toISOString().slice(0, 10)}</dd>
        </div>
        <div className="sp-spec-row">
          <dt>{copy.checksum}</dt>
          <dd className="sp-mono" style={{ wordBreak: "break-all" }}>
            {sources.snapshot_sha256}
          </dd>
        </div>
        <div className="sp-spec-row">
          <dt>{copy.records}</dt>
          <dd className="sp-mono">{num(sources.record_count)}</dd>
        </div>
        <div className="sp-spec-row">
          <dt>{copy.covers}</dt>
          <dd className="sp-mono">
            {num(sources.approved_asset_count)} / {num(sources.total_asset_candidate_count)}
            {coverPct != null ? ` (${coverPct}%)` : ""}
          </dd>
        </div>
      </dl>

      <p className="sp-muted" style={{ maxWidth: "76ch", lineHeight: 1.65 }}>
        {copy.coverPolicy}
      </p>
    </main>
  );
}
