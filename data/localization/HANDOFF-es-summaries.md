# Traducción de sinopsis al español — handoff para otra IA

**Objetivo:** que cada obra del corpus gobernado con sinopsis en inglés tenga
`GameWork.summary_es` en español, empezando por las más populares.

**Alcance de esta tanda (acordado con el autor, 2026-09-07):** obras del corpus
gobernado (`is_dlc = false`, `in_corpus = true`) con `summary` no vacío y
`total_rating_count >= 20`. Son **5.559** obras, ordenadas por popularidad
(`total_rating_count` desc, luego `rating_count` desc, luego `canonical_slug`).
La cola larga (`< 20`) queda en inglés por ahora.

**Estado actual (2026-09-07): 1.898 / 5.559 traducidas y cargadas** (1.896
automáticas por `claude-sonnet-5` + 2 curadas a mano). Las 1.896 primeras de la
cola por popularidad — los títulos más jugados — ya devuelven sinopsis en español
en `/es`. Quedan **3.663** por traducir. Reanuda con el bucle de abajo.

**Punto de control de la sesión del 2026-09-07 (se acabaron los tokens):**
- `data/localization/summaries-es.work.jsonl` versionado con 1.896 líneas
  (`claude-sonnet-5`); `summaries-es.json` regenerado y cargado en la BD del
  contenedor (`load_localized_summaries` → "Loaded 1898 Spanish game summaries").
- Progreso por lotes de 115: el último cargado deja la cola en `1897/5559`.
- Para continuar: `PYTHONUTF8=1 python scripts/next_es_batch.py 115 > data/localization/_batches/todo.jsonl`,
  leer ese fichero, escribir las traducciones en `data/localization/_batches/in.json`
  como objeto plano `{slug: "texto es"}`, y luego
  `PYTHONUTF8=1 python scripts/append_es_batch.py data/localization/_batches/in.json --engine claude-sonnet-5`
  seguido de `PYTHONUTF8=1 python scripts/build_summaries_es.py && docker compose -f infra/compose.yaml exec -T api python manage.py load_localized_summaries`.
- `_pending-es.jsonl` y `_batches/` están gitignored; `summaries-es.work.jsonl`,
  `summaries-es.curated.json`, `summaries-es.json` y `summaries-es.provenance.json`
  se versionan y son la fuente de verdad para reanudar.
- Pendiente sin hacer: ADR-009 (origen de la TA), pasar `load_localized_summaries`
  a `bulk_update`, y el fallback del serializer al inglés para las ~3.663 obras aún
  sin `summary_es`.

**Windows:** ejecuta los scripts Python con `PYTHONUTF8=1` por delante
(`PYTHONUTF8=1 python scripts/next_es_batch.py 120`), o la salida no ASCII se
corrompe a cp1252 al redirigirla a un fichero.

**Regenerar `_pending-es.jsonl`** (si se pierde; es un working file no versionado):
```sh
docker compose -f infra/compose.yaml exec -T db psql -U savepoint_test -d savepoint_test -t -A -c "
SELECT json_build_object('slug', canonical_slug, 'sha256', encode(sha256(convert_to(summary,'UTF8')),'hex'), 'trc', total_rating_count, 'en', summary)
FROM catalogue_gamework
WHERE is_dlc = false AND in_corpus = true AND summary <> '' AND total_rating_count >= 20
ORDER BY total_rating_count DESC NULLS LAST, rating_count DESC NULLS LAST, canonical_slug
" > data/localization/_pending-es.jsonl
```

## Estado y archivos

Todo vive en `data/localization/`:

| Archivo | Qué es | ¿Se versiona? |
|---|---|---|
| `_pending-es.jsonl` | Cola completa: `{slug, sha256, trc, en}` por línea, orden de popularidad. Generada desde la BD. | working file, no commitear |
| `summaries-es.work.jsonl` | **Log append-only de traducciones automáticas.** `{slug, sha256, es, engine, at}` por línea. Es lo que se continúa. | sí (fuente de verdad de la TA) |
| `summaries-es.curated.json` | `slug -> texto` revisado a mano. Siempre gana sobre la TA. Hoy: 2 entradas (Elden Ring). | sí |
| `summaries-es.json` | Manifiesto `slug -> texto` que lee el comando de carga. **Generado**, no editar a mano. | sí |
| `summaries-es.provenance.json` | `slug -> {src_sha256, engine, translated_at}`. Generado. | sí |

`sha256` es el SHA-256 del `summary` inglés de origen (UTF-8). Si un re-import de
IGDB cambia una sinopsis, ese hash deja de coincidir y esa entrada se puede
re-traducir sin tocar las demás.

## Cómo continuar la traducción

1. **Siguiente lote a traducir:**
   ```sh
   python scripts/next_es_batch.py 120 > /tmp/batch-en.jsonl
   ```
   Imprime hasta 120 filas `{"slug","en"}` que aún no están en
   `summaries-es.work.jsonl` (resume automático).

2. **Traducir** cada `en` al español. Reglas de estilo:
   - Español neutro, registro de ficha de catálogo (como las 2 entradas de
     `summaries-es.curated.json`).
   - **No traducir** nombres propios de juegos, franquicias, personajes,
     estudios, plataformas ni marcas registradas. "open world" -> "mundo
     abierto"; nombres como *Los Santos*, *FromSoftware*, *Nintendo Switch* se
     mantienen.
   - Conservar el sentido y la longitud aproximada; no inventar, no resumir de
     más, no añadir opinión.
   - Sin comillas envolventes ni markdown; texto plano.

3. **Guardar el lote:** escribe un JSON plano `{slug: "texto en español", ...}`
   en `/tmp/batch-es.json` y ejecútalo:
   ```sh
   python scripts/append_es_batch.py /tmp/batch-es.json --engine <modelo>
   ```
   Valida los slugs contra la cola, copia el `sha256`, salta los ya hechos y
   añade líneas a `summaries-es.work.jsonl`. Imprime `progress X/5559`.

4. Repetir 1–3 hasta `progress 5559/5559`.

## Cómo publicar las sinopsis en la web

1. **Construir el manifiesto:**
   ```sh
   python scripts/build_summaries_es.py
   ```
   Funde `curated` + `work.jsonl` en `summaries-es.json` (+ `provenance.json`).

2. **Cargar en la BD:**
   ```sh
   docker compose -f infra/compose.yaml exec -T api python manage.py load_localized_summaries
   ```
   `apps/api/catalogue/management/commands/load_localized_summaries.py` ya existe
   y lee `data/localization/summaries-es.json`.
   **Mejora recomendada antes de cargar 5,5k filas:** hoy hace un `UPDATE` por
   slug dentro de una transacción; cambiarlo a `bulk_update` por lotes o a un
   `UPDATE ... FROM (VALUES ...)`.

3. **Verificar:** `GET /api/catalogue/games/<slug>/` con locale español debe
   devolver `summary` en español. El serializer
   (`apps/api/catalogue/serializers.py`, `GameDetailSerializer.get_summary`)
   devuelve `summary_es` cuando `context["locale"] == "es"`.

4. **Fallback pendiente (bug de UX actual):** si `summary_es` está vacío, el
   serializer devuelve cadena vacía en `/es` en lugar del inglés. Mientras la
   cola no esté completa, cambiar `get_summary` para que caiga al inglés
   (idealmente con una marca "traducción automática pendiente" en la UI) en vez
   de mostrar la ficha sin sinopsis.

## Evidencia de tesis (pendiente)

Crear **ADR-009** (`docs/adr/`, en español, con los 7 encabezados que exige
`scripts/check-evidence.ps1`): origen de la traducción (TA con
`<modelo>`), reproducibilidad (cola por popularidad + hash de origen),
alternativas descartadas (DeepL/Google de pago), y limitaciones (TA con control
de calidad por muestreo, no revisión humana completa; cola larga sin traducir).
Registrar también la decisión del corte `total_rating_count >= 20` en
`.planning/`.
