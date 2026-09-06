# ADR-006: IGDB como fuente del catálogo a escala real, y entrega de portadas

- **Estado:** Aceptado
- **Fecha:** 2026-09-05
- **Autor de la decisión:** Felipe (`requests 2.34.2 aprobado` — aprobación explícita de la dependencia y del gate de decisión de fuente)
- **Redacción / evidencia:** agente de ejecución; la verificación automática (`scripts/verify-igdb-adr.ps1`, `scripts/verify-igdb-probe.ps1`, `scripts/check-dependencies.ps1`) y la decisión humana se mantienen separadas.
- **Fase / Plan:** 01.1 / 01.1-01 Tarea 3 · **Requisito:** DATA-04 (también desbloquea el trabajo de catálogo de CAT-02, REC-10) · **Issue de GitHub:** #7
- **Sustituye, para el catálogo a escala real:** la posición "sin proveedor en runtime, solo Wikidata" de [ADR-003](ADR-003-data-sources.md) — ver *Consecuencias › Relación con ADR-003*.

## Contexto

La Fase 1 entregó un snapshot curado de 150 juegos de Wikidata ([ADR-003](ADR-003-data-sources.md)). La Fase 01.1 hace crecer el catálogo a escala de producto real (D-01, D-05). DATA-04 exige que la fuente de enriquecimiento se seleccione mediante una **comparación documentada de cobertura, plataformas, licencia, atribución, cuotas, estabilidad y coste**, y el autor pidió que esa comparación quedara registrada para la tesis.

La comparación de abajo se apoya en un sondeo autenticado en vivo de la API v4 de IGDB — [`docs/verification/igdb-api-probe.md`](../verification/igdb-api-probe.md), sondeo ejecutado el **2026-09-05T14:56:27Z**. Las filas de RAWG y de Wikidata-escalado provienen de fuentes secundarias y de la experiencia directa de la Fase 1, y se etiquetan como tales.

## Alternativas consideradas

Tres candidatos: **IGDB** (Twitch/Amazon), **RAWG** (rawg.io) y **scaled Wikidata** (extender la tubería SPARQL de la Fase 1).

### Comparación DATA-04

| Eje | IGDB (elegido) | RAWG | Wikidata escalado |
|---|---|---|---|
| **Cobertura** | 374,555 entradas de juego totales; **312,418** juegos primarios (`game_type = 0`). 336,568 portadas, 23 géneros, 220 plataformas. Medido en vivo, 2026-09-05. | ~350,000–500,000 juegos declarados (fuente secundaria, no sondeada). Amplio, incluye metadatos de tienda. | Escaso y desigual para juegos: sin modelado fiable de género/plataforma, arte de portada solo vía entradas por archivo de Wikimedia Commons. La Fase 1 necesitó curación manual para llegar a 150 filas usables. |
| **Plataformas** | Entidad `platforms` de primera clase (220 filas), expandible por punto como `platforms.name`; confirmado en vivo. | Metadatos de plataforma de primera clase (fuente secundaria). | Datos de plataforma presentes pero inconsistentes; requiere subconsultas y normalización a medida (experiencia de la Fase 1). |
| **Licencia** | La API es "free for both non-commercial and commercial projects", regida por el **Twitch Developer Services Agreement**; los ejemplos de código son "Program Materials". Fuentes textuales en la evidencia del sondeo §5. | Tier gratuito para uso no comercial bajo los ToS de la API de RAWG; el uso comercial exige un plan de pago y un acuerdo de reparto de ingresos/atribución (fuente secundaria). | Los datos estructurados son **CC0** (dominio público) — la licencia más limpia de las tres. Los medios de Commons son por archivo (CC-BY / CC-BY-SA / PD), requieren revisión individual — ver ADR-003. |
| **Atribución** | IGDB espera "fair attribution … visible to your users and located in a static location". SavePoint añade atribución estática y visible a IGDB.com (página de fuentes + pie) pese a ser no comercial. | Atribución obligatoria **y un backlink a rawg.io** en cada página que use los datos (fuente secundaria) — más pesada y prescriptiva que la de IGDB. | Los datos estructurados CC0 no necesitan atribución; los medios de Commons requieren crédito por archivo de autor + licencia (modelo de ADR-003). |
| **Cuotas** | **Sin cuota mensual de peticiones.** Límite documentado: **4 requests/second, 8 concurrent open requests**; `429` al exceder; multiquery limitada a 10 subconsultas (todo observado en vivo). No devuelve cabeceras de rate-limit. | **20,000 requests/month** en el tier gratuito (fuente secundaria) — un techo mensual duro que limitaría una importación de varios cientos de miles de filas. | Sin cuota, sin auth (endpoint SPARQL público), pero sujeto a timeouts del endpoint y throttling por uso razonable en consultas grandes. |
| **Estabilidad** | Respaldado por Twitch/Amazon; API v4 estable desde la migración a Twitch de 2020; vida del token OAuth ~57 días observada. El dataset muta durante pulls largos → paginación por cursor de id requerida (RESEARCH.md Patrón 1). | Operador independiente (rawg.io); organización más pequeña, mayor riesgo de discontinuación/cambio de precios (fuente secundaria). | Wikidata/Wikimedia es muy estable institucionalmente, pero los datos de *juegos* dependen de edición voluntaria — la cobertura y el modelado cambian de forma impredecible y no son estables para importar. |
| **Coste** | **0 €.** Gratis para este uso; la nueva dependencia de Python es solo `requests==2.34.2`. | 0 € dentro de 20k req/mes; una importación de catálogo completo probablemente excedería el tier gratuito y requeriría un plan de pago. | 0 €. |

## Decisión

1. **Adoptar IGDB v4 como la fuente del catálogo a escala real** (D-05). Es el único candidato que combina cobertura real, modelado de primera clase de género/plataforma/portada, **sin cuota mensual**, coste cero y un permiso publicado por el operador para almacenar y servir los datos — a cambio de una obligación de atribución más pesada que la de Wikidata CC0 y de una licencia que es un acuerdo en vez de una dedicación al dominio público.
2. **Frontera de categoría elegible (D-06):** el catálogo de SavePoint importa IGDB **`game_type = 0` (juegos principales) — 312,418 filas en el momento del sondeo**. `game_type` 1–14 (DLC, expansion, bundle, standalone_expansion, mod, episode, season, remake, remaster, expanded_game, port, fork, pack, update) son no primarios y quedan **excluidos** del catálogo primario, coherente con el precedente existente `RelatedContent` / `is_dlc` en `apps/api/catalogue/models.py`. El Plan 01.1-02 vuelve a medir el conteo elegible inmediatamente antes de importar y debe importar ≥ 90% de esa medición fresca y **> 100,000 obras primarias**.
3. **Regla de entrega / almacenamiento de portadas (D-06):** las portadas se sirven por **hotlink**, no se replican, en la Fase 01.1. Se construyen las URL como `https://images.igdb.com/igdb/image/upload/t_{size}/{hash}.jpg` donde `{hash}` es `cover.image_id` (p. ej. `t_cover_big`, `t_cover_small`, añadir `_2x` para retina). IGDB documenta una ventana de retención de 30 días para imágenes eliminadas/reemplazadas — aceptable para hotlinking, y la razón por la que se difiere el mirroring local (heredaría esa carga de reconciliación y se apoyaría con más fuerza en el permiso de almacenamiento para imágenes "Twitch Content"). Una portada ausente o que falla cae de vuelta al **placeholder de primera parte de la Fase 1** (D-06, y D-07 de `01-CONTEXT.md`). El mirroring local de portadas solo se revisa si la fiabilidad del hotlink resulta inadecuada.
4. **Regla de caché / redistribución:** SavePoint almacena metadatos estructurados de IGDB (juegos, géneros, plataformas) en su propia base de datos PostgreSQL y los sirve a sus propios usuarios finales. **No** re-sindica ni redistribuye el dataset en bloque — sin dump público de datos, sin compartir datos con terceros, sin una API que re-sirva filas de IGDB en bloque. El permiso escrito operativo de referencia es la FAQ de la documentación de la API de IGDB (Q3 "we prefer if you store and serve the data to your end users", Q5 "you are allowed to keep all data you retrieve"), que actúa como la "prior written authorization … otherwise" contemplada por el carve-out de almacenamiento del Twitch Developer Services Agreement. Fuentes textuales: [`igdb-api-probe.md`](../verification/igdb-api-probe.md) §5.
5. **Atribución:** se muestra una atribución estática y visible "Data from IGDB.com" en la página de fuentes y en el pie del sitio.
6. **Preservar el corpus offline de la Fase 1:** el snapshot de Wikidata, sus manifiestos, `docs/verification/catalogue-freeze.md` y la congelación de ADR-003 se **conservan sin cambios**. El corpus CC0 de 150 juegos y su revisión de Commons por asset siguen siendo evidencia válida y citable; la importación de IGDB es aditiva y se indexa por `SourceRecord(source="igdb", source_id=<id de igdb>)` junto a las filas existentes `source="wikidata"`. `CAT-06` / `OPS-03` siguen vigentes: no se llama a ningún proveedor en tiempo de petición — el acceso a IGDB queda confinado al comando de gestión offline y reanudable.
7. **Dependencia de cliente HTTP:** añadir exactamente **`requests==2.34.2`** (Apache-2.0, `requires-python >=3.10`, verificada en PyPI — release real de `psf/requests` subida el 2026-05-14, no yanked) vía `uv add`, fijada en `pyproject.toml` y `uv.lock`. Su fila de dependencia aprobada se añade a `scripts/check-dependencies.ps1` y a `docs/verification/dependency-legitimacy.md`. **Do not** add `django-allauth` ni `dj-rest-auth` — en su lugar se extiende la app `accounts` hecha a mano (RESEARCH.md *Alternatives Considered*).

## Evidencia y fuentes

- **Sondeo autenticado:** [`docs/verification/igdb-api-probe.md`](../verification/igdb-api-probe.md) — sondeo ejecutado el 2026-09-05T14:56:27Z; conteos, confirmación de nombres de campo, comportamiento de rate-limit y citas textuales de los términos.
- **Fuentes primarias de términos:** `https://api-docs.igdb.com/` (Getting Started, License, Business FAQ, Images); `https://legal.twitch.com/legal/developer-agreement/` (Program Materials — almacenamiento/redistribución).
- **Dependencia:** `https://pypi.org/project/requests/2.34.2/` — Apache-2.0, `requires-python >=3.10`, wheel + sdist subidos el 2026-05-14, `yanked: false`; repositorio de origen `github.com/psf/requests`.
- **Investigación:** [`.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-RESEARCH.md`](../../.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-RESEARCH.md) — los supuestos A1 (sin cuota mensual) y A3 (nombres de campo) quedan ahora **confirmados** por el sondeo; A5 (tamaño del catálogo) se mide en 374,555 total / 312,418 primarios.
- Las filas de RAWG y de Wikidata-escalado son de fuente secundaria / experiencia directa de la Fase 1, explícitamente no sondeadas de forma independiente en este plan.

## Consecuencias

**Positivas**
- El catálogo a escala real (100k+ obras primarias) pasa a ser alcanzable a coste cero y sin techo mensual.
- Los datos de género y plataforma de primera clase desbloquean el filtrado/ordenación de CAT-02 y el heurístico de géneros de REC-10.
- El permiso de almacenar + servir es explícito en la propia documentación del operador, registrado textualmente para defensibilidad en la tesis (DATA-08).

**Negativas / límites**
- La licencia es un **acuerdo** (Twitch DSA), no una dedicación al dominio público; puede cambiar, y la reconciliación FAQ-vs-DSA del punto 4 es una lectura razonada, no asesoramiento legal.
- La atribución es ahora una obligación continua sobre la interfaz.
- La importación debe respetar 4 req/s + 8 concurrentes y ser reanudable a lo largo de una ejecución larga (RESEARCH.md Patrones 1–2).
- Las portadas por hotlink mueven la disponibilidad de imagen a un CDN de terceros fuera del control de SavePoint; la ventana de eliminación de 30 días significa que algunas portadas darán 404 con el tiempo y caerán al placeholder.
- Una dependencia de runtime nueva (`requests`) más su árbol transitivo (`certifi`, `charset-normalizer`, `idna`, `urllib3`).

**Relación con ADR-003**
La congelación de Wikidata de ADR-003 y su regla "sin proveedor en runtime" siguen vigentes para el corpus de la Fase 1 y para el comportamiento en tiempo de petición. ADR-006 acota el rechazo de la alternativa 2 de ADR-003 sobre "RAWG/IGDB … credentials, quotas, terms and drift": esos riesgos ahora están medidos y mitigados (sin cuota, términos registrados, importación por cursor de id, acceso solo offline) en vez de evitados, específicamente para el catálogo a escala real que la Fase 01.1 requiere.

## Reversibilidad

El corpus de IGDB se indexa por `SourceRecord(source="igdb", …)` y puede eliminarse sin tocar las filas de Wikidata. Cambiar de fuente más adelante implica un nuevo fetch, una nueva congelación y una nueva decisión humana. El pin de `requests` es reversible vía `uv remove`.

## Aprobación y revisión

**Aceptado.** Cualquier cambio en la fuente, en la frontera de categoría elegible, en la regla de entrega de portadas o en el pin de `requests` invalida esta decisión y requiere un nuevo gate de decisión humana y una nueva ejecución de los scripts de verificación.
