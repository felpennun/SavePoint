# Similitud de etiquetas curadas e IDF — 2026-09-10

## Decisión

La similitud principal de contenido prioriza las etiquetas curadas como la
señal diferenciativa del catálogo. El núcleo queda configurado así:

| Faceta | Peso máximo |
|---|---:|
| Etiquetas curadas (`tag:<slug>`) | 0,75 |
| Plataformas permitidas (`platform:<slug>`) | 0,25 |
| Franquicia (`franchise:<slug>`) | bonus 0,02 |
| Desarrollador (`developer:<slug>`) | bonus 0,015 |

Etiquetas y plataformas suman el 100 % del núcleo. Franquicia y desarrollador
continúan siendo señales opcionales de confirmación y no redistribuyen su peso
cuando faltan.

Cada tag utiliza IDF suavizado por rareza en el corpus:

```text
idf(tag) = ln((N + 1) / (df_tag + 1)) + 1
```

`N` es el número de obras gobernadas y `df_tag` el número de obras gobernadas
que contienen el tag. Para cada obra, los IDF de sus tags se normalizan por L2
al peso de familia `0,75`:

```text
peso(tag, obra) = 0,75 * idf(tag) / sqrt(sum(idf(tag_j)^2))
```

Los tags genéricos aportan menos y los específicos más, sin permitir que la
rareza aumente la norma total del bloque. El cálculo queda congelado por
`corpus_version`; los workers web y la evaluación offline reciben el mismo
mapa IDF.

## Alcance técnico

El cambio se aplica a `feature_vector`, `facet_similarity`, los rankers de
contenido, los híbridos, MMR, los workers web y la evaluación offline, porque
todos consumen `FACET_WEIGHTS` y el mismo vector versionado. La procedencia
original de una etiqueta (género, theme, gamemode o keyword) no altera su peso:
una vez curada, pertenece a la familia común `tag:`.

Se han versionado los contratos para invalidar vectores cacheados y evitar
mezclar resultados incompatibles:

- `FEATURE_SET_VERSION = fs-v12-curated-tags-idf`.
- `SIMILARITY_RULE_VERSION = facet-similarity-v7`.
- `protocol_version = 12`.

La afinidad F0,5, el reparto interno por `sqrt(k)`, la señal de valoración,
PopScore, recencia, penalización negativa y MMR no cambian. Solo cambia la
importancia relativa del núcleo de contenido.

## Fuente canónica

- `apps/api/recommendations/content/features.py`
- `apps/api/recommendations/content/similarity.py`
- `apps/api/recommendations/content/variants.py`
- `apps/api/recommendations/hybrid.py`
- `docs/methodology/protocol.json`
