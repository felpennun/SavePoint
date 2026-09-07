# ADR-008: ratings externos gobernados y enriquecimiento RAWG acotado

- **Estado:** Aceptado
- **Fecha:** 2026-09-07
- **Autor de la decisión:** Felipe, decisión explícita: intentar IGDB primero y añadir RAWG si IGDB no permite encontrar ratings suficientes.
- **Fase / Plan:** 02 / 02 · **Requisito:** DATA-05, DATA-06, DATA-07, DATA-08, DOC-02 · **Issue de GitHub:** #18

## Contexto

El catálogo gobernado contiene 193.885 obras en la base de desarrollo persistente.
La importación original se ejecutó antes de ampliar `GAME_FIELDS` con los campos de
rating de usuario de IGDB. Al medir el estado persistente después de las migraciones,
`total_rating IS NOT NULL` y `rating IS NOT NULL` devolvieron 0 filas. Se intentó
repetir el importador ampliado, pero el entorno operativo no tenía
`IGDB_CLIENT_ID`/`IGDB_CLIENT_SECRET`; no se publicó ningún secreto.

La señal primaria para los experimentos es el rating de usuarios, no
`aggregated_rating` ni `total_rating`: IGDB define `rating` como el promedio de sus
usuarios, `rating_count` como el número total de ratings de usuarios y `total_rating`
como una media combinada de usuarios y críticos externos. Las observaciones se
congelan en `CorpusRatingSnapshot` por `corpus_version` y fuente.

## Alternativas consideradas

1. **IGDB-only:** medir y aceptar la cobertura disponible. Es la fuente primaria y no
   añade otra licencia, cuota ni backlink.
2. **RAWG acotado:** consultar únicamente el top-10.000 de obras gobernadas, ordenado
   por `rating_count` descendente con desempate determinista. El límite queda por
   debajo de las 20.000 peticiones mensuales del plan gratuito y conserva margen para
   reintentos y comprobaciones.
3. **RAWG sobre todo el catálogo:** rechazado por superar previsiblemente la cuota y
   por aumentar innecesariamente la segunda cadena de procedencia.

## Decisión

Se conserva IGDB como fuente primaria y se añade un enriquecimiento RAWG offline,
acotado a `N=10.000` obras por ejecución y al corpus gobernado activo. El comando
`enrich_rawg_ratings`:

- no se ejecuta en rutas HTTP y exige `RAWG_API_KEY` por entorno;
- no modifica `GameWork.rating`; escribe observaciones separadas en
  `CorpusRatingSnapshot(source="rawg")`;
- reconcilia primero por `slug` exacto y, si no existe, por título normalizado más
  año de lanzamiento; no usa fuzzy matching y cuenta cada no emparejamiento;
- conserva `SourceRecord(source="rawg")` con URL de la ficha, fecha y hash del
  payload normalizado;
- usa solo `rating` y `ratings_count` de RAWG, convirtiendo la escala 0–5 a 0–100.

En cualquier comparación futura, IGDB gana los empates de procedencia; RAWG solo
rellena la ausencia de una observación IGDB para la misma obra y versión de corpus.
La cifra de RAWG no se considera cobertura medida hasta ejecutar el comando con una
clave válida y guardar su JSON de evidencia.

## Evidencia y fuentes

- [RAWG API documentation](https://rawg.io/apidocs): exige una API key, documenta los
  campos `rating` y `ratings_count`, y publica el plan gratuito de hasta 20.000
  peticiones mensuales.
- [RAWG API Terms of Service](https://rawg.io/tos_api): fija el uso permitido, la
  atribución y las restricciones de redistribución.
- `docs/verification/igdb-catalogue-freeze.md`: medición reproducible de 193.885
  obras gobernadas y 0 ratings presentes en el estado persistente antes del
  re-import ampliado.
- `apps/api/catalogue/rawg.py` y `enrich_rawg_ratings.py`: cliente offline,
  redirecciones bloqueadas, backoff para 429/5xx y reconciliación determinista.

## Consecuencias

La fase puede aumentar la cobertura de ratings populares sin hacer una descarga
completa ni convertir RAWG en fuente de identidad. La contrapartida es una segunda
procedencia con términos propios: toda interfaz que muestre datos RAWG debe incluir
un backlink activo a `https://rawg.io`, y los datos no se redistribuyen en bloque.
La ausencia de `RAWG_API_KEY` sigue siendo un bloqueo operativo para medir cobertura
real, no una razón para inventar resultados.

## Reversibilidad

El enriquecimiento es aditivo y se identifica por `source="rawg"`; se puede dejar de
ejecutar o eliminar sus snapshots y `SourceRecord` sin tocar las filas de IGDB,
Wikidata ni los ratings vivos de `GameWork`. Cambiar `N` requiere una nueva medición
de cuota y una actualización de esta decisión.

## Aprobación y revisión

**Aceptado por el autor el 2026-09-07.** Revisar esta decisión si cambian la cuota,
los términos de RAWG, la necesidad de backlink, la escala del corpus o la regla de
reconciliación. La evidencia de cobertura debe actualizarse solo con una ejecución
real autenticada y su JSON asociado.
