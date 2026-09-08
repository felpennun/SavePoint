---
phase: "03"
slug: "explainable-content-recommenders-and-baseline-comparison"
status: complete
created: "2026-09-08"
---

# Mapa de patrones reutilizables de la Fase 3

Este mapa se limita a los módulos que la fase debe extender. No es una auditoría general del
repositorio ni reabre decisiones de la Fase 2.

## Evaluación y artefactos

| Necesidad de Fase 3 | Análogo existente | Patrón que se debe conservar |
|---|---|---|
| Contrato v2 | `apps/api/evaluation/protocol.py` | Dataclass tipada, parser con límites, hash canónico, rechazo de versión/configuración inválida y consumo de test fail-closed. |
| Candidatos comunes | `apps/api/evaluation/candidates.py`, `splits.py` | Construir una vez por usuario/semilla/corpus; conservar `candidate_manifest_sha256`; excluir vistos y held-out antes del ranking. |
| Ejecución | `apps/api/evaluation/runner.py` | Registro explícito de algoritmos, mismo payload de candidatos, comprobación de IDs devueltos y manifiesto con metadatos de ejecución. |
| Métricas | `apps/api/evaluation/metrics.py` y `tests/test_metrics.py` | Funciones puras, entradas ordenadas, casos límite explícitos y tests con valores pequeños calculados manualmente. |
| Comandos reproducibles | `apps/api/evaluation/management/commands/run_evaluation.py` y `generate_synthetic_users.py` | Flags explícitos, corpus/versionado en la salida, errores visibles y ningún cálculo implícito en una vista HTTP. |

## Recomendación de contenido y baselines

| Necesidad | Análogo existente | Patrón que se debe conservar |
|---|---|---|
| Ranking aleatorio | `apps/api/recommendations/baselines.py` | Orden canónico antes de usar semilla; fingerprint de entrada y salida; DTO estable. |
| Popularidad | `apps/api/library/popularity.py` | Snapshot/procedencia, desempate determinista y separación entre rating, volumen y popularidad. |
| Features | `apps/api/recommendations/content/features.py` | Vectores reproducibles por `FEATURE_SET_VERSION`, campos canónicos y caché `WorkFeatureVector`. |
| Perfil | `apps/api/recommendations/content/profile.py` | Derivar perfil solo de la colección permitida, ponderar estados definidos y no leer el held-out. |
| Similitud y ranking | `apps/api/recommendations/content/similarity.py`, `rank.py`, `variants.py` | Registro de variantes por ID, componentes separados, orden estable y parámetros serializables. |
| Explicación | `apps/api/recommendations/content/explain.py` | Razón determinista basada solo en señales presentes; no inventar metadatos ni exponer pesos internos sin escala de producto. |

## Datos y procedencia

- `apps/api/catalogue/corpus.py` es la fuente de scoping gobernado; los planes deben reutilizar
  sus querysets para no mezclar obras fuera del corpus.
- `apps/api/catalogue/models.py` contiene `GameWork`, `CorpusVersion` y snapshots de rating;
  los cambios de procedencia requieren migración y tests específicos.
- `apps/api/catalogue/management/commands/govern_corpus.py` y
  `snapshot_corpus_ratings.py` muestran el patrón de comandos one-shot con versión y evidencia.
- `apps/api/library/models.py` y `library/views.py` son la fuente de estado/valoración de la
  colección; el recomendador debe consultar el servicio o queryset existente, no copiar datos a
  una tabla paralela sin decisión documentada.

## Web y traducciones

- La superficie vigente es `apps/web/app/[locale]/recommendations/page.tsx`.
- Los componentes reutilizables son `ContentRecommendationShelf.tsx`,
  `RecommendationShelf.tsx`, `RecommendationStrip.tsx`, `GameCard.tsx`, `CoverImage.tsx` y
  `ScorePill.tsx`; el plan debe mantener carátulas de tamaño uniforme y no ordenar en cliente.
- `apps/web/components/AppShell.tsx` y `LanguageToggle.tsx` son el patrón de navegación e i18n.
- El frontend debe consumir el DTO real mediante `apps/web/lib/api.ts`, conservar estados de
  loading/empty/error/parcial y mantener el orden recibido. Las claves ES/EN se prueban con la
  suite existente; no se introducen textos hardcodeados en el componente.
- `03-UI-SPEC.md` es el contrato visual aprobado: secciones con título, separación de 48 px,
  tarjetas de 120×288 px, track con overflow propio y sin dashboard experimental.

## Pruebas y seguridad

- Tests backend siguen `apps/api/*/tests/test_*.py`, fixtures Django y comandos Docker con
  PostgreSQL.
- Tests frontend siguen Vitest para funciones/componentes y Playwright para la ruta real; las
  pruebas deben consultar por roles y nombres accesibles.
- Los planes han de incluir `<threat_model>` por tarea relevante: validación de hashes/versiones,
  candidato común, ausencia de leakage, límites de remuestras, ausencia de secretos y rechazo de
  artefactos incompletos.
- Los comandos de verificación deben tener un `<fails_when>` inmediatamente después y describir
  una señal observable.

## Rutas que el planner debe verificar como git-tracked

`apps/api/evaluation/protocol.py`, `candidates.py`, `metrics.py`, `runner.py`, `splits.py`,
`apps/api/evaluation/tests/`, `apps/api/evaluation/management/commands/`,
`apps/api/recommendations/baselines.py`, `apps/api/recommendations/content/`,
`apps/api/recommendations/tests/`, `apps/api/library/popularity.py`,
`apps/web/app/[locale]/recommendations/page.tsx`, `apps/web/components/` y
`apps/web/lib/api.ts`. Toda ruta heredada en un PLAN debe confirmarse con `git ls-files`; nunca
se debe escribir en espejos runtime o rutas ignoradas.

## PATTERNS COMPLETE
