# Firma de la Fase 2: corpus gobernado y primera evaluación

**Estado: ACEPTADA** por Felipe (autor), 2026-09-08, contra el commit `e10db0ead9c29fdc9851210d55b55d657717c4dd`.

Este documento registra la aprobación humana de la Fase 2 después de completar sus trece planes, la verificación metodológica, la auditoría de seguridad y la revisión del primer artefacto de evaluación reproducible.

## Alcance aceptado

- Corpus gobernado y versionado, con checksum, procedencia e informe de calidad.
- Ratings externos aislados de los datos vivos del producto mediante snapshots inmutables.
- Búsqueda tolerante, filtros múltiples y superficies de catálogo, ficha y recomendaciones actualizadas.
- Protocolo de evaluación congelado antes de la comparación, con split, candidatos, exclusiones, métricas y semillas trazables.
- Usuarios sintéticos reproducibles, baseline aleatorio y de popularidad, y tres variantes del recomendador de contenido.
- Explicaciones deterministas, exclusión de obras ya consumidas y estrategia explícita de arranque en frío.
- Evidencia académica y controles sobre simulación, leakage, alucinaciones, sesgo, errores y exposición de información.

## Decisión sobre el resultado experimental

El autor acepta como resultado válido de esta primera simulación que los cinco algoritmos obtuvieran `nDCG@10 = 0.000`. No se interpreta como igualdad general de calidad ni como evidencia sobre usuarios reales. Se conserva sin repetir el split de test ni ajustar el protocolo después de observarlo.

La explicación aceptada es que la evaluación usa un único positivo retenido por usuario, 26 usuarios sintéticos elegibles y conjuntos de aproximadamente 27.000 candidatos frente a un corte máximo de 20 resultados. La Fase 3 ampliará el análisis con varias semillas, cohortes, cobertura, diversidad, novedad, incertidumbre y pruebas estadísticas, manteniendo intacto este primer artefacto.

## Evidencia revisada

- `.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/02-VERIFICATION.md`.
- `docs/verification/evaluation-run-first.artifact.json` y `evaluation-run-first.md`.
- `docs/methodology/protocol.json` y `evaluation-protocol.md`.
- `.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/02-SECURITY.md`.
- `docs/verification/repo-security-audit-2026-09-08.md`.

## Limitaciones aceptadas

1. La población es sintética y no permite generalizar a usuarios reales.
2. Solo 26 de los 40 usuarios solicitados tenían un positivo elegible para leave-one-out.
3. La densidad de ratings externos condiciona el universo evaluable.
4. La primera ejecución no estima todavía variabilidad entre semillas ni significación estadística.
5. La ausencia de CI y la protección de `main` no disponible en el plan actual de GitHub son seguimientos no bloqueantes registrados en la Issue #31.

## Veredicto

Los seis criterios de éxito de la Fase 2 quedan aceptados. La fase se cierra sin ocultar el resultado nulo ni sus amenazas a la validez y queda habilitada la planificación de la Fase 3.

---

*Firmado por Felipe, autor del TFG, el 2026-09-08.*

*Commit revisado: `e10db0ead9c29fdc9851210d55b55d657717c4dd`.*
