---
phase: "03"
slug: "explainable-content-recommenders-and-baseline-comparison"
status: complete
created: "2026-09-08"
---

# Investigación técnica de la Fase 3

## Resumen ejecutivo

La fase puede construirse sobre el harness ya cerrado en la Fase 2 sin reabrirlo. La
implementación debe crear una versión aditiva del contrato (`protocol_version: 2`), congelar
una instantánea de candidatos por ejecución y producir rankings, explicaciones y resultados
estadísticos con la misma semántica de candidato para todos los algoritmos. La comparación no
debe reducirse a precisión: se informarán también cobertura, concentración, diversidad
intra-lista y novedad, junto con incertidumbre y diferencias pareadas por usuario.

La investigación confirma el uso metodológico de SciPy, pero NumPy y SciPy no están todavía en
`pyproject.toml`. Su versión exacta, lockfile y legitimidad deben aprobarse antes de instalarse
en ejecución. Hasta entonces se mantiene la alternativa reversible de implementar las fórmulas
pequeñas con la biblioteca estándar, como ya ocurre en las métricas de la Fase 2.

## Estado de la base existente

- `apps/api/evaluation/protocol.py` valida el contrato congelado, hash y consumo de test.
- `apps/api/evaluation/splits.py` y `candidates.py` generan el conjunto común y el split
  leave-one-out por usuario.
- `apps/api/evaluation/runner.py` ya ejecuta algoritmos sobre el mismo conjunto y rechaza
  candidatos fuera del manifiesto.
- `apps/api/evaluation/metrics.py` contiene precision, recall, nDCG y MAP a mano.
- `apps/api/recommendations/baselines.py` contiene el baseline aleatorio reproducible.
- `apps/api/library/popularity.py` contiene el baseline de popularidad.
- `apps/api/recommendations/content/` contiene features, perfil, similitud, ranking, variantes y
  explicaciones del recomendador de contenido de la Fase 2.

Los planes deben extender estos puntos de entrada y conservar sus invariantes, no crear un
segundo runner ni permitir que cada ranker reconstruya candidatos.

## Universo de candidatos y fecha de corte

El catálogo gobernado completo sigue siendo navegable y utilizable para búsqueda, detalle y
colección. El universo del recomendador se restringe a obras gobernadas que cumplan al menos
una de estas condiciones:

1. `rating_count >= 1`; o
2. existe un `rating` válido, aunque el contador sea nulo.

Se excluyen obras consumidas por el usuario y obras cuya fecha de lanzamiento sea posterior a
la fecha de corte de la ejecución. La fecha de corte debe ser explícita en el manifiesto y no
debe depender de la hora local del servidor. La ordenación por nombre del catálogo es una
preocupación distinta y no hereda este filtro de recomendación.

El conjunto debe quedar materializado o hasheado por usuario, semilla y versión de corpus. La
misma lista, el mismo `heldout_work_id` y el mismo hash se pasan a cada algoritmo; una diferencia
de candidatos invalida la comparación.

## Señales de contenido y ranking

Las señales acordadas son rating global, géneros, saga, desarrollador, plataforma, número total
de valoraciones, novedad y tendencia/popularidad. Los planes deben separar la extracción de
features, la normalización, la combinación y la explicación.

### Representación recomendada

- Géneros, saga, desarrollador y plataformas: features categóricas binarias, con identificadores
  canónicos y orden estable.
- Texto disponible: TF-IDF solo si el campo y el idioma están gobernados; no introducir texto
  libre de procedencia desconocida en el snapshot experimental.
- Rating: normalizar a `[0, 1]` respecto de la escala IGDB; si se usa como señal directa, documentar
  que no equivale a una predicción de la valoración del usuario.
- Volumen de valoraciones: `log1p(rating_count)` normalizado dentro del snapshot para evitar que
  unas pocas obras dominen por escala.
- Tendencia/popularidad: usar el PopScore calculado desde datos disponibles y fechado; debe ser
  un snapshot versionado, no una llamada en tiempo real durante evaluación.
- Novedad: señal separada de tendencia. Para evaluación se recomienda la auto-información
  `-log2(p_i)`, donde `p_i` es la proporción de interacciones históricas del ítem en el snapshot.
  La novedad de producto y las novedades de lanzamiento se mantienen separadas.

Los pesos exactos no se fijan en esta investigación. Se deben congelar por configuración de
ejecución, registrar en el manifiesto y probar con una rejilla acotada que no use el test para
tuning. Una variante negativa puede restar una penalización de género cuando el usuario tiene
al menos tres juegos de ese género con valoración propia inferior a 3,5; debe aparecer como
variante identificable y no mezclarse silenciosamente con la variante positiva.

La explicación debe devolver únicamente señales realmente presentes: por ejemplo, género
compartido, saga compartida, desarrollador coincidente o plataforma coincidente. No debe afirmar
causalidad ni mostrar pesos internos no calibrados.

## Baselines y variantes

La comparación mínima de esta fase es:

- aleatorio con semilla y orden canónico;
- popularidad/PopScore con desempates deterministas;
- contenido de la Fase 2 como referencia compatible;
- variantes de contenido que incorporen de forma aislada las señales acordadas;
- variante con penalización negativa, solo si el dato de colección permite probarla.

El colaborativo pleno y el híbrido final quedan para las fases posteriores, aunque el contrato de
salida debe ser suficientemente común para añadirlos sin cambiar las métricas.

## Diseño experimental reproducible

Cada ejecución debe identificar como mínimo: commit, versión de corpus, hash del protocolo,
hash del manifiesto de candidatos, semillas, split, configuración del algoritmo, versión de
Python y dependencias. La generación de usuarios sintéticos y el ranking deben usar generadores
locales derivados de la semilla, nunca el estado global.

Se recomienda una batería multi-semilla con la misma familia de arquetipos y cohortes. El split
leave-one-out se realiza antes de ranking: el elemento retenido no puede entrar en el perfil ni
en el conjunto de vistos, y el algoritmo no puede leer el resultado esperado. Los usuarios sin
historial se enrutan al camino de cold start documentado, no se descartan sin contador.

La unidad de comparación estadística es el usuario evaluable. Para cada métrica y algoritmo se
conserva el valor por usuario antes de agregar medias o medianas. Así se pueden formar pares
`metric_algorithm_a[user] - metric_algorithm_b[user]` y evitar tratar cada juego recomendado como
una observación independiente.

## Métricas más allá de accuracy

Para `K` y usuario `u`, se conservan las métricas de la Fase 2 y se añaden:

- Cobertura de catálogo: `|union_u TopK(u)| / |C|`, donde `C` es el universo de candidatos del
  snapshot. Debe informarse también cobertura de predicción si algún algoritmo no puede puntuar
  todos los candidatos.
- Concentración: distribución de apariciones por obra en todas las listas. Se recomienda HHI:
  `sum_i (exposures_i / total_exposures)^2`; valores altos indican dependencia de pocas obras.
- Diversidad intra-lista (ILD): `1 - media(cosine_similarity(v_i, v_j))` sobre todos los pares
  distintos de una lista no vacía. Los vectores deben proceder del snapshot de contenido y los
  casos con menos de dos elementos deben quedar como no aplicables, no como cero silencioso.
- Novedad: media de `-log2(p_i)` en la lista, con `p_i` obtenido de interacciones de entrenamiento
  o del snapshot de popularidad definido antes de observar el test. Si no existe exposición o
  interacción válida, se informa como no estimable.

La cobertura y la concentración son métricas agregadas; ILD y novedad deben conservarse por
usuario para producir distribución e incertidumbre. Los resultados deben indicar denominadores,
listas vacías y valores no estimables.

Estas definiciones siguen la literatura de objetivos beyond-accuracy. El survey de Kaminskas y
Bridge recoge diversidad, serendipia, novedad y cobertura como objetivos distintos de accuracy
([ACM DOI 10.1145/2926720](https://doi.org/10.1145/2926720)). Una formulación publicada de ILD
usa la disimilitud coseno media y una de cobertura usa la unión de los Top-K sobre usuarios
([métricas y fórmulas de cobertura/ILD](https://pmc.ncbi.nlm.nih.gov/articles/PMC13123970/)).

## Incertidumbre y contraste estadístico

### Bootstrap

Para intervalos de confianza de una métrica agregada se recomienda remuestrear usuarios con
reemplazo, manteniendo juntas las observaciones de los algoritmos cuando la estadística sea
pareada (`paired=True`). SciPy documenta `scipy.stats.bootstrap`, sus métodos `percentile`,
`basic` y `BCa`, el uso de `rng` y el tratamiento de distribuciones degeneradas
([documentación oficial de bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)).

La configuración exacta —número de remuestras, método, nivel de confianza y semilla derivada—
debe fijarse en el protocolo v2. Si BCa produce NaN por una distribución degenerada, el runner
debe conservar la advertencia y aplicar el método alternativo explícitamente configurado, nunca
ocultarla ni sustituirla por cero.

### Friedman

Para comparar tres o más algoritmos sobre los mismos usuarios y métrica se puede usar
`scipy.stats.friedmanchisquare`. La documentación exige al menos tres muestras del mismo tamaño,
corrige empates y advierte que la aproximación chi-cuadrado es fiable con `n > 10` y más de seis
medidas repetidas ([documentación oficial de Friedman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.friedmanchisquare.html)).

En esta fase el test se debe tratar como contraste global de rangos por usuario, no como prueba
de superioridad causal. Si faltan usuarios para una comparación, se informa y no se rellena con
imputación silenciosa.

### Wilcoxon pareado

Para contrastes por parejas se recomienda Wilcoxon sobre las diferencias por usuario. SciPy
advierte que prueba simetría de las diferencias alrededor de cero, que ceros y empates alteran la
distribución exacta y que con ties/zeros el método exacto deja de ser exacto. Conviene calcular y
redondear las diferencias antes de llamar al test para evitar empates falsos por error de coma
flotante ([documentación oficial de Wilcoxon](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html)).

La configuración base será bilateral, con `zero_method` y método (`exact`, permutación o
asintótico) fijados en el protocolo. El resultado debe incluir `n`, estadístico, p-valor, método,
tratamiento de ceros y magnitud descriptiva de la diferencia.

### Holm

Cuando se realizan varias comparaciones por métrica/cohorte, se ordenan los p-valores y se aplica
la corrección step-down de Holm para controlar el family-wise error rate. La referencia primaria
es Holm, “A simple sequentially rejective multiple test procedure”, *Scandinavian Journal of
Statistics* 6 (1979), pp. 65–70, DOI
[10.2307/4615733](https://doi.org/10.2307/4615733). El algoritmo y la familia de hipótesis deben
quedar serializados, incluyendo el orden usado para desempatar p-valores.

Los p-valores no seleccionan por sí solos el mejor algoritmo: se informan junto con intervalos,
diferencias, métricas absolutas y limitaciones de los datos sintéticos.

## Ratings externos, PopScore y legalidad

- IGDB es la fuente real ya gobernada y con procedencia existente en el repositorio; sus datos
  experimentales deben congelarse en snapshots.
- RAWG ya se usó dentro del alcance ratificado y no se debe asumir cuota adicional. La segunda
  pasada queda como trabajo separado y no debe convertirse en una dependencia de la Fase 3.
- No se debe hacer scraping de Metacritic u OpenCritic. Solo se incorporarían fuentes con API,
  licencia, términos de redistribución y atribución comprobados y registrados en un ADR o
  evidencia equivalente.
- La documentación de Twitch/IGDB debe seguir siendo la fuente primaria para campos IGDB,
  identificadores y condiciones de uso ([referencia oficial de Twitch Developers](https://dev.twitch.tv/docs/api/reference/)).

PopScore puede alimentar la página de tendencia y el recomendador, pero debe tener fórmula,
fecha de corte, campos de entrada, normalización, snapshot y hash. Popularidad no debe sustituir
rating ni convertir un juego sin rating en una observación evaluable.

## Dependencias y decisiones pendientes

`numpy` y `scipy` no están declarados en el `pyproject.toml` actual. La incorporación requiere:

1. aprobación humana explícita;
2. versión exacta compatible con Python 3.13 y el entorno Docker;
3. actualización de `uv.lock`;
4. fila en `docs/verification/dependency-legitimacy.md`, `scripts/check-dependencies.ps1` y
   `docs/methodology/agent-ledger.jsonl`;
5. smoke test numérico y prueba de instalación limpia.

La alternativa sin dependencia se conserva para métricas pequeñas, pero no debe implementarse en
paralelo con dos fórmulas divergentes: una sola función canónica debe ser la fuente del artefacto.

## Seguridad e integridad académica

Los planes deben incluir un bloque de amenaza por tarea relevante. Como mínimo:

- validar tipos, rangos, versión de protocolo y hashes antes de consumir un artefacto;
- rechazar resultados con candidatos fuera del manifiesto, duplicados inesperados o datos de
  test filtrados al perfil;
- limitar remuestras, tamaño de listas y cardinalidad de entrada para evitar agotamiento de
  recursos;
- escribir solo nombres de secretos y nunca valores en logs, JSON o issues;
- usar rutas de artefacto controladas y nombres derivados de identificadores validados;
- marcar explícitamente ejecuciones incompletas, degeneradas o no comparables como no válidas;
- separar resultados sintéticos de datos de producción y conservar procedencia/licencia.

## Arquitectura de validación Nyquist

Cada plan debe declarar pruebas que fallen de forma observable:

- protocolo v2: hash, versión y rechazo de split consumido o configuración fuera de límites;
- candidatos: igualdad byte a byte entre algoritmos, filtro `rating_count >= 1 OR valid rating`,
  exclusión de futuros y ausencia de vistos;
- features/ranking: determinismo por semilla, límites, desempates y explicación fundada;
- métricas: casos manuales con denominadores, listas vacías, empates, ceros y distribución
  degenerada;
- estadística: bootstrap pareado reproducible, Friedman con tamaños inválidos rechazados,
  Wilcoxon con diferencias redondeadas y Holm monotónico;
- runner: artefacto completo, fingerprint de entrada y estado fail-closed;
- web: `work_id` y orden score-desc del payload coinciden, sin sort cliente ni fixtures; estados
  loading/empty/error/parcial y tamaños definidos en `03-UI-SPEC.md`.

## Decisiones para el planner

1. Mantener el catálogo navegable completo y separar estrictamente el universo evaluable.
2. Crear `protocol_version: 2` como artefacto nuevo y no modificar el JSON firmado de Fase 2.
3. Hacer explícitos los parámetros de señales y dejarlos congelados en cada run; los pesos
   concretos requieren una decisión posterior informada por pruebas de sensibilidad.
4. Comparar accuracy, cobertura, concentración, ILD y novedad con resultados por usuario y
   contrastes estadísticos corregidos.
5. No instalar todavía NumPy/SciPy: convertirlo en checkpoint de ejecución con evidencia y lock.
6. Consumir en la web el ranking real y sus razones; el dashboard y los selectores de experimentos
   siguen diferidos a la Fase 7.

## Fuentes primarias y técnicas consultadas

- [SciPy `bootstrap`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).
- [SciPy `friedmanchisquare`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.friedmanchisquare.html).
- [SciPy `wilcoxon`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).
- [Holm (1979), DOI 10.2307/4615733](https://doi.org/10.2307/4615733).
- [Kaminskas y Bridge, ACM DOI 10.1145/2926720](https://doi.org/10.1145/2926720).
- [Ejemplo publicado de ILD, cobertura y novedad](https://pmc.ncbi.nlm.nih.gov/articles/PMC13123970/).
- [Twitch Developers / IGDB API reference](https://dev.twitch.tv/docs/api/reference/).

## RESEARCH COMPLETE
