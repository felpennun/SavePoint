---
quick_id: 260909-wgm
status: planned
phase: quick-documentation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - docs/verification/recommendation-architecture-2026-09-09.md
  - ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md
  - ideas-vault/Conceptos/Recomendador hibrido.md
autonomous: true
requirements:
  - REC-05
  - DOC-03
estimate:
  tokens: 8000
  raw_tokens: 8000
  tasks: 2
  confidence: low
must_haves:
  truths:
    - "La arquitectura canónica explica por qué Item-KNN, los recomendadores neuronales y otros modelos complejos quedan fuera del alcance metodológico actual sin afirmar que sean inferiores."
    - "hybrid-mmr-v1 está descrito con una fórmula reproducible y aparece explícitamente como propuesta futura no implementada."
    - "El vault vivo refleja la misma frontera entre lo implementado en Fase 4 y lo propuesto, con enlaces a la fuente canónica y a las notas relacionadas."
  artifacts:
    - path: "docs/verification/recommendation-architecture-2026-09-09.md"
      provides: "Decisión metodológica, límites de alcance y especificación propuesta de hybrid-mmr-v1"
      contains: "hybrid-mmr-v1"
    - path: "ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md"
      provides: "Estado de Fase 4 y propuesta futura enlazada"
      contains: "Propuesta"
    - path: "ideas-vault/Conceptos/Recomendador hibrido.md"
      provides: "Definición conceptual del híbrido actual y del híbrido con MMR propuesto"
      contains: "no implementado"
  key_links:
    - from: "docs/verification/recommendation-architecture-2026-09-09.md"
      to: "ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md"
      via: "enlace explícito desde la nota de fase a la arquitectura canónica"
      pattern: "recommendation-architecture-2026-09-09"
    - from: "docs/verification/recommendation-architecture-2026-09-09.md"
      to: "ideas-vault/Conceptos/Recomendador hibrido.md"
      via: "enlace explícito desde el concepto híbrido a la arquitectura canónica"
      pattern: "recommendation-architecture-2026-09-09"
---

<objective>
Documentar de forma auditable el límite metodológico de la Fase 4 y dejar definida, sin implementarla, la propuesta hybrid-mmr-v1.

Purpose: Preservar la validez, interpretabilidad y reproducibilidad de la comparación actual, separando con claridad los algoritmos aceptados de las líneas de trabajo no ejecutadas.
Output: Una sección canónica de arquitectura y dos actualizaciones coherentes del vault vivo, todas en español y sin cambios de código o infraestructura.
</objective>

<execution_context>
@.planning/STATE.md
@AGENTS.md
@CONVENTIONS.md
@docs/verification/recommendation-architecture-2026-09-09.md
@ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md
@ideas-vault/Conceptos/Recomendador hibrido.md
@ideas-vault/README.md
@ideas-vault/Conceptos/Vault vivo y sincronizacion.md
</execution_context>

<context>
La fuente canónica ya fija `cf-user-knn-v1` y `hybrid-weighted-cf-v1` como las dos variantes personales de la Fase 4. También fija `content-cbf-mmr-v1` y `content-cbf-mmr-pop-v1` como variantes MMR de contenido, con pool de 100 candidatas o 5K, `lambda = 0,80`, similitud coseno sobre `fs-v9` y publicación de hasta 20 resultados. La propuesta nueva debe combinar primero la relevancia híbrida existente y aplicar después la misma regla MMR, sin presentar ningún worker, estantería, registro, evaluación o resultado que todavía no exista.

El árbol de trabajo contiene cambios ajenos y las tres fuentes de documentación ya pueden tener modificaciones paralelas. Antes de editar, conservar el contenido vigente y modificar únicamente las secciones necesarias.

## Source coverage audit

| Fuente | Elementos que deben quedar cubiertos | Cobertura |
|---|---|---|
| GOAL | Decisión metodológica documentada y hybrid-mmr-v1 propuesto sin implementación | Tareas 1 y 2 |
| REQ | `REC-05` y `DOC-03`, identificados en las notas de Fase 4 y del recomendador híbrido | Tareas 1 y 2 |
| RESEARCH | Contrato canónico de variantes, pesos, elegibilidad, profundidad de presentación y MMR | Tarea 1; reflejado en tarea 2 |
| CONTEXT | Documentación-only, español, actualización canónica y del vault, sin código ni ejecución algorítmica | Tareas 1 y 2 |

No se han proporcionado ideas diferidas adicionales; la propuesta `hybrid-mmr-v1` se documenta como propuesta y no se convierte en alcance ejecutable.
</context>

<tasks>

<task type="tracer">
  <name>Task 1: Fijar en la arquitectura la frontera metodológica y hybrid-mmr-v1</name>
  <read_first>
    docs/verification/recommendation-architecture-2026-09-09.md
    .planning/STATE.md
    CONVENTIONS.md
  </read_first>
  <files>docs/verification/recommendation-architecture-2026-09-09.md</files>
  <action>Añadir, junto a las secciones de Fase 4 y de variantes MMR, una sección nueva en español con fecha 2026-09-09 que: (1) declare que la comparación actual implementa únicamente `cf-user-knn-v1` y `hybrid-weighted-cf-v1`, manteniendo intactas las variantes de contenido existentes; (2) documente por separado la exclusión metodológica de Item-KNN, de los recomendadores neuronales y de otros modelos complejos, razonando desde el corpus controlado y sintético, el uso de valoraciones explícitas, el protocolo congelado, la necesidad de interpretación y el control de grados de libertad de tuning; (3) aclare que la exclusión es una decisión de alcance y validez de la fase, no una afirmación de inferioridad algorítmica, y que no produce artefactos ejecutables ni resultados comparables en esta fase; y (4) especifique `hybrid-mmr-v1` como propuesta: primero calcula la relevancia de `hybrid-weighted-cf-v1` con `0,60 * content-cbf-weighted-v1 + 0,40 * cf-user-knn-v1`, conserva el fallback Weighted cuando falta señal colaborativa, después aplica MMR sobre las 100 mejores candidatas o `5 * K` cuando sea mayor, elige primero la mayor relevancia base y maximiza después `0,80 * relevancia - 0,20 * similitud_maxima` usando el coseno de `fs-v9`, con profundidad de presentación de 20. Compararla explícitamente con `content-cbf-mmr-v1`, `content-cbf-mmr-pop-v1` y `hybrid-weighted-cf-v1`, marcarla como propuesta/no implementada y preservar el contrato de corpus, exclusiones, semillas y evaluación para cualquier trabajo futuro. No editar código, modelos, workers, shelves, registros, snapshots, protocolo ni resultados.</action>
  <verify>
    <automated>powershell -NoProfile -Command "$p=Get-Content -Raw -LiteralPath 'docs/verification/recommendation-architecture-2026-09-09.md'; $patterns=@('Item-KNN','hybrid-mmr-v1','cf-user-knn-v1','hybrid-weighted-cf-v1','content-cbf-mmr-v1','content-cbf-mmr-pop-v1','0,60','0,40','5 * K','lambda = 0,80','fs-v9','no implementada'); foreach($x in $patterns){ if($p -notmatch [regex]::Escape($x)){ throw ('Falta el término requerido: '+$x) } }"</automated>
  </verify>
  <done>La arquitectura canónica contiene una decisión metodológica completa, distingue alcance de calidad algorítmica y describe `hybrid-mmr-v1` con los pesos, fallback, pool, fórmula MMR, similitud y profundidad correctos, siempre marcado como no implementado.</done>
</task>

<task type="auto">
  <name>Task 2: Sincronizar la decisión en las notas vivas del vault</name>
  <read_first>
    ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md
    ideas-vault/Conceptos/Recomendador hibrido.md
    ideas-vault/README.md
    ideas-vault/Conceptos/Vault vivo y sincronizacion.md
    docs/verification/recommendation-architecture-2026-09-09.md
  </read_first>
  <files>ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md, ideas-vault/Conceptos/Recomendador hibrido.md</files>
  <action>Actualizar únicamente los apartados afectados de ambas notas, en español y con fecha/estado. En `Fase 4 - Colaborativo e hibrido.md`, conservar la decisión aceptada de `cf-user-knn-v1` y `hybrid-weighted-cf-v1` y añadir una sección que resuma por qué Item-KNN, los modelos neuronales y otros modelos complejos no forman parte de la comparación actual, junto con `hybrid-mmr-v1` como `Propuesta` y `no implementado`. En `Recomendador hibrido.md`, mantener la definición aceptada del híbrido 0,60/0,40 y añadir la formulación propuesta de hybrid-mmr-v1 como composición posterior de esa relevancia y la regla MMR ya vigente; distinguirla de las variantes MMR de contenido y dejar claro que todavía no tiene worker, estantería, registro, snapshot ni resultados. Enlazar ambas notas con `docs/verification/recommendation-architecture-2026-09-09.md` y con sus notas relacionadas, siguiendo la política del vault, sin crear artefactos de implementación ni alterar notas paralelas fuera de los apartados necesarios.</action>
  <verify>
    <automated>powershell -NoProfile -Command "$files=@('ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md','ideas-vault/Conceptos/Recomendador hibrido.md'); foreach($f in $files){ $p=Get-Content -Raw -LiteralPath $f; foreach($x in @('Propuesta','hybrid-mmr-v1','no implementado','recommendation-architecture-2026-09-09')){ if($p -notmatch [regex]::Escape($x)){ throw ($f+' no contiene: '+$x) } } }"</automated>
  </verify>
  <done>Las dos notas del vault reflejan la misma frontera metodológica y la misma especificación propuesta, mantienen la implementación aceptada separada de la propuesta y enlazan la fuente canónica y las notas relacionadas.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Working tree → documentación canónica | Las ediciones documentales atraviesan un árbol de trabajo con cambios paralelos y deben preservar contenido ajeno. |
| Fuente canónica → vault vivo | El vault resume la decisión y puede desincronizarse o convertir una propuesta en una decisión aceptada si no se enlaza y etiqueta correctamente. |
| Documentación → lector de la tesis | Las afirmaciones metodológicas pueden interpretarse como resultados experimentales si no se separan alcance, implementación y propuesta. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| T-260909-WGM-01 | Tampering | Tres documentos objetivo | high | mitigate | Leer el estado actual, editar solo los apartados afectados y ejecutar `git diff --check` sobre los tres archivos. |
| T-260909-WGM-02 | Repudiation | Etiquetas de estado de `hybrid-mmr-v1` | medium | mitigate | Repetir en arquitectura y vault la fecha, el estado `Propuesta` y la marca `no implementado`, sin inventar workers, resultados o registros. |
| T-260909-WGM-03 | Information disclosure | Vault vivo y documentación de tesis | low | mitigate | Mantener la actualización limitada a prosa metodológica y no introducir secretos, credenciales, datos personales ni logs. |
</threat_model>

<verification>
- Las dos comprobaciones automáticas de las tareas pasan.
- `git diff --check -- docs/verification/recommendation-architecture-2026-09-09.md "ideas-vault/Fases/Fase 4 - Colaborativo e hibrido.md" "ideas-vault/Conceptos/Recomendador hibrido.md"` no informa errores de formato.
- La revisión final confirma que solo se modifican los tres documentos objetivo dentro de este plan y que ningún cambio de código, base de datos, worker, shelf, protocolo o ejecución algorítmica forma parte del trabajo.
</verification>

<success_criteria>
La decisión metodológica queda trazable y técnicamente defendible en la arquitectura canónica; `hybrid-mmr-v1` queda definido con precisión como propuesta no implementada; y las dos notas vivas del vault reflejan exactamente esa distinción y enlazan la fuente canónica.
</success_criteria>

<output>
Este plan solo describe el trabajo. La ejecución posterior actualizará los tres documentos y generará el SUMMARY del quick task según el flujo GSD; esta creación del plan no requiere commit.
</output>
