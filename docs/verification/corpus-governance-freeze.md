# Gobernanza del corpus de catálogo — contrato de congelación

**Estado:** contrato implementado; los valores medidos se generan con `govern_corpus`.
**Requisitos:** DATA-03, DATA-06 · **Issue:** #17

Este documento fija la frontera reproducible del catálogo IGDB que pueden consumir los
filtros, los snapshots de rating y los experimentos. `govern_corpus` conserva todas las
obras importadas y solo marca `GameWork.in_corpus=True` cuando se cumplen simultáneamente
las cinco reglas D-03: título válido, release en la allowlist D-01, no DLC, al menos un
género y fecha de lanzamiento.

## Evidencia generada

La orden:

```text
python manage.py govern_corpus --evidence-json docs/verification/corpus-governance-freeze.json
```

emite un JSON con:

- `checksum`: SHA-256 de `(source_id, snapshot_sha256)` de las filas IGDB gobernadas,
  ordenadas por `source_id` numérico;
- `data_dictionary`: tipo, fuente, nulabilidad y descripción de los campos relevantes;
- `quality_report`: conteo gobernado, coberturas de campos, distribuciones de género y
  plataforma, histograma de años, motivos de exclusión y slugs de allowlist no resueltos;
- `sampled_manifest`: manifiesto determinista de como máximo 300 obras.

La muestra usa `step=max(1, governed_count//300)` y no aleatoriedad. Una segunda ejecución
con la misma base de datos y ruleset conserva el checksum y reutiliza la versión activa.
Una ejecución con una versión explícita distinta crea una nueva fila `CorpusVersion`; los
snapshots de versiones anteriores no se modifican.

El rating no participa en D-03: una obra gobernada sin `total_rating` (o sin el rating de
usuarios que incorporará el plan 02-02) permanece en el corpus. La presentación y el
ranking por rating aplican después sus propias reglas de ausencia de dato.

## Limitaciones y procedencia

La allowlist se resuelve por slug de `Platform`, no por el nombre mostrado ni por la
categoría IGDB obsoleta. El informe lista explícitamente cualquier slug que no exista en la
base de datos para que una deriva de importación no quede oculta. La evidencia contiene
agregados y una muestra acotada, nunca una enumeración completa ni credenciales.

El JSON de esta ruta es un artefacto generado y debe conservarse junto con el commit,
`corpus_version` y las versiones de código que lo produjeron.
