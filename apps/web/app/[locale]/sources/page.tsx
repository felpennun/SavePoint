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

  if (!sources) {
    return (
      <main className="sp-page">
        <h1 className="sp-h1">{copy.heading}</h1>
        <p role="alert">{copy.unavailable}</p>
        <a href={`/${locale}/sources`}>{copy.reload}</a>
      </main>
    );
  }

  return (
    <main>
      <h1>{copy.heading}</h1>
      <dl>
        <dt>{copy.dataset}</dt>
        <dd>
          {sources.source} —{" "}
          <a href={sources.source_url} target="_self" rel="noopener">
            {sources.source_url}
          </a>
        </dd>
        <dt>{copy.license}</dt>
        <dd>{sources.licence}</dd>
        <dt>{copy.retrieved}</dt>
        <dd>{new Date(sources.retrieved_at).toISOString().slice(0, 10)}</dd>
        <dt>{copy.checksum}</dt>
        <dd style={{ wordBreak: "break-all" }}>{sources.snapshot_sha256}</dd>
        <dt>{copy.records}</dt>
        <dd>{sources.record_count}</dd>
        <dt>{copy.covers}</dt>
        <dd>
          {sources.approved_asset_count} / {sources.total_asset_candidate_count}
        </dd>
      </dl>
      <p>{copy.coverPolicy}</p>
      <p>{copy.offline}</p>
    </main>
  );
}
